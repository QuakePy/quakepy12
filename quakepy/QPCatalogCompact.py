# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import os
import time
import datetime
import cPickle

import string
import re

import gzip, bz2

import cStringIO

import math
import numpy

#import convertunit
#import operator

import pyRXP
from   xml.sax   import saxutils

from mx.DateTime     import DateTime
from mx.DateTime     import utc
from mx.DateTime     import DateTimeFromAbsDays, DateTimeDeltaFromSeconds, \
                            DateTimeDelta, DateTimeDeltaFrom, TimeDelta
from mx.DateTime     import RelativeDateTime
from mx.DateTime.ISO import ParseDateTimeUTC

# internal includes

from QPCore import *
from QPUtils import *


class QPCatalogCompact( QPObject ):
    """
    QuakePy: QPCatalogCompact
    """

    __standardCols = ( 'lon', 'lat', 'depth', 'time', 'mag' )

    # floating-point format for columns except for time
    __floatFmt     = '%12.8e'

    # floating-point format for time and time_err columns (decimal year)
    __floatFmtTime = '%20.16e'
    
    def __init__( self, **kwargs ):
        """
        """
        super( QPCatalogCompact, self ).__init__( **kwargs )

        self.map     = {}
        self.idMap   = []
        self.catalog = None
        self.comment = ''
        

    def read( self, input, **kwargs ):
        """
        read compact catalog from ASCII row/column file
        """
        if isinstance( input, basestring ):
            istream = getQPDataSource( input, **kwargs )
        else:
            istream = input

        parametersFound = False
        
        # read first lines in input file to get columns and comment
        for line in istream:

            # read parameter header line
            if string.upper( line[0] ) == 'P':

                line_arr = line.split()
                
                if parametersFound is True:
                    error_str = ""
                    raise ValueError, error_str
                else:
                    parametersFound = True

                    for col_ctr, col in enumerate( line_arr[1:] ):
                        self.map[col] = col_ctr
            
            elif string.upper( line[0] ) == 'C':
                self.comment = ''.join( ( self.comment, line[2:], '\n' ) )
            
            else:
                # stop looping over file
                break

        # reset stream
        istream.seek( 0 )

        # read whole file again using numpy.loadtxt()
        self.catalog = self.__loadASCIIFile( istream )
        

    def write( self, output, **kwargs ):
        """
        write compact catalog to ASCII row/column file

        format:
        P idx lon lat depth time mag ...
        C This is a
        C multiline comment
        0.0 5.0 45.0 10.0 2009.000242 3.4
        1.0 5.5 44.3 12.2 2009.123123 3.1 
        ...

        "P" header lines denote the columns
        "C" comment lines are optional
        """

        # open file for writing
        if isinstance( output, basestring ):
            ostream = writeQPData( output, **kwargs )
        else:
            ostream = output

        # write header columns
        headerColumns = self.__getOrderedColumns( True )
        ostream.write( 'P ' + ' '.join( headerColumns ) + '\n' )

        # write comment lines
        if len( self.comment ) > 0:
            for curr_comment in self.comment.split( '\n' ):
                if len( curr_comment ) > 0:
                    ostream.write( 'C ' + curr_comment + '\n' )

        # write event lines
        for curr_ev_idx in xrange( self.catalog.shape[0] ):

            line_arr = []
            
            for curr_col in headerColumns:

                if curr_col == 'time':
                    fmt   = QPCatalogCompact.__floatFmtTime
                    # value = decimalYear( DateTimeFromAbsDays( self.catalog[curr_ev_idx, self.map[curr_col]] ) )
                    value = self.catalog[curr_ev_idx, self.map[curr_col]]
                    
                elif curr_col == 'time_err':
                    fmt   = QPCatalogCompact.__floatFmtTime
                    value = self.catalog[curr_ev_idx, self.map[curr_col]]
                else:
                    fmt   = QPCatalogCompact.__floatFmt
                    value = self.catalog[curr_ev_idx, self.map[curr_col]]
                    
                line_arr.append( fmt % value )

            ostream.write( ' '.join( line_arr ) + '\n' )

        # close file
        ostream.close()


    def importZMAP( self, input, **kwargs ):
        """

        import catalog from ZMAP format (10 or 13 columns)
        
        col   value                     type
         ---   -----                     ----
           1   longitude                 float
           2   latitude                  float
           3   decimal year              float
           4   month                     float (!)
           5   day                       float (!)
           6   magnitude                 float
           7   depth, in km              float
           8   hour                      float (!)
           9   minute                    float (!)
          10   second                    float
         ---   [CSEP extension] ----------------
          11   horizontal error, in km   float
          12   depth error, in km        float
          13   magnitude error           float
          
        """
        
        if isinstance( input, basestring ):
            istream = getQPDataSource( input, **kwargs )
        else:
            istream = input

        if 'withUncertainties' in kwargs.keys() and kwargs['withUncertainties'] is True:
            withUncertainties = True
            self.map    = { 'idx': 0, 'lon': 1, 'lat': 2, 'time': 3, 'mag': 4, 'depth': 5,
                            'hz_err': 6, 'depth_err': 7, 'mag_err': 8 }
            col_indices = ( 3, 0, 1, 2, 5, 6, 10, 11, 12 )
            
        else:
            withUncertainties = False
            self.map    = { 'idx': 0, 'lon': 1, 'lat': 2, 'time': 3, 'mag': 4, 'depth': 5 }
            col_indices = ( 3, 0, 1, 2, 5, 6 )

        self.catalog = numpy.loadtxt( istream, usecols=col_indices )

        # set indices in first columns (replace read-in column)
        self.catalog[:,self.map['idx']] = range( self.catalog.shape[0] )


    def exportZMAP( self, output, **kwargs ):
        """
        export compact catalog to 10- or 13-column ZMAP format
        """
        if isinstance( output, basestring ):
            ostream = writeQPData( output, **kwargs )
        else:
            ostream = output

        if 'withUncertainties' in kwargs.keys() and kwargs['withUncertainties'] is True:
            withUncertainties = True
        else:
            withUncertainties = False
            
        for curr_ev_ctr in xrange( self.catalog.shape[0] ):

            # curr_datetime = DateTimeFromAbsDays( self.catalog[curr_ev_ctr, self.map['time']] )
            curr_datetime = fromDecimalYear( self.catalog[curr_ev_ctr, self.map['time']] )

            if withUncertainties is False:
                ostream.write( '\t'.join(
                              ( '%10.6f' % self.catalog[curr_ev_ctr, self.map['lon']],
                                '%10.6f' % self.catalog[curr_ev_ctr, self.map['lat']],
                                '%18.12f' % self.catalog[curr_ev_ctr, self.map['time']],
                                str( float( curr_datetime.month ) ),
                                str( float( curr_datetime.day ) ),
                                str( self.catalog[curr_ev_ctr, self.map['mag']] ),
                                str( self.catalog[curr_ev_ctr, self.map['depth']] ),
                                str( float( curr_datetime.hour ) ),
                                str( float( curr_datetime.minute ) ),
                                str( curr_datetime.second )
                              ) ) + '\n' )
            else:
                ostream.write( '\t'.join(
                              ( '%10.6f' % self.catalog[curr_ev_ctr, self.map['lon']],
                                '%10.6f' % self.catalog[curr_ev_ctr, self.map['lat']],
                                '%18.12f' % self.catalog[curr_ev_ctr, self.map['time']],
                                str( float( curr_datetime.month ) ),
                                str( float( curr_datetime.day ) ),
                                str( self.catalog[curr_ev_ctr, self.map['mag']] ),
                                str( self.catalog[curr_ev_ctr, self.map['depth']] ),
                                str( float( curr_datetime.hour ) ),
                                str( float( curr_datetime.minute ) ),
                                str( curr_datetime.second ),
                                str( self.catalog[curr_ev_ctr, self.map['hz_err']] ),
                                str( self.catalog[curr_ev_ctr, self.map['depth_err']] ),
                                str( self.catalog[curr_ev_ctr, self.map['mag_err']] )
                              ) ) + '\n' )
                        

    def update( self, qpcatalog, columns = None, **kwargs ):

        if columns is None:
            columns = QPCatalogCompact.__standardCols
        
        noCols = len( columns ) + 1

        ##  resize catalog, add dimensions of new chunk

        if self.catalog is None:

            eventCtr = 0
            
            # catalog is empty, init map
            self.map['idx'] = 0
            for col_ctr, col in enumerate( columns ):
                self.map[col] = col_ctr + 1
            
            self.catalog = numpy.ones( ( qpcatalog.size, noCols ), dtype=float ) * numpy.nan

        else:

            eventCtr = self.catalog.shape[0]
            
            # check if added columns match type of existing cols
            # order key dictionary by value and skip first (index) entry

            referenceColumns = self.__getOrderedColumns()
            if list( columns ) != referenceColumns:
                error_msg = "QPCatalogCompact.update(): added columns %s do not match type of existing columns %s" % (
                        columns, referenceColumns )
                raise ValueError, error_msg
            
            self.catalog.resize( eventCtr + qpcatalog.size, noCols )

        # event.origin.latitude.value
        # longitude, latitude, depth, time, magnitude

        # set comment if present in input QPCatalog and if not yet set
        if len( self.comment ) == 0 and len( qpcatalog.eventParameters.comment ) > 0:

            for curr_comment in qpcatalog.eventParameters.comment:
                self.comment = ''.join( ( self.comment, curr_comment.text, '\n' ) )

        # loop over events in input catalog
        for curr_ev_ctr, curr_ev in enumerate( qpcatalog.eventParameters.event ):

            # update first column with id
            self.catalog[eventCtr + curr_ev_ctr, 0] = float( eventCtr + curr_ev_ctr )

            # update entry in id map
            self.idMap.append( curr_ev.publicID )

            # get preferred origin and magnitude
            curr_ori = curr_ev.getPreferredOrigin()

            if 'mag' in columns:
                try:
                    curr_mag = curr_ev.getPreferredMagnitude()
                except Exception, e:
                    print e
                    raise ValueError
            else:
                curr_mag = None
                
            # loop over columns to add, time column is decimal year
            for curr_col_ctr, curr_col in enumerate( columns ):
                self.catalog[eventCtr + curr_ev_ctr, curr_col_ctr + 1] = \
                    self.__setColumnValue( curr_col, curr_ev, curr_ori, curr_mag )


    def addColumn( self, column ):

        evCtr  = self.catalog.shape[0]
        colCtr = self.catalog.shape[1]
        self.catalog.resize( evCtr, colCtr + 1 )
        self.map[column] = colCtr + 1


    def __getOrderedColumns( self, withIdx = False ):
        
        ## nodes.sort( key=operator.itemgetter('cell_rate') )

        # order map entries by index, use only column token
        
        if withIdx is False:
            # skip column with index '0', which is always the idx column
            ref_cols_sort = sorted( self.map.items(), key = lambda (k,v): (v,k) )[1:]
        else:
            ref_cols_sort = sorted( self.map.items(), key = lambda (k,v): (v,k) )
            
        ref_cols = [ pair[0] for pair in ref_cols_sort ]

        return ref_cols

        
    def __loadASCIIFile( self, istream ):
        return numpy.loadtxt( istream, comments='C', skiprows=1 )

        
    def __setColumnValue( self, curr_col, curr_ev, curr_ori, curr_mag ):

        return_value = None
        
        if curr_col == 'lon':
            try:
                return_value = curr_ori.longitude.value
            except:
                return numpy.nan
            
        elif curr_col == 'lon_err':
            try:
                return_value = curr_ori.longitude.uncertainty
            except:
                return numpy.nan
            
        elif curr_col == 'lat':
            try:
                return_value = curr_ori.latitude.value
            except:
                return numpy.nan
            
        elif curr_col == 'lat_err':
            try:
                return_value = curr_ori.latitude.uncertainty
            except:
                return numpy.nan
            
        elif curr_col == 'depth':
            try:
                return_value = curr_ori.depth.value
            except:
                return numpy.nan
            
        elif curr_col == 'depth_err':
            try:
                return_value = curr_ori.depth.uncertainty
            except:
                return numpy.nan
            
        elif curr_col == 'time':
            try:
                return_value = curr_ori.time.value.toDecimalYear()
                # return_value = curr_ori.time.value.datetime.absdays
            except:
                return numpy.nan
            
        elif curr_col == 'time_err':
            try:
                return_value = curr_ori.time.uncertainty
            except:
                return numpy.nan
            
        elif curr_col == 'mag':
            try:
                return_value = curr_mag.mag.value
            except:
                return numpy.nan
            
        elif curr_col == 'mag_err':
            try:
                return_value = curr_mag.mag.uncertainty
            except:
                return numpy.nan
            
        elif curr_col == 'hz_err':

            hzErrorFound = False
                
            # look if explicit horizontal error is given in OriginUncertainty object
            # this overrides possible separate lat/lon errors
            if len( curr_ori.originUncertainty ) > 0:
                ou = curr_ori.originUncertainty[0]

                if hasattr( ou, 'horizontalUncertainty' ):
                    try:
                        return_value = ou.horizontalUncertainty
                        hzErrorFound = True
                    except:
                        pass

            # if no explicit horizontal error is given, compute horizontal error from lat/lon errors
            if hzErrorFound is False:

                if ( hasattr( curr_ori.longitude, 'uncertainty' ) and hasattr( curr_ori.latitude, 'uncertainty' ) ):

                    try:
                        curr_lon_err = curr_ori.longitude.uncertainty
                        curr_lat_err = curr_ori.latitude.uncertainty
                        
                        # math.pi * 6371.0087714 / 180
                        return_value = math.sqrt( math.pow( curr_lat_err * EARTH_KM_PER_DEGREE, 2 ) +
                                                  math.pow( curr_lon_err * math.cos(curr_lat * math.pi/180.0) *
                                                            EARTH_KM_PER_DEGREE, 2 ) )
                        hzErrorFound = True
                    except:
                        pass

                if hzErrorFound is False:
                    return numpy.nan

        elif curr_col == 'strike1':
            try:
                return_value = curr_ev.getPreferredFocalMechanism().nodalPlanes.nodalPlane1.strike.value
            except:
                return numpy.nan

        elif curr_col == 'strike2':
            try:
                return_value = curr_ev.getPreferredFocalMechanism().nodalPlanes.nodalPlane2.strike.value
            except:
                return numpy.nan

        elif curr_col == 'dip1':
            try:
                return_value = curr_ev.getPreferredFocalMechanism().nodalPlanes.nodalPlane1.dip.value
            except:
                return numpy.nan

        elif curr_col == 'dip2':
            try:
                return_value = curr_ev.getPreferredFocalMechanism().nodalPlanes.nodalPlane2.dip.value
            except:
                return numpy.nan

        elif curr_col == 'rake1':
            try:
                return_value = curr_ev.getPreferredFocalMechanism().nodalPlanes.nodalPlane1.rake.value
            except:
                return numpy.nan

        elif curr_col == 'rake2':
            try:
                return_value = curr_ev.getPreferredFocalMechanism().nodalPlanes.nodalPlane2.rake.value
            except:
                return numpy.nan
                
        else:
            error_msg = "QPCatalogCompact.__setColumnValue(): illegal column type: %s" % curr_col
            raise ValueError, error_msg

        return return_value
