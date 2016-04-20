# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import bz2
import cPickle
import cStringIO
import datetime
import gzip

import math
import numpy
import os
import re

import urllib2

import geopy.distance

from lxml import etree

from mx.DateTime import Date, DateTime, DateTimeType
from mx.DateTime import DateTimeDeltaFromSeconds, DateTimeFromAbsDays
from mx.DateTime import DateTimeDelta, DateTimeDeltaFrom, TimeDelta
from mx.DateTime.ISO import ParseDateTimeUTC

from pyproj import Geod

from quakepy import QPCore


ARANGE_SAFETY_FACTOR = 1e12

EARTH_RADIUS_KM = 6371.0087714
EARTH_KM_PER_DEGREE = math.pi * EARTH_RADIUS_KM / 180.0

PYPROJ_WGS84_ELLIPSOID = 'WGS84'

WEB_DATASOURCE_URL_SCHEMA = ('http:', 'https:', 'ftp:')

CATALOG_FILE_NAN_STRING = 'NaN'


def getQPDataSource(filename, compression=None, binary=False, **kwargs):

    if filename.startswith(WEB_DATASOURCE_URL_SCHEMA):

        request = urllib2.Request(filename)
        opener = urllib2.build_opener()
        
        try:
            file_object = opener.open(request)
        except:
            raise IOError, "cannot open data source from URL %s" % filename

        if compression is not None:

            file_contents = file_object.read()
            
            if compression == 'gz':

                try:
                    file_object = gzip.GzipFile(fileobj=cStringIO.StringIO(
                        file_contents))
                except:
                    raise IOError, \
                        "cannot open data source from gzipped stream, URL "\
                            "%s" % filename

            elif compression == 'bz2':

                try:
                    file_object = cStringIO.StringIO(bz2.decompress(
                        file_contents))
                except:
                    raise IOError, \
                        "cannot open data source from b2zipped stream, URL "\
                            "%s" % filename

            else:
                raise IOError, "no valid compression format given"
            
    else:
        
        if compression is None:
            
            if binary is True:
                open_flag = 'rb'
            else:
                open_flag = 'r'

            try:
                file_object = open(filename, open_flag)
            except:
                raise IOError, "cannot open data source file %s" % filename
            
        else:

            if compression == 'gz':
                try:
                    file_object = gzip.GzipFile(filename)
                except:
                    raise IOError, \
                        "cannot open gzipped data source file %s" % filename

            elif compression == 'bz2':
                try:
                    file_object = bz2.BZ2File(filename)
                except:
                    raise IOError, \
                        "cannot open b2zipped data source file %s" % filename
                
            else:
                raise IOError, "no valid compression format given"

    return file_object


def writeQPData(filename, compression=None, binary=False, **kwargs):

    if compression is None:
        
        if binary is True:
            open_flag = 'wb'
        else:
            open_flag = 'w'

        try:
            file_object = open(filename, open_flag)
        except:
            raise IOError, "cannot write to plain file"
        
    elif compression == 'gz':

        try:
            file_object = gzip.GzipFile(filename, 'wb')
        except:
            raise IOError, "cannot write to gzip file"
            
    elif compression == 'bz2':
        
        try:
            file_object = bz2.BZ2File(filename, 'wb')
        except:
            raise IOError, "cannot write to bzip2 file"
        
    else:
        raise IOError, "no valid compression format given"

    return file_object


def xmlPrettyPrint(input_data, output, **kwargs):
    """
    input_data: (1) file-like stream (cStringIO.StringIO, StringIO.StringIO, 
                                      file handle)
                (2) character string

    output: filename or file-like object (stream)
    
    """

    if isinstance(output, QPCore.STRING_TYPES):
        ostream = writeQPData(output, **kwargs)
    else:
        ostream = output

    try:
        if isinstance(input_data, QPCore.STRING_TYPES):
            xml = etree.fromstring(input_data)
        else:
            input_data.seek(0)
            xml = etree.parse(input_data)
        
        txt_pretty = etree.tostring(xml, pretty_print=True, 
            xml_declaration=True, encoding=QPCore.XML_ENCODING)
    
    except:
        raise IOError, "cannot parse/pretty-print XML"

    try:
        ostream.write(txt_pretty)
    except:
        raise IOError, "cannot write to file"


