'''
Finds polynomial relations between constants and/or continued fractions in the DB, using PSLQ.

Configured as such:
'bulk': How many CFs to scan. (since there can be many in the DB)
'num_denom_factor': Tuple of the form (factor: int, strict: bool). Every PCF in the DB can be characterized
                    by the ratio between the degrees of its polynomials, so factor is either the exact ratio
                    of PCFs to look for if strict, else the greatest ratio to look for (meaning lower ratios
                    will also be scanned).
'num_of_consts': Tuple of the form (num: int, strict: bool), num is how many constants to relate, and
                 if strict then only relate exactly num constants, else relate 1..num constants.
                 Since the code eliminates redundant constants, it may still find relations using
                 less constants, so in practice there will probably be little benefit to nonstrict.
'num_of_cfs': Similar to num_of_constants, but with CFs instead.
'degree': Tuple of the form (polydegree: int, innerdegree: int). All relations are structured like
          multivariate polynomials over the constants and CFs, of degree polydegree with a maximum
          exponent of innerdegree. For example, a 2-variable polynomial of degree (2,1) will be of
          the form a+bx+cy+dxy (note the lack of x^2 and y^2), and a 4-variable polynomial of degree
          (3,1) will be of the form:
              a + bx+cy+dz+ew + fxy+gxz+hxw+iyz+jyw+kzw + lxyz+mxyw+nxzw+oyzw
          Note here the lack of any single variable with an exponent greater than 1, and also the lack of xyzw.
'use_artificial': Some constants are considered "artificial" for one reason or another, say they're easily related
                  to other constants. Whatever the reason, if this is True then the code is allowed to use artificial
                  constants when checking relations, otherwise it's not allowed to.

Examples:
    'num_of_consts': (1, True), 'num_of_cfs': (1, True), 'degree': (2, 1)
        Replicates the old single-constant 'job_const_cf_pslq'.
    'num_of_consts': (0, True), 'num_of_cfs': (2, True), 'degree': (2, 1)
        Replicates 'job_cf_to_cf_pslq'.
    'num_of_consts': (n, *), 'num_of_cfs': (m, *), 'degree': (n+m, 1)
        Find general multilinear relations. (for any nonnegative integers n,m)
'''
from db import models, ramanujan_db
import mpmath as mp
from time import time
from sqlalchemy import Integer, or_, Float
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import func
from jobs import pslq_utils
from logging import getLogger
from logging.config import fileConfig
from os import getpid
from itertools import chain, combinations, combinations_with_replacement, takewhile, product
from collections import Counter
from functools import reduce
from operator import mul
from traceback import format_exc

mp.mp.dps = 2000

EXECUTE_NEEDS_ARGS = True

ALGORITHM_NAME = 'POLYNOMIAL_PSLQ'
LOGGER_NAME = 'job_logger'
BULK_SIZE = 500
BULK_TYPES = {'PcfCanonical'}
SUPPORTED_TYPES = ['Named', 'PcfCanonical']
DEFAULT_CONST_COUNT = (1, True)
DEFAULT_DEGREE = (2, 1)
DEFAULT_USE_ARTIFICIAL = False

FILTERS = [
        models.Constant.precision > 100
        #or_(models.Cf.scanned_algo == None, ~models.Cf.scanned_algo.has_key(ALGORITHM_NAME)) # TODO USE scan_history TABLE!!!
        ]

def get_filters(subdivide, const_type):
    filters = FILTERS
    if const_type == 'PcfCanonical':
        filters += [models.PcfCanonicalConstant.convergence != models.PcfConvergence.RATIONAL.value]
        if subdivide['PcfCanonical'].get('balanced_only', False):
            filters += [func.cardinality(models.PcfCanonicalConstant.p) == func.cardinality(models.PcfCanonicalConstant.q)]

    return filters 

def poly_check(values, exponents):
    if 1 in values:
        return None # solely for backwards-compatibility. We don't need 1 in the DB!
    poly = [mp.mpf(str(reduce(mul, (values[i] ** exp[i] for i in range(len(values))), 1))) for exp in exponents]
    result = pslq_utils.find_null_polynomial(poly)
    
    if result:
        getLogger(LOGGER_NAME).info('Found relation')

    return result

