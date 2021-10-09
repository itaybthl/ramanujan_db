import math
import time
import os
import logging
import logging.config
from decimal import getcontext
from dataclasses import dataclass, asdict
from enum import Enum
import mpmath

from sqlalchemy.sql.expression import func
from sqlalchemy import exc

from db import ramanujan_db
from db import models
from jobs.cf_calc import CfCalc, get_poly_deg, check_rational, check_fr


getcontext().prec = 2000
mpmath.mp.dps = 2000

BULK_SIZE = 5000
DEPTH = 1200
CALC_JUMP = 200
REDUCE_JUMP = 100
PRECISION_FILTER = 50
LOGGER_NAME = 'job_logger'

FILTERS = [models.Cf.precision_data is None]


@dataclass
class CfData:
    an_deg: int = 0
    bn_deg: int = 0
    factorial_reduction: float = 0
    rational: float = 0
    rounded: bool = False
    original_value: str = ''
    converges: bool = True
    reduction: int = 0


def get_filters(num_denom_factor):
    filters = FILTERS
    if num_denom_factor is not None:
        factor, strict = num_denom_factor
        num_deg = func.cardinality(models.Cf.partial_numerator) - 1
        denom_deg = func.cardinality(models.Cf.partial_denominator) - 1
        if factor > 0:
            low_deg = denom_deg * factor
            high_deg = num_deg
        else:
            low_deg = num_deg * abs(factor)
            high_deg = denom_deg

        if strict:
            new_filter = low_deg == high_deg
        else:
            new_filter = low_deg <= high_deg

        filters = filters + [new_filter]

    return filters


class PrecisionType(Enum):
    HIGH_PREC = 1
    LOW_PREC = 2
    NO_PREC = 3


def calculate_cf(num, denom, depth, previous_calc=None, iteration=0):
    num = [int(i) for i in num]
    denom = [int(i) for i in denom]

    precision = 0
    cf_calc = CfCalc(num=num, denom=denom,
                     previous_calc=previous_calc, iteration=iteration)

    data = CfData(bn_deg=get_poly_deg(num), an_deg=get_poly_deg(denom))

    fr_calculations = []

    for i in range(0, depth+1, CALC_JUMP):
        num_calc, denom_calc = cf_calc.calc_depth(CALC_JUMP)
        if i != 0:
            fr_calculations.append(
                mpmath.log(mpmath.mpf(math.gcd(num_calc, denom_calc))) / mpmath.mpf(i)
                + data.an_deg * (1 - mpmath.log(i))
            )

    can_calc, prec = cf_calc.precision
    if not can_calc:
        logging.getLogger(LOGGER_NAME).debug(
            'Cf does not converge since denom is zero: %s, %s',  num, denom
        )
        data.converges = False
        return math.inf, 0, cf_calc.data, asdict(data), i

    value = cf_calc.value
    precision = 2000 if prec == math.inf else prec
    data.factorial_reduction = check_fr(fr_calculations)
    if mpmath.almosteq(0, mpmath.mpf(num_calc) / mpmath.mpf(denom_calc)):
        logging.getLogger(LOGGER_NAME).debug('Rounding to 0')
        data.original_value = str(value)
        data.rounded = True
        value = 0

    data.rational = check_rational(num_calc, denom_calc)
    data.reduction = cf_calc.reduction

    return value, precision, cf_calc.data, asdict(data), i


def parse_result_type(cf_id, val, precision):
    if val == math.inf:
        logging.getLogger(LOGGER_NAME).debug(
            'cf %s could not be calculated since q goes to 0', cf_id
        )
        return PrecisionType.NO_PREC

    if precision >= PRECISION_FILTER:
        logging.getLogger(LOGGER_NAME).debug(
            'cf_id %s has high precision: %s', cf_id, precision
        )
        return PrecisionType.HIGH_PREC

    logging.getLogger(LOGGER_NAME).debug(
        'cf_id %s has low precision: %s', cf_id, precision
    )
    return PrecisionType.LOW_PREC