def pyrxpTupleTree2XML(node, stream):

    if node is None:
        return

    # is current node a simple string?
    if isinstance(node, basestring):
        stream.write(node)
        return

    # check if current node has element name
    try:
        elementname = node[QPCore.POS_TAGNAME]
    except:
        elementname = ""

    # if node has no element name, output the children
    if len(elementname.strip()) == 0:

        for child in node[QPCore.POS_CHILDREN]:
            pyrxpTupleTree2XML(child, stream)
        
        return

    # regular element with element name
    stream.write(''.join(("<", elementname)))

    # set attributes
    try:

        # loop over attribute/value pairs
        for attributeName in node[QPCore.POS_ATTRS].keys():
            stream.write(
                " %s=\"%s\"" % (attributeName, 
                node[QPCore.POS_ATTRS][attributeName]))

    except AttributeError, IndexError:

        # if there are no attributes, do nothing
        pass

    if node[QPCore.POS_CHILDREN] is None or (
        node[QPCore.POS_CHILDREN] is not None and len(
            node[QPCore.POS_CHILDREN]) == 0):

        # node has no further children, close tag
        stream.write("/>")
        
    else:

        # node has children, close starting tag and insert child nodes
        stream.write(">")

        for child in node[QPCore.POS_CHILDREN]:
            pyrxpTupleTree2XML(child, stream)

        # write closing tag
        stream.write("</%s>" % elementname)


def pickleObj(obj, file, **kwargs):
    
    fh = writeQPData(file, binary=True, **kwargs)
    
    try:
        cPickle.dump(obj, fh, 2)
    
    except cPickle.PickleError:
        
        # raise cPickle.PickleError, "pickleObj - error pickling object"
        print "pickleObj - error pickling object"
    
    fh.close()
    
    return True


def unpickleObj(file, **kwargs):
    
    fh = getQPDataSource(file, binary=True, **kwargs)
    
    try:
        obj = cPickle.load(fh)
    
    except cPickle.PickleError:
        
        # raise cPickle.PickleError, "unpickleObj - error unpickling object"
        print "unpickleObj - error unpickling object"
    
    fh.close()
    
    return obj


class picklable_boundmethod(object):
    """
    Python Cookbook, O'Reilly, Recipe 7.5
    by Peter Cogolo
    
    """
    
    def __init__(self, mt):
        self.mt = mt
        print self.mt
        print self.mt.im_self
    
    def __getstate__(self):
        return self.mt.im_self, self.mt.im_func.__name__
    
    def __setstate__(self, (s, fn)):
        self.mt = getattr(s, fn)
    
    def __call__(self, *a, **kw):
        return self.mt(*a, **kw)


class Callable(object):
    """
    from ASPN Python Cookbook
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52304
    by Alex Martelli
    
    """
    
    def __init__(self, anycallable):
        self.__call__ = anycallable


def addUnique(baseList, otherList):
    """
    Python Cookbook, O'Reilly, Recipe 5.12
    by Alex Martelli
    works only for Python >= 2.4 due to use of set

    add list to existing list if elements are not yet included
    
    """
    
    auxSet = set(baseList)
    
    for item in otherList:
        if item not in auxSet:
            baseList.append(item)
            auxSet.add(item)


class CombinationsNumPy(object):
    """
    holds lists for m-element combination of index vector of length N
    m = 2, 3, ..., M
    uses NumPy array to store numbers

    kwargs: 
        nocompute=True - do not compute combinations, leave list empty
        onlyMaxM=True - compute only combinations for M, not for 2, ..., M-1
    
    """
    
    def __init__(self, M, N, **kwargs):
      
        if M <= 1 or N <= 1 or M > N:
            raise ValueError, \
                "CombinationsNumPy: illegal M or N (%s, %s)" % (M, N)

        self.M = M
        self.N = N

        # list of dictionaries {m, last combinationlist index}
        self.index = [] 
        
        # list with M entries, holds numpy arrays
        self.combinations = [] 

        for idx in xrange(M + 1):

            if idx <= 1:
                self.combinations.append(None)
                self.index.append(None)
            else:
                self.combinations.append([])
                self.index.append({})

        if 'onlyMaxM' in kwargs and kwargs['onlyMaxM'] is True:
            
            # use only one m value: M
            self.mRange = range(self.M, self.M + 1, 1)
        
        else:
            
            # m range is 2, ..., M
            self.mRange = range(2, self.M + 1, 1)
            
        if not ('nocompute' in kwargs and kwargs['nocompute'] is True):
            self.compute()


    def getCombinations(self, m, n):
        
        if n > self.N or n < 2:
            raise ValueError, \
                "CombinationsNumPy::getCombinations - illegal n (%s)" % n
        
        if m > n:
            raise ValueError, \
                "CombinationsNumPy::getCombinations - illegal m, n (%s, %s)" % (
                    m, n)
        
        if m > 1 and m <= self.M:
          
            slice_start = self.index[m][n-1]
            for cc in self.combinations[m][slice_start:]:
                yield cc
                
        elif m == self.M+1:
          
            # reversed range goes from n-1, ..., m-1
            for curr_n in reversed(xrange(m - 1, n)):
              
                slice_start = self.index[m-1][curr_n-1]
              
                for cc in self.combinations[m-1][slice_start:]:
                    yield numpy.concatenate((cc, numpy.array([ curr_n, ])))
                  
        else:
            raise ValueError, \
                "CombinationsNumPy::getCombinations - illegal m (%s)" % m


    def compute(self):

        for m in self.mRange:

            # get unordered list of combinations
            print " compute combinations of %s elements out of %s" % (
                m, self.N)
            
            temp_list = list(xuniqueCombinations(range(self.N), m))
            combiCnt = len(temp_list)
            added = 0
            
            # initialize combinations array with NaN
            self.combinations[m] = numpy.ones(
                (combiCnt, m), dtype=int) * numpy.nan
            
            # re-order list of combinations:
            # first collect all combinations with largest possible member (N-1),
            # then collect combinations with second largest member (N-2),
            # continue until the (one) combination with the smallest possible 
            # member (m-1)
            for ctr in reversed(xrange(m - 1, self.N)):

                print " re-arrange combinations of %s elements containing "\
                    "entry %s" % (m, ctr)
                
                # get number of elements that have not yet been re-arranged
                dim = len(temp_list)
                
                # self.index[m][ctr] = len( self.combinations[m] )
                self.index[m][ctr] = combiCnt - dim
                
                # find all list entries that have an element as high as ctr
                # iterate through list from end because we delete elements
                for tmp_entry_idx in reversed( xrange(dim)):

                    if max(temp_list[tmp_entry_idx]) == ctr:

                        # add matching entry to end of re-ordered combinations 
                        # list
                        self.combinations[m][added] = temp_list[tmp_entry_idx]
                        
                        # delete matching entry from un-ordered list
                        del temp_list[tmp_entry_idx]
                        added = added + 1


