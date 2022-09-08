from db import models
from db import ramanujan_db
from decimal import Decimal
import xlrd
import os
from tools.constants_generator import Constants

script_dir = os.path.dirname(__file__) 
rel_path = "constToDB.xls"
 
loc = os.path.join(script_dir, rel_path)

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
                print(f'Calculation of {x} is expected to take somewhat longer...')
            named_const.base.precision = precision
            named_const.base.value = Decimal(str(const_func()))
        else:
            print(f'Skipping calculation of {x}, too inefficient!')
        named_const.name = x
        named_const.description = const_func.__doc__[:const_func.__doc__.index('.\n')]
        db_handle.session.add_all([named_const])
    db_handle.session.commit()
    db_handle.session.close()
