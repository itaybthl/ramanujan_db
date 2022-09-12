from db import models
from db import ramanujan_db
from decimal import Decimal
import xlrd
import os
import re
from tools.constants_generator import Constants

script_dir = os.path.dirname(__file__) 
rel_path = "constToDB.xls"
 
loc = os.path.join(script_dir, rel_path)

MIN_PRECISION = 90

def parse_row(sheet, row):
   precision = sheet.cell_value(row, 3)
   precision = str(precision)
#   precision = precision.removesuffix('.0')
   precision = precision.rsplit('.0', 1)[0]
   const = models.Constant()
   const.precision = precision
   const.value =  Decimal(str(sheet.cell_value(row, 2)))
   const.description = sheet.cell_value(row, 1)
   const.name = sheet.cell_value(row, 0)
      
   return const

def parse_constants(filename):
   # To open Workbook
   wb = xlrd.open_workbook(filename)
   sheet = wb.sheet_by_index(0)
   constants = []

   for row in range(1, sheet.nrows):
      constants.append(parse_row(sheet,row))

   return constants

def insert_constants(filename=""):
   if not filename:
      filename = loc
   constants = parse_constants(filename)
   db_handle = ramanujan_db.RamanujanDB()
   db_handle.session.add_all(constants)
   db_handle.session.commit()

def get_manual_value(path): # works with the OEIS format, credit where credit is due
    lines = open(path)
    value = ''
    first_index = None
    precision = None
    while True:
        line = lines.readline()
        if not line:
            return value, int(precision)
        res = re.match('\\s*(\\d+)\\s*(\\d+)\\s*', line)
        if not res:
            continue
        if not value:
            first_index = int(res.group(1)) # this is the number of digits before the decimal point!
        if first_index == 0:
            if not value:
                value = '0'
            value += '.'
        value += res.group(2)
        first_index -= 1
        precision = res.group(1)

def insert_constants_v2(precision=4000):
    print(f'Using {precision} digits of precision')
    Constants.set_precision(precision)
    db_handle = ramanujan_db.RamanujanDB()
    for x in Constants.__dict__.keys():
        if x[0] == '_' or x == 'set_precision':
            continue
        print(f'Adding named constant {x}')
        named_const = models.NamedConstant()
        const_func = eval(f'Constants.{x}')
        named_const.base = models.Constant()
        if 'WARNING' not in const_func.__doc__: # too slow to calculate!!
            if 'CAUTION' in const_func.__doc__:
                print(f'    Calculation of {x} is expected to take somewhat longer...')
            named_const.base.precision = precision
            named_const.base.value = Decimal(str(const_func()))
        else:
            print(f'    Skipping calculation of {x}, too inefficient or no calculation available!')
            path = f'tools\\manual_values\\{x}.txt'
            if os.path.isfile(path):
                value, precision2 = get_manual_value(path)
                if precision2 < MIN_PRECISION:
                    print(f'    Manual value has too low precision, update it to {MIN_PRECISION} digits if you can.')
                else:
                    print('    Manual value found, will be used instead')
                    named_const.base.value = value[:16001] # the numeric type is limited to 16383 digits after the decimal point apparently, so for now this sits here
                    named_const.base.precision = min(precision2, 16000)
                
        named_const.name = x
        named_const.description = const_func.__doc__[:const_func.__doc__.index('.\n')]
        db_handle.session.add_all([named_const])
    
    from mpmath import zeta
    
    for x in [2, 4, 5, 6, 7]:
        named_const = models.NamedConstant()
        named_const.base = models.Constant()
        named_const.base.precision = 4000
        named_const.base.value = Decimal(str(zeta(x)))
        named_const.name = f'Zeta{x}'
        named_const.description = f'zeta({x})'
        db_handle.session.add_all([named_const])
    
    db_handle.session.commit()
    db_handle.session.close()
