from db import ramanujan_db

import logging
import logging.config
import numpy as np
from pcf import PCF

logging.config.fileConfig('logging.config', defaults={'log_filename': 'generate_random'})

LOGGER_NAME = 'job_logger'
POLY_MAX_DEGREE = 3
POLY_MAX_COEFF = 50
BULK_SIZE = 5000
CHUNK_SIZE = 500

def get_degrees(max_deg, num_denom_factor):
    if num_denom_factor == None:
        return np.random.randint(max_deg + 1), np.random.randint(max_deg + 1)
    
    factor, strict = num_denom_factor
    low_deg = np.random.randint(max_deg + 1)
    if strict:
        high_deg = low_deg * abs(factor)
    else:
        high_deg = np.random.randint(abs(factor) * low_deg, abs(factor) * max_deg + 1)

    return (low_deg, high_deg) if factor > 0 else (high_deg, low_deg)

def generate_pcf(max_deg, max_coeff, num_denom_factor):
    coeffs = range(-max_coeff, max_coeff)
    coeffs_nonzero = [x for x in coeffs if x != 0]
    a_deg, b_deg = get_degrees(max_deg, num_denom_factor)
    # reminder that np.concatenate requires the arrays to be inside a tuple
    a = np.concatenate((np.random.choice(coeffs_nonzero, 1), np.random.choice(coeffs, a_deg)))
    b = np.concatenate((np.random.choice(coeffs_nonzero, 1), np.random.choice(coeffs, b_deg)))
    return PCF(a, b)

def execute_job(bulk=0, max_deg=-1, max_coeff=-1, num_denom_factor=None):
    bulk = bulk if bulk else BULK_SIZE
    max_deg = max_deg if max_deg > 0 else POLY_MAX_DEGREE
    max_coeff = max_coeff if max_coeff > 0 else POLY_MAX_COEFF

    logging.getLogger(LOGGER_NAME).info(f'starting to generate cfs randomly: {bulk}, {max_deg}, {max_coeff}, {num_denom_factor}')
    db_handle = ramanujan_db.RamanujanDB()
    while bulk > 0:
        db_handle.add_pcfs(generate_pcf(max_deg, max_coeff, num_denom_factor) for i in range(min(bulk, CHUNK_SIZE)))
        bulk -= CHUNK_SIZE

    logging.getLogger(LOGGER_NAME).info('finished generating')
    db_handle.session.close()
