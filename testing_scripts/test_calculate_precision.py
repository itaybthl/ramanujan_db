import jobs.job_generate_cfs
import jobs.job_calculate_precision


def run_on_cf(num, denom):
    try:
        jobs.job_generate_cfs.add_one(num, denom)
    except:
        print('Already existed')

    return jobs.job_calculate_precision.run_specific(num, denom)

