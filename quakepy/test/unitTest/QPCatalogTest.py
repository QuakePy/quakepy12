#!/usr/bin/env python
"""
This file is part of QuakePy12.

"""

import sys
import shutil
import os
import unittest
import datetime

from random import Random

from mx.DateTime import DateTime

from quakepy.test import QPTestCase

from quakepy import QPCatalog
from quakepy import QPCore

from quakepy.datamodel.EventParameters            import EventParameters
from quakepy.datamodel.Event                      import Event
from quakepy.datamodel.Origin                     import Origin
from quakepy.datamodel.Magnitude                  import Magnitude
from quakepy.datamodel.RealQuantity               import RealQuantity
from quakepy.datamodel.TimeQuantity               import TimeQuantity


class QPCatalogTest(QPTestCase.QPTestCase):

    ## static data of the class

    # unit tests use sub-directory of global reference data directory
    __referenceDataDir = os.path.join( QPTestCase.QPTestCase.ReferenceDataDir,
                                       'unitTest', 'qpcatalog' )

    # set number of decimal places for seconds to 10 for tests
    # if we use default value of 6 decimal places, tests will fail
    # due to floating-point accuracy
    QPCore.QPObject.secondsDigits = 10

    def testBasicSerialization( self ):
        """
        - create an empty catalog
        - set some random values manually
        - serialize catalog to XML
        - read catalog from XML, compare catalogs
        """
        print
        print " ----- testBasicSerialization: serialize/deserialize catalog to/from XML (QuakeML) -----"
        
        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-BasicSerialization" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:
            
            N        = 50
            rd       = Random()
            outfile  = 'qpcat.basic.check.qml'
            
            # limits for random lat/lon generation
            lat_central  =   50.0
            lon_central  = -110.0
            latlon_delta =   20.0
            
            # limits for random magnitude generation
            mag_central = 4.0
            mag_delta   = 2.0
            
            # limits for random timestamp generation
            time_central = datetime.datetime( 2006, 07, 01, 1, 0, 0 )
            time_delta   = 365 * 24 * 60 * 60
            
            qpc   = QPCatalog.QPCatalog()
            evpar = EventParameters()
            qpc.eventParameters = evpar
            
            for curr_ev in xrange( N ):
                ev = Event()
                ev.add(evpar)
                
                ori = Origin()
                
                seconds_delta = rd.randrange( -time_delta, time_delta+1 )
                curr_time     = time_central + datetime.timedelta( seconds=seconds_delta ) 
                ori.time      = TimeQuantity( curr_time.strftime( '%Y-%m-%dT%H:%M:%S') )
                
                ori.latitude  = RealQuantity( lat_central + rd.choice( (-1.0, 1.0) ) * rd.uniform( 0.0, latlon_delta ) )
                ori.longitude = RealQuantity( lon_central + rd.choice( (-1.0, 1.0) ) * rd.uniform( 0.0, latlon_delta ) )
                ori.add(ev)
        
                nm = Magnitude()
                nm.mag = RealQuantity( mag_central + rd.choice( (-1.0, 1.0) ) * rd.uniform( 0.0, mag_delta )  )
                nm.setOriginAssociation( ori.publicID )
                nm.add(ev)

            print " write uncompressed QuakeML catalog file %s with %s events" % ( outfile, qpc.size )
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )
            
        finally:
            # return to the original directory
            os.chdir( cwd )
        
        
    def testXML(self):
        """
        - read a catalog from XML
        - write catalog to XML
        - read catalog from written XML, compare
        - do this for uncompressed, gzipped, and b2zipped catalog
        """
        
        print
        print " ----- testXML: read/write XML (QuakeML) catalogue -----"
        
        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-XML" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            N = 500

            ##  test uncompressed input
            
            infile   = 'qpcat.' + str(N) + '.qml'
            outfile  = 'qpcat.' + str(N) + '.check.qml'

            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            print " testing uncompressed input ..."
            qpc = QPCatalog.QPCatalog( infile )
            print " read uncompressed catalog file %s with %s events" % ( infile, qpc.size )

            error = "Error: number of events in imported catalog is wrong: %s / %s " % ( qpc.size, N )
            self.failIf( qpc.size != N, error )
            
            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read uncompressed QuakeML catalogfile %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )
            
            print "-----"

            ##  test gzipped input

            infile   = 'qpcat.' + str(N) + '.qml.gz'
            outfile  = 'qpcat.' + str(N) + '.check.qml.gz'

            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
                             
            print " testing gz compressed input ... reading"
            qpc = QPCatalog.QPCatalog( infile, compression = 'gz' )
            print " read in gzipped catalog file %s with %s events" % ( infile, qpc.size )

            error = "Error: number of events in imported catalog is wrong: %s / %s " % ( qpc.size, N )
            self.failIf( qpc.size != N, error )
            
            print " testing gz compressed input ... writing catalog file %s" % outfile
            qpc.writeXML( outfile, compression = 'gz' )

            qpc2 = QPCatalog.QPCatalog( outfile, compression = 'gz' )
            print " checking, read gzipped QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )
            
            print "-----"

            ##  test b2zipped input

            infile   = 'qpcat.' + str(N) + '.qml.bz2'
            outfile  = 'qpcat.' + str(N) + '.check.qml.bz2'

            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
                             
            print " testing bz2 compressed input ... reading"
            qpc = QPCatalog.QPCatalog( infile, compression = 'bz2' )
            print " read in b2zipped catalog file %s with %s events" % ( infile, qpc.size )

            error = "Error: number of events in imported catalog is wrong: %s / %s " % ( qpc.size, N )
            self.failIf( len( qpc.eventParameters.event ) != N, error )
            
            print " testing b22 compressed input ... writing"
            qpc.writeXML( outfile, compression = 'bz2' )

            qpc2 = QPCatalog.QPCatalog( outfile, compression = 'bz2' )
            print " checking, read b2zipped QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )
            
        finally:
            # return to the original directory
            os.chdir( cwd )


    def testZMAP( self ):
        """
        - read a catalog from ZMAP format
        - write catalog to ZMAP format
        - read catalog from written ZMAP format, compare
        - write catalog as QuakeML
        - read catalog from written QuakeML, compare
        """
        
        print
        print " ----- testZMAP: read/write ZMAP catalogue -----"
        
        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-ZMAP" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile         = 'zmap.test.dat'
            outfile_zmap   = 'zmap.test.out.dat'
            outfile_qml    = 'zmap.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            
            qpc = QPCatalog.QPCatalog()
            qpc.importZMAP( infile )
            print " read uncompressed ZMAP catalog file %s with %s events"% ( infile, qpc.size )

            print " write uncompressed ZMAP catalog file %s" % outfile_zmap
            qpc.exportZMAP( outfile_zmap )

            qpc2 = QPCatalog.QPCatalog()
            qpc2.importZMAP( outfile_zmap )
            print " checking, read ZMAP catalog file %s: %s events" % ( outfile_zmap, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )
            
            print " write uncompressed QuakeML catalog file %s" % outfile_qml
            qpc.writeXML( outfile_qml )

            qpc2 = QPCatalog.QPCatalog( outfile_qml )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile_qml, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )


    def testZMAP_WithUncertainties( self ):
        """
        - read a catalog from extended ZMAP format with uncertainties
        - write catalog to extended ZMAP format with uncertainties
        - read catalog from written ZMAP format, compare
        - write catalog as QuakeML
        - read catalog from written QuakeML, compare
        """
        
        print
        print " ----- testZMAP_WithUncertainties: read/write extended ZMAP catalogue -----"
        
        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-ZMAP-WithUncertainties" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile         = 'zmap.extended.test.dat'
            outfile_zmap   = 'zmap.extended.test.out.dat'
            outfile_qml    = 'zmap.extended.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            
            qpc = QPCatalog.QPCatalog()
            qpc.importZMAP( infile, withUncertainties = True )
            print " read uncompressed ZMAP catalog file %s with %s events"% ( infile, qpc.size )

            print " write uncompressed ZMAP catalog file %s" % outfile_zmap
            qpc.exportZMAP( outfile_zmap, withUncertainties = True )

            qpc2 = QPCatalog.QPCatalog()
            qpc2.importZMAP( outfile_zmap, withUncertainties = True )
            print " checking, read ZMAP catalog file %s: %s events" % ( outfile_zmap, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )
            
            print " write uncompressed QuakeML catalog file %s" % outfile_qml
            qpc.writeXML( outfile_qml )

            qpc2 = QPCatalog.QPCatalog( outfile_qml )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile_qml, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )


    def testSTP( self ):
        """
        - read a catalog from STP phase format
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """

        print
        print " ----- testSTP: read/write STP phase catalogue -----"
        
        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-STP" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'stp.phase.test.dat'
            outfile  = 'stp.phase.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            
            qpc = QPCatalog.QPCatalog()
            qpc.importSTPPhase( infile )
            print " read uncompressed STP phase catalog file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )


    def testCMT(self):
        """
        - read a catalog from CMT format
        - write to CMT format
        - read catalog from written CMT, compare
        
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testCMT: read CMT catalogue, write as CMT, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-CMT" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'gcmt.test.dat'
            testfile = 'gcmt.test.check.dat'
            outfile  = 'gcmt.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing CMT catalog ..."
            qpc.importCMT( infile )
            print " read uncompressed CMT catalog file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed CMT catalog file %s" % testfile
            qpc.exportCMT( testfile )

            qpc2 = QPCatalog.QPCatalog()
            qpc2.importCMT( testfile )

            # copy EventParameters.publicID from first catalog for comparison
            # otherwise comparison will fail
            qpc2.eventParameters.publicID = qpc.eventParameters.publicID
            print " checking, read CMT catalog file %s: %s events" % ( testfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

            # ---------------------------------------------------------------------------------------

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )


    def testANSSUnified( self ):
        """
        - read a catalog from ANSS unified format
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testANSSUnified: read ANSS unified catalogue, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-ANSSUnified" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'anss.unified.test.dat'
            outfile  = 'anss.unified.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing ANSS unified catalog ..."
            qpc.importANSSUnified( infile )
            print " read uncompressed ANSS unified catalog file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )
            
            
    def testPDECompressed( self ):
        """
        - read a catalog from PDE compressed format
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testPDECompressed: read PDE compressed catalogue, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-PDECompressed" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'pde.compressed.test.dat'
            outfile  = 'pde.compressed.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing PDE compressed catalog ..."
            qpc.importPDECompressed( infile )
            print " read uncompressed PDE compressed catalog file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )
            
            
    def testJMADeck( self ):
        """
        - read a catalog from JMA Deck format
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testJMADeck: read JMA Deck catalogue, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-JMADeck" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'jma.deck.test.dat'
            outfile  = 'jma.deck.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing JMA Deck catalog ..."
            qpc.importJMADeck( infile )
            print " read uncompressed JMA Deck catalog file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )


    def testJMADeck_JMAONLY( self ):
        """
        - read a catalog from JMA Deck format, import only JMA origins
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testJMADeck_JMAONLY: read JMA Deck catalogue, import only JMA origins, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-JMADeck-JMAONLY" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'jma.deck.test.dat'
            outfile  = 'jma.jmaonly.deck.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing JMA Deck catalog ..."
            qpc.importJMADeck( infile, jmaonly=True )
            print " read uncompressed JMA Deck catalog file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )
            
            
    def testGSE2_0Bulletin( self ):
        """
        - read a catalog from GSE2.0 Bulletin format
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testGSE2_0Bulletin: read GSE2.0 Bulletin, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-GSE2_0Bulletin" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'gse2.0.ingv.test.dat'
            outfile  = 'gse2.0.ingv.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing GSE2.0 Bulletin ..."
            qpc.importGSE2_0Bulletin( infile, authorityID = 'it.ingv', networkCode = 'IV' )
            print " read uncompressed GSE2.0 Bulletin file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )


    def testOGS_HPL( self ):
        """
        - read a catalog from OGS HPL format
        - write catalog to QuakeML format
        - read catalog from written QuakeML format, compare
        """
        print
        print " ----- testOGS_HPL: read OGS HPL format, write as QuakeML -----"

        # setup test name
        QPTestCase.QPTestCase.setTestName( self, "QPCatalog-OGS_HPL" )

        # cd to the test directory, remember current directory 
        cwd = os.getcwd()
        os.chdir( QPTestCase.QPTestCase.TestDirPath )
      
        try:

            infile   = 'ogs.hpl.test.dat'
            outfile  = 'ogs.hpl.test.out.qml'
            
            # copy reference catalog file to test dir
            shutil.copyfile( os.path.join( self.__referenceDataDir, infile ),
                             os.path.join( QPTestCase.QPTestCase.TestDirPath, infile ) )
            
            qpc = QPCatalog.QPCatalog()

            print " importing OGS HPL catalog ..."
            qpc.importOGS_HPL( infile, authorityID = 'OGS' )
            print " read uncompressed OGS HPL file %s with %s events" % ( infile, qpc.size )

            print " write uncompressed QuakeML catalog file %s" % outfile
            qpc.writeXML( outfile )

            qpc2 = QPCatalog.QPCatalog( outfile )
            print " checking, read QuakeML catalog file %s: %s events" % ( outfile, qpc2.size )

            error = "Error: original and re-read catalog are not equal"
            self.failIf( qpc != qpc2, error )

        finally:
            # return to the original directory
            os.chdir( cwd )
                        

if __name__ == '__main__':
   
   # Invoke all tests
   unittest.main()

