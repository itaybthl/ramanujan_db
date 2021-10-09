import unittest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import unittest
from unittest import mock
from db import models

session = UnifiedAlchemyMagicMock(data=[
         (
            [mock.call.query(models.Cf),
             mock.call.filter(
                 #models.Cf.scanned == False and
                  models.Cf.precision_data)],
            [models.Cf(partial_numerator=[0], partial_denominator=[0],precision_data = models.CfPrecision(cf_id =1 ,
                depth = 2000,
                precision = 500,
                value = 2.0943951023931954923084289221863352561314462662500705473166297282052109375241393324186898835614113786547653910088548710980625630730337214878169062720856540783001894018012923474037064297486326366202546429525406504439556307523170988225245221101808012727637657112823068990736362177654755957381734994275158163913377375437254499210139473085528360611435762452617269066742203536992136443475894313012943410729553715135771730613020614574115879550745287367456987163082533084997115679238351499274852921220079661
            # value = pi*3/2
            ))]
        ),
         (
            [mock.call.query(models.Cf),
             mock.call.filter(models.Cf.precision_data == None)],
            [models.Cf(cf_id = 2,partial_numerator=[1], partial_denominator=[1],precision_data =None)]
        ) 
    ])
