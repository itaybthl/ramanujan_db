configuration = {
        'pool_size': 10,
        'jobs_to_run': {
           'generate_cfs_random': {
               'args': { 'bulk': 5000, 'max_deg': 3, 'max_coeff': 50, 'num_denom_factor': (2, True)  },
               'iterations': 50 
               },
           'calculate_precision': {
               'args': { 'bulk': 1000, 'num_denom_factor': (2, True) },
               'run_async': True,
               'async_cores': 4,
               'cooldown': 30,
               'no_work_timeout': 60
               },
           'const_cf_pslq': {
               'args': { 'bulk': 1000, 'num_denom_factor': (2, True) },
               'run_async': True,
               'async_cores': 4,
               'cooldown': 30,
               'no_work_timeout': 60
               },
            }
        }

db_configuration = {
        'host': '',
        'port': 5432,
        'user': '',
        'passwd': '',
        'name': ''
}

def get_connection_string(db_name=None):
    conf = db_configuration.copy()
    if db_name:
        conf['name'] = db_name
    return 'postgresql://{user}:{passwd}@{host}:{port}/{name}'.format(**conf)

