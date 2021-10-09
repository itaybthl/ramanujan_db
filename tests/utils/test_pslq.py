import pytest
import mpmath

from utils import pslq_utils as utils

def test_pslq():
    result = utils.check_int_null_vector(mpmath.e, (mpmath.e - 2) / mpmath.e)
    assert result == [1, -2, 1, 0]

def test_verify():
    assert utils.verify_result(1, 0.25, [1, 0, 4, 0])
    assert not utils.verify_result(1, 0.25, [1, 1, 1, 1])