class Combinations(object):
    """
    holds lists for m-element combination of index vector of length N
    m = 2, 3, ..., M
    uses Python list to store numbers

    """
    
    def __init__( self, M, N, **kwargs  ):
        """
        kwargs: 
            nocompute=True - do not compute combinations, leave list empty
            onlyMaxM=True - compute only combinations for M, not for 2, ..., M-1
        """
        
        if ( M <= 1 or N <= 1 or M > N ):
            raise ValueError, "Combinations: illegal M or N"

        self.M = M
        self.N = N

        self.index           = [] # list of dictionaries { m, last combinationlist index }
        self.combinations    = [] # list with M entries, holds lists of combinations

        for idx in xrange( M+1 ):

            if idx <= 1:
                self.combinations.append( None )
                self.index.append( None )
            else:
                self.combinations.append( [] )
                self.index.append( {} )
        
        if 'onlyMaxM' in kwargs and kwargs['onlyMaxM'] is True:
            # use only one m value: M
            self.mRange = range( self.M, self.M+1, 1)
        else:
            # m range is 2, ..., M
            self.mRange = range( 2, self.M+1, 1)
            
        if not ( 'nocompute' in kwargs and kwargs['nocompute'] is True ):
            self.compute()


    def getCombinations( self, m, n ):
        
        if n > self.N or n < 2:
            raise ValueError, "Combinations::getCombinations - illegal n"
        
        if m > n:
            raise ValueError, "Combinations::getCombinations - illegal m, n"
        
        if m > 1 and m <= self.M:
          
            slice_start = self.index[m][n-1]
            for cc in self.combinations[m][slice_start:]:
                yield cc
                
        elif m == self.M+1:
          
            # reversed range goes from n-1, ..., m-1
            for curr_n in reversed( xrange( m-1, n ) ):
              
                slice_start = self.index[m-1][curr_n-1]
              
                for cc in self.combinations[m-1][slice_start:]:
                    yield cc + [ curr_n ]
                  
        else:
            raise ValueError, "Combinations::getCombinations - illegal m"


    def compute( self ):

        for m in self.mRange:

            # get unordered list of combinations
            print " compute combinations of %s elements out of %s" % ( m, self.N )
            
            temp_list = list( xuniqueCombinations( range( self.N ), m ) )
            combiCnt  = len( temp_list )

            # re-order list of combinations:
            # first collect all combinations with largest possible member (N-1),
            # then collect combinations with second largest member (N-2),
            # continue until the (one) combination with the smallest possible member (m-1)
            for ctr in reversed( xrange( m-1, self.N ) ):

                print " re-arrange combinations of %s elements containing "\
                    "entry %s" % ( m, ctr )
                
                # get number of elements that have not yet been re-arranged
                dim = len( temp_list )

                # starting index for combinations with ctr as largest entry
                # self.index[m][ctr] = len( self.combinations[m] )
                self.index[m][ctr] = combiCnt - dim

                # find all list entries that have an element as high as ctr
                # iterate through list from end because we delete elements
                for tmp_entry_idx in reversed( xrange( dim ) ):

                    if max( temp_list[tmp_entry_idx] ) == ctr:

                        # add matching entry at end of re-ordered combinations list
                        self.combinations[m].append( temp_list[tmp_entry_idx] )

                        # delete matching entry from un-ordered list
                        del temp_list[tmp_entry_idx]


