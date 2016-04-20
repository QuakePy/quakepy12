#!/usr/bin/env python

import sys
import shutil
import os
import unittest
import datetime

from random import Random

from mx.DateTime import DateTime

#sys.path.append('../../..')
#sys.path.append('../..')
#sys.path.append('..')

from quakepy.test import QPTestCase

from quakepy import QPCore


class QPDateTimeTest(QPTestCase.QPTestCase):

    ## static data of the class

    # unit tests use sub-directory of global reference data directory
    __referenceDataDir = os.path.join( QPTestCase.QPTestCase.ReferenceDataDir,
        'unitTest', 'qpdatetime' )

    # set number of decimal places for seconds to 10 for tests
    # if we use default value of 6 decimal places, tests will fail
    # due to floating-point accuracy
    QPCore.QPObject.secondsDigits = 10

    def test( self ):
        pass


if __name__ == '__main__':
   
   # Invoke all tests
   unittest.main()
