from db import models
from db import ramanujan_db
import mpmath as mp
import time
from sqlalchemy import Integer, or_, Float
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import func
from utils import pslq_utils
import logging
import logging.config
import sys
import os

mp.mp.dps = 2000

ALGORITHM_NAME = 'PSLQ_CF_CONST'
LOGGER_NAME = 'job_logger'
BULK_SIZE = 500

FILTERS = [
        models.Cf.precision_data != None,
        models.Cf.precision_data.has(models.CfPrecision.precision > 100),
        models.Cf.precision_data.has(models.CfPrecision.general_data != None),
        models.Cf.precision_data.has(models.CfPrecision.general_data['rational'].cast(Float) == 0.0),
        or_(models.Cf.scanned_algo == None, ~models.Cf.scanned_algo.has_key(ALGORITHM_NAME))
        ]

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

        filters = [new_filter] + filters

    return filters 

def check_cf_to_const(cf_value, const_value):
    if const_value == 1:
        return None

    result = pslq_utils.check_int_null_vector(mp.mpf(str(const_value)), cf_value)
    if result:
        logging.getLogger(LOGGER_NAME).info('Found connection')

    return result

def check_cf(cf, constants):
    logging.getLogger(LOGGER_NAME).info(f'checking cf: {cf.cf_id}: {cf.partial_numerator}, {cf.partial_denominator}')
    connection_data = None
    cf_precision = cf.precision_data.precision
    for const in constants:
        logging.getLogger(LOGGER_NAME).debug(f'checking const {const.name} with cf {cf.cf_id}')
        mp.mp.dps = min(const.precision, cf_precision) * 9 // 10
        cf_value = mp.mpf(str(cf.precision_data.previous_calc[2])) / mp.mpf(str(cf.precision_data.previous_calc[3]))
        result = check_cf_to_const(cf_value, const.value)
        if result:
            if connection_data:
                # TODO: Report because we found 2 different constants
                logging.getLogger(LOGGER_NAME).critical(f'found connection to multiple constants. cf_id: {cf.cf_id}')
            connection_data = models.CfConstantConnection(cf_id=cf.cf_id, constant_id=const.constant_id, connection_type="PSLQ", connection_details=result)
    
    return connection_data

def execute_job(query_data):
    logging.config.fileConfig('logging.config', defaults={'log_filename': f'pslq_const_worker_{os.getpid()}'})
    db_handle = ramanujan_db.RamanujanDB()
    connections = []
    cfs = []
    for cf in query_data:
        connection_data = check_cf(cf, db_handle.constants)
        if connection_data:
            connections.append(connection_data)
        if not cf.scanned_algo:
            cf.scanned_algo = dict()
        cf.scanned_algo[ALGORITHM_NAME] = int(time.time())
        # for postgres < 9.4
        flag_modified(cf, 'scanned_algo')
        cfs.append(cf)
    logging.getLogger(LOGGER_NAME).info(f'finished - worked on {len(cfs)} cfs - found {len(connections)} results')
    db_handle.session.add_all(cfs)
    db_handle.session.add_all(connections)
    db_handle.session.commit()
    db_handle.session.close()
    
    logging.getLogger(LOGGER_NAME).info(f'Commit done')

    return len(cfs), len(connections)

def run_query(bulk=0, num_denom_factor=None):
    logging.config.fileConfig('logging.config', defaults={'log_filename': f'pslq_const_manager'})
    if not bulk:
        bulk = BULK_SIZE
    logging.getLogger(LOGGER_NAME).debug(f'Starting to check connections, bulk size: {bulk}')
    db_handle = ramanujan_db.RamanujanDB()
    results = db_handle.session.query(models.Cf).filter(*get_filters(num_denom_factor)).limit(bulk).all()
    db_handle.session.close()
    logging.getLogger(LOGGER_NAME).info(f'size of batch is {len(results)}')
    return results

def summarize_results(results):
    total_cfs = 0
    total_connections = 0
    for cfs, connections in results:
        total_cfs += cfs
        total_connections += connections
    logging.getLogger(LOGGER_NAME).info(f'Total iteration over: {total_cfs} cfs, found {total_connections} connections')

def run_one(cf_id, db_handle,write_to_db=False):
    #db_handle = ramanujan_db.RamanujanDB()
    cf = db_handle.session.query(models.Cf).filter(models.Cf.cf_id == cf_id).first()
    connection_data = check_cf(cf, db_handle.constants)
    if write_to_db:
        if not cf.scanned_algo:
            cf.scanned_algo = dict()
        cf.scanned_algo[ALGORITHM_NAME] = int(time.time())
        # for postgres < 9.4
        flag_modified(cf, 'scanned_algo')

        db_handle.session.add_all([cf])
        if connection_data:
            db_handle.session.add_all([connection_data])
        db_handle.session.commit()
      #  db_handle.session.close()

    return connection_data