def xuniqueCombinations(items, n):
    """
    from ASPN Python Cookbook
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/190465
    by Ulrich Hoffmann
    
    See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/105962
    See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66463
    See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66465
    """
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for cc in xuniqueCombinations(items[i+1:],n-1):
                yield [items[i]]+cc


def xuniqueCombinations_2(items, n):
    """
    from ASPN Python Cookbook
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/190465
    Comment by Li Daobing
    
    See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/105962
    See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66463
    See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66465
    """
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)-n+1):
            for cc in xuniqueCombinations_2(items[i+1:],n-1):
                yield [items[i]]+cc


def convertLatLonDepth2Cartesian(p):
    """
    Converts a point given as lat/lon/depth (deg/deg/kilometers) to Cartesian coordinates
    assuming WGS84. Returns x/y/z in meters

    Source: "Department of Defense World Geodetic System 1984"
            Page 4-4
            National Imagery and Mapping Agency
            Last updated June, 2004
            NIMA TR8350.2
    """

    lat = p[0] * math.pi/180.0  # Convert to radians
    lon = p[1] * math.pi/180.0  # Convert to radians
    alt = -p[2] / 1000          # Altitude in meters

    # WGS84 ellipsoid constants:
    a = 6378137.0;
    b = 8.1819190842622e-2;

    # intermediate calculation
    # (prime vertical radius of curvature)
    N = a / math.sqrt(1 - (math.pow(b, 2) * math.pow(math.sin(lat), 2)))

    # results:
    x = (N + alt) * math.cos(lat) * math.cos(lon);
    y = (N + alt) * math.cos(lat) * math.sin(lon);
    z = (((1 - math.pow(b, 2)) * N) + alt) * math.sin(lat);

    return [x, y, z]  # Cartesian coordinates in meters


def distanceBetweenPointsWGS84(p1, p2):
    """
    Computes the distance in kilometres between two points given as lat/lon/depth 
    (deg/deg/kilometers) assuming WGS84
    """

    c1 = convertLatLonDepth2Cartesian(p1)
    c2 = convertLatLonDepth2Cartesian(p2)

    return math.sqrt(math.pow(c1[0] - c2[0], 2) + math.pow(c1[1] - c2[1], 2) + \
        math.pow(c1[2] - c2[2], 2)) / 1000


def distanceBetweenPoints(p1, p2, lat_for_londist=None):
    """
    computes distance between two geographical points
    points are given as ( lat, lon, depth )
    lat, lon in degrees, depth in kilometers, positive towards center of earth
    lat_for_londist tells which point to use for cos in longitude difference
    if not set or not 1 or 2, use arithmetic mean of latitudes
    """

    p1_lat = p1[0]
    p1_lon = p1[1]
    p1_dep = p1[2]

    p2_lat = p2[0]
    p2_lon = p2[1]
    p2_dep = p2[2]

    if lat_for_londist == 1:
        use_lat = p1_lat
    elif lat_for_londist == 2:
        use_lat = p2_lat
    else:
        use_lat = 0.5 * (p1_lat + p2_lat)
    
    distanceXY = math.sqrt( 
        math.pow( (p1_lon - p2_lon) * math.cos(
            use_lat * math.pi/180.0) * EARTH_KM_PER_DEGREE, 2 ) + math.pow( 
                (p1_lat - p2_lat) * EARTH_KM_PER_DEGREE, 2 ) )
    
    distanceXYZ = math.sqrt( 
        math.pow( distanceXY, 2 ) + math.pow( p1_dep - p2_dep, 2) )
    
    return (distanceXYZ, distanceXY)


def geodetic_azimuth_distance(
    p_start, p_end, ellipsoid=PYPROJ_WGS84_ELLIPSOID):
    """Compute geodetic azimuth, backazimuth, and distance 
    from two (lat, lon) points. Assume WGS84 ellipsoid.
    
    p_start: (lat_1, lon_1)
    p_end: (lat_2, lon_2)
    
    """
    
    g = Geod(ellps=ellipsoid)
    azimuth, backazimuth, dist = g.inv(
        p_start[1], p_start[0], p_end[1], p_end[0])
    
    distance_km = dist / 1000
    distance_degrees = central_angle_degrees_from_distance(distance_km)
    
    return (azimuth, backazimuth, distance_degrees, distance_km)


def central_angle_radians_from_points(p1, p2):
    """Computes great circle distance in radians from two points.
    
    p1: (lat_1, lon_1)
    p2: (lat_2, lon_2)
    
    """
                
    great_circle_distance = geopy.distance.great_circle(p1, p2)
    return (great_circle_distance.km / great_circle_distance.RADIUS)


