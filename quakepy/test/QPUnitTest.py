#!/usr/bin/env python

import unittest

# invoke unit tests
from quakepy.test.unitTest.QPCatalogTest import QPCatalogTest
from quakepy.test.unitTest.QPDateTimeTest import QPDateTimeTest
from quakepy.test.unitTest.QPUtilsTest import QPUtilsTest


if __name__ == '__main__':
   
   # Invoke all tests
   unittest.main()
