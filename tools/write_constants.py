from db import models
from db import ramanujan_db
from decimal import Decimal
import xlrd
import os

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
