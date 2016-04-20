

import datetime
import os
import unittest


DATA_DIR = 'data'
RESULTS_DIR = 'results'

class QPTestCase(unittest.TestCase):

    ## static data
    
    # test date, initialize with current date/time (UTC)
    Date = datetime.datetime.utcnow()
    
    # top-level directory for the tests
    # is directory of this module
    __Dir = os.path.dirname(__file__)
    
    # directory that stores reference data (e.g., EQ catalogs)
    ReferenceDataDir = os.path.join(__Dir, DATA_DIR)

    # directory for execution of particular test and storing result data
    TestDirPath = os.path.join(__Dir, RESULTS_DIR)

    # should test result directory be kept?
    KeepTestDir = True
    
    # name of the test currently being invoked
    __TestName = ''
    
    def setUp(self):
        """
        setup test environment
        create test directory if not there
        """
        
        if os.path.exists( self.TestDirPath ) is False:
            os.mkdir( self.TestDirPath )


    def tearDown(self):
        """
        clean up test environment
        remove test directory *or* move to a unique directory name
        """

        if os.path.exists( self.TestDirPath ) is True:
                       
            # move test directory to unique location
            if self.KeepTestDir is True:
                new_dir = "%s-%s" % ( self.TestDirPath, self.__TestName )
                new_location = os.path.join( self.__Dir, new_dir )
                os.rename( self.TestDirPath, new_location )
            else:
                os.remove( self.TestDirPath )


    def setTestName(self, name):
        """
        set name for test
        will be called from specific test module
        """
        self.__TestName = name
        
