from db import ramanujan_db
from db import models


import itertools
import numpy as np
import logging

POLY_DEGREE = 3
POLY_ABS_RANGE = range(-3, 4)
BULK_SIZE = 1000

def generate_cfs():
    coeffs_space = [i for i in POLY_ABS_RANGE]
    coeffs = itertools.product(coeffs_space, repeat=POLY_DEGREE+1)
    coeffs_tuples = itertools.product(coeffs, repeat=2)
    while True:
        chunk = itertools.islice(coeffs_tuples, 100)
        try:
            first_el = next(chunk)
        except StopIteration:
            return
        yield itertools.chain((first_el, ), chunk)

def run_job():
    db_handle = ramanujan_db.RamanujanDB()
    for slice_coeffs in generate_cfs():
        slice_list = []
        for i, j in slice_coeffs:
            num = np.trim_zeros(i, 'f')
            denom = np.trim_zeros(j, 'f')
            if num:
                slice_list.append(models.Cf(partial_numerator=num, partial_denominator=denom))
        db_handle.add_cfs(slice_list)

    #db_handle.add_cfs(cfs)

def add_one(num, denom, db_handle):
    cf = db_handle.session.query(models.Cf).filter(models.Cf.partial_denominator == denom,models.Cf.partial_numerator == num).one_or_none()

    if not cf:
        cf = models.Cf(partial_numerator=num, partial_denominator=denom)
        db_handle.session.add(cf)
        db_handle.session.commit()
    cf_id = cf.cf_id
#    db_handle.session.close()
    return cf_id
