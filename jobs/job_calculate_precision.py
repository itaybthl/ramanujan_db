from __future__ import annotations
from logging import getLogger
from logging.config import fileConfig
import numpy as np
import mpmath as mp
from sympy import Poly, Symbol
from decimal import Decimal, getcontext
from collections import Counter
from dataclasses import dataclass, asdict
from enum import Enum
from traceback import format_exc
from time import time
from os import getpid
from pcf import PCF

from db import ramanujan_db
from db import models
from tools.constants_generator import Constants

from sqlalchemy.sql.expression import func

getcontext().prec = 2000
mp.mp.dps = 2000

EXECUTE_NEEDS_ARGS = True

BULK_SIZE = 5000
DEPTH = 1200
FR_THRESHOLD = 0.1
CALC_JUMP = 200
REDUCE_JUMP = 100
PRECISION_FILTER = 50
LOGGER_NAME = 'job_logger'

FILTERS = [models.Constant.value == None]

# TODO two feature upgrades:
# 1: "refining" mode that repeatedly doubles precision (or depth) for constants with existing value
# 2: allow calculating NamedConstants as well (mostly intended for refining them)
#SUPPORTED_TYPES = ['Named', 'PcfCanonical']
SUPPORTED_TYPES = ['PcfCanonical']

def get_filters(const_type, balanced_only):
    filters = FILTERS
    if const_type == 'PcfCanonical':
        if balanced_only:
            filters += [func.cardinality(models.PcfCanonicalConstant.p) == func.cardinality(models.PcfCanonicalConstant.q)]
        # the old code used to do something similar to num_denom_factor in job_generate_cfs_random,
        # and while it's possible to implement given the canonical form, it's way clunkier to do as a filter...

    return filters

def check_convergence(p, q, fr_list) -> models.PcfConvergence:
    val = p / q
    if mp.almosteq(p, 0) or mp.almosteq(val, 0):
        getLogger(LOGGER_NAME).debug(f'Checking rational that is too close to 0 p={p},q={q}')
        return models.PcfConvergence.RATIONAL
    
    if mp.pslq([val, 1], tol=mp.power(10, -100)):
        return models.PcfConvergence.RATIONAL
    
    if any(abs(fr_list[i + 1] - fr_list[i]) < FR_THRESHOLD for i in range(len(fr_list) - 1)):
        return models.PcfConvergence.FR
    
    if any(abs(fr_list[i + 1] - fr_list[i + 2]) > abs(fr_list[i] - fr_list[i + 1]) for i in range(len(fr_list) - 2)):
        return models.PcfConvergence.NO_FR

    return models.PcfConvergence.INDETERMINATE_FR

class PcfCalc:
    a: Poly
    b: Poly
    mat: mp.matrix
    depth: int
    
    def __init__(self: PcfCalc, a: Poly, b: Poly, prev: List[int] or None=None, depth: int = 0):
        self.a = a
        self.b = b
        #self.reduction = 1 # used to exist in the old code, not sure what use we have for this
        self.mat = mp.matrix([prev[0:2], prev[2:4]] if prev else [[mp.polyval(a, 0), 1], [1, 0]])
        self.depth = depth

    def refine(self: PcfCalc):
        # TODO upgrade to mergesort-like binary tree scheme?
        self.depth += 1
        mat = mp.matrix([[self.a(self.depth), self.b(self.depth)], [1, 0]]) * self.mat
        # the old code only did this gcd step every REDUCE_JUMP steps, for now I
        # decided to do it every step to see how much of a performance hit it really is
        gcd = np.gcd.reduce(self.mat)
        #self.reduction *= gcd
        self.mat = mat / mp.mpf(gcd)

    @property
    def value(self: PcfCalc):
        return self.mat[0,0] / self.mat[0,1]

    @property
    def precision(self: PcfCalc):
        return mp.floor(-mp.log10(abs(self.value() - self.mat[1,0] / self.mat[1,1]))) if all(self.mat[:,1]) else -mp.inf

def update_PcfCanonical(const, depth, pcf_override=None):
    canonical = pcf_override if pcf_override else (const.p, const.q)
    pcf = PCF.from_canonical_form(canonical)
    calc = PcfCalc(pcf.a, pcf.b, pcf.last_matrix)
    
    fr_list = []
    for n in range(1, depth):
        calc.refine()
        if n % CALC_JUMP == 0:
            # yes this calculation converges as i -> inf if there's factorial
            # reduction, ask me for proof if you can't figure out the details. (Itay)
            # (though as far as i could tell, the reverse direction might not be necessarily true)
            fr_list.append(mp.log(mp.mpf(np.gcd(*calc.mat[0,:]))) / mp.mpf(n) + pcf.a.degree() * (1 - mp.log(n)))
    
    prec = calc.precision
    if prec == -mp.inf:
        getLogger(LOGGER_NAME).debug(f'pcf {canonical} has continuant denominator zero')
        const.base.precision = 0 # value column stays null!
        const.convergence = models.PcfConvergence.ZERO_DENOM.value
    else:
        value = calc.value
        precision = 2000 if prec == mp.inf else int(prec)
        if value and mp.almosteq(0, value):
            getLogger(LOGGER_NAME).debug('Rounding to 0')
            value = 0
        const.base.value = Decimal(value)
        const.base.precision = precision
        const.convergence = check_convergence(calc.mat[0,0], calc.mat[0,1], fr_list).value
    const.last_matrix = [int(x) for x in calc.mat]
    const.depth = depth
    return const

