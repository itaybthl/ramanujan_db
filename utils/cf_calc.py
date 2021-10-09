import math
import logging
from collections import namedtuple
from decimal import Decimal, getcontext
import numpy as np
import mpmath
from numba import jit


getcontext().prec = 2000

LOGGER_NAME = 'job_logger'
FR_THRESHOLD = 0.1

CalcData = namedtuple('CalcData', ['a0', 'b0', 'a1', 'b1'])

class CfCalc:
    def __init__(self, num, denom, previous_calc=None, iteration=0):
        self.num = num
        self.denom = denom
        self.reduction = 1
        if not previous_calc:
            self.data = CalcData(1, 0, int(np.polyval(denom, 0)), 1)
        else:
            self.data = CalcData(*previous_calc)

        self.iteration = iteration

    def calc_iter(self, use_numba):
        if use_numba:
            num_calc = int(polyval(self.num, self.iteration+1))
            denom_calc = int(polyval(self.denom, self.iteration+1))
        else:
            num_calc = int(np.polyval(self.num, self.iteration+1))
            denom_calc = int(np.polyval(self.denom, self.iteration+1))

        iter_num = denom_calc*self.data.a1 + num_calc*self.data.a0
        iter_denom = denom_calc*self.data.b1 + num_calc*self.data.b0

        self.iteration += 1

        self.data = CalcData(self.data.a1, self.data.b1, iter_num, iter_denom)

    def calc_depth(self, depth, use_numba=True):
        for _ in range(0, depth):
            self.calc_iter(use_numba)

        return self.data.a1, self.data.b1

    def reduce(self):
        gcd_reduce = math.gcd(
                math.gcd(self.data.a1, self.data.b1),
                math.gcd(self.data.a0, self.data.b0)
                )
        self.reduction *= gcd_reduce
        self.data = CalcData(
                self.data.a0 // gcd_reduce,
                self.data.b0 // gcd_reduce,
                self.data.a1 // gcd_reduce,
                self.data.b1 // gcd_reduce
                )

    @property
    def value(self):
        return Decimal(self.data.a1) / self.data.b1

    @property
    def precision(self):
        if self.data.b0 == 0 or self.data.b1 == 0:
            return False, 0

        precision = -1 * abs(self.value - Decimal(self.data.a0)/self.data.b0).log10()
        if precision != math.inf:
            precision = math.floor(precision)

        return True, precision

    @property
    def calc_data(self):
        return [self.data.a0, self.data.b0, self.data.a1, self.data.b1]

def get_poly_deg(coeff_list):
    trimmed = np.trim_zeros(coeff_list, 'f')
    if trimmed:
        return len(trimmed) - 1
    raise ValueError('no coefficients')

def check_fr(fr_list):
    for i in range(1, len(fr_list)):
        if abs(fr_list[i] - fr_list[i-1]) < FR_THRESHOLD:
            return 1

    for i in range(2, len(fr_list)):
        if abs(fr_list[i-1] - fr_list[i]) > abs(fr_list[i-2] - fr_list[i-1]):
            return 0

    return 0.5

def check_rational(num, denom):
    val = mpmath.mpf(num) / mpmath.mpf(denom)
    if mpmath.almosteq(num, 0) or mpmath.almosteq(val, 0):
        logging.getLogger(LOGGER_NAME).debug(
                'Checking rational that is too close to 0 p=%s,q=%s', num, denom
                )
        return 1

    if mpmath.pslq([val, 1], tol=mpmath.power(10, -100)):
        return 1
    return 0

@jit(nopython=True)
def polyval(coeff, point):
    value = 0
    for i in coeff:
        value = point * value + i
    return value