def execute_job(cfs):
    logging.config.fileConfig(
        'logging.config',
        defaults={'log_filename': f'precision_worker_{os.getpid()}'}
    )
    results = []
    prec_types = {
        PrecisionType.HIGH_PREC: 0,
        PrecisionType.LOW_PREC: 0,
        PrecisionType.NO_PREC: 0
    }

    for pcf in cfs:
        logging.getLogger(LOGGER_NAME).debug(
            'calculating for %s: %s, %s', pcf.cf_id, pcf.partial_numerator, pcf.partial_denominator
        )
        previous_calc = None
        if pcf.precision_data:
            logging.getLogger(LOGGER_NAME).debug(
                'cf %s has old precision data', pcf.cf_id
            )
            previous_calc = pcf.precision_data.previous_calc
        start_time = time.time()
        val, precision, calc_data, general_data, real_depth = calculate_cf(
            pcf.partial_numerator, pcf.partial_denominator, DEPTH, previous_calc
        )
        logging.getLogger(LOGGER_NAME).debug(
            'calculation of %s, %s, took %s seconds', pcf.partial_numerator,
                pcf.partial_denominator, time.time() - start_time)
        prec_types[parse_result_type(pcf.cf_id, val, precision)] += 1
        if val == math.inf:
            val = 0
        results.append(models.CfPrecision(
            cf_id=pcf.cf_id, depth=real_depth, precision=precision,
            value=val, previous_calc=calc_data, general_data=general_data
        ))

    logging.getLogger(LOGGER_NAME).info('Done calculation')
    return results, prec_types


def run_query(bulk=0, num_denom_factor=None):
    logging.config.fileConfig('logging.config', defaults={
                              'log_filename': 'precision_manager'})
    db_handle = ramanujan_db.RamanujanDB()

    if not bulk:
        bulk = BULK_SIZE
    logging.getLogger(LOGGER_NAME).info(
        'starting to calculate precision for %s cfs', bulk)

    queried_data = db_handle.session.query(models.Cf).filter(
        *get_filters(num_denom_factor)).limit(bulk).all()
    db_handle.session.close()
    logging.getLogger(LOGGER_NAME).info(
        'size of batch is %s', len(queried_data))
    return queried_data


def summarize_results(results):
    db_handle = ramanujan_db.RamanujanDB()
    agg_passed = 0
    agg_prec_types = {}

    logging.getLogger(LOGGER_NAME).info('Committing work')
    for passed_cfs, prec_types in results:
        db_handle.session.add_all(passed_cfs)
        try:
            db_handle.session.commit()
            agg_passed += len(passed_cfs)
            logging.getLogger(LOGGER_NAME).debug('sub commit happenned')
            for k in prec_types.keys():
                if k not in agg_prec_types:
                    agg_prec_types[k] = 0
                agg_prec_types[k] += prec_types[k]
        except exc.SQLAlchemyError as ex:
            logging.getLogger(LOGGER_NAME).info(
                'There was an error while committing %s', ex)
            db_handle.session.rollback()

    db_handle.session.close()
    logging.getLogger(LOGGER_NAME).info('Commit done')

    logging.getLogger(LOGGER_NAME).info(
        'Calculated precision for: %s cfs, which are segmented by: %s',
        agg_passed, agg_prec_types)


def run_one(numerator, denominator, db_handle=None, depth=DEPTH, write_to_db=False, cf_id=None):
    if not db_handle:
        db_handle = ramanujan_db.RamanujanDB()
    precision_data = db_handle.session.query(models.CfPrecision).filter(
        models.CfPrecision.cf_id == cf_id).one_or_none()

    if not precision_data:

        if not write_to_db:
            cf_id = 0
        val, precision, calc_data, general_data, real_depth = calculate_cf(
            numerator, denominator, depth)
        if val == math.inf:
            val = 0
            print('Val is 0')
        precision_data = models.CfPrecision(cf_id=cf_id,
                depth=real_depth, precision=precision,
                value=val, previous_calc=calc_data, general_data=general_data)
        if write_to_db:
            db_handle.session.add_all([precision_data])
            db_handle.session.commit()
#        db_handle.session.close()
    return precision_data