def update(const, const_type, depth):
    if const_type == 'PcfCanonical':
        return update_PcfCanonical(const, depth)

class PrecisionType(Enum):
    HIGH_PREC = 1
    LOW_PREC = 2
    NO_PREC = 3

def get_precision(const, const_type):
    if const_type == 'PcfCanonical':
        if const.convergence == models.PcfConvergence.ZERO_DENOM.value:
            return PrecisionType.NO_PREC
    
    if const.base.precision >= PRECISION_FILTER:
        getLogger(LOGGER_NAME).debug(f'constant {const.const_id} has high precision: {const.base.precision}')
        return PrecisionType.HIGH_PREC
    
    getLogger(LOGGER_NAME).debug(f'constant {const.const_id} has low precision: {const.base.precision}')
    return PrecisionType.LOW_PREC


def execute_job(consts, bulk=0, const_type='PcfCanonical', balanced_only=True):
    fileConfig('logging.config', defaults={'log_filename': f'precision_worker_{getpid()}'})
    prec_types = Counter()
    
    updated = []
    for const in consts:
        getLogger(LOGGER_NAME).debug(f'calculating for {const.const_id}')
        previous_calc = None
        if const.value is not None:
            getLogger(LOGGER_NAME).debug(f'{const.const_id} has old value')
        start_time = time()
        updated += [update(const, const_type, DEPTH)]
        getLogger(LOGGER_NAME).debug(f'calculation of {const.const_id}, took {time() - start_time} seconds')
        prec_types[get_precision(const, const_type)] += 1
        #val = 0 if val == mp.inf else val
        #results.append(models.CfPrecision(cf_id=cf.cf_id, depth=real_depth, precision=precision, value=val, previous_calc=calc_data, general_data=general_data))
    
    getLogger(LOGGER_NAME).info('Done calculation')
    return updated, prec_types

def get_model(const_type):
    if const_type not in SUPPORTED_TYPES:
        msg = f'Unsupported constant type {const_type}! Must be one of {SUPPORTED_TYPES}.'
        print(msg)
        getLogger(LOGGER_NAME).error(msg)
        return None
    return eval(f'models.{const_type}Constant')

def run_query(bulk=0, const_type='PcfCanonical', balanced_only=True):
    fileConfig('logging.config', defaults={'log_filename': 'precision_manager'})
    model = get_model(const_type)
    if not model:
        return []

    bulk = bulk if bulk else BULK_SIZE
    getLogger(LOGGER_NAME).info(f'starting to calculate precision for {bulk} cfs')

    db_handle = ramanujan_db.RamanujanDB()
    queried_data = db_handle.session.query(model).filter(*get_filters(const_type, balanced_only)).limit(bulk).all()
    db_handle.session.close()
    getLogger(LOGGER_NAME).info(f'size of batch is {len(queried_data)}')
    return queried_data

def summarize_results(results):
    # ok so fun fact: querying a db_handle, closing it, changing the queried data and then committing
    # it in a new db_handle updates the db correctly. Creating new rows with copies of the original
    # data and then trying to commit them the same way doesn't work. Why? I don't know, and
    # at this point I'm not going to question it, because that's the reason this code works.
    db_handle = ramanujan_db.RamanujanDB()
    agg_prec_types = Counter()
    
    logging.getLogger(LOGGER_NAME).info('Committing work')
    for updated, prec_types in results:
        db_handle.session.add_all(updated)
        try:
            db_handle.session.commit()
            getLogger(LOGGER_NAME).debug('sub commit happened')
            agg_prec_types += prec_types
        except:
            getLogger(LOGGER_NAME).info(f'Error while committing: {format_exc()}')
            db_handle.session.rollback()

    db_handle.session.close()
    getLogger(LOGGER_NAME).info(f'Commit done, calculated precision for {sum(agg_prec_types.values())} consts, segmented into {dict(agg_prec_types)}')
    

def run_one(p, q, db_handle=None, depth=DEPTH, write_to_db=False, const_id=None, const_type='PcfCanonical'):
    model = get_model(const_type)
    if not model:
        return None
    db_handle = db_handle if db_handle else ramanujan_db.RamanujanDB()
    const = db_handle.session.query(model).filter(models.Constant.const_id == const_id).one_or_none()

    if not const:
        const = update_PcfCanonical(models.PcfCanonicalConstant(), const_type, depth, (p, q))
        if write_to_db:
            db_handle.session.add(const)
            db_handle.session.commit()
    return const