def compress_relation(result, consts, exponents, degree):
    # will need to use later, so evaluating into lists
    getLogger(LOGGER_NAME).info(f'Original relation is {result}')
    
    indices_per_var = list(list(i[0] for i in enumerate(exponents) if i[1][j]) for j in range(len(consts)))
    redundant_vars = list(i[0] for i in enumerate(indices_per_var) if not any(result[j] for j in i[1]))
    redundant_coeffs = set()
    for redundant_var in redundant_vars: # remove redundant variables
        getLogger(LOGGER_NAME).info(f'Removing redundant variable #{redundant_var}')
        redundant_coeffs |= set(indices_per_var[redundant_var])
        consts = consts[:redundant_var] + consts[redundant_var + 1:]
    
    polydegree, innerdegree = degree # remove redundant degrees
    indices_per_polydegree = list(list(i[0] for i in enumerate(exponents) if sum(i[1].values())==j) for j in range(polydegree+1))
    redundant_polydegrees = list(i[0] for i in enumerate(indices_per_polydegree) if not any(result[j] for j in i[1]))
    redundant_polydegrees = list(takewhile(lambda x: sum(x) == polydegree, enumerate(sorted(redundant_polydegrees, reverse=True))))
    if redundant_polydegrees:
        polydegree = redundant_polydegrees[-1][1] - 1
    redundant_coeffs.update(*indices_per_polydegree[polydegree+1:])
    
    indices_per_innerdegree = list(list(i[0] for i in enumerate(exponents) if max(i[1].values(), default=0)==j) for j in range(innerdegree+1))
    redundant_innerdegrees = list(i[0] for i in enumerate(indices_per_innerdegree) if not any(result[j] for j in i[1]))
    redundant_innerdegrees = list(takewhile(lambda x: sum(x) == innerdegree, enumerate(sorted(redundant_innerdegrees, reverse=True))))
    if redundant_innerdegrees:
        innerdegree = redundant_innerdegrees[-1][1] - 1
    redundant_coeffs.update(*indices_per_innerdegree[innerdegree+1:])
    
    degree = [polydegree, innerdegree]
    getLogger(LOGGER_NAME).info(f'True degree is {degree}')
    for i in sorted(redundant_coeffs, reverse=True):
        del result[i]
    
    getLogger(LOGGER_NAME).info(f'Compressed relation is {result}')

    # TODO now also manually test for smaller sub-relations! PSLQ is only guaranteed to return
    # a small norm, but not guaranteed to return a 1-dimensional relation! see for example pslq([1,3,5])

    return models.Relation(relation_type=ALGORITHM_NAME, details=degree+result, constants=list(consts))

def check_consts(consts, exponents, degree):
    getLogger(LOGGER_NAME).info(f'checking consts: {[c.const_id for c in consts]}')
    relations = []
    mp.mp.dps = min([c.base.precision for c in consts]) * 9 // 10
    result = poly_check([c.base.value for c in consts], exponents)
    if result:
        if relations: # TODO: Report because we found 2 different constants
            getLogger(LOGGER_NAME).critical('found connection to multiple constants!!!')
        relations.append(compress_relation(result, consts, exponents, degree))
    
    return relations

def transpose(l):
    return [[l[j][i] for j in range(len(l))] for i in range(len(l[0]))]

def get_consts(const_type, db_handle, subdivide):
    if const_type == 'Named':
        res = db_handle.constants
        if not subdivide['Named'].get('use_artificial', False):
            res = res.filter(models.NamedConstant.artificial == 0)
        return res

def run_query(subdivide=None, degree=None, bulk=None):
    fileConfig('logging.config', defaults={'log_filename': 'pslq_const_manager'})
    if not subdivide:
        return []
    bulk_types = set(subdivide.keys()) & BULK_TYPES
    if not bulk_types:
        return []
    bulk = bulk if bulk else BULK_SIZE
    getLogger(LOGGER_NAME).debug(f'Starting to check relations, using bulk size {bulk}')
    db_handle = ramanujan_db.RamanujanDB()
    results = [db_handle.session.query(eval(f'models.{const_type}Constant')).filter(*get_filters(subdivide, const_type)).order_by(func.random()).limit(bulk).all() for const_type in bulk_types]
    # apparently postgresql is really slow with the order_by(random) part,
    # but on 1000 CFs it only takes 1 second, which imo is worth it since
    # that allows us more variety in testing the CFs
    db_handle.session.close()
    getLogger(LOGGER_NAME).info(f'size of batch is {len(results)}')
    return transpose(results) # so pool_handler can correctly divide among the sub-processes

