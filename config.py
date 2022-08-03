# how this works:
# Every job is run (at most) 'iterations' amount of times, defaults to infinity.
# Every name must correspond to a file in jobs folder of the format 'job_*.py'.
# In each file, the simpler case is when it doesn't have the function 'run_query', and then it runs 'execute_job' with 'args' and finishes.
# Otherwise it runs 'run_query' with 'args' and then 'execute_job' with its results, and finally 'summarize_results' with the results of that.
# In the latter mode, the results of 'execute_job' can be piped back into additional 'execute_job' calls of the same job via "subjobs".
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

# If you make your own database, 'name' must match the name in 'create_db.sql' in the line 'CREATE DATABASE <name>'
db_configuration = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'passwd': 'apery',
        'name': 'ramanujan'
}

def get_connection_string(db_name=None):
    conf = db_configuration.copy()
    if db_name:
        conf['name'] = db_name
    return 'postgresql://{user}:{passwd}@{host}:{port}/{name}'.format(**conf)

