import pytest
import jobs.cf_calc as utils
import math
import mpmath
from decimal import getcontext
import time
import numpy as np

getcontext().prec = 2000
mpmath.mp.dps = 2000

def test_fr():
    # TODO: Find factorial reduction PCF and then get its list
    pass

def test_poly_deg():
    deg = utils.get_poly_deg([1, 2, 3, 4])
    assert deg == 3
    deg = utils.get_poly_deg([3])
    assert deg == 0
    deg = utils.get_poly_deg([0, 0, 1, 2])
    assert deg == 1
    with pytest.raises(ValueError, match='no coefficients'):
        utils.get_poly_deg([])

def test_polyval():
    coeffs = [1, 4, 2, 5]
    assert utils.polyval(coeffs, 3) == np.polyval(coeffs, 3)

def get_exec_time(func, args):
    start = time.monotonic_ns()
    func(*args)
    return time.monotonic_ns() - start

def test_calc_time():
    calc = utils.CfCalc(num=[1], denom=[1])
    start = time.monotonic_ns()
    calc.calc_depth(2000)
    first_numba_time = time.monotonic_ns() - start
    
    calc = utils.CfCalc(num=[1], denom=[1])
    start = time.monotonic_ns()
    calc.calc_depth(2000)
    second_numba_time = time.monotonic_ns() - start

    calc = utils.CfCalc(num=[1], denom=[1])
    start = time.monotonic_ns()
    calc.calc_depth(2000, False)
    np_time = time.monotonic_ns() - start

    assert second_numba_time <= np_time

def test_calc():
    # TODO: Add new PCF
    calc = utils.CfCalc(num=[1], denom=[1])
    p, q = calc.calc_depth(3000)
    _, prec = calc.precision
    prec = 2000 if prec == math.inf else prec
    mpmath.mp.dps = prec - 10
    assert mpmath.mpf(p) / mpmath.mpf(q) == mpmath.phi

def test_continued_calc():
    calc = utils.CfCalc(num=[1], denom=[1])
    calc_split = utils.CfCalc(num=[1], denom=[1])
    
    calc_split.calc_depth(30)
    calc.calc_depth(1000)
    assert calc.value != calc_split.value
    calc_split.calc_depth(970)
    assert calc.value == calc_split.value
    
    calc_split = utils.CfCalc(num=[1], denom=[1])
    calc_split.calc_depth(30)
    assert calc.value != calc_split.value
    assert calc_split.iteration == 30
    calc_split = utils.CfCalc(num=[1], denom=[1], previous_calc=calc_split.data, iteration=30)
    calc_split.calc_depth(970)
    assert calc.value == calc_split.value

def test_calc_reduce():
    calc = utils.CfCalc(num=[1], denom=[1])
    calc.calc_depth(300)
    calc.reduce()
    calc.calc_depth(2700)
    _, prec = calc.precision
    prec = 2000 if prec == math.inf else prec
    mpmath.mp.dps = prec - 10
    assert mpmath.mpf(calc.data.a1) / mpmath.mpf(calc.data.b1) == mpmath.phi

def check_rational():
    assert utils.check_rational(3, 4) == 1
    assert utils.check_rational(0, 4) == 1
    assert utils.check_rational(1, 3) == 1
    assert utils.check_rational(2, 1323) == 0

if __name__ == '__main__':
    unittest.main()
