import time
import logging 
import mpmath as mp

from sqlalchemy import or_, Integer, Float
from sqlalchemy.orm.attributes import flag_modified

from db import models
from db import ramanujan_db
from jobs import pslq_utils

mp.mp.dps = 2000

ALGORITHM_NAME = 'PSLQ_CF_CF'
LOGGER_NAME = 'job_logger'
BULK_SIZE = 500
PRECISION_FACTOR = 9 / 10
MIN_PRECISION = 100
      
logging.config.fileConfig('logging.config', defaults={'log_filename': 'cf_to_cf'})

BASE_FILTERS = [
        models.Cf.precision_data,
        models.Cf.precision_data.has(models.CfPrecision.precision > 100),
        models.Cf.precision_data.has(models.CfPrecision.general_data != None),
        models.Cf.precision_data.has(models.CfPrecision.general_data['rational'].cast(Float) == 0.0),
        ]

FILTERS = BASE_FILTERS + [
        or_(models.Cf.scanned_algo == None, ~models.Cf.scanned_algo.has_key(ALGORITHM_NAME))
        ]

def get_filter_per_cf(cf_id, insertion_time):
    return BASE_FILTERS + [
            models.Cf.cf_id != cf_id,
            or_(models.Cf.scanned_algo == None,
                ~models.Cf.scanned_algo.has_key(ALGORITHM_NAME),
                models.Cf.scanned_algo[ALGORITHM_NAME].cast(Integer) < insertion_time.timestamp() + 30*60
                )
            ]

def get_cf_connection(cf, cfs):
    logging.getLogger(LOGGER_NAME).debug(f'checking cf {cf.cf_id} - numerator: {cf.partial_numerator}, denominator: {cf.partial_denominator}')
    
    cf_precision = cf.precision_data.precision
    check_against = 0

    for second in cfs.filter(*get_filter_per_cf(cf.cf_id, cf.precision_data.insertion_date)).all():
        logging.getLogger(LOGGER_NAME).debug(f'Starting to check with cf_id {second.cf_id}')

        prec = int(min(second.precision_data.precision, cf_precision) * PRECISION_FACTOR)
        if prec < MIN_PRECISION * PRECISION_FACTOR:
            logging.getLogger(LOGGER_NAME).error(f'Minimum precision is too low: {prec}. main cf precision: {cf_precision}, checked against cf precision: {second.precision_data.precision}')
            continue

        check_against += 1
        
        mp.mp.dps = prec
        first_value = mp.mpf(str(cf.precision_data.previous_calc[2])) / mp.mpf(str(cf.precision_data.previous_calc[3]))
        second_value = mp.mpf(str(second.precision_data.previous_calc[2])) / mp.mpf(str(second.precision_data.previous_calc[3]))

        result = None
        try:
            result = pslq_utils.check_int_null_vector(first_value, second_value)
        except Exception as e:
            logging.getLogger(LOGGER_NAME).error(f'Exception occurred in pslq. {cf.cf_id} - {second.cf_id}. values: {first_value} - {second_value}', exc_info=True)

        if result:
            logging.getLogger(LOGGER_NAME).info(f'Found connection {cf.cf_id} - {second.cf_id}: {result}')
            yield models.ContinuedFractionRelation(source_cf=cf.cf_id, target_cf=second.cf_id, connection_type="PSLQ", connection_details=result)

    logging.getLogger(LOGGER_NAME).debug(f'compared {cf.cf_id} to {check_against} other cfs')

def run_job(bulk=0):
    if not bulk:
        bulk = BULK_SIZE
    db_handle = ramanujan_db.RamanujanDB()
    logging.getLogger(LOGGER_NAME).info(f'Starting to check connections, bulk size: {bulk}')
    
    cfs = 0
    connections = 0
    for cf in db_handle.cfs.filter(*FILTERS).limit(bulk):
        if not cf.scanned_algo:
            cf.scanned_algo = dict()
        cf.scanned_algo[ALGORITHM_NAME] = int(time.time())
        for connection_data in get_cf_connection(cf, db_handle.cfs):
            db_handle.session.add(connection_data)
            db_handle.session.commit()
            connections += 1

        # for postgres < 9.4
        flag_modified(cf, 'scanned_algo')
        db_handle.session.add(cf)
        db_handle.session.commit()
        cfs += 1


    logging.getLogger(LOGGER_NAME).info(f'finished - worked on {cfs} cfs - found {connections} results')
