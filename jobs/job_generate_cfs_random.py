from db import ramanujan_db

import logging
import logging.config
import numpy as np

logging.config.fileConfig('logging.config', defaults={'log_filename': 'generate_random'})

LOGGER_NAME = 'job_logger'
POLY_MAX_DEGREE = 3
POLY_MAX_COEFF = 50
BULK_SIZE = 5000
CHUNK_SIZE = 500

def get_degrees(max_deg, num_denom_factor):
    if num_denom_factor == None:
        return np.random.randint(max_deg+1), np.random.randint(max_deg+1)
    
    factor, strict = num_denom_factor
    low_deg = np.random.randint(max_deg+1)
    if strict:
        high_deg = low_deg*abs(factor)
    else:
        high_deg = np.random.randint(low_deg*abs(factor), abs(factor)*max_deg + 1)

    return (high_deg, low_deg) if factor > 0 else (low_deg, high_deg)

def generate_poly(max_deg, max_coeff, num_denom_factor):
    a_n = []
    b_n = []
    num_deg, denom_deg = get_degrees(max_deg, num_denom_factor)

    while not any(a_n) and len(a_n) != num_deg + 1:
        a_n = np.trim_zeros(np.random.choice(range(-max_coeff, max_coeff), num_deg + 1), 'f')
    while not any(b_n) and len(b_n) != denom_deg + 1:
        b_n = np.trim_zeros(np.random.choice(range(-max_coeff, max_coeff), denom_deg + 1), 'f')

    return a_n, b_n

def execute_job(bulk=0, max_deg=-1, max_coeff=-1, num_denom_factor=None):
    if not bulk:
        bulk = BULK_SIZE

    max_deg = max_deg if max_deg > 0 else POLY_MAX_DEGREE
    max_coeff = max_coeff if max_coeff > 0 else POLY_MAX_COEFF

    logging.getLogger(LOGGER_NAME).info(f'starting to generate cfs randomly: {bulk}, {max_deg}, {max_coeff}, {num_denom_factor}')
    db_handle = ramanujan_db.RamanujanDB()
    cfs = []
    for i in range(1, bulk+1):
        num, denom = generate_poly(max_deg, max_coeff, num_denom_factor)
        cfs.append({'partial_numerator': num.tolist(), 'partial_denominator': denom.tolist()})
        if i % CHUNK_SIZE == 0:
            db_handle.add_cfs(cfs, conflict=True)
            cfs = []
    if cfs:
        db_handle.add_cfs(cfs)

    logging.getLogger(LOGGER_NAME).info('finished generating')
    db_handle.session.close()
