import config
import tools.write_constants
import os
import time

COMMAND = 'psql {connection_string} < tools/db/create_db.sql'

if __name__ == '__main__':
    os.system(COMMAND.format(connection_string=config.get_connection_string(db_name='postgres')))
    tools.write_constants.insert_constants()
