import pytest
import mpmath
import jobs.job_calculate_precision as precision

def test_calc_cf():
    # TODO: Check code effeciency with timer
    value, prec, matrix, data, iteration = precision.calculate_cf([1], [1], 3000)
    mpmath.mp.dps = prec - 5
    assert value == mpmath.phi()
    assert iteration == 3000
    assert data['an_deg'] == 0
    assert data['bn_deg'] == 0
    assert not data['rounded']
    assert data['converges']


def test_run_one():
    pass

def test_sanity():
   queried_data = precision.run_query(5)
   results, prec = precision.execute_job(queried_data)
   precision.summarize_results((results, prec))


if __name__ == '__main__':
    unittest.main()
