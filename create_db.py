from config import get_connection_string
from tools.write_constants import insert_constants_v2
from os import system

COMMAND = 'psql {connection_string} < tools/db/create_db.sql'

if __name__ == '__main__':
    system(COMMAND.format(connection_string=get_connection_string(db_name='postgres')))
    insert_constants_v2()
