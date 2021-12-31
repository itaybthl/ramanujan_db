import os
import time
import logging
import logging.config

import mpmath as mp
from sqlalchemy import or_, Float
from sqlalchemy.orm.attributes import flag_modified

from db import models
from db import ramanujan_db
from utils import pslq_utils
from utils.db_utils import get_filters

mp.mp.dps = 2000

ALGORITHM_NAME = 'PSLQ_CF_CONST'
LOGGER_NAME = 'job_logger'
BULK_SIZE = 500

FILTERS = [
    models.Cf.precision_data is not None,
    models.Cf.precision_data.has(models.CfPrecision.precision > 100),
    models.Cf.precision_data.has(models.CfPrecision.general_data is not None),
    models.Cf.precision_data.has(
        models.CfPrecision.general_data['rational'].cast(Float) == 0.0),
    or_(models.Cf.scanned_algo is None, ~
        models.Cf.scanned_algo.has_key(ALGORITHM_NAME))
]


def check_cf_to_const(cf_value, const_value):
    if const_value == 1:
        return None

    result = pslq_utils.check_int_null_vector(
        mp.mpf(str(const_value)), cf_value)
    if result:
        logging.getLogger(LOGGER_NAME).info('Found connection')

    return result


def check_cf(pcf, constants):
    logging.getLogger(LOGGER_NAME).info(
        'checking cf: %s: %s, %s', pcf.cf_id, pcf.partial_numerator, pcf.partial_denominator)
    connection_data = None
    cf_precision = pcf.precision_data.precision
    for const in constants:
        logging.getLogger(LOGGER_NAME).debug(
            'checking const %s with cf %s', const.name, pcf.cf_id)
        mp.mp.dps = min(const.precision, cf_precision) * 9 // 10
        cf_value = mp.mpf(str(
            pcf.precision_data.previous_calc[2])) / mp.mpf(str(pcf.precision_data.previous_calc[3]))
        result = check_cf_to_const(cf_value, const.value)
        if result:
            if connection_data:
                # TODO: Report because we found 2 different constants
                logging.getLogger(LOGGER_NAME).critical(
                    'found connection to multiple constants. cf_id: %s', pcf.cf_id)
            connection_data = models.CfConstantConnection(
                cf_id=pcf.cf_id, constant_id=const.constant_id,
                connection_type="PSLQ", connection_details=result)

    return connection_data


def execute_job(query_data):
    logging.config.fileConfig('logging.config', defaults={
                              'log_filename': f'pslq_const_worker_{os.getpid()}'})
    db_handle = ramanujan_db.RamanujanDB()
    connections = []
    cfs = []
    for pcf in query_data:
        connection_data = check_cf(pcf, db_handle.constants)
        if connection_data:
            connections.append(connection_data)
        if not pcf.scanned_algo:
            pcf.scanned_algo = {}
        pcf.scanned_algo[ALGORITHM_NAME] = int(time.time())
        # for postgres < 9.4
        flag_modified(pcf, 'scanned_algo')
        cfs.append(pcf)
    logging.getLogger(LOGGER_NAME).info(
        'finished - worked on %s cfs - found %s results', len(cfs), len(connections))
    db_handle.session.add_all(cfs)
    db_handle.session.add_all(connections)
    db_handle.session.commit()
    db_handle.session.close()

    logging.getLogger(LOGGER_NAME).info('Commit done')

    return len(cfs), len(connections)


def run_query(bulk=0, num_denom_factor=None):
    logging.config.fileConfig('logging.config', defaults={
                              'log_filename': 'pslq_const_manager'})
    if not bulk:
        bulk = BULK_SIZE
    logging.getLogger(LOGGER_NAME).debug(
        'Starting to check connections, bulk size: %s', bulk)
    db_handle = ramanujan_db.RamanujanDB()
    results = db_handle.session.query(models.Cf).filter(
        *(FILTERS + get_filters(num_denom_factor))).limit(bulk).all()
    db_handle.session.close()
    logging.getLogger(LOGGER_NAME).info('size of batch is %s', len(results))
    return results


def summarize_results(results):
    total_cfs = 0
    total_connections = 0
    for cfs, connections in results:
        total_cfs += cfs
        total_connections += connections
    logging.getLogger(LOGGER_NAME).info(
        'Total iteration over: %s cfs, found %s connections', total_cfs, total_connections)


def run_one(cf_id, db_handle, write_to_db=False):
    #db_handle = ramanujan_db.RamanujanDB()
    pcf = db_handle.session.query(models.Cf).filter(
        models.Cf.cf_id == cf_id).first()
    connection_data = check_cf(pcf, db_handle.constants)
    if write_to_db:
        if not pcf.scanned_algo:
            pcf.scanned_algo = {}
        pcf.scanned_algo[ALGORITHM_NAME] = int(time.time())
        # for postgres < 9.4
        flag_modified(pcf, 'scanned_algo')

        db_handle.session.add_all([pcf])
        if connection_data:
            db_handle.session.add_all([connection_data])
        db_handle.session.commit()
      #  db_handle.session.close()

    return connection_data