def central_angle_degrees_from_points(p1, p2):
    return math.degrees(central_angle_radians_from_points(p1, p2))


def central_angle_radians_from_distance(distance_km):
    """Computes great circle distance in radians from distance on sphere
    in kilometres.
    
    """
    return (distance_km / geopy.distance.EARTH_RADIUS)
    
    
def central_angle_degrees_from_distance(distance_km):
    return math.degrees(central_angle_radians_from_distance(distance_km))


def horizontalErrorFromLatLon(lat_err, lon_err, latitude):
    """
    compute horizontal error in km from errors on lat/lon given in degrees
    latitude of point in question is required
    """
    lat_err_km = lat_err * EARTH_KM_PER_DEGREE
    lon_err_km = lon_err * math.cos(
        latitude * math.pi/180.0) * EARTH_KM_PER_DEGREE
    horizontal_error = math.sqrt( 
        math.pow( lat_err_km, 2 ) + math.pow( lon_err_km, 2) )
    return horizontal_error


def backazimuth_from_azimuth_flat(azimuth):
    """Compute backazimuth from azimuth (in degrees) in plane geometry, 
    i.e., add or subtract 180 degrees.
    
    Assumes that azimuth is between -180 and 360 degrees.
    
    """
    if azimuth < 180.0:
        backazimuth = azimuth + 180.0
    else:
        backazimuth = azimuth - 180.0
        
    return backazimuth
    
# -------------------------------------------------------------------------------------

def mxDateTime2ISO(date_arr, **kwargs):
    """
    outputs string representation of mxDateTime object
    
    input: tuple/list of mxDateTime objects OR single mxDateTime object
    output: list of strings OR single string

    kwargs: showtime           = True (default) | False - show time part (only YYYY-MM-DD date otherwise) 
            showsecfrac        = True (default) | False - show fractions of seconds in time part, default: full digits
            secondsdigits      = int - number of decimal places of second fraction
            round              = False (default) | True - round last decimal place of seconds
                                 
            partsepreplacechar = string, e.g. ' ' - replaces 'T' separator between date and time part
            timesepreplacechar = string, e.g. ''  - replaces ':' between time components
            datesepreplacechar = string, e.g. '/' - replaces '-' between date components
            
    showtime = False overrides secondsformat and showsecfrac options
    showsecfrac = False overrides secondsformat option
    
    example: dt = mx.DateTime.DateTime( 2007, 1, 1, 12, 0, 0.12345678 )
    
    mxDateTime2ISO( dt )                                   2007-01-01T12:00:00.12345678
    mxDateTime2ISO( dt, secondsdigits = 4 )                2007-01-01T12:00:00.1234
    mxDateTime2ISO( dt, secondsdigits = 4, round = True )  2007-01-01T12:00:00.1235
    mxDateTime2ISO( dt, showsecfrac = False )              2007-01-01T12:00:00
    mxDateTime2ISO( dt, showtime = False )                 2007-01-01
    """

    # check if tuple/list was provided
    if not ( isinstance( date_arr, list ) or isinstance( date_arr, tuple ) ):
        date_arr = [ date_arr ]
        
    new_arr = []
    part_separator = 'T'

    for date in date_arr:
        
        ( date_part, time_part ) = str( date ).split()
         
        # do we show seconds fraction?
        if ( 'showsecfrac' in kwargs ) and ( kwargs['showsecfrac'] is False ):
            
            # do not show seconds fraction
            time_part = time_part[:-3]
        else:
          
            # is explicit format string given?
            if (     'secondsdigits' in kwargs 
                 and isinstance( kwargs['secondsdigits'], int ) 
                 and kwargs['secondsdigits'] > 0 ):
                  
                # round last decimal place?
                if ( 'round' in kwargs ) and ( kwargs['round'] is True ):
                  
                    # use format operator for formatting - it rounds automatically
                    # no zero padding at the beginning
                    fmt = '%.' + str( kwargs['secondsdigits'] ) + 'f'
                    curr_seconds = ( fmt % date.second ).strip()
                    
                else:
                  
                    # format string without '%' operator
                    
                    sec_str     = str( date.second )
                    sec_str_len = len( sec_str )
                    
                    if int( date.second ) < 10:
                        # one place before decimal point
                        offset = 2
                    else:
                        # two places before decimal point
                        offset = 3
                    
                    end_idx = offset + kwargs['secondsdigits']
                    
                    # 1.12345
                    # 11.1234
                    # 11.1234000
                    # ----------
                    # 0123456789
                    
                    if ( sec_str_len >= end_idx ):
                        # seconds string has enough decimal places - no padding
                        curr_seconds = sec_str[:end_idx]
                    else:
                        # more decimal places requested than in original seconds string
                        # pad end of string with zeros
                        curr_seconds = sec_str + ('0' * (end_idx - sec_str_len))
                    
            else:
                # standard display of seconds fraction: full digits
                curr_seconds =  str( date.second )
            
            # pad beginning of string with zero if only one place before decimal point
            if int( date.second ) < 10:
                curr_seconds = '0' + curr_seconds
                
            time_part = time_part[:-5] + curr_seconds

        # replace separator chars
        if 'datesepreplacechar' in kwargs:
            date_part = re.sub( r'-', kwargs['datesepreplacechar'], date_part )
            
        if 'timesepreplacechar' in kwargs:
            time_part = re.sub( r':', kwargs['timesepreplacechar'], time_part )

        if 'partsepreplacechar' in kwargs:
            part_separator = kwargs['partsepreplacechar']
            
        if 'showtime' in kwargs and kwargs['showtime'] is False:
            datetime_str = date_part
        else:
            datetime_str = date_part + part_separator + time_part

        new_arr.append( datetime_str )
    
    if len( new_arr ) > 1:
        return new_arr
    else:
        return new_arr[0]