def execute_job(query_data, subdivide=None, degree=None):
    fileConfig('logging.config', defaults={'log_filename': f'pslq_const_worker_{getpid()}'})
    if not subdivide:
        getLogger(LOGGER_NAME).error('Nothing to do! Aborting...')
        return 0 # this shouldn't happen unless pool_handler changes, so just in case...
    try:
        to_ignore = []
        for const_type in subdivide:
            if const_type not in SUPPORTED_TYPES:
                msg = f'Unsupported constant type {const_type} will be ignored! Must be one of {SUPPORTED_TYPES}.'
                print(msg)
                getLogger(LOGGER_NAME).warn(msg)
                to_ignore += [const_type]
            elif 'count' not in subdivide[const_type]:
                subdivide[const_type]['count'] = DEFAULT_CONST_COUNT
        for ignore in to_ignore:
            del subdivide[ignore]
        total_consts = sum(c['count'] for c in subdivide.values())
        degree = degree if degree else DEFAULT_DEGREE
        getLogger(LOGGER_NAME).info(f'checking against {total_consts} constants at a time, subdivided into {({k : subdivide[k]["count"] for k in subdivide})}, using degree-{degree} relations')
        if degree[0] > total_consts * degree[1]:
            degree = (total_consts * degree[1], degree[1])
            getLogger(LOGGER_NAME).info(f'redundant degree detected! reducing to {degree}')
        
        polydegree, innerdegree = degree
        exponents = list(c for c in map(Counter, chain.from_iterable(combinations_with_replacement(range(total_consts), i) for i in range(polydegree+1)))
                         if not any(i for i in c.values() if i > innerdegree))
        
        query_data = transpose(query_data)
        db_handle = ramanujan_db.RamanujanDB()
        subsets = []
        for const_type in subdivide:
            num, strict = subdivide[const_type]['count']
            options = None
            if const_type in bulk_types:
                index = [i for i in range(len(query_data)) if isinstance(query_data[i], eval(f'models.{const_type}Constant'))][0]
                options = query_data[index]
            else
                options = get_consts(const_type, db_handle, subdivide)
            subsets += [combinations(options, num) if strict else chain.from_iterable(combinations(options, n) for n in range(1,num+1))]
        
        relations = []
        for consts in product(*subsets):
            # evaluate once to reuse over all subsets of constants
            existing = list(r for r in db_handle.session.query(models.Relation).all() + relations
                            if set(c.const_id for c in r.constants) <= set(c.const_id for c in consts) and r.details[0] <= polydegree and r.details[1] <= innerdegree)
            if not existing:
                new_relations = check_consts(consts, exponents, degree)
                if new_relations:
                    relations += new_relations
            #for cf in consts:
            #    if not cf.scanned_algo:
            #        cf.scanned_algo = dict()
            #    cf.scanned_algo[ALGORITHM_NAME] = int(time())
            #db_handle.session.add_all(consts)
        getLogger(LOGGER_NAME).info(f'finished - found {len(relations)} results')
        db_handle.session.add_all(relations)
        db_handle.session.commit()
        db_handle.session.close()
        
        getLogger(LOGGER_NAME).info('Commit done')
        
        return len(relations)
    except:
        getLogger(LOGGER_NAME).error(f'Exception in execute job: {format_exc()}')

def summarize_results(results):
    getLogger(LOGGER_NAME).info(f'In total found {sum(results)} relations')

def run_one(cf_id, db_handle,write_to_db=False, num_of_consts=None):
    #db_handle = ramanujan_db.RamanujanDB()
    cf = db_handle.session.query(models.Cf).filter(models.Cf.cf_id == cf_id).first()
    connection_data = check_cf2(cf, db_handle.constants, num_of_consts)
    if write_to_db:
        if not cf.scanned_algo:
            cf.scanned_algo = dict()
        cf.scanned_algo[ALGORITHM_NAME] = int(time())
        # for postgres < 9.4
        flag_modified(cf, 'scanned_algo')

        db_handle.session.add_all([cf])
        if connection_data:
            db_handle.session.add_all([connection_data])
        db_handle.session.commit()
      #  db_handle.session.close()

    return connection_data