def decimalYear(datetime):
    """
    return (floating point) decimal year representation of a mx.DateTime input value

    NOTE:
    this method yields the same result as if the .absdays attribute of DateTimeType were used

    mx.DateTime provides:
     .absdate - integer days since epoch
     .abstime - (fractional) seconds from beginning (time 00:00:00) of day (no leap seconds)
     .absdays - (fractional) days since epoch
    """

    if not isinstance( datetime, DateTimeType ):
        raise ValueError, "QPUtils.decimalYear() - input parameter must be of "\
            "type mx.DateTime.DateTimeType"
    
    # get seconds since beginning of year
    # (86400 seconds for each passed day, and .abstime seconds for today)
    year_seconds = ( datetime.day_of_year - 1 ) * 86400.0 + datetime.abstime

    # get year's fraction by dividing by number of seconds per full year
    # no leap year: 365 days, leap year: 366 days
    if datetime.is_leapyear:
        year_fraction = year_seconds / ( 86400.0 * 366 )
    else:
        year_fraction = year_seconds / ( 86400.0 * 365 )

    # return decimal year as sum of integer year (AD) and fraction of year
    # computed above
    return datetime.year + year_fraction


def fromDecimalYear(decimalyear):
    """
    return mx.DateTime object corresponding to (floating point) decimal year

    mx.DateTime provides:
     .absdate - integer days since epoch
     .abstime - (fractional) seconds from beginning (time 00:00:00) of day (no leap seconds)
     .absdays - (fractional) days since epoch
    """

    # get year = integer fraction of decimalyear
    # NOTE: if decimal year is very close to the next higher integer value, rounding takes place
    year_fraction, year = math.modf( decimalyear )
    startyear_dt = DateTime( int( year ), 1, 1 )

    # get seconds that have passed in fraction of the current year
    if startyear_dt.is_leapyear:
        year_seconds = year_fraction * 86400.0 * 366
    else:
        year_seconds = year_fraction * 86400.0 * 365

    return startyear_dt + DateTimeDeltaFromSeconds( year_seconds )


def fixTimeComponents( hour, minute, second ):
    """
    in time strings with the format HH:MM:SS[.ss...], values are sometimes HH=24, MM=60, and SS=60
    meaning the next day, next hour, and next minute

    this function resets the components to allowed values and sets a flag if day, hour, or minute
    must be increased
    """
    checked_hour = hour
    checked_min  = minute
    checked_sec  = float( second )

    increaseDay  = 0
    increaseHour = 0
    increaseMin  = 0

    if hour >= 24:
        checked_hour = 0
        increaseDay  = hour/24
    if minute >= 60:
        checked_min  = 0
        increaseHour = minute/60
    if checked_sec >= 60.0:
        checked_sec = checked_sec - math.floor(checked_sec) # Preserve fraction of seconds
        increaseMin = int(checked_sec//60)
         
    return { 'component'     : ( checked_hour, checked_min, checked_sec ),
             'increaseDelta' : ( increaseDay, increaseHour, increaseMin ) }


def adjustDateTime( adjustDelta, dateTime ):
    """
    sometimes a DateTime object has to be adjusted, when illegal components were specified
    adjustDateTime corrects DateTime object with specifications obtained from
    fixTimeComponents()

    input: adjustFlags is tuple/list of flags for adjusting ( increaseDay, increaseHour, increaseMin )
    output: corrected DateTime object
    """

    # Increase day
    dateTime += DateTimeDelta( adjustDelta[0] )

    # Increase hour
    dateTime += TimeDelta( adjustDelta[1] )

    # Increase minute
    dateTime += DateTimeDeltaFromSeconds( 60.0 * adjustDelta[2] )
        
    return dateTime

def correctedDateTimeFromString(year_str, month_str, day_str, hour_str,
                                minute_str, second_str):
    """Return mx.DateTime object from string components. Correct if illegal
    components are given: hour=24, minute=60, second=60.
    
    """
    
    correction_applied = False
    
    # check if one of the time components has to be corrected
    timeCorrection = fixTimeComponents( int(hour_str), int(minute_str), 
        float(second_str) )

    if sum(timeCorrection['increaseDelta']) > 0:
        correction_applied = True
        
    uncorrected_datetime = DateTime( int(year_str), int(month_str), 
        int(day_str), timeCorrection['component'][0], 
        timeCorrection['component'][1], timeCorrection['component'][2] )
                                
    corrected_datetime = adjustDateTime( timeCorrection['increaseDelta'], 
        uncorrected_datetime )
    
    return (corrected_datetime, correction_applied)
    
# -------------------------------------------------------------------------------------

def normalizeFloat( value ):
    """
    compute components of scientific notation in normalized format
    returns tuple of float mantissa and integer exponent
    """

    exponent = int( math.log10( value ) )
    mantissa = float( value / (10**exponent) )
    return ( mantissa, exponent )


def exponentialFloatFromString( mantissa, exponent ):
    """
    create floating point number from mantissa and exponent without computation
    by concatenating to a string and casting to float()

    mantissa: float
    exponent: int

    this is required if we compare mantissae that have no exact binary representation

    example:

    >>> 1.283e23 - (10**23 * 1.283)
    16777216.0

    >>> 1.283e23 - float( 'e'.join( ( '+1.283', '23' ) ) )
    0.0
    """

    return float( 'e'.join( ( str(mantissa), str(exponent) ) ) )

# -------------------------------------------------------------------------------------

def frange( start, end = None, inc = 1.0 ):
    """
    borrowed from Python Cookbook (O'Reilly), Recipe 19.1
    changed to use numpy instaed of Numeric
    
    usage: frange(5.0)            - [ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0 ] 
           frange(5.0, 10.0)      - [ 5.0, 6.0, 7.0, 8.0, 9.0, 10.0 ]
           frange(5.0, 15.0, 5.0) - [ 5.0, 10.0, 15.0 ]
    """
    if end is None:
        # ensure that end is a floating point number
        end = start + 0.0
        start = 0.0

    ## NOTE: original code from Cookbook is WRONG
    ## - try frange(31.5, 38.0, 0.1): gives 38.1 as last value
    #nitems = math.ceil(((end + inc) - start)/inc)

    ## CHECK: also does not work properly!!
    nitems = int( round( (end - start) / inc ) ) + 1
    return numpy.arange( nitems ) * inc + start

def createFloatRange(xmin, xmax, xstep, center='edge'):
    """Another version of frange, using integer
    
    center: 'edge' put nodes on edges of sub-intervals 
            'mid' put nodes on centers of  sub-intervals
            
    TODO(fab): implement 'edge' method
    """
    
    if center == 'egde':
        raise NotImplementedError, "method 'edge' not yet implemented"
    
    # compute x array in integer to avoid floating point roundoff
    # errors
    xmin_scaled = int(ARANGE_SAFETY_FACTOR * (xmin + 0.5 * xstep))
    xmax_scaled = int(ARANGE_SAFETY_FACTOR * (xmax - 0.5 * xstep))
    xstep_scaled = int(ARANGE_SAFETY_FACTOR * xstep)
    
    xsize_scaled = (xmax_scaled - xmin_scaled + xstep_scaled) / \
        xstep_scaled

    x_arr = numpy.linspace(xmin_scaled, xmax_scaled, num=xsize_scaled) / \
        ARANGE_SAFETY_FACTOR
    
    return x_arr

def remove_ij( x, i=None, j=None ):
    """
    from http://www.scipy.org/PerformanceTips
    Removing the i-th row and j-th column of a 2d array or matrix (fast way, without copies)
    Author: Keith Goodman (?)

    operates on numpy array x
    """

    ## Row i and column j divide the array into 4 quadrants

    # full array, including upper left quadrant
    y = x[:-1,:-1]

    if j is None:
        
        # lower part
        y[i:,:] = x[i+1:,:]

    elif i is None:

        # right part
        y[:,j:] = x[:,j+1:]
        
    else:

        # upper right quadrant
        y[:i,j:] = x[:i,j+1:]

        # lower left quadrant
        y[i:,:j] = x[i+1:,:j]

        # lower right quadrant
        y[i:,j:] = x[i+1:,j+1:]
    
    return y


def locateInArray( array, value ):
    """
    locate floating-point value 'value' in list or tuple of floats 'array'
    return zero-offset array index 'idx'

    returns idx so that array[idx] <= value <  array[idx+1] for idx in 0...len(array)-3
                        (value is in bin of idx, upper bound of bin excluded)

                        array[idx] <= value <= array[idx+1] for idx=len(array)-2
                        (value is in bin of idx, upper bound included, if value is in last array bin)

                        idx=-1:             value is smaller than lower array bound
                        idx=len(array)-1:   value is larger than upper array bound

    built after Numerical Recipes 'locate' routine
    
    NOTE(fab): obsolete, use numpy.searchsorted()
    """

    n          = len( array )
    checkLower = 0
    checkUpper = n+1

    if array[n-1] >= array[0]:
        ascending = True
    else:
        ascending = False

    while ( ( checkUpper - checkLower ) > 1 ):

        checkMean = ( checkUpper + checkLower ) // 2

        if ( ( value >= array[checkMean-1] ) is ascending ):
            checkLower = checkMean
        else:
            checkUpper = checkMean

    if checkLower == 0:

        # out of range at bottom of array
        idx = -1

    else:

        if checkLower == n:

            # we are either on last array value or out of upper bound
            if floatEqual( value, array[n-1] ):

                # exception: exactly last array value
                idx = n-2

            else:

                # out of range at top of array
                idx = n-1

        else:
            # standard case: return zero-offset bin idx
            idx = checkLower - 1

    return idx

# -------------------------------------------------------------------------------------

def floatEqual( f1, f2, epsilon = 1e-12 ):
    """
    checks if two floating point values can be considered equal
    returns True if difference of the two values is smaller or equal to epsilon
    """
    if abs( f1 - f2 ) > epsilon:
        return False
    else:
        return True


def floatEqualPairs( pairs, epsilon = 1e-12 ):
    """
    checks for a sequence of floating point value pairs if they can be considered equal
    
    pairs has to be a list or tuple of pairs of floating-point values (as list or tuple), e.g.
    ( ( 0.1, 0.1 ), ( 0.2, 0.2 ) ) 
    """
    for pair in pairs:
        if floatEqual( pair[0], pair[1], epsilon ) is False:
            raise ValueError, "QPUtils:floatEqualPairs - pair %s and %s are "\
                "not equal" % ( pair[0], pair[1] )

    return True


def equalPairs( pairs ):
    """
    checks for a sequence of integer/string value pairs if they are equal
    
    pairs has to be a list or tuple of pairs of integer or string values (as list or tuple), e.g.
    ( ( 1, 1 ), ( 2, 2 ) ), ( ( 'foo', 'foo' ), ( 'bar', 'bar' ) )
    """
    for pair in pairs:
        if pair[0] != pair[1]:
            raise ValueError, "QPUtils:EqualPairs - pair %s and %s are not "\
                "equal" % ( pair[0], pair[1] )

    return True


def rebin_float(self, value, binsize):
    """
    Rebin a given value to binsize..
    """
    return binsize * round(float(value) / binsize) 


def build_resource_identifier(auth_id, identifier_type, curr_id):
    return "%s:%s/%s/%s" % (QPCore.RESOURCE_IDENTIFIER_URI_SCHEME, auth_id, 
        identifier_type, curr_id)


def xml_tagname(full_tagname):
    """Return tag name w/o namespace prefix."""
    
    prefix_last_idx = full_tagname.find(QPCore.XML_NAMESPACE_SEPARATOR_CHAR)
    if prefix_last_idx == -1:
        tagname = full_tagname
    else:
        tagname = full_tagname[prefix_last_idx+1:]
    
    return tagname


def xml_tagns(full_tagname):
    tag = etree.QName(full_tagname)
    return tag.namespace


def line_is_empty(line):
    if len(line.strip()) == 0:
        return True
    else:
        return False


## functions to determine memory usage

_proc_status = '/proc/%d/status' % os.getpid( )
_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
          'KB': 1024.0, 'MB': 1024.0*1024.0}


def _VmB(VmKey):
    """
    taken from Python Cookbook
    Recipe by Jean Brouwers
    
    given a VmKey string, returns a number of bytes.
    # get pseudo file  /proc/<pid>/status
    """
    try:
        t = open(_proc_status)
        v = t.read( )
        t.close( )
    except IOError:
        return 0.0  # non-Linux?
    # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
    i = v.index(VmKey)
    v = v[i:].split(None, 3)  # split on runs of whitespace
    if len(v) < 3:
        return 0.0  # invalid format?
    # convert Vm value to bytes
    return float(v[1]) * _scale[v[2]]

def memory(since=0.0):
    ''' Return virtual memory usage in bytes. '''
    return _VmB('VmSize:') - since

def resident(since=0.0):
    ''' Return resident memory usage in bytes. '''
    return _VmB('VmRSS:') - since

def stacksize(since=0.0):
    ''' Return stack size in bytes. '''
    return _VmB('VmStk:') - since
