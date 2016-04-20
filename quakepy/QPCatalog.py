# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""


import bz2
import cPickle
import cStringIO
import csv
import datetime
import gzip
import math
import numpy
import os
import pyRXP
import re
import string
import sys
import time

import shapely.geometry

from lxml import etree

from mx.DateTime import DateTime, utc
from mx.DateTime import DateTimeDeltaFromSeconds, DateTimeDelta
from mx.DateTime import DateTimeDeltaFrom, TimeDelta
from mx.DateTime import RelativeDateTime
from mx.DateTime.ISO import ParseDateTimeUTC

from xml.sax import saxutils

from quakepy.datamodel.EventParameters            import EventParameters
from quakepy.datamodel.Event                      import Event
from quakepy.datamodel.Origin                     import Origin
from quakepy.datamodel.Magnitude                  import Magnitude
from quakepy.datamodel.FocalMechanism             import FocalMechanism
from quakepy.datamodel.MomentTensor               import MomentTensor
from quakepy.datamodel.Tensor                     import Tensor
from quakepy.datamodel.DataUsed                   import DataUsed
from quakepy.datamodel.SourceTimeFunction         import SourceTimeFunction
from quakepy.datamodel.PrincipalAxes              import PrincipalAxes
from quakepy.datamodel.Axis                       import Axis
from quakepy.datamodel.NodalPlanes                import NodalPlanes
from quakepy.datamodel.NodalPlane                 import NodalPlane
from quakepy.datamodel.OriginUncertainty          import OriginUncertainty
from quakepy.datamodel.StationMagnitude           import StationMagnitude
from quakepy.datamodel.StationMagnitudeContribution  import StationMagnitudeContribution
from quakepy.datamodel.Amplitude                  import Amplitude
from quakepy.datamodel.Pick                       import Pick
from quakepy.datamodel.Arrival                    import Arrival
from quakepy.datamodel.CreationInfo               import CreationInfo
from quakepy.datamodel.Comment                    import Comment

from quakepy.datamodel.Phase                      import Phase
from quakepy.datamodel.RealQuantity               import RealQuantity
from quakepy.datamodel.IntegerQuantity            import IntegerQuantity
from quakepy.datamodel.TimeQuantity               import TimeQuantity
from quakepy.datamodel.TimeWindow                 import TimeWindow
from quakepy.datamodel.CompositeTime              import CompositeTime
from quakepy.datamodel.WaveformStreamID           import WaveformStreamID
from quakepy.datamodel.EventDescription           import EventDescription
from quakepy.datamodel.OriginQuality              import OriginQuality

from quakepy import QPCore
from quakepy import QPUtils
from quakepy import QPDateTime

from quakepy import QPCatalogCompact
from quakepy import QPPolygon
from quakepy import QPGrid

import quakepy.cumuldist
import quakepy.qpplot
import quakepy.qpseismicityplot


EVENT_DESCRIPTION_REGION_NAME_STRING = 'region name'

ZMAP_PARAMETER_COUNT = 10
ZMAP_WITH_UNCERTAINTIES_PARAMETER_COUNT = 13

STP_AUTHORITY_ID = 'SCSN'
STP_EVENT_PARAMETER_COUNT = 9
STP_PHASE_PARAMETER_COUNT = 13
STP_LOCATION_CODE_PLACEHOLDER = '--'

CMT_LINE_LENGTH = 80
CMT_LINES_PER_EVENT = 5
CMT_AUTHORITY_KEY = 'org.globalcmt'

ANSS_AUTHORITY_ID = 'ANSS'
ANSS_MINIMUM_LINE_LENGTH = 51
ANSS_MINIMUM_LINE_LENGTH_MAGNITUDE = 123
ANSS_MINIMUM_LINE_LENGTH_ADDITIONAL = 172

PDE_AUTHORITY_ID = 'PDE'
PDE_MINIMUM_LINE_LENGTH = 42
PDE_MAGNITUDE_SOURCE_NEIS = 'NEIS'

JMA_AUTHORITY_ID = 'JMA'
JMA_USGS_AUTHORITY_ID = 'USGS'
JMA_ISC_AUTHORITY_ID = 'ISC'
JMA_JST_TIME_SHIFT = 9.0
JMA_MAGNITUDE_COUNT = 2

GSE2_0_LINESTART_EVENT = 'EVENT'
GSE2_0_LINESTART_STOP = 'STOP'
GSE2_0_HEADER_LINE_BEGIN = 'BEGIN GSE2.0'
GSE2_0_HEADER_LINE_DATA_TYPE = 'DATA_TYPE BULLETIN GSE2.0'
GSE2_0_EVENT_SEPARATOR = '.'
GSE2_0_MAGNITUDE_COUNT = 3
GSE2_0_STATION_MAGNITUDE_COUNT = 2

IMS_ARRIVAL_THRESHOLD_SECONDS = -3600
IMS_NETWORK_CODE_MEXICO = 'MAD'
IMS_LINESTART_DATE = 'Date'
IMS_LINESTART_STATION = 'Sta'
IMS_LINESTART_MAGNITUDE = 'Magnitude'

NCSN_AUTHORITY_ID = 'NCSN'

OGS_AUTHORITY_ID = 'OGS'
OGS_NETWORK_CODE_DUMMY = 'XX'
OGS_LINESTART_LOCALIZED_EVENT = '^'
OGS_LINESTART_COMMENT = '*'
OGS_YEAR_START_1900 = 77
OGS_ARRIVAL_PHASE_P = 'P'
OGS_ARRIVAL_PHASE_S = 'S'

HYPOINVERSE_EVENT_LINE_LENGTH = 169
HYPOINVERSE_NON_EVENT_LINE_LENGTH_MIN = 81
HYPOINVERSE_NON_EVENT_LINE_LENGTH_MAX = 150

SHEEC_CSV_DELIMITER = ','

ATTICIVY_HEADER_LINE = \
    "YYYY MM DD HH IIAABB PPPPPP LLLLLLL  EE RRR FFF WWWWKKKSSSSS"
ATTICIVY_BLANK_FIELD = '     '

LOCAL_AUTHORITY_ID = 'local'

DEFAULT_MAG_REBIN_BINSIZE = 0.1

class QPCatalog(QPCore.QPObject):
    """
    QuakePy: QPCatalog 
    represents an earthquake catalog
    holds an object of type EventParameters and provides methods for reading,
    writing, filtering, ...
    
    """
    
    root_attributes = {}
    
    def __init__(self, input=None, **kwargs):
        """
        input can either be a iostream like a file handle or StringIO object,
        or a string, which is then interpreted as a filename
        """
        super(QPCatalog, self).__init__(**kwargs)

        # set publicID style
        if 'idstyle' in kwargs and kwargs['idstyle'] is not None :
            QPCore.QPPublicObject.setPublicIDStyle(kwargs['idstyle'])

        # set element axis
        self.setElementAxis(QPCore.ROOT_ELEMENT_AXIS)

        # add eventParameters explicitly
        # child elements of eventParameters are defined via QPElementList
        self.eventParameters = EventParameters(
            parentAxis=self.elementAxis, 
            elementName=QPCore.PACKAGE_ELEMENT_NAME)
        
        if input is not None:

            if isinstance(input, QPCore.STRING_TYPES):
                istream = QPUtils.getQPDataSource(input, **kwargs)
            else:
                istream = input
                
            self.readXML(istream)


    def merge(self, T):
        """
        merge contents of another QPCatalog object with self
        NOTE: loses publicID, creationInfo, and comment of merged catalog
        """
        self.eventParameters.event.extend(T.eventParameters.event)
        
    
    def __eq__(self, T):
        """
        compare two catalogs
        call __eq__() method on eventParameter attribute
        """

        if hasattr(self, QPCore.PACKAGE_ELEMENT_NAME) \
            and self.eventParameters is not None:
          
            if hasattr(T, QPCore.PACKAGE_ELEMENT_NAME) and \
                    T.eventParameters is not None:
                if not (self.eventParameters == T.eventParameters):
                    return False
            else:
                return False
            
        # if no unequal comparison so far, return True
        return True

    
    def save(self, filename):
        """
        write catalog object to cPickle
        """
        fh = QPUtils.writeQPData(filename, binary=True)
        try:
            cPickle.dump(self, fh, 2)
        except cPickle.PickleError:
            raise cPickle.PickleError, "error pickling catalog"
        fh.close()
    
    
    def readXML(self, input, **kwargs):
        """
        read catalog from QuakeML serialization
        """
        
        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input
                
        # get whole content of stream at once
        lines = istream.read()
        
        # check if it is XML
        if not lines.startswith(QPCore.XML_DECLARATION_STARTTAG):
            raise RuntimeError, "no XML declaration in input stream"
            
        tree = pyRXP.Parser().parse(lines)
        
        # check only for tag name, ignore namespace
        tagname = QPUtils.xml_tagname(tree[QPCore.POS_TAGNAME])
        
        if tagname != QPCore.ROOT_ELEMENT_NAME:
            error_msg = "input stream is not QuakeML, root element is %s" % (
                tagname)
            raise RuntimeError, error_msg

        # save attributes of quakeml element, make shallow copy of dict
        if tree[QPCore.POS_ATTRS] is not None:
            self.root_attributes = tree[QPCore.POS_ATTRS].copy()
        
        # look for eventParameters tag in children component of 4-tuple
        for child in tree[QPCore.POS_CHILDREN]:
            
            # skip whitespace children, grab first eventParameters child
            if QPUtils.xml_tagname(child[QPCore.POS_TAGNAME]) == \
                QPCore.PACKAGE_ELEMENT_NAME:
                
                self.eventParameters.fromXML(child)
                break
                    
        if not hasattr(self, QPCore.PACKAGE_ELEMENT_NAME):
            raise RuntimeError, "no %s tag found" % (
                QPCore.PACKAGE_ELEMENT_NAME)


    def writeXML(self, output, prettyPrint=True, **kwargs):
        """
        serialize catalog to QuakeML

        Input:
            prettyPrint - pretty formatting of output XML
        """
        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData(output, **kwargs)
        else:
            ostream = output
            
        if prettyPrint:

            # serialize to string stream
            streamSuccess = False
            try:
                curr_stream = cStringIO.StringIO()
                self.toXML(curr_stream)
                streamSuccess = True
            except Exception, e:
                print "error in self.toXML() to StringIO, %s" % e

            if streamSuccess:
                try:
                    QPUtils.xmlPrettyPrint(curr_stream, ostream)
                    return
                except Exception, e:
                    print "error in xmlPrettyPrint(), %s" % e

        # write to output stream w/o pretty print
        # fallback if pretty-print has not succeeded
        # this happens sometime for very large streams
        try:
            self.toXML(ostream)
        except Exception, e:
            raise IOError, "error in self.toXML(), %s" % e

    
    def toXML(self, stream):

        stream.write(QPCore.XML_DECLARATION)

        xmlns_set = False
        stream.write("<%s:%s" % (QPCore.XML_NAMESPACE_QML_ABBREV, 
            QPCore.ROOT_ELEMENT_NAME))

        # namespaces
        stream.write(' xmlns:%s="%s" xmlns="%s"' % (
            QPCore.XML_NAMESPACE_QML_ABBREV, QPCore.XML_NAMESPACE_QML, 
            QPCore.XML_NAMESPACE_BED))
        
        # loop over root attributes from input document
        for curr_attr_name in self.root_attributes:

            # ignore namespace definitons
            if curr_attr_name.find('xmlns') == -1:
                stream.write(' %s="%s"' % (curr_attr_name, 
                    self.root_attributes[curr_attr_name]))

        stream.write('>')
        
        try:
            self.eventParameters.toXML(QPCore.PACKAGE_ELEMENT_NAME, stream)
        except Exception, e:
            error_msg = "error in eventParameters.toXML(), %s" % e
            raise RuntimeError, error_msg
        
        stream.write("</%s:%s>" % (QPCore.XML_NAMESPACE_QML_ABBREV, 
            QPCore.ROOT_ELEMENT_NAME))


    def importZMAP(self, input, **kwargs):
        """ 
        Input ZMAP stream has to provide the first 10 columns as 
        specified below (classical ZMAP format)
        
        there can be additional columns
        e.g., CSEP uses three additional columns with uncertainties

        NOTE: All input columns are floats, including those that are in 
              principle integers (month, day, hour, minute).
              Class attributes, however, are integers.

        Extended ZMAP format as used in CSEP (www.cseptesting.org) is 
        supported by using keyword argument withUncertainties=True 
        (default: False)

        Additional CSEP columns:
        11: horizontal error (km) 12: depth error (km) 13: magnitude error

        ZMAP format
        
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

        correct illegal time components: YES
        
        """

        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'withUncertainties' in kwargs and kwargs['withUncertainties']:
            withUncertainties = True
        else:
            withUncertainties = False
            
        # over lines (= events) in ZMAP input stream
        for line_ctr, line in enumerate(istream):

            # line entries need to be separated by whitespace
            # split input line into components 
            zmap_pars = line.strip().split()
            
            if len(zmap_pars) < ZMAP_PARAMETER_COUNT:
                error_str = "format error in input file, line %s: %s" % (
                    line_ctr+1, line)
                raise RuntimeError, error_str
              
            # create event
            ev = Event()
            ev.add(self.eventParameters)
              
            # create origin
            ori = Origin()
            ori.add(ev)
            
            ori.longitude = RealQuantity(float(zmap_pars[0]))
            ori.latitude = RealQuantity(float(zmap_pars[1]))
            
            # NOTE: changed to metres, QuakeML v1.2
            ori.depth = RealQuantity(1000 * float(zmap_pars[6]))
            
            # get time components
            corrected_time = QPUtils.correctedDateTimeFromString(
                float(zmap_pars[2]), float(zmap_pars[3]), float(zmap_pars[4]),
                float(zmap_pars[7]), float(zmap_pars[8]), 
                float(zmap_pars[9]))
            ori.time = TimeQuantity(QPDateTime.QPDateTime(corrected_time[0]))
                
            if corrected_time[1]:
                print "corrected illegal datetime components in line %s: "\
                    "%s, %s" % (line_ctr+1, zmap_pars[2:5], zmap_pars[7:10])
            
            # create magnitude
            mag = Magnitude()
            mag.add(ev)
            mag.mag = RealQuantity(float(zmap_pars[5]))
            mag.setOriginAssociation(ori.publicID)
            
            # set preferred origin and magnitude
            ev.preferredOriginID = ori.publicID
            ev.preferredMagnitudeID = mag.publicID

            ## add uncertainties, if present

            # input line must have at least 13 whitespace-separated entries
            if withUncertainties and \
                len(zmap_pars) >= ZMAP_WITH_UNCERTAINTIES_PARAMETER_COUNT:

                # horizontal error
                try:
                    horizontal_error = float(zmap_pars[10])

                    ou = OriginUncertainty.OriginUncertainty()
                    
                    # NOTE: changed from kilometres to metres, QuakeML v1.2
                    ou.horizontalUncertainty = 1000 * horizontal_error
                    ou.add(ori)
                except Exception:
                    pass
            
                # depth error
                try:
                    # NOTE: changed from kilometres to metres, QuakeML v1.2
                    ori.depth.uncertainty = 1000 * float(zmap_pars[11])
                except Exception:
                    pass

                # magnitude error
                try:
                    mag.mag.uncertainty = float(zmap_pars[12])
                except Exception:
                    pass


    def exportZMAP(self, output, **kwargs):
        """ 
        NOTE: All output columns are floats, including those that are in 
              principle integers (month, day, hour, minute).
              Class attributes, however, are integers.

        Extended ZMAP format as used in CSEP (www.cseptesting.org) is 
        supported by using keyword argument withUncertainties=True 
        (default: False)
        """
        
        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData( output, **kwargs)
        else:
            ostream = output

        if 'withUncertainties' in kwargs and kwargs['withUncertainties']:
            withUncertainties = True
        else:
            withUncertainties = False
            
        outstring_arr = []
        for ev in self.eventParameters.event:

            # check if event has preferred origin and coordinates, 
            # otherwise skip
            try:
                ori = ev.getPreferredOrigin()
                curr_lon = ori.longitude.value
                curr_lat = ori.latitude.value
            except Exception:
                continue

            try:
                mag = ev.getPreferredMagnitude()
            except Exception:
                mag = None
            
            # if event has no associated magnitude, set magnitude column 
            # to 'NaN'
            if hasattr(mag, 'mag') and mag is not None:
                mag_str = str(mag.mag.value)
            else:
                mag_str = QPUtils.CATALOG_FILE_NAN_STRING

            # if origin has no depth, set depth column to 'NaN'
            if hasattr(ori, 'depth'):
                depth_str = str(ori.depth.value / 1000.0)
            else:
                depth_str = QPUtils.CATALOG_FILE_NAN_STRING

            line_arr = ['%10.6f' % ori.longitude.value,
                '%10.6f' % ori.latitude.value,
                '%18.12f' % ori.time.value.toDecimalYear(),
                str(float(ori.time.value.datetime.month)),
                str(float(ori.time.value.datetime.day)),
                mag_str,
                depth_str,
                str(float(ori.time.value.datetime.hour)),
                str(float(ori.time.value.datetime.minute)),
                str(ori.time.value.datetime.second)]
            
            if withUncertainties:

                hzErrorFound = False
                
                # look if explicit horizontal error is given in 
                # OriginUncertainty object
                # this overrides possible separate lat/lon errors
                if ori.originUncertainty:
                    ou = ori.originUncertainty[0]

                    if hasattr(ou, 'horizontalUncertainty'):
                        try:
                            horizontal_uncertainty_str = str(
                                ou.horizontalUncertainty / 1000.0)
                            hzErrorFound = True
                        except Exception:
                            pass

                # if no explicit horizontal error is given, compute horizontal 
                # error from lat/lon errors
                if not hzErrorFound:

                    if hasattr(ori.longitude, 'uncertainty') and hasattr(
                        ori.latitude, 'uncertainty'):

                        try:
                            curr_lon_err = ori.longitude.uncertainty
                            curr_lat_err = ori.latitude.uncertainty
                            
                            # TODO(fab): use geodesy module
                            horizontal_uncertainty_str = str(math.sqrt(
                                math.pow(curr_lat_err * \
                                    QPUtils.EARTH_KM_PER_DEGREE, 2) +
                                math.pow(curr_lon_err * math.cos(
                                    curr_lat * math.pi/180.0) *
                                QPUtils.EARTH_KM_PER_DEGREE, 2)))
                            hzErrorFound = True
                        except Exception:
                            pass

                if not hzErrorFound:
                    horizontal_uncertainty_str = \
                        QPUtils.CATALOG_FILE_NAN_STRING

                # depth error
                if depth_str != QPUtils.CATALOG_FILE_NAN_STRING and \
                    hasattr(ori.depth, 'uncertainty') and \
                    ori.depth.uncertainty is not None:
                        
                    depth_uncertainty_str = str(ori.depth.uncertainty / 1000.0)
                else:
                    depth_uncertainty_str = QPUtils.CATALOG_FILE_NAN_STRING

                # magnitude error
                if mag_str != QPUtils.CATALOG_FILE_NAN_STRING and hasattr(
                    mag.mag, 'uncertainty') and \
                    mag.mag.uncertainty is not None:
                    
                    magnitude_uncertainty_str = str(mag.mag.uncertainty)
                else:
                    magnitude_uncertainty_str = QPUtils.CATALOG_FILE_NAN_STRING

                line_arr.extend([horizontal_uncertainty_str, 
                    depth_uncertainty_str, magnitude_uncertainty_str])
                
            ostream.writelines(('\t'.join(line_arr), '\n'))

    
    def importSTPPhase(self, input, **kwargs):
        """
        Import SCSN event/phase data as obtained via STP:
        http://www.data.scec.org/STP/stp.html
        
        Sata example (note: ruler shown below is not part of data)
        
                 10        20        30        40        50        60        70        80
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        
        14018180 le 2004/01/01,00:28:59.260   34.1630   -116.4237  13.14  1.52  l 1.0
            CI    BLA HHZ --   34.0695  -116.3890  1243.0 P d. w  1.0   10.87   2.760
            CI    BLA HHN --   34.0695  -116.3890  1243.0 S .. e  0.5   10.87   4.929
            CI    RMR EHZ --   34.2128  -116.5763  1663.0 P c. i  1.0   15.09   3.391
            CI    GTM EHZ --   34.2946  -116.3560   836.0 P .. e  0.5   15.89   3.362
            CI    GTM EHZ --   34.2946  -116.3560   836.0 S .. i  0.8   15.89   5.913
            CI    JVA HHZ --   34.3662  -116.6127   904.0 P c. i  1.0   28.49   5.207
            CI    JVA HHE --   34.3662  -116.6127   904.0 S .. e  0.5   28.49   8.937

        correct illegal time components: NO
        
        kwargs: nopicks=True - do not read pick lines
                authorityID  - authority id used in public ids, default: 'SCSN'
        
        """

        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'authorityID' in kwargs and isinstance(
            kwargs['authorityID'], QPCore.STRING_TYPES):
            
            auth_id = kwargs['authorityID']
        else:
            auth_id = STP_AUTHORITY_ID
            
        event_line = False
        event_ctr = 0
        
        for line in istream:
            
            scsn_pars = line.split()
            
            # check type of line
            if len(scsn_pars) == STP_EVENT_PARAMETER_COUNT:
                
                ## event line
                event_line = True
                pick_ctr = 0
                
                # create event
                
                curr_id = scsn_pars[0]
                
                ev = Event(QPUtils.build_resource_identifier(auth_id, 
                    'event', curr_id))
                ev.add(self.eventParameters)
                
                # event type
                
                #le Local event (southern California events)
                #re Regional event (northern California events)
                #ts Teleseism (large event anywhere in the world)
                #qb Quarry blast
                #nt Nuclear blast
                #uk Unknown event
                #sn Sonic blast
                ev_type = scsn_pars[1]
                
                # 'unknown' events don't get an ev.type attribute
                # no distinction between local, regional, telesesmic
                if ev_type in ('le', 're', 'ts'):
                    ev.type = 'earthquake'
                
                elif ev_type == 'qb':
                    ev.type = 'quarry blast'
                
                elif ev_type == 'nt':
                    ev.type = 'nuclear explosion'
                
                elif ev_type == 'sn':
                    ev.type = 'sonic blast'

                # create origin
                ori = Origin(QPUtils.build_resource_identifier(auth_id,
                    'origin', curr_id))
                ori.add(ev)
                
                ori.latitude = RealQuantity(float(scsn_pars[3]))
                ori.longitude = RealQuantity(float(scsn_pars[4]))
                
                # NOTE: metres, QuakeML v1.2
                ori.depth = RealQuantity(1000 * float(scsn_pars[5]))
                
                # get time components
                datetime_str = scsn_pars[2]
    
                year = datetime_str[0:4]
                month = datetime_str[5:7]
                day = datetime_str[8:10]
                hour = datetime_str[11:13]
                mins = datetime_str[14:16]
                sec = datetime_str[17:]
                ori.time = TimeQuantity(QPDateTime.QPDateTime((int(year), 
                    int(month), int(day), int(hour), int(mins), float(sec))))
                
                # create magnitude
                mag = Magnitude(QPUtils.build_resource_identifier(auth_id,
                    'magnitude', curr_id))
                mag.add(ev)
                
                mag.mag = RealQuantity(float(scsn_pars[6]))
                
                # magnitude type
                mag_type = scsn_pars[7]
                
                #b = body-wave magnitude (MB)
                #l = local magnitude (ML)
                #s = surface-wave magnitude (MS)
                #c = coda magnitude (Md)
                #w = moment magnitude (MW)
                
                #e = energy magnitude (ME)
                #h = helicorder magnitude
                #n = no magnitude
                
                if mag_type == 'b':
                    mag.type = 'MB'
                
                elif mag_type == 'l':
                    mag.type = 'ML'
                
                elif mag_type == 's':
                    mag.type = 'MS'
                
                elif mag_type == 'c':
                    mag.type = 'Md'
                    
                elif mag_type == 'w':
                    mag.type = 'MW'
                
                elif mag_type == 'e':
                    mag.type = 'ME'
                
                elif mag_type == 'h':
                    mag.type = 'helicorder magnitude'
                    
                mag.setOriginAssociation(ori.publicID)
                
                # set preferred origin and magnitude
                ev.preferredOriginID = ori.publicID
                ev.preferredMagnitudeID = mag.publicID
                
                event_ctr += 1
                
            elif len(scsn_pars) == STP_PHASE_PARAMETER_COUNT:
                
                # if nopicks set, skip line
                if 'nopicks' in kwargs and kwargs['nopicks']:
                    continue
                    
                # if no event line defined: error
                if not event_line:
                    raise RuntimeError, "phase line without event"
                
                ## phase line
                pick_ctr = pick_ctr + 1
                
                # create pick
                curr_pickid = QPUtils.build_resource_identifier(auth_id, 
                    'event', "%s/pick/%s" % (curr_id, pick_ctr))
                pick = Pick(curr_pickid)
                
                # get pick time (origin time plus time diff in column 13)
                pick.time = TimeQuantity(QPDateTime.QPDateTime(
                    ori.time.value.datetime + DateTimeDeltaFromSeconds(
                    float(scsn_pars[12]))))
                
                # get waveform id
                pick.waveformID = WaveformStreamID(
                    scsn_pars[0], scsn_pars[1], scsn_pars[2])
                
                if scsn_pars[3] != STP_LOCATION_CODE_PLACEHOLDER:
                    pick.waveformID.locationCode = scsn_pars[3]
                    
                # onset
                if scsn_pars[9].lower() == 'e':
                    pick.onset = 'emergent'
                elif scsn_pars[9].lower() == 'i':
                    pick.onset = 'impulsive'
                elif scsn_pars[9].lower() == 'w':
                    pick.onset = 'questionable'
                
                # polarity
                #The first character represents short-period channels
                #c=compression, d=dilation, .=empty character position

                # NOTE: we only use information for short-period channels 
                # compression - "up" - positive
                # dilation - "down" - negative
                if scsn_pars[8][0].lower() == 'c':
                    pick.polarity = 'positive'
                elif scsn_pars[8][0].lower() == 'd':
                    pick.polarity = 'negative'
                else:
                    pick.polarity = 'undecidable'
                    
                pick.add(ev)
                
                # create arrival
                arrv = Arrival()
                arrv.pickID = curr_pickid
                arrv.phase = Phase(scsn_pars[7])

                # epicentral distance and azimuth
                
                # NOTE: STP phase format has epicentral distance in kilometres
                # This is not explicitly stated in the manual, but can be 
                # inferred from example data.
                
                # Since coordinates of the station are given in the phase
                # line, we compute azimuth and epicentral distance in degrees,
                # as it is required for QuakeML 1.2
                
                # The provided distance in km is ignored. 

                sta_lat = float(scsn_pars[4])
                sta_lon = float(scsn_pars[5])
                
                az, baz, dist, foo = QPUtils.geodetic_azimuth_distance(
                    (ori.latitude.value, ori.longitude.value), 
                    (sta_lat, sta_lon))
                
                arrv.distance = dist
                arrv.azimuth = az
                
                arrv.add(ori)
                
            elif len(scsn_pars) == 0:
                # skip empty line
                continue
            else:
                raise RuntimeError, "format error in input stream"

    
    def importCMT(self, input, **kwargs):
        """
        TODO(fab): avoid 'magic numbers' in import and export
        
        import data from Global CMT catalog in NDK format:
            http://www.globalcmt.org/
            http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/allorder.ndk_explained

        data example (note: ruler shown below is not part of data)
        
                 10        20        30        40        50        60        70        80
        12345678901234567890123456789012345678901234567890123456789012345678901234567890

        PDE  2005/01/01 01:20:05.4  13.78  -88.78 193.1 5.0 0.0 EL SALVADOR             
        C200501010120A   B:  4    4  40 S: 27   33  50 M:  0    0   0 CMT: 1 TRIHD:  0.6
        CENTROID:     -0.3 0.9  13.76 0.06  -89.08 0.09 162.8 12.5 FREE S-20050322125201
        23  0.838 0.201 -0.005 0.231 -0.833 0.270  1.050 0.121 -0.369 0.161  0.044 0.240
        V10   1.581 56  12  -0.537 23 140  -1.044 24 241   1.312   9 29  142 133 72   66
        PDE  2005/01/01 01:42:24.9   7.29   93.92  30.0 5.1 0.0 NICOBAR ISLANDS, INDIA R
        C200501010142A   B: 17   27  40 S: 41   58  50 M:  0    0   0 CMT: 1 TRIHD:  0.7
        CENTROID:     -1.1 0.8   7.24 0.04   93.96 0.04  12.0  0.0 BDY  S-20050322125628
        23 -1.310 0.212  2.320 0.166 -1.010 0.241  0.013 0.535 -2.570 0.668  1.780 0.151
        V10   3.376 16 149   0.611 43  44  -3.987 43 254   3.681 282 48  -23  28 73 -136

        correct illegal time components: YES (correct seconds=60.0 by hand)
        
        """
        
        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        line_ctr = 0
        target_line = 0
        
        for line in istream:
            # line  event_ctr  ev_line_ctr
            # 0     0          0
            # 1     0          1
            # 2     0          2
            # 3     0          3
            # 4     0          4
            # 5     1          0
            # 6     1          1
            # 7     1          2
            # 8     1          3
            # 9     1          4
            # 10    2          0
            
            # current event counter: use integer division
            # current line in event = line_ctr modulo 5
            event_ctr, ev_line_ctr = divmod(int(line_ctr), 
                int(CMT_LINES_PER_EVENT))
            
            # truncate line to 80 chars (remove trailing newline chars)
            line = line[0:CMT_LINE_LENGTH]
                
            if line_ctr < target_line:
                line_ctr = line_ctr+1
                continue

            if ev_line_ctr == 0:

                # First line: Hypocenter line
                # 12345678901234567890123456789012345678901234567890123456789012345678901234567890
                
                # PDE  2005/01/01 01:20:05.4  13.78  -88.78 193.1 5.0 0.0 EL SALVADOR
                #[1-4]   Hypocenter reference catalog (e.g., PDE for USGS location, ISC for
                        #ISC catalog, SWE for surface-wave location, [Ekstrom, BSSA, 2006])
                #[6-15]  Date of reference event
                #[17-26] Time of reference event
                #[28-33] Latitude
                #[35-41] Longitude
                #[43-47] Depth
                #[49-55] Reported magnitudes, usually mb and MS
                #[57-80] Geographical location (24 characters)

                try:
                    ref_catalog       = line[0:4].strip()
                    curr_date_str     = line[5:15].strip()
                    curr_time_str     = line[15:26].strip()
                    curr_lat          = float( line[26:33].strip() )
                    curr_lon          = float( line[33:41].strip() )
                    curr_depth        = 1000 * float( line[41:47].strip() )
                    curr_mag_str      = line[47:55].strip()
                    curr_location_str = line[55:80].strip()
                except Exception:
                    print " error in hypocenter input line %s: %s" % ( line_ctr, line )
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue
                
                ev = Event()
                ev.add(self.eventParameters)

                # check if curr_location_str is set (is sometimes missing in NDK file)
                if curr_location_str != '':

                    # sanitize curr_location_str for XML
                    curr_location_str_xml = saxutils.escape(curr_location_str)
                    descr = EventDescription(curr_location_str_xml, 
                        EVENT_DESCRIPTION_REGION_NAME_STRING)
                    ev.description.append(descr)

                ori = Origin()
                ori.add(ev)
                
                # write reference catalog code to origin comment, if not empty string
                # this may be changed in a later version of QuakeML
                if ref_catalog:
                    ct = Comment("CMT:catalog=%s" % ref_catalog)
                    ori.comment.append(ct)
                
                ori.latitude  = RealQuantity( curr_lat )
                ori.longitude = RealQuantity( curr_lon )
                ori.depth     = RealQuantity( curr_depth )
                
                # get time components
                try:
                    year   = int( curr_date_str[0:4] )
                    month  = int( curr_date_str[5:7] )
                    day    = int( curr_date_str[8:10] )
                    hour   = int( curr_time_str[0:2] )
                    mins   = int( curr_time_str[3:5] )
                    sec    = float( curr_time_str[6:] )
                except Exception:
                    print " date/time error in input line %s: %s" % (line_ctr,
                        curr_time_str)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue

                # TODO(fab): use time correction mechanism
                # look if seconds are 60.0 (can occur in NDK format)
                # in that case, set seconds to 59, create time object, 
                # and add one second
                add_second = False
                if sec == 60.0:
                    sec = 59.0
                    add_second = True
                    
                try:
                    ori.time = TimeQuantity(QPDateTime.QPDateTime((year, 
                        month, day, hour, mins, sec)))
                except ValueError:
                    print " TimeQuantity error in input line ", \
                        line_ctr, " ", curr_time_str, " seconds: ", sec
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue

                # if required, add one second to ori.time
                if add_second:
                    ori.time = TimeQuantity(QPDateTime.QPDateTime(
                        ori.time.value.datetime + DateTimeDeltaFromSeconds(
                        1.0)))
                                           
                # two magnitude values, 2nd can be 0.0 
                # (that means, it is not set)
                try:
                    curr_mag_arr = [float(curr_mag_str[0:4].strip()),
                        float(curr_mag_str[4:8].strip())]
                except Exception:
                    print " magnitude error in input line %s: %s" % (line_ctr,
                        curr_mag_str)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue
                    
                for curr_mag_idx, curr_mag in enumerate(curr_mag_arr):

                    # if one of the magnitudes is 0.0, skip
                    if curr_mag > 0.0:
                        mag = Magnitude()
                        mag.mag = RealQuantity(curr_mag)

                        if curr_mag_idx == 0:
                            # first magnitude is always there, is preferred
                            mag.type = 'mb'
                            ev.preferredMagnitudeID = mag.publicID
                        elif curr_mag_idx == 1:
                            mag.type = 'MS'

                        mag.add(ev)
                        mag.setOriginAssociation(ori.publicID)

            elif ev_line_ctr == 1:
                # Second line: CMT info (1)
                # 12345678901234567890123456789012345678901234567890123456789012345678901234567890
                
                # C200501010120A   B:  4    4  40 S: 27   33  50 M:  0    0   0 CMT: 1 TRIHD:  0.6
                #[1-16]  CMT event name. This string is a unique CMT-event identifier. Older
                        #events have 8-character names, current ones have 14-character names.
                        #See note (1) below for the naming conventions used.
                #[18-61] Data used in the CMT inversion. Three data types may be used: 
                        #Long-period body waves (B), Intermediate-period surface waves (S),
                        #and long-period mantle waves (M). For each data type, three values
                        #are given: the number of stations used, the number of components 
                        #used, and the shortest period used.
                #[63-68] Type of source inverted for: "CMT: 0" - general moment tensor; 
                        #"CMT: 1" - moment tensor with constraint of zero trace (standard); 
                        #"CMT: 2" - double-couple source.
                #[70-80] Type and duration of moment-rate function assumed in the inversion. 
                        #"TRIHD" indicates a triangular moment-rate function, "BOXHD" indicates
                        #a boxcar moment-rate function. The value given is half the duration
                        #of the moment-rate function. This value is assumed in the inversion,
                        #following a standard scaling relationship (see note (2) below),
                        #and is not derived from the analysis.

                ev_name = line[0:16].strip()
                data_used_str = line[17:61].strip()
                source_type_str = line[62:68].strip()
                moment_rate_str = line[69:80].strip()

                fm = FocalMechanism(QPUtils.build_resource_identifier(
                    CMT_AUTHORITY_KEY, 'cmt', ev_name))
                
                fm.triggeringOriginID = ori.publicID
                fm.add(ev)
                
                mt = MomentTensor()

                ## dataUsed
                du_fields = re.match( r'^B:(.+)S:(.+)M:(.+)$', data_used_str )

                # split dataUsed string into components
                du_B_part = du_fields.group(1)
                du_S_part = du_fields.group(2)
                du_M_part = du_fields.group(3)
                
                ## long-period body waves
                try:
                    du_B_1 = int( du_B_part[0:3].strip() )
                    du_B_2 = int( du_B_part[3:8].strip() )
                    du_B_3 = float( du_B_part[8:12].strip() )
                except Exception:
                    print " error (dataUsed B) in input line %s: %s" % (
                        line_ctr, du_B_part)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue
                
                # only create object if first value (number of stations) is not zero
                if du_B_1 > 0:
                    du_B = DataUsed( 'body waves', du_B_1, du_B_2, du_B_3 )
                    mt.dataUsed.append( du_B )

                ## intermediate-period surface waves
                try:
                    du_S_1 = int( du_S_part[0:3].strip() )
                    du_S_2 = int( du_S_part[3:8].strip() )
                    du_S_3 = float( du_S_part[8:12].strip() )
                except Exception:
                    print " error (dataUsed S) in input line %s: %s" % (
                        line_ctr, du_S_part)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue
                
                # only create object if first value (number of stations) is not zero
                if du_S_1 > 0:
                    du_S = DataUsed( 'surface waves', du_S_1, du_S_2, du_S_3 )
                    mt.dataUsed.append( du_S )

                ## long-period mantle waves
                try:
                    du_M_1 = int( du_M_part[0:3].strip() )
                    du_M_2 = int( du_M_part[3:8].strip() )
                    du_M_3 = float( du_M_part[8:12].strip() )
                except Exception:
                    print " error (dataUsed M) in input line %s: %s" % (
                        line_ctr, du_M_part)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue
                
                # only create object if first value (number of stations) is not zero
                if du_M_1 > 0:
                    du_M = DataUsed( 'mantle waves', du_M_1, du_M_2, du_M_3 )
                    mt.dataUsed.append( du_M )

                # method
                method_nr_fields = re.match( r'^CMT:(.+)$', source_type_str )
                method_nr_arr = method_nr_fields.group(1).split()

                if int( method_nr_arr[0] ) == 0:
                    method_nr_str = 'general'
                elif int( method_nr_arr[0] ) == 1:
                    method_nr_str = 'zero trace'
                elif int( method_nr_arr[0] ) == 2:
                    method_nr_str = 'double couple'
                else:
                    raise RuntimeError, "illegal MomentTensor method"
                
                mt.inversionType = method_nr_str

                # sourceTimeFunction
                source_time_arr = moment_rate_str.split(':')
                source_time_type = source_time_arr[0].strip()
                source_time_duration = 2.0 * float( source_time_arr[1].strip() )

                if source_time_type == 'TRIHD':
                    source_time_type_str = 'triangle'
                elif source_time_type == 'BOXHD':
                    source_time_type_str = 'box car'
                else:
                    source_time_type_str = 'unknown'
                mt.sourceTimeFunction = SourceTimeFunction(
                    source_time_type_str, source_time_duration)
                
                mt.add(fm)
                ev.preferredFocalMechanismID = fm.publicID
                
            elif ev_line_ctr == 2:
                # Third line: CMT info (2)
                # 12345678901234567890123456789012345678901234567890123456789012345678901234567890
                
                # CENTROID:     -0.3 0.9  13.76 0.06  -89.08 0.09 162.8 12.5 FREE S-20050322125201
                #[1-58]  Centroid parameters determined in the inversion. Centroid time, given
                        #with respect to the reference time, centroid latitude, centroid
                        #longitude, and centroid depth. The value of each variable is followed
                        #by its estimated standard error. See note (3) below for cases in
                        #which the hypocentral coordinates are held fixed.
                #[60-63] Type of depth. "FREE" indicates that the depth was a result of the
                        #inversion; "FIX " that the depth was fixed and not inverted for;
                        #"BDY " that the depth was fixed based on modeling of broad-band 
                        #P waveforms.
                #[65-80] Timestamp. This 16-character string identifies the type of analysis that
                        #led to the given CMT results and, for recent events, the date and 
                        #time of the analysis. This is useful to distinguish Quick CMTs ("Q-"), 
                        #calculated within hours of an event, from Standard CMTs ("S-"), which 
                        #are calculated later. The format for this string should not be 
                        #considered fixed.
                        
                centroid_par_str = line[0:58].strip()
                depth_type       = line[59:63].strip()
                timestamp_str    = line[64:80].strip()

                try:
                    curr_time      = float( centroid_par_str[9:18].strip() )
                    curr_time_err  = float( centroid_par_str[18:22].strip() )
                    curr_lat       = float( centroid_par_str[22:29].strip() )
                    curr_lat_err   = float( centroid_par_str[29:34].strip() )
                    curr_lon       = float( centroid_par_str[34:42].strip() )
                    curr_lon_err   = float( centroid_par_str[42:47].strip() )
                    curr_depth     = 1000 * float(
                        centroid_par_str[47:53].strip())
                    curr_depth_err = 1000 * float(
                        centroid_par_str[53:58].strip())
                except Exception:
                    print " error (centroid) in input line %s: %s" % (
                        line_ctr, centroid_par_str)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue
                
                # origin from inversion
                ori_inv = Origin()
                mt.derivedOriginID = ori_inv.publicID
                ori_inv.add(ev)

                # set origin from mt inversion as preferred origin
                ev.preferredOriginID = ori_inv.publicID

                ori_inv.latitude  = RealQuantity( curr_lat, curr_lat_err )
                ori_inv.longitude = RealQuantity( curr_lon, curr_lon_err )
                ori_inv.depth     = RealQuantity( curr_depth, curr_depth_err )

                # add seconds of centroid correction to time from triggering origin
                inv_time = ori.time.value.datetime + DateTimeDeltaFromSeconds( curr_time )
                ori_inv.time = TimeQuantity(QPDateTime.QPDateTime(inv_time),  
                    curr_time_err)
                                      
                # depth type
                if depth_type == 'FREE':
                    depth_type_str = 'from moment tensor inversion'
                elif depth_type == 'FIX':
                    depth_type_str = 'from location'
                elif depth_type == 'BDY':
                    depth_type_str = 'from modeling of broad-band P waveforms'
                else:
                    depth_type_str = 'other'

                ori_inv.depthType = depth_type_str

                if timestamp_str[0:1] == 'S':
                    analysis = 'standard'
                elif timestamp_str[0:1] == 'Q':
                    analysis = 'quick'
                else:
                    analysis = ''
                
                ct = Comment("CMT:analysis=%s" % analysis)
                mt.comment.append(ct)

                # check if timestamp is valid (not valid if it starts with 0)
                if not timestamp_str[2:3] == '0':
                    
                    curr_datetime = QPDateTime.QPDateTime(
                        (int(timestamp_str[2:6]),
                        int(timestamp_str[6:8]),
                        int(timestamp_str[8:10]),
                        int(timestamp_str[10:12]),
                        int(timestamp_str[12:14]),
                        float(timestamp_str[14:])))

                    mt.creationInfo = CreationInfo(creationTime=curr_datetime)
                    fm.creationInfo = CreationInfo(creationTime=curr_datetime)
                 
            elif ev_line_ctr == 3:
                # Fourth line: CMT info (3)
                # 12345678901234567890123456789012345678901234567890123456789012345678901234567890
                
                # 23 -1.310 0.212  2.320 0.166 -1.010 0.241  0.013 0.535 -2.570 0.668  1.780 0.151
                #[1-2]   The exponent for all following moment values. For example, if the
                        #exponent is given as 24, the moment values that follow, expressed in 
                        #dyne-cm, should be multiplied by 10**24.
                #[3-80]  The six moment-tensor elements: Mrr, Mtt, Mpp, Mrt, Mrp, Mtp, where r
                        #is up, t is south, and p is east. See Aki and Richards for conversions
                        #to other coordinate systems. The value of each moment-tensor
                    #element is followed by its estimated standard error. See note (4)
                    #below for cases in which some elements are constrained in the inversion.

                # errors are non-negative, therefore use only 6 digits (values use 7 digits)

                try:

                    moment_exponent = int( line[0:2].strip() )
                    
                    mrr             = float( line[2:9].strip() )
                    mrr_err         = float( line[9:15].strip() )
                    mtt             = float( line[15:22].strip() )
                    mtt_err         = float( line[22:28].strip() )
                    mpp             = float( line[28:35].strip() )
                    mpp_err         = float( line[35:41].strip() )
                    mrt             = float( line[41:48].strip() )
                    mrt_err         = float( line[48:54].strip() )
                    mrp             = float( line[54:61].strip() )
                    mrp_err         = float( line[61:67].strip() )
                    mtp             = float( line[67:74].strip() )
                    mtp_err         = float( line[74:80].strip() )
                    
                except Exception:
                    print " error (tensor) in input line %s: %s" % (line_ctr,
                        line)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue

                mt.tensor = Tensor(
                    RealQuantity(
                        QPUtils.exponentialFloatFromString( mrr, moment_exponent ),
                        QPUtils.exponentialFloatFromString( mrr_err, moment_exponent ) ),
                    RealQuantity(
                        QPUtils.exponentialFloatFromString( mtt, moment_exponent ),
                        QPUtils.exponentialFloatFromString( mtt_err, moment_exponent ) ),
                    RealQuantity(
                        QPUtils.exponentialFloatFromString( mpp, moment_exponent ),
                        QPUtils.exponentialFloatFromString( mpp_err, moment_exponent ) ),
                    RealQuantity(
                        QPUtils.exponentialFloatFromString( mrt, moment_exponent ),
                        QPUtils.exponentialFloatFromString( mrt_err, moment_exponent ) ),
                    RealQuantity(
                        QPUtils.exponentialFloatFromString( mrp, moment_exponent ),
                        QPUtils.exponentialFloatFromString( mrp_err, moment_exponent ) ),
                    RealQuantity(
                        QPUtils.exponentialFloatFromString( mtp, moment_exponent ),
                        QPUtils.exponentialFloatFromString( mtp_err, moment_exponent ) ) )
                                    
            elif ev_line_ctr == 4:
                # Fifth line: CMT info (4)
                # 12345678901234567890123456789012345678901234567890123456789012345678901234567890
                
                # V10   1.581 56  12  -0.537 23 140  -1.044 24 241   1.312   9 29  142 133 72   66
                #[1-3]   Version code. This three-character string is used to track the version 
                        #of the program that generates the "ndk" file.
                #[5-48]  Moment tensor expressed in its principal-axis system: eigenvalue,
                        #plunge, and azimuth of the three eigenvectors. The eigenvalue should be
                        #multiplied by 10**(exponent) as given on line four.
                #[50-56] Scalar moment, to be multiplied by 10**(exponent) as given on line four.
                #[58-80] Strike, dip, and rake for first nodal plane of the best-double-couple 
                        #mechanism, repeated for the second nodal plane. The angles are defined
                        #as in Aki and Richards.

                # dip is only from 0-90 degrees, therefore uses only 2 digits
                        
                try:
                    version_str         = line[0:3].strip()

                    pa_ei_1             = float( line[3:11].strip() )
                    pa_pl_1             = float( line[11:14].strip() )
                    pa_az_1             = float( line[14:18].strip() )

                    pa_ei_2             = float( line[18:26].strip() )
                    pa_pl_2             = float( line[26:29].strip() )
                    pa_az_2             = float( line[29:33].strip() )

                    pa_ei_3             = float( line[33:41].strip() )
                    pa_pl_3             = float( line[41:44].strip() )
                    pa_az_3             = float( line[44:48].strip() )

                    scalar_moment       = float( line[48:56].strip() )

                    np_st_1             = float( line[56:60].strip() )
                    np_di_1             = float( line[60:63].strip() )
                    np_ra_1             = float( line[63:68].strip() )

                    np_st_2             = float( line[68:72].strip() )
                    np_di_2             = float( line[72:75].strip() )
                    np_ra_2             = float( line[75:80].strip() )
                    
                except Exception:
                    print " error (principal axes/nodal planes) in input "\
                        "line %s: %s" % (line_ctr, line)
                    target_line = line_ctr + CMT_LINES_PER_EVENT - ev_line_ctr
                    line_ctr = line_ctr + 1
                    continue

                ct = Comment("CMT:cmtVersion=%s" % version_str)
                mt.comment.append(ct)
                
                # scalar moment M0 (in dyne*cm) to moment magnitude MW:
                # Kanamori (1977): MW = (2/3)*(log10(M0) - 16.1)
                # see http://www.globalcmt.org/CMTsearch.html#MWnote
                mt.scalarMoment = RealQuantity(
                    QPUtils.exponentialFloatFromString(scalar_moment, 
                        moment_exponent))
                
                mag = Magnitude(QPUtils.build_resource_identifier(
                    CMT_AUTHORITY_KEY, 'magnitude', ev_name))
                mag.add(ev)
                
                mag.mag = RealQuantity(2 * (math.log10(
                    mt.scalarMoment.value) - 16.1) / 3.0)
                mag.type = 'MW'
                mag.setOriginAssociation(ori.publicID)
                ev.preferredMagnitudeID = mag.publicID

                fm.principalAxes = PrincipalAxes(
                    Axis( RealQuantity( pa_az_1 ),
                        RealQuantity( pa_pl_1 ),
                        RealQuantity(
                            QPUtils.exponentialFloatFromString( pa_ei_1, moment_exponent ) ) ),
                    Axis( RealQuantity( pa_az_2 ),
                        RealQuantity( pa_pl_2 ),
                        RealQuantity(
                            QPUtils.exponentialFloatFromString( pa_ei_2, moment_exponent ) ) ),
                    Axis( RealQuantity( pa_az_3 ),
                        RealQuantity( pa_pl_3 ),
                        RealQuantity(
                            QPUtils.exponentialFloatFromString( pa_ei_3, moment_exponent ) ) ) )

                fm.nodalPlanes = NodalPlanes(
                    NodalPlane(
                        RealQuantity( np_st_1 ),
                        RealQuantity( np_di_1 ),
                        RealQuantity( np_ra_1 ) ),
                    NodalPlane(
                        RealQuantity( np_st_2 ),
                        RealQuantity( np_di_2 ),
                        RealQuantity( np_ra_2 ) ) )

                
            else:
                raise RuntimeError, "error (never get here)"

            # everything fine, increase line_ctr and target_line
            line_ctr    = line_ctr+1
            target_line = target_line+1


    def exportCMT(self, output, **kwargs):
        """
        Output earthquake catalog in NDK format (Global CMT):
        
        http://www.globalcmt.org/
        http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/allorder.ndk_explained
        
                 10        20        30        40        50        60        70        80
        12345678901234567890123456789012345678901234567890123456789012345678901234567890

      
        PDE  2005/01/01 01:20:05.4  13.78  -88.78 193.1 5.0 0.0 EL SALVADOR             
        C200501010120A   B:  4    4  40 S: 27   33  50 M:  0    0   0 CMT: 1 TRIHD:  0.6
        CENTROID:     -0.3 0.9  13.76 0.06  -89.08 0.09 162.8 12.5 FREE S-20050322125201
        23  0.838 0.201 -0.005 0.231 -0.833 0.270  1.050 0.121 -0.369 0.161  0.044 0.240
        V10   1.581 56  12  -0.537 23 140  -1.044 24 241   1.312   9 29  142 133 72   66
        PDE  2005/01/01 01:42:24.9   7.29   93.92  30.0 5.1 0.0 NICOBAR ISLANDS, INDIA R
        C200501010142A   B: 17   27  40 S: 41   58  50 M:  0    0   0 CMT: 1 TRIHD:  0.7
        CENTROID:     -1.1 0.8   7.24 0.04   93.96 0.04  12.0  0.0 BDY  S-20050322125628
        23 -1.310 0.212  2.320 0.166 -1.010 0.241  0.013 0.535 -2.570 0.668  1.780 0.151
        V10   3.376 16 149   0.611 43  44  -3.987 43 254   3.681 282 48  -23  28 73 -136
        """

        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData(output, **kwargs)
        else:
            ostream = output

        ## loop over events, use preferred origin
        for curr_ev in self.eventParameters.event:

            # get shortcuts for required objects
            fm = curr_ev.getPreferredFocalMechanism()

            # NOTE: can there be more than one moment tensor?
            mt = fm.momentTensor[0]

            trig_ori = curr_ev.getOrigin(fm.triggeringOriginID)
            derived_ori = curr_ev.getOrigin(mt.derivedOriginID)

            # First line: Hypocenter line
            # 12345678901234567890123456789012345678901234567890123456789012345678901234567890

            # PDE  2005/01/01 01:20:05.4  13.78  -88.78 193.1 5.0 0.0 EL SALVADOR
            
            #[1-4]   Hypocenter reference catalog (e.g., PDE for USGS location, ISC for
                    #ISC catalog, SWE for surface-wave location, [Ekstrom, BSSA, 2006])
            #[6-15]  Date of reference event
            #[17-26] Time of reference event
            #[28-33] Latitude
            #[35-41] Longitude
            #[43-47] Depth
            #[49-55] Reported magnitudes, usually mb and MS
            #[57-80] Geographical location (24 characters)

            # look if hypocenter reference is there
            # ('micro-format' in comment of triggering origin)
            match_str = r'CMT:catalog=(.*)'
            hyporef = None
            for curr_co in trig_ori.comment:
                matches = re.match( match_str, curr_co.text )
                if ( matches is not None and matches.group(1).strip() > 0 ):
                    hyporef = matches.group(1).strip()
                    break

            if hyporef is not None:
                # add a space char after max. 4 chars of hyporef
                ostream.write( '%-4s ' % string.upper(hyporef) )
            else:
                ostream.write( '     ' )

            # date/time of triggering origin
            # TODO(fab): seconds fraction
            datetime_str = trig_ori.time.value.datetime.strftime(
                '%Y/%m/%d %H:%M:%S')
            ostream.write( '%-21s' % datetime_str )

            # lat
            ostream.write( '%7.2f' % trig_ori.latitude.value )
            
            # lon
            ostream.write( '%8.2f' % trig_ori.longitude.value )

            # depth
            if trig_ori.depth.value is not None:
                ostream.write( '%6.1f' % (trig_ori.depth.value / 1000.0) )
            else:
                ostream.write( '%6.1f' % 0.0 )
            
            # mb
            mags = curr_ev.getMagnitudes( trig_ori )
            
            mb = None
            for curr_mag in mags:

                if curr_mag.type.lower() == 'mb':
                    mb = curr_mag.mag.value
                    break

            if mb is None:
                mb = 0.0

            ostream.write( '%4.1f' % float(mb) )

            # MS
            ms = None
            for curr_mag in mags:

                if curr_mag.type.lower() == 'ms':
                    ms = curr_mag.mag.value
                    break

            if ms is None:
                ms = 0.0

            ostream.write( '%4.1f' % float(ms) )
            
            # description (uppercase)
            desc_found = None
            for desc in curr_ev.description:

                if desc.type == EVENT_DESCRIPTION_REGION_NAME_STRING:
                    desc_found = desc.text.encode('ascii').upper()
                    break

            if desc_found is None:
                desc_found = ''

            # write leading space char before description
            ostream.write( ' %-24s' % desc_found )
            ostream.write( '\n' )
            
            ## 2nd line ()
            # Second line: CMT info (1)
            # 12345678901234567890123456789012345678901234567890123456789012345678901234567890

            # C200501010120A   B:  4    4  40 S: 27   33  50 M:  0    0   0 CMT: 1 TRIHD:  0.6
            #[1-16]  CMT event name. This string is a unique CMT-event identifier. Older
                    #events have 8-character names, current ones have 14-character names.
                    #See note (1) below for the naming conventions used.
            #[18-61] Data used in the CMT inversion. Three data types may be used:
                    #Long-period body waves (B), Intermediate-period surface waves (S),
                    #and long-period mantle waves (M). For each data type, three values
                    #are given: the number of stations used, the number of components
                    #used, and the shortest period used.
            #[63-68] Type of source inverted for: "CMT: 0" - general moment tensor;
                    #"CMT: 1" - moment tensor with constraint of zero trace (standard);
                    #"CMT: 2" - double-couple source.
            #[70-80] Type and duration of moment-rate function assumed in the inversion.
                    #"TRIHD" indicates a triangular moment-rate function, "BOXHD" indicates
                    #a boxcar moment-rate function. The value given is half the duration
                    #of the moment-rate function. This value is assumed in the inversion,
                    #following a standard scaling relationship (see note (2) below),
                    #and is not derived from the analysis.

            fm_pid_start = QPUtils.build_resource_identifier(
                CMT_AUTHORITY_KEY, 'cmt', '')
            
            if fm.publicID.startswith(fm_pid_start):
                cmtName = fm.publicID[len(fm_pid_start):]
            else:
                cmtName = ''
            
            ostream.write( '%-16s' % cmtName )

            # fill different types (B, S, M) of dataUsed
            # if not set, set to 0
            ( bStaCnt, bCompCnt, bShortestPeriod ) = ( None, None, None )
            ( sStaCnt, sCompCnt, sShortestPeriod ) = ( None, None, None )
            ( mStaCnt, mCompCnt, mShortestPeriod ) = ( None, None, None )

            for du in mt.dataUsed:
                if du.waveType.lower() == 'body waves':
                    bStaCnt         = du.stationCount
                    bCompCnt        = du.componentCount
                    bShortestPeriod = du.shortestPeriod
                if du.waveType.lower() == 'surface waves':
                    sStaCnt         = du.stationCount
                    sCompCnt        = du.componentCount
                    sShortestPeriod = du.shortestPeriod
                if du.waveType.lower() == 'mantle waves':
                    mStaCnt         = du.stationCount
                    mCompCnt        = du.componentCount
                    mShortestPeriod = du.shortestPeriod

                    
            ostream.write( ' B:' )
            ostream.write( '%3d' % ( 
                bStaCnt is not None and [int(bStaCnt)] or [0] )[0] )
            ostream.write( '%5d' % ( 
                bCompCnt is not None and [int(bCompCnt)] or [0] )[0] )
            ostream.write( '%4d' % ( 
                bShortestPeriod is not None and [int(bShortestPeriod)] or [0] )[0] )

            ostream.write( ' S:' )
            ostream.write( '%3d' % ( 
                sStaCnt is not None and [int(sStaCnt)] or [0] )[0] )
            ostream.write( '%5d' % ( 
                sCompCnt is not None and [int(sCompCnt)] or [0] )[0] )
            ostream.write( '%4d' % ( 
                sShortestPeriod is not None and [int(sShortestPeriod)] or [0] )[0] )

            ostream.write( ' M:' )
            ostream.write( '%3d' % ( 
                mStaCnt is not None and [int(mStaCnt)] or [0] )[0] )
            ostream.write( '%5d' % ( 
                mCompCnt is not None and [int(mCompCnt)] or [0] )[0] )
            ostream.write( '%4d' % ( 
                mShortestPeriod is not None and [int(mShortestPeriod)] or [0] )[0] )

            ostream.write( ' CMT:' )

            # if moment tensor type is not set, set to default (1)
            if mt.inversionType.lower() == 'general':
                mtmethod = 0
            elif mt.inversionType.lower() in ('double couple', 
                    'double-couple'):
                mtmethod = 2
            else:
                mtmethod = 1

            ostream.write(' %1d' % mtmethod)

            # if source time function not given, set type to TRI:
            # and value to 0.0
            if mt.sourceTimeFunction.type.lower() == 'triangle':
                stf = ' TRIHD:'
            elif mt.sourceTimeFunction.type.lower() in ('box car', 'boxcar'):
                stf = ' BOXHD:'
            else:
                stf = ' TRIHD:'

            ostream.write( stf )
            ostream.write( '%5.1f' % ( 
                mt.sourceTimeFunction.duration is not None \
                and [float(0.5*mt.sourceTimeFunction.duration)] or [0] )[0] )

            ostream.write( '\n' )
            
            ## 3rd line ()
            # Third line: CMT info (2)
            # 12345678901234567890123456789012345678901234567890123456789012345678901234567890

            # CENTROID:     -0.3 0.9  13.76 0.06  -89.08 0.09 162.8 12.5 FREE S-20050322125201
            #[1-58]  Centroid parameters determined in the inversion. Centroid time, given
                    #with respect to the reference time, centroid latitude, centroid
                    #longitude, and centroid depth. The value of each variable is followed
                    #by its estimated standard error. See note (3) below for cases in
                    #which the hypocentral coordinates are held fixed.
            #[60-63] Type of depth. "FREE" indicates that the depth was a result of the
                    #inversion; "FIX " that the depth was fixed and not inverted for;
                    #"BDY " that the depth was fixed based on modeling of broad-band
                    #P waveforms.
            #[65-80] Timestamp. This 16-character string identifies the type of analysis that
                    #led to the given CMT results and, for recent events, the date and
                    #time of the analysis. This is useful to distinguish Quick CMTs ("Q-"),
                    #calculated within hours of an event, from Standard CMTs ("S-"), which
                    #are calculated later. The format for this string should not be
                    #considered fixed.

            ostream.write('CENTROID:')

            # time difference
            time_diff = derived_ori.time.value.datetime - \
                trig_ori.time.value.datetime

            ostream.write( '%9.1f' % time_diff )
            ostream.write( '%4.1f' % derived_ori.time.uncertainty )

            # latitude & error
            ostream.write( '%7.2f' % derived_ori.latitude.value )
            ostream.write( '%5.2f' % derived_ori.latitude.uncertainty )

            # longitude & error
            ostream.write( '%8.2f' % derived_ori.longitude.value )
            ostream.write( '%5.2f' % derived_ori.longitude.uncertainty )

            # depth & error
            ostream.write( '%6.1f' % (derived_ori.depth.value / 1000.0))
            ostream.write( '%5.1f' % (derived_ori.depth.uncertainty / 1000.0))

            # if depth type not given, use FIX as default
            if derived_ori.depthType.lower() == 'from moment tensor inversion':
                dt = ' FREE'
            elif derived_ori.depthType.lower() == \
                'from modeling of broad-band p waveforms':
                dt = ' BDY '
            else:
                dt = ' FIX '
                
            ostream.write( dt )
            
            # TODO(fab): if method not given, use standard 'S-' as default
            # avoid 'None'
            
            match_str = r'CMT:analysis=(.*)'
            analysis = ''
            
            for curr_co in mt.comment:
                matches = re.match( match_str, curr_co.text )
                if ( matches is not None and matches.group(1).strip() > 0 ):
                    analysis = matches.group(1).strip()
                    break
                    
            if analysis.lower() == 'quick':
                st = ' Q-'
            else:
                st = ' S-'
                
            ostream.write( st )
            if mt.creationInfo.creationTime is not None:
                ostream.write(mt.creationInfo.creationTime.datetime.strftime(
                    '%Y%m%d%H%M%S'))
            else:
                ostream.write('00000000000000')
                
            ostream.write('\n')
            
            ## 4th line ()
            # Fourth line: CMT info (3)
            # 12345678901234567890123456789012345678901234567890123456789012345678901234567890

            # 23 -1.310 0.212  2.320 0.166 -1.010 0.241  0.013 0.535 -2.570 0.668  1.780 0.151
            #[1-2]   The exponent for all following moment values. For example, if the
                    #exponent is given as 24, the moment values that follow, expressed in
                    #dyne-cm, should be multiplied by 10**24.
            #[3-80]  The six moment-tensor elements: Mrr, Mtt, Mpp, Mrt, Mrp, Mtp, where r
                    #is up, t is south, and p is east. See Aki and Richards for conversions
                    #to other coordinate systems. The value of each moment-tensor
                #element is followed by its estimated standard error. See note (4)
                #below for cases in which some elements are constrained in the inversion.

            # errors are non-negative, therefore use only 6 digits (values use 7 digits)

            # get exponent from scalar moment value
            scm_mantissa, exponent = QPUtils.normalizeFloat(
                mt.scalarMoment.value)
            power = 10**exponent
            
            ostream.write( '%02d' % exponent )
            
            ostream.write( '%7.3f' % (mt.tensor.Mrr.value / power) )
            ostream.write( '%6.3f' % (mt.tensor.Mrr.uncertainty / power) )

            ostream.write( '%7.3f' % (mt.tensor.Mtt.value / power) )
            ostream.write( '%6.3f' % (mt.tensor.Mtt.uncertainty / power) )

            ostream.write( '%7.3f' % (mt.tensor.Mpp.value / power) )
            ostream.write( '%6.3f' % (mt.tensor.Mpp.uncertainty / power) )

            ostream.write( '%7.3f' % (mt.tensor.Mrt.value / power) )
            ostream.write( '%6.3f' % (mt.tensor.Mrt.uncertainty / power) )

            ostream.write( '%7.3f' % (mt.tensor.Mrp.value / power) )
            ostream.write( '%6.3f' % (mt.tensor.Mrp.uncertainty / power) )

            ostream.write( '%7.3f' % (mt.tensor.Mtp.value / power) )
            ostream.write( '%6.3f' % (mt.tensor.Mtp.uncertainty / power) )
            
            ostream.write( '\n' )
            
            ## 5th line ()
            # Fifth line: CMT info (4)
            # 12345678901234567890123456789012345678901234567890123456789012345678901234567890

            # V10   1.581 56  12  -0.537 23 140  -1.044 24 241   1.312   9 29  142 133 72   66
            #[1-3]   Version code. This three-character string is used to track the version
                    #of the program that generates the "ndk" file.
            #[5-48]  Moment tensor expressed in its principal-axis system: eigenvalue,
                    #plunge, and azimuth of the three eigenvectors. The eigenvalue should be
                    #multiplied by 10**(exponent) as given on line four.
            #[50-56] Scalar moment, to be multiplied by 10**(exponent) as given on line four.
            #[58-80] Strike, dip, and rake for first nodal plane of the best-double-couple
                    #mechanism, repeated for the second nodal plane. The angles are defined
                    #as in Aki and Richards.

            # dip is only from 0-90 degrees, therefore uses only 2 digits

            match_str = r'CMT:cmtVersion=(.*)'
            cmtVersion = None
            
            for curr_co in mt.comment:
                matches = re.match( match_str, curr_co.text )
                if ( matches is not None and matches.group(1).strip() > 0 ):
                    cmtVersion = matches.group(1).strip()
                    break
                    
            if cmtVersion is not None:
                ostream.write('%-3s ' % cmtVersion)
            else:
                ostream.write('    ')

            ( tev, tpl, taz ) = ( None, None, None )
            ( pev, ppl, paz ) = ( None, None, None )
            ( nev, npl, naz ) = ( None, None, None )

            if fm.principalAxes is not None:
                if fm.principalAxes.tAxis is not None:
                    tev     = fm.principalAxes.tAxis.length.value / power
                    tpl     = fm.principalAxes.tAxis.plunge.value
                    taz     = fm.principalAxes.tAxis.azimuth.value
                if fm.principalAxes.pAxis is not None:
                    pev     = fm.principalAxes.pAxis.length.value / power
                    ppl     = fm.principalAxes.pAxis.plunge.value
                    paz     = fm.principalAxes.pAxis.azimuth.value
                if fm.principalAxes.nAxis is not None:
                    nev     = fm.principalAxes.nAxis.length.value / power
                    npl     = fm.principalAxes.nAxis.plunge.value
                    naz     = fm.principalAxes.nAxis.azimuth.value


            ostream.write(
                '%7.3f' % ( tev is not None and [float(tev)] or [0.0] )[0] )
            ostream.write('%3d' % ( tpl is not None and [int(tpl)] or [0] )[0])
            ostream.write('%4d' % ( taz is not None and [int(taz)] or [0] )[0])

            ostream.write(
                '%8.3f' % ( pev is not None and [float(pev)] or [0.0] )[0] )
            ostream.write( '%3d' % ( ppl is not None and [int(ppl)] or [0] )[0] )
            ostream.write( '%4d' % ( paz is not None and [int(paz)] or [0] )[0] )

            ostream.write(
                '%8.3f' % ( nev is not None and [float(nev)] or [0.0] )[0] )
            ostream.write( '%3d' % ( npl is not None and [int(npl)] or [0] )[0] )
            ostream.write( '%4d' % ( naz is not None and [int(naz)] or [0] )[0] )

            if mt.scalarMoment.value is not None:
                ostream.write( '%8.3f' % scm_mantissa )
            else:
                ostream.write( '%8.3f' % ( 0.0 ) )

            ( s1, d1, r1 ) = ( None, None, None )
            ( s2, d2, r2 ) = ( None, None, None )
            
            if fm.nodalPlanes is not None:
                if fm.nodalPlanes.nodalPlane1 is not None:
                    s1     = fm.nodalPlanes.nodalPlane1.strike.value
                    d1     = fm.nodalPlanes.nodalPlane1.dip.value
                    r1     = fm.nodalPlanes.nodalPlane1.rake.value
                if fm.nodalPlanes.nodalPlane2 is not None:
                    s2     = fm.nodalPlanes.nodalPlane2.strike.value
                    d2     = fm.nodalPlanes.nodalPlane2.dip.value
                    r2     = fm.nodalPlanes.nodalPlane2.rake.value

            ostream.write( '%4d' % ( s1 is not None and [int(s1)] or [0] )[0] )
            ostream.write( '%3d' % ( d1 is not None and [int(d1)] or [0] )[0] )
            ostream.write( '%5d' % ( r1 is not None and [int(r1)] or [0] )[0] )

            ostream.write( '%4d' % ( s2 is not None and [int(s2)] or [0] )[0] )
            ostream.write( '%3d' % ( d2 is not None and [int(d2)] or [0] )[0] )
            ostream.write( '%5d' % ( r2 is not None and [int(r2)] or [0] )[0] )
            
            ostream.write( '\n' )

    
    def importANSSUnified(self, input, **kwargs):
        """
        Import data from ANSS "reduced" unified catalog, one event per line
        
        Format description:
            http://www.ncedc.org/ftp/pub/doc/cat5/cnss.catalog.txt
        
        get monthly chunks:
            ftp://www.ncedc.org/pub/catalogs/cnss/YYYY/YYYY.MM.cnss

        data example for first 10 events from 2001.01.cnss (note: ruler shown below is not part of data)
        
                 10        20        30        40        50        60        70        80        90        100       110       120       130       140       150       160
        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012

        $loc 20010101000748.8000 34.28100-118.45000 17.7100H CI   22              0.1930        0.0000 4.6660L 20010101     9172296 $magP 1.20h CI              20010101     9172296 $add$loc                                                                                  9172296     9172296
        $loc 20010101001207.7600 38.81816-122.78683  1.7500H NC   10 50    1.0000 0.0500        0.2800 0.3700L 20070622             $magP 1.36d NC    9 0.17    20070622             $add$loc  10   0  1016418    0.2300 8015    0.290020865    0.4100                        21141544            
        $locP20010101003246.2300 45.61300  26.47900125.0000H NEI  17              0.6900                               200101014001                                                                                                                                                               
        $locP20010101005217.3600 55.57900-159.70401 56.2000H AEI  17              0.0000                               200101014002 $magP 3.30l AEI                     200101014002                                                                                                              
        $locP20010101011510.7200 18.18200 -67.13300 23.2000H RSP   4              0.0000                               200101014003 $magP 2.60l RSP                     200101014003                                                                                                              
        $loc 20010101011625.7640 35.12300-118.53800  5.1600H CI    8              0.0350        0.0000 0.4010L 20010101     9172298 $magP 1.00h CI              20010101     9172298 $add$loc                                                                                  9172298     9172298
        $loc 20010101012155.9550 35.04700-119.08300 10.9400H CI   18              0.1770        0.0000 1.7770L 20010101     9172300 $magP 1.60h CI              20010101     9172300 $add$loc                                                                                  9172300     9172300
        $loc 20010101013345.5100 36.23650-120.79283  8.0500H NC   10157    2.0000 0.0500        0.6200 0.3800L 20070622             $magP 1.37d NC    4 0.13    20070622             $add$loc  10   1   9316 6    0.290023862    0.4300 4226    0.6900                        21141564            
        $loc 20010101013549.5960 34.47000-116.04500  4.0700H CI   14              0.1350        0.0000 0.8970L 20010101     9172301 $magP 1.63c CI              20010101     9172301 $add$loc                                                                                  9172301     9172301
        $loc 20010101013808.8400 37.62933-118.98534  8.0100H NC   32 83    2.0000 0.0400        0.1900 0.3400L 20070622             $magP 1.54d NC   21 0.16    20070622             $add$loc  35   2  24265 0    0.140017512    0.190035277    0.3500                        21141567            

        correct illegal time components: NO
        
        kwargs:
            authorityID - authority id used in public ids, default: 'ANSS'
        
        """

        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'authorityID' in kwargs and isinstance(kwargs['authorityID'], 
                QPCore.STRING_TYPES):
            auth_id = kwargs['authorityID']
        else:
            auth_id = ANSS_AUTHORITY_ID
            
        line_ctr = 0
        for line in istream:

            line_ctr += 1
            
            # in order to accept a location, we require focal time, lat, lon, 
            # and depth to be present
            # ignore lines shorter than 51 characters
            if len(line.strip()) < ANSS_MINIMUM_LINE_LENGTH:
                continue

            ## get location information ($loc)

            #columns  frmt   description
            #------- -----   -------------
            #1-  4   4s    $loc
            #5-  5    s    identification for preferred location ("P") when 
                        #multiple entries present, otherwise blank
            #6-  9  *4d    year of origin time (all four digits required)
            #10- 11  *2d    month of origin time (1-12)
            #12- 13  *2d    day of origin time (1-31)
            #14- 15  *2d    hour of origin time (0-23)
            #16- 17  *2d    minutes of origin time (0-59)
            #18- 24  *7.4f  seconds of origin time (0-59.9999)
            #25- 33  *9.5f  latitude in decimal degrees (-90.00000 -  90.00000,  N = +)
            #34- 43  *10.5f longitude in decimal degrees (-180.00000 -  180.00000, E = +)
            #44- 51  *8.4f  depth in km (datum reference defined by method, + down)
            #52- 53   2s    type of location (Table 1)
            #54- 56  *3s    source code of location information (Table 2a)
            #57- 60  *4d    number of non-null weighted travel times (P & S) 
                        #used to compute this hypocenter
            #61- 63   3d    azimuthal gap in degrees
            #64- 73   10.4f distance to nearest station in km
            #74- 80   7.4f  RMS residual of phases used in location
            #81- 87   7.4f  origin time error (s)
            #88- 94   7.4f  horizontal error (km)
            #95-101   7.4f  depth error (km)
            #102-103  *2s    auxillary event remarks (Table 3)
            #104-111    8d   date solution created in the form YYYYMMDD (eg, 19960125)
            #112-123  *12d   data center id # (right justified)
            #------- -----   -------------
            
            try:
                # first get required fields
                # NOTE: 
                # "data center id" is claimed to be a required field,
                # but is often only whitespace in the cnss catalog files
                # therefore it is not treated as 'required' here
                # all fields right from depth can be missing in cnss files, 
                # are not truly required 
                # we do not process lines that are shorter that 51 characters
                curr_year   = int( line[5:9] )
                curr_month  = int( line[9:11] )
                curr_day    = int( line[11:13] )
                curr_hour   = int( line[13:15] )
                curr_minute = int( line[15:17] )
                curr_second = float( line[17:24] )
                
                curr_lat    = float( line[24:33].strip() )
                curr_lon    = float( line[33:43].strip() )
                curr_depth  = 1000 * float( line[43:51].strip() )

            except Exception:
                print " error in $loc block of line %s: %s" % (line_ctr, line)
                continue

            ## define event id
            # - do not use 'data center id' since is is not always set
            # - use location datetime block instead
            # - use datetime block also for magnitude URI below
            #   (format provides only one location & magnitude,
            #    so we there is no need to discriminate several locations and 
            #    magnitudes for same event)
            curr_id = line[5:24].strip()
            
            # create event
            ev = Event(QPUtils.build_resource_identifier(auth_id, 'event',
                curr_id))
            ev.add(self.eventParameters)

            # create origin
            ori = Origin(QPUtils.build_resource_identifier(auth_id, 'origin', 
                curr_id))
            ori.add(ev)
            
            ori.latitude = RealQuantity( curr_lat )
            ori.longitude = RealQuantity( curr_lon )
            ori.depth = RealQuantity( curr_depth )
            ori.time = TimeQuantity(QPDateTime.QPDateTime((curr_year, 
                curr_month, curr_day, curr_hour, curr_minute, curr_second)))
            
            # set preferred origin
            ev.preferredOriginID = ori.publicID

            ## get optional fields
            
            try:
                curr_loctype = line[51:53].strip()
                if curr_loctype.lower() ==  'h':
                    ori.type = 'hypocenter'
                elif curr_loctype.lower() == 'c':
                    ori.type = 'centroid'
                elif curr_loctype.lower() == 'a':
                    ori.type = 'amplitude'    
            except Exception: 
                  pass
                
            # this can be a network code or a different agency/institution ID
            # map this to creationInfo.agencyID
            try:
                curr_locsource = line[53:56].strip()
                
                if curr_locsource:
                    self.create_object_creationinfo(ori)
                    ori.creationInfo.agencyID = curr_locsource
            except Exception:
                pass
                
            try:    
                curr_traveltime_cnt = int( line[56:60].strip() )
                self.create_origin_quality(ori)
                ori.quality.usedPhaseCount = curr_traveltime_cnt
            except Exception: 
                pass
            
            try:
                curr_azimuthalGap = float( line[60:63].strip() )
                self.create_origin_quality(ori)
                ori.quality.azimuthalGap = curr_azimuthalGap
            except Exception: 
                pass

            # distance to nearest station is given in km
            try:
                curr_nearestStation = float( line[63:73].strip() )
                self.create_origin_quality(ori)
                ori.quality.minimumDistance = \
                    QPUtils.central_angle_degrees_from_distance(
                        curr_nearestStation)
            except Exception: 
                pass
            
            try:
                curr_rms_residual_phases = float( line[73:80].strip() )
                self.create_origin_quality(ori)
                ori.quality.standardError = curr_rms_residual_phases
            except Exception: 
                pass
            
            try:    
                ori.time.uncertainty = float( line[80:87].strip() )
            except Exception: 
                pass
            
            try:
                che = float( line[87:94].strip() )
                ou = OriginUncertainty.OriginUncertainty()
                ou.horizontalUncertainty = 1000 * che
                ou.add(ori)
            except Exception:
                pass
            
            try:    
                ori.depth.uncertainty = 1000 * float( line[94:101].strip() )
            except Exception: 
                pass
            
            # NOTE: QuakeML does not have EventType entries for all possible 
            # values of ANSS format
            
             #2s B = seismic reflection/refraction blast
                #L = local earthquake
                #N = nuclear test
                #Q = quarry blast
                #T = teleseism
                #R = regional earthquake
                #F = felt
                #D = damage
                #C = casualties
                #H = (Harmonic) Tremor associated
                #V = Long Period event
                        
            try:
                curr_ev_remarks = line[101:103].strip()
                
                ec = Comment("ANSS:event_type=%s" % curr_ev_remarks)
                ev.comment.append(ec)
                
                if curr_ev_remarks.lower() in ('l', 't', 'r'):
                    ev.type = 'earthquake'
                elif curr_ev_remarks.lower() == 'n':
                    ev.type = 'nuclear explosion'
                elif curr_ev_remarks.lower() == 'q':
                    ev.type = 'quarry blast'
            except Exception:
                pass
            
            # date of creation of solution, has format YYYYMMDD
            try:
                curr_solution_date = line[103:111].strip()
                cict = QPDateTime.QPDateTime(
                    (int( curr_solution_date[0:4] ), 
                    int( curr_solution_date[4:6] ), 
                    int( curr_solution_date[6:8] ) ) )
                                 
                self.create_object_creationinfo(ori)
                ori.creationInfo.creationTime = cict
            except Exception:
                pass
            
            # data center id: there is no good way to preserve 'legacy ids' 
            # in QuakeML, ignore this field
            # curr_loc_datacenterid = line[111:123].strip()
            
            ## get magnitude information ($mag)

            #columns  frmt   description
            #------- -----   -------------
            #1-  4   4s    $mag
            #5-  5    s    identification for preferred magnitude ("P") when 
                        #multiple entries present, otherwise blank
            #6- 10  *5.2f  magnitude
            #11- 12  *2s    magnitude type (Table 4)
            #13- 15  *3s    source code of magnitude information (Table 2a)
            #16- 19  *4d    number of observations for magnitude determination
            #20- 24   5.2f  error in magnitude estimate 
                        #(type of error depends on magnitude definition)
            #25- 28   4.1f  total of magnitude weights.
            #29- 36    8d   date solution created in the form YYYYMMDD (eg, 19960125)
            #37- 48  *12d   data center id # (right justified)
            #------- -----   -------
            
            # if line length > 123 chars, look for magitude information
            if len(line.strip()) > ANSS_MINIMUM_LINE_LENGTH_MAGNITUDE:

                # copy rest of line into new zero-offset string
                # $mag block goes potentially from column 125 to column 172 (48 columns, list indices 124-171)
                # but can contain fewer characters, therefore we cannot specify an end position explicitly
                mag_info = line[124:]

                ## NOTE: although documentation says that some fields are required,
                ## there lines in the cnss files with almost ALL entries missing (even magnitude value)
                ## 'source code' of magnitude information seems to be always there 
                ## input line can end after 'source code'
                ## -> we treat none of the fields as required
                ## NOTE: last field "data center id" is not padded with whitespace if missing
                
                # we need a magnitude value (is a required attribute for QuakeML)
                # skip magnitude block if magnitude is missing
                validMagBlock = True
                try:
                    curr_mag = float(mag_info[5:10].strip())
                except Exception:
                    validMagBlock = False
                    
                if validMagBlock:
                  
                    mag = Magnitude(
                        QPUtils.build_resource_identifier(
                            auth_id, 'magnitude', curr_id))
                    mag.add(ev)
                    mag.mag = RealQuantity( curr_mag )
                    mag.setOriginAssociation( ori.publicID )
                    
                    # set preferred magnitude
                    ev.preferredMagnitudeID = mag.publicID
                    
                    # write ANSS magnitude code in comment
                    
                     #2s a  = Primary amplitude magnitude (Jerry Eaton's XMAG)
                        #b  = Body-wave magnitude
                        #e  = Energy magnitude
                        #l  = Local magnitude
                        #l1 = Traditional UCB local magnitude
                        #l2 = Network UCB local magnitude
                        #lg = Lg magnitude
                        #c  = Primary coda magnitude
                        #s  = Ms - Surface-wave magnitude
                        #w  = Moment magnitude
                        #z  = Low gain (Z component) magnitude of Hirshorn and Lindh (1989)
                        #B  = magnitude estimated from 14-kg Benioff's 
                        #un = unknown magnitude type
                        #d = duration magnitude
                        #h = helicorder magnitude (CIT, short-period Benioff)
                        #n = no magnitude
                                        
                    try:
                        curr_magtype = mag_info[10:12].strip()
                        mc = Comment("ANSS:magnitude_type=%s" % curr_magtype)
                        mag.comment.append(mc)
                        
                        if curr_magtype.lower() == 'b':
                            mag.type = 'MB'
                        elif curr_magtype.lower() in ('l', 'l1', 'l2'):
                            mag.type = 'ML'
                        elif curr_magtype.lower() == 's':
                            mag.type = 'MS'
                        elif curr_magtype.lower() == 'w':
                            mag.type = 'MW'
                        elif curr_magtype.lower() == 'e':
                            mag.type = 'ME'
                        elif curr_magtype.lower() == 'c':
                            mag.type = 'Mc'
                        elif curr_magtype.lower() == 'd':
                            mag.type = 'Md'
                    except Exception:
                        pass
                    
                    try:
                        curr_magsource = mag_info[12:15].strip()
                        if curr_magsource:
                            self.create_object_creationinfo(mag)
                            mag.creationInfo.agencyID = curr_magsource
                    except Exception:
                        pass
                    
                    try:    
                        mag.stationCount = int(mag_info[15:19].strip())
                    except Exception: 
                        pass
                    
                    try:    
                        mag.mag.uncertainty = float(mag_info[19:24].strip())
                    except Exception: 
                        pass

                    # date of creation of solution, has format YYYYMMDD
                    try:
                        curr_mag_solution_date = mag_info[28:36].strip()
                        cict = QPDateTime.QPDateTime(
                            ( int( curr_mag_solution_date[0:4] ), 
                            int( curr_mag_solution_date[4:6] ), 
                            int( curr_mag_solution_date[6:8] ) ) )
                                            
                        self.create_object_creationinfo(mag)
                        mag.creationInfo.creationTime = cict
                    except Exception:
                        pass
                
                    # TODO(fab): legacy ID
                    # data center id: there is no good way to preserve 
                    # legacy IDs in QuakeML
                    # ignore this field
                    #curr_mag_datacenterid = line[36:48].strip()

            ## get additional location information ($addloc)

            #columns  frmt   description
            #------- -----   -------------
            #1-  4   4s    $add
            #5-  8   4s    $loc
            #9- 12   4d    number of valid P & S readings with non-null weights
            #13- 16   4d    number of S readings with non-null weights
            #17- 20   4d    number of P first motions
            #21- 23   3d    azimuth of smallest principal error (deg E of N)
            #24- 25   2d    dip of smallest principal error (deg)
            #26- 35   10.4f magnitude of smallest principal error (km)
            #36- 38   3d    azimuth of intermediate principal error (deg E of N)
            #39- 40   2d    dip of intermediate principal error (deg)
            #41- 50   10.4f magnitude of intermediate principal error (km)
            #51- 53   3d    azimuth of largest principal error (deg E of N)
            #54- 55   2d    dip of largest principal error (deg)
            #56- 65   10.4f magnitude of largest principal error (km)
            #66- 75   10.4f error in latitude    (km)
            #76- 85   10.4f error in longitude   (km)
            #86- 97   12d   local event id # (right justified)
            #98-109  *12d   data center id # (right justified)
            #------- -----   -------

            # if line length > 172 chars, look for additional location 
            # information
            if len(line.strip()) > ANSS_MINIMUM_LINE_LENGTH_ADDITIONAL:

                # copy remaining $addloc block into new zero-offset string
                # $addloc block can go from column 174 to column 282 
                # (109 columns, list indices 173-281)
                # NOTE: $addloc block can contain fewer characters, has no 
                # required fields
                addloc_info = line[ANSS_MINIMUM_LINE_LENGTH_ADDITIONAL+1:]
                
                try:
                    self.create_origin_quality(ori)
                    ori.quality.associatedPhaseCount = int(
                        addloc_info[8:12].strip())
                except Exception: 
                    pass
                    
                try:
                    first_motion_cnt = int(addloc_info[16:20].strip())
                    fm = FocalMechanism(
                        QPUtils.build_resource_identifier(auth_id, 
                        'focalmechanism', curr_id))
                    fm.stationPolarityCount = first_motion_cnt
                    fm.add(ev)
                    ev.preferredFocalMechanismID = fm.publicID
                except Exception:
                    pass
                
                # if lat/lon uncertainties in km are given, convert to 
                # degrees and add to quantity
                try:
                    ori.latitude.uncertainty = float(
                        addloc_info[65:75].strip()) / (
                        QPUtils.EARTH_KM_PER_DEGREE)
                except Exception:
                    pass
                
                try:
                    # if latitude is +/- 90 degrees, set longitude error to 0.0
                    # avoid division by zero
                    if abs( ori.latitude.value ) == 90.0:
                        ori.longitude.uncertainty = 0.0
                    else:
                        ori.longitude.uncertainty = float(
                            addloc_info[75:85].strip()) / (
                                QPUtils.EARTH_KM_PER_DEGREE * math.cos( 
                                    ori.latitude.value))
                except Exception:
                    pass

    
    def importPDECompressed(self, input, **kwargs):
        """
        Import data from USGS/NEIC (PDE) catalog in "compressed" format,
        one event per line.
        
        Get data from web form:
            http://neic.usgs.gov/neis/epic/epic_global.html

        Data example from web site (note: ruler shown below is not part of data)

                  10        20        30        40        50        60        70        80        90        100       110
        01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345

         GS    1987 0130222942.09  -60.063 -26.916 47  D171.416.2237.0Z266.90MsBRK  6.80MsPAS  153172...FG...........       
         GS    1987 0208183358.39   -6.088 147.689 54     1.31     7.4Z217.60MsBRK  7.00MsPAS  2072907C.FG..........M       
         GS    1987 0305091705.28  -24.388 -70.161 62  G  1.216.5667.3Z167.20MsBRK  7.00MsPAS  1223036C.FG.....T.....       
         GS    1987 0306041041.96    0.151 -77.821 10  G  1.226.5516.9Z217.00MsBRK  6.70MsPAS  106344.C.FG..........S       
         GS    1987 0706024942.78  -14.074 167.828 47     0.985.9526.6Z237.10MsBRK  6.50MsPAS  186304.F..G.....T.....       
         GS    1987 0903064013.91  -58.893 158.513 33  N  1.035.9437.3Z207.70MsBRK  6.90MsPAS  167292....G...........       
         GS    1987 1006041906.08  -17.940-172.225 16  G  1.036.7367.3Z267.30MsBRK  7.20MsPAS  174455.F.FG.....T.....       
         GS    1987 1016204801.64   -6.266 149.060 47  G  1.245.9267.4Z227.70MsBRK  7.00MsPAS  1923458D.FG.....T.....       
         GS    1987 1025165405.69   -2.323 138.364 33  N  1.126.2437.0Z196.70MsBRK  6.70MsPAS  201290.F.F............       
         GS    1987 1117084653.32AS 58.586-143.270 10  G      6.6766.9Z197.00MsBRK  7.00MLPMR  0155815FUFG.....T.....       
         GS    1987 1130192319.59   58.679-142.786 10  G      6.7577.6Z117.70MsBRK  7.10MLPMR  0155846DUFG.X...T.....       

        NOTE: column numbers are zero-offset (C style)

        0      blank
        1-5    Catalog Source (a5)
        6-11   Year (a6)
        12-13   Month (i2)
        14-15   Day (i2)
        16-24   Origin Time (f9.2)
        25-26   Coordinate/OT Auth.(a2)
        27-33   Latitude (f7.3) [-=South] 
        34-41   Longitude (f8.3) [-=West]
        42-44   Depth (i3)
        47      Depth Control Designator (a1)
        48-49   pP Phases( i2)
        50-53   Std. Dev.(4.2)
        54-56   mb magnitude (f3.1)
        57-58   mb obs (i2)
        59-61   Ms magnitude (f3.1)
        62      Z/H Component (a1)
        63-64   Ms obs. (i2)
        65-68   Magnitude1 (f4.2)
        69-70   Mag1. Scale (a2)
        71-75   Mag1 Donor (a5)
        76-79   Magnitude2 (f4.2)
        80-81   Mag2. Scale (a2)
        82-86   Mag2 Donor (a5)
        87-89   Region Number (i3)
        90-92   Sta. No./Qual. (a3)
        93      Io value (a1)
        94      Cultural Effect (a1)
        95      Isoseismal Map (a1)
        96      Fault Plane Sol. (a1)
        97      Moment Flag (a1)
        98      ISC Depth Flag (a1)
        99      IDE Flag (a1)
        100     Preferred Flag (a1)
        101     Flag (a1)
        102-108 Phenomena Codes (7a1)
        109-115 Radial Distance (a7)

        correct illegal time components: NO
        
        kwargs:
            authorityID - authority id used in public ids, default: 'PDE'
        """

        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'authorityID' in kwargs and isinstance(
                kwargs['authorityID'], QPCore.STRING_TYPES):
            auth_id = kwargs['authorityID']
        else:
            auth_id = PDE_AUTHORITY_ID
            
        line_ctr = 0
        for line in istream:

            line_ctr += 1
            
            # in order to accept a location, we require focal time, lat, lon 
            # to be present, depth can be missing
            # ignore lines shorter than 42 characters
            # use rstrip() in order to keep leading space char
            if len(line.rstrip()) < PDE_MINIMUM_LINE_LENGTH:
                continue

            try:
                # first get required fields
                # NOTE: minutes, seconds, and depth can be missing!
                curr_source = line[1:6].strip()
                
                curr_year   = int( line[6:12].strip() )
                curr_month  = int( line[12:14] )
                curr_day    = int( line[14:16] )
                
                curr_hour   = int( line[16:18] )
                curr_lat    = float( line[27:34].strip() )
                curr_lon    = float( line[34:42].strip() )
            except Exception:
                print " error in line %s: %s" % (line_ctr, line)
                continue

            # if minutes part is not given, set to 0
            try:
                curr_minute = int( line[18:20].strip() )
            except Exception:
                curr_minute = 0
                
            # if seconds part is not given, set to 0.0
            try:
                curr_second = float( line[20:25].strip() )
            except Exception:
                curr_second = 0.0

            ## define event id
            # - use year + datetime block 
            curr_id = "%s%s" % (str(curr_year), line[12:25].strip())
            
            # create event
            ev = Event(QPUtils.build_resource_identifier(auth_id, 'event',
                curr_id))
            ev.add(self.eventParameters)

            # create origin
            ori = Origin(QPUtils.build_resource_identifier(auth_id, 'origin',
                curr_id))
            ori.add(ev)
            
            ori.latitude  = RealQuantity( curr_lat )
            ori.longitude = RealQuantity( curr_lon )
            ori.time = TimeQuantity(QPDateTime.QPDateTime((curr_year, 
                curr_month, curr_day, curr_hour, curr_minute, curr_second)))
            
            # set preferred origin
            ev.preferredOriginID = ori.publicID

            ## get optional fields

            # depth
            try:
                curr_depth = 1000 * float(line[42:45].strip())
                ori.depth = RealQuantity( curr_depth )
            except Exception:
                pass
                    
            # location authority
            # map this to creationInfo.agencyID
            try:
                curr_locsource = line[25:27].strip()
                
                if curr_locsource:
                    self.create_object_creationinfo(ori)
                    ori.creationInfo.agencyID = curr_locsource
            except Exception:
                pass

            # depth control designator
            try:
                curr_depthcontrol = line[47:48].strip()

                if curr_depthcontrol:
                    oc = Comment(
                        "PDE:depth_control_designator=%s" % curr_depthcontrol)
                    ori.comment.append(oc)
                
                # TODO(fab): look up in documentatioin
                if curr_depthcontrol.lower() == 'a':
                    ori.depthType = 'operator assigned'
                elif curr_depthcontrol.lower() ==  'd':
                    ori.depthType = 'constrained by depth phases'
                elif curr_depthcontrol.lower() in ('n', 'g', 's'):
                    ori.depthType = 'other'
            except Exception: 
                  pass

            # number of pP phases for depth determination
            try:    
                curr_pP_cnt = int( line[48:50].strip() )
                self.create_origin_quality(ori)
                ori.quality.depthPhaseCount = curr_pP_cnt
            except Exception: 
                pass
                
            # standard deviation of arrival time residuals
            try:    
                curr_std_dev = float( line[50:54].strip() )
                self.create_origin_quality(ori)
                ori.quality.standardError = curr_std_dev
            except Exception: 
                pass

            # Flinn-Engdahl region
            try:
                curr_fe_region = line[87:90].strip()
                if curr_fe_region:
                    desc = EventDescription(curr_fe_region)
                    desc.type = 'Flinn-Engdahl region'
                    
                    ev.description.append( desc )
            except Exception: 
                  pass
                
            # up to 4 magnitudes
            mag_indices = [ 
                { 'from': 54, 'to': 57, 'obs_from': 57, 'obs_to': 59, 
                    'mag_type': 'mb' },
                { 'from': 59, 'to': 62, 'obs_from': 63, 'obs_to': 65, 
                    'mag_type': 'Ms' },
                { 'from': 65, 'to': 69, 'magtype_from': 69, 'magtype_to': 71, 
                    'magsrc_from': 71, 'magsrc_to': 76 },
                { 'from': 76, 'to': 80, 'magtype_from': 80, 'magtype_to': 82, 
                    'magsrc_from': 82, 'magsrc_to': 87 }]
                            
            for mag_ctr in xrange(len(mag_indices)):
                
                validMagBlock = True
                try:
                    curr_mag = float(
                        line[mag_indices[mag_ctr]['from']:\
                        mag_indices[mag_ctr]['to']].strip())
                except Exception:
                    validMagBlock = False

                if validMagBlock:
                    mag = Magnitude(QPUtils.build_resource_identifier(auth_id,
                        'magnitude',  "%s/%s" % (curr_id, mag_ctr+1)))
                    mag.add(ev)
                    mag.mag = RealQuantity( curr_mag )
                    mag.setOriginAssociation( ori.publicID )

                    # magnitude type
                    try:
                        if mag_ctr <= 1:
                            curr_magtype = mag_indices[mag_ctr]['mag_type']
                        else:    
                            curr_magtype = \
                                line[mag_indices[mag_ctr]['magtype_from']:\
                                mag_indices[mag_ctr]['magtype_to']].strip()

                        if curr_magtype:
                            mag.type = curr_magtype
                    except Exception:
                        pass

                    # source of magnitude determination 
                    # (for mb and Ms it is 'NEIS')
                    try:
                        if mag_ctr <= 1:
                            curr_magsource = PDE_MAGNITUDE_SOURCE_NEIS
                        else:
                            curr_magsource = \
                                line[mag_indices[mag_ctr]['magsrc_from']:\
                                mag_indices[mag_ctr]['magsrc_to']].strip()
                            
                        if curr_magsource:
                            self.create_object_creationinfo(mag)
                            mag.creationInfo.agencyID = curr_magsource
                    except Exception:
                        pass
                                
                    # number of observations (only for mb and Ms)
                    if mag_ctr <= 1:
                        try:
                            curr_obs = int(
                                line[mag_indices[mag_ctr]['obs_from']:\
                                mag_indices[mag_ctr]['obs_to']].strip() )
                            mag.stationCount = curr_obs
                        except Exception:
                            pass

            ## set preferred magnitude
            # - take first given magnitude from the 4 positions as preferred
            # - usually this is mb
            # - if neither mb nor Ms is given, use first of 
            #   additional magnitudes
            # - this is usually ML or MW
             
            if ev.magnitude:
                ev.preferredMagnitudeID = ev.magnitude[0].publicID

    
    def importJMADeck(self, input, **kwargs):
        """
        import data from Japanese JMA catalog in "deck" format
        
        data example (note: ruler shown below is not part of data)
        
                 10        20        30        40        50        60        70        80        90
        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456

        J2007040100030476 011 370929 018 1363520 053  76511322V   511   4167OFF NOTO PENINSULA       29K
        _N.TGIH2511 h 1P   00030729S   030908 6899 01  2 5235 01  2 3867 00  01                 7 4MM  1
        _N.SHKH2507 h 1P   00030929S   031241 2047 01  3 3035 01  3  953 01  31                 7 4MM  1
        _HAKUI  575 N 1P   00031046S   031464                       1985 01  51                 7 4MM  1
        _E.WAJ  811 % 1P   00031064S   031496                        405 01  54                 7 4MM  1
        _N.AMZH2508 h 1P   00031106S   031527 4930 01  5 4550 01  4 3348 00  4J                 7 4MM  1
        E
        J2007040110182065 033 304356 099 1423717 561 47     41V   571   8329FAR E OFF IZU ISLANDS    24S
        U2007040110181893     303624     1422862     10     36B         8   SOUTH OF HONSHU, JAPAN      
        _CHIJI3 589 N 1EP  10191592                                 1335 03 47J                 7 4N   1
        _KUWANO 692 N 1EP  10191638                                                             7 4N   1
        _BS1OBS 159 Q 1EP  10192333ES  201007                                                   7 4NN  1
        _BS2OBS 160 Q 1ES  10201622                                                             7 4N   1
        _BS3OBS 161 Q 1EP  10192722ES  201757                                                   7 4NN  1
        _N.ST2H 983 r 1EP  10192957ES  201998 4129 01 57 6330 01 57 1880 02 69J                 7 4NN  1
        _BS4OBS 162 Q 1EP  10193229ES  202262                        244 01  3J                 7 4NN  1
        _N.KIBH2770 s 1EP  10195294ES  210031                                                   7 4NN  1
        _MATSUS  67 G 1EP  10200041ES  211542                        106 03  2J                 7 4NN  1
        _MATSUS  67 H01P   1020010 S   21169                                                    7 4   R0
        E
        U2007040114175318    -175652    -1783258    608     49B         9   FIJI REGION
        J2007040114274820                                          8    8400FAR FIELD                  F
        _RYOKAM 561 N 1P   14274820                                                             7 4M   1
        _MATSUS  67 G 1P   14275230                                                             7 4M   1
        _WACHI  592 N 1P   14275740                                                             7 4M   1
        _AIDA   608 N 1P   14280122                                                             7 4M   1
        _SAIJYO 605 N 1P   14280515                                                             7 4M   1
        _KAMIAS 505 N 1P   14281401                                                             7 4M   1
        _SHIMAM 511 N 1P   14281389                                                             7 4M   1
        _MATSUS  67 H01P   1427522                                                              7 4   R0
        E

        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456

        NOTE: this is an illegal line, 2nd magnitude does not have correct format
                we interpret this as a magnitude 8.0
                                                                ||
        U198703061839542     -24122     - 70044      45     57B8 S      9   NEAR COAST OF N-CHILE  5

        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456

        NOTE: there can be a block like the following after the hypocenter line
                we ignore all lines that are not hypocenter, phase, comment, or end
    
        J199201012203556  01  34084  06  135355  05  681 19 39D40V1112  5189NE WAKAYAMA PREF           K
        MI JMAM       1N AM  91 67 206 10 300 20 273 39 -123 133 58  -66 92  52  91  35        92 1LOW
        NUNZEND  93 S 1            # 93  32 4390  130 1620                             U       92 1JMA
        NSHIMO2 130 S 1            #130  34  750  131  650                             U       92 1JMA
        NKIRISH 155 S 1            #155  31 5380  130 5240                             U       92 1JMA
        NOOSAKI 364 S 1            #364  35   28  139  607                             U       92 1JMA
        NASAHI  408 S 1            #408  36  733  137 5117                             U       92 1JMA
        NHOKIGI 412 S 1            #412  34 5098  139  238                             U       92 1JMA
        NOKABE  431 S 1            #431  34 5700  138 1523                             U       92 1JMA
        NNAKAIZ 432 S 1            #432  34 5477  138 5980                             U       92 1JMA
        NTENRYU 433 S 1            #433  34 5447  137 5312                             U       92 1JMA
        NKOZU   440 S 1            #440  34 1177  139  835                             U       92 1JMA
        NINUYAM 451 S 1            #451  35 2098  137  172                             U       92 1JMA
        NMIKAWA 452 S 1            #452  34 4575  137 2820                             U       92 1JMA
        NTSUKEC 454 S 1            #454  35 3920  137 2797                             U       92 1JMA
        NOSHIKA 455 S 1            #455  35 3478  138  293                             U       92 1JMA
        NTOYONE 456 S 1            #456  35  813  137 4462                             D       92 1JMA

        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456
        
        NOTE: there are invalid event blocks like the following (focal time information is not complete)
                such blocks are discarded

        J198302010039                                              81       INSUFFICIENT N OF DATA
        _MATSUS  670U 1IP  0039408 S   5000                                            U       83 2
        E

        NOTE: there can be phase lines like the following, which are discard
        _JNEMUR4320 j28M   2322               5829 30   18780 33    5094 42   2                 0 1

            
        all lines have 96 regular chars, with trailing hex '0A'
        separator lines start with 'E' (hex '45'), then 95x space char (hex '20')

        NOTE: there can be blank lines, e.g., line 158 in catalog file 198301.deck.Z
              we just skip them

        first there are hypocenter lines starting with:
            J: JMA location
            U: USGS location
            I: ISC location
        then there are optional comment lines starting with 'C'
        then there are phase lines starting with '_' which can contain one OR two phases
        NOTE: there can be other line types which will be ignored
        finally there is a separator line starting with 'E'

        phases belong to JMA location
        JMA location is not always preferred (sometimes it is incomplete)

        preferred origin:
         - JMA if complete
         - other (USGS) if complete
         - if no one is complete, use JMA

        correct illegal time components: YES (use QPUtils.fixTimeComponents)
        
        kwargs: nopicks        = True - do not read in pick lines
                jmaonly        = True - import only JMA origins
                minimumDataset = True - only read basic information (save memory)
                authorityID           - authority id used in public ids, default: 'JMA'
        """
        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'minimumDataset' in kwargs and kwargs['minimumDataset']:
            minConf = True
        else:
            minConf = False

        if 'authorityID' in kwargs and isinstance(kwargs['authorityID'], 
            QPCore.STRING_TYPES):
            auth_id = kwargs['authorityID']
        else:
            auth_id = JMA_AUTHORITY_ID
            
        # time shift in hours of Japan Standard Time
        time_delta_jst = JMA_JST_TIME_SHIFT

        mag_indices = [
            {'from': 52, 'to': 54, 'magtype_from': 54, 'magtype_to': 55},
            {'from': 55, 'to': 57, 'magtype_from': 57, 'magtype_to': 58}]
                                
        line_ctr = 0

        phasesMode     = None
        hypocenterMode = None
        newEventMode   = None
        commentMode    = None
        validHypocenter = False
        
        comment_str_xml = ''
        
        for line in istream:

            line_ctr += 1

            # if line is blank, skip
            if QPUtils.line_is_empty(line):
                continue
            
            # check if it is hypocenter, comment, pick, or separator line
            line_type = line[0]

            if line_type in ('J', 'U', 'I'):

                # previous mode can be: None, Hypocenter
                if hypocenterMode is None:
                    newEventMode    = True
                    validHypocenter = False
                    jma_origin      = None
                else:
                    newEventMode = False
                    
                hypocenterMode = True
                phasesMode     = False
                
            elif line_type == '_':

                # previous mode can be: Hypocenter, Phases, Comment
                hypocenterMode = False
                phasesMode     = True

                # if nopicks set or no valid hypocenter exists, skip line
                if ('nopicks' in kwargs and kwargs['nopicks']) or (
                        not validHypocenter):
                    continue

            elif line_type == 'C':

                # previous mode can be: Hypocenter, Comment

                hypocenterMode = False
                commentMode    = True
                
            elif line_type == 'E':
                phasesMode     = None
                hypocenterMode = None
                newEventMode   = None
                commentMode    = None

                # if no valid hypocenter has been found (no event object 
                # exists), go to next line
                if validHypocenter:
                
                    # add comment to event
                    if comment_str_xml.strip():

                        if not minConf:
                            ct = Comment(comment_str_xml.strip())
                            ev.comment.append(ct)

                        comment_str_xml = ''

                    # assign preferred origin and preferred magnitude
                    if len(ev.origin) == 1:
                        ev.preferredOriginID = ev.origin[0].publicID

                        # get first magnitude for that origin, if there are any
                        if ev.magnitude:
                            ev.preferredMagnitudeID = ev.getMagnitudes(
                                ev.origin[0])[0].publicID
                        
                    else:
                        # there are more than one origins
                        # look for JMA origin and see if it is complete

                        # TODO: at first, use JMA origin even if it is incomplete
                        for my_ori in ev.origin:
                            if my_ori.creationInfo.agencyID == \
                                JMA_AUTHORITY_ID:
                                ev.preferredOriginID = my_ori.publicID

                                # get first magnitude for that origin
                                ori_mag = ev.getMagnitudes(my_ori)
                                if ori_mag:
                                    ev.preferredMagnitudeID = \
                                        ori_mag[0].publicID

                # proceed to next input line
                continue
                
            else:
                continue

            if hypocenterMode:

                # on entering this block for the first hypocenter line, 
                #  validHypocenter is False
                # set this to True if a good hypocenter (with full time 
                #  information) has been found
                try:
                    # first get required fields
                    # NOTE: coordinates and depth need not be there
                    # NOTE: sometimes seconds are not there, this is not a 
                    #       valid hypocenter
                    curr_source = line[0]
                    
                    curr_year   = int( line[1:5] )
                    curr_month  = int( line[5:7] )
                    curr_day    = int( line[7:9] )
                    
                    curr_hour   = int( line[9:11] )
                    curr_minute = int( line[11:13] )

                    # seconds are given w/o decimal point
                    curr_second_int  = int( line[13:15] )
                    curr_second_frac = line[15:17].strip()

                except Exception:
                    continue

                # if only JMA hypocenters are requested, discard all others
                if 'jmaonly' in kwargs and kwargs['jmaonly'] and \
                        curr_source != 'J':
                    continue
                    
                ## define event id: use agency + datetime block
                pick_ctr = 0
                curr_id  = line[0:17].strip()
                
                # create event
                ev = Event()
                ev.add(self.eventParameters)
                
                if minConf is not True:
                    ev.publicID = QPUtils.build_resource_identifier(auth_id,
                        'event', curr_id)

                # create origin
                ori = Origin()
                ori.add(ev)
                
                if not minConf:
                    ori.publicID = QPUtils.build_resource_identifier(auth_id, 
                        'origin', curr_id)
                    
                try:
                    curr_second = float('.'.join((str(curr_second_int), 
                        curr_second_frac)))
                except Exception:
                    print " illegal time format (seconds) in hypocenter line "\
                        "%s: %s" % (line_ctr, line)
                    continue

                ## check if time components are well-behaved and fix if necessary
                # seconds and minutes are sometimes set to 60
                # possibly hours can be set to 24
                timeCorrection = QPUtils.fixTimeComponents(curr_hour, 
                    curr_minute, curr_second)

                # if we have arrived here, we call this a valid hypocenter 
                # (valid time information is there)
                validHypocenter = True
                    
                focal_time_utc = DateTime(curr_year, curr_month, curr_day,
                    timeCorrection['component'][0],
                    timeCorrection['component'][1],
                    timeCorrection['component'][2]) - TimeDelta(time_delta_jst)
                                           
                focal_time_utc = QPUtils.adjustDateTime(
                    timeCorrection['increaseDelta'], focal_time_utc)
                ori.time = TimeQuantity(QPDateTime.QPDateTime(focal_time_utc))
                
                # set agency
                ori.creationInfo = CreationInfo()

                if curr_source == 'J':
                    ori.creationInfo.agencyID = JMA_AUTHORITY_ID
                    jma_origin = ori

                    # TODO: set preferred origin
                    ev.preferredOriginID = ori.publicID
                
                elif curr_source == 'U':
                    ori.creationInfo.agencyID = JMA_USGS_AUTHORITY_ID
                elif curr_source == 'I':
                    ori.creationInfo.agencyID = JMA_ISC_AUTHORITY_ID

                ## get optional fields

                # latitude is given as degrees + decimal minutes (w/o decimal 
                # point)
                try:
                    curr_lat_deg      = line[22:24].strip()
                    curr_lat_min_int  = line[24:26].strip()
                    curr_lat_min_frac = line[26:28].strip()

                    curr_lat_min = float('.'.join((curr_lat_min_int, 
                        curr_lat_min_frac)))
                    curr_lat = float(curr_lat_deg) + (curr_lat_min / 60.0)

                    ori.latitude = RealQuantity(curr_lat)

                except Exception:
                    pass

                # longitude is given as degrees + decimal minutes (w/o decimal 
                # point)
                try:
                    curr_lon_deg      = line[33:36].strip()
                    curr_lon_min_int  = line[36:38].strip()
                    curr_lon_min_frac = line[38:40].strip()
                    
                    curr_lon_min = float('.'.join((curr_lon_min_int, 
                        curr_lon_min_frac)))
                    curr_lon = float(curr_lon_deg) + (curr_lon_min / 60.0)

                    ori.longitude = RealQuantity(curr_lon)

                except Exception:
                    pass

                # depth
                try:
                    curr_depth_int  = line[44:47].strip()
                    curr_depth_frac = line[47:49].strip()

                    # if depth was determined using 'depth slice method', no 
                    # fraction is there
                    if curr_depth_frac:
                        curr_depth = float('.'.join((curr_depth_int, 
                            curr_depth_frac)))
                    else:
                        curr_depth = float( curr_depth_int )

                    ori.depth = RealQuantity( 1000 * curr_depth )

                except Exception:
                    pass

                # do not read uncertainties if minimum configuration is 
                # selected
                if not minConf:

                    # focal time error (seconds)
                    try:
                        curr_second_err_int  = line[17:19].strip()
                        curr_second_err_frac = line[19:21].strip()
                        curr_second_err = float('.'.join((curr_second_err_int,
                            curr_second_err_frac)))
                        ori.time.uncertainty = curr_second_err
                    except Exception:
                        pass
                    
                    # latitude minutes error
                    try:
                        curr_lat_err_min_int  = line[28:30].strip()
                        curr_lat_err_min_frac = line[30:32].strip()
                        curr_lat_err = float('.'.join((curr_lat_err_min_int, 
                            curr_lat_err_min_frac))) / 60.0
                        ori.latitude.uncertainty = curr_lat_err
                    except Exception:
                        pass
                    
                    # longitude minutes error
                    try:
                        curr_lon_err_min_int  = line[40:42].strip()
                        curr_lon_err_min_frac = line[42:44].strip()
                        curr_lon_err = float('.'.join( (curr_lon_err_min_int, 
                            curr_lon_err_min_frac))) / 60.0
                        ori.longitude.uncertainty = curr_lon_err
                    except Exception:
                        pass
                    
                    # depth error
                    try:
                        # NOTE: format %3.2f, so 9.99 km is maximum error!
                        curr_depth_err_int  = line[49:50].strip()
                        curr_depth_err_frac = line[50:52].strip()
                        curr_depth_err = float('.'.join((curr_depth_err_int,
                            curr_depth_err_frac)))
                        ori.depth.uncertainty = 1000 * curr_depth_err
                    except Exception:
                        pass
                  
                ## magnitudes
                for mag_ctr in xrange(JMA_MAGNITUDE_COUNT):

                    curr_mag_code = \
                        line[mag_indices[mag_ctr]['from']:\
                        mag_indices[mag_ctr]['to']]

                    # something there?
                    if curr_mag_code.strip():

                        # magnitude entry should have 2 characters, but
                        #  sometimes a charcater is missing
                        # last character missing (this occurs, e.g., in the 
                        #  1987/03 USGS entry U198703061839542):
                        #   - assume missing character as '0'
                        # first character missing (don't know if there is a 
                        # case):
                        #  - illegal magnitude, don't register

                        # check if one component is whitespace
                        if len(curr_mag_code) > len(curr_mag_code.strip()):

                            if not curr_mag_code[0].strip():

                                # not fixable, discard entry
                                print " illegal one-character magnitude "\
                                    "format %s in hypocenter line %s: %s" % (
                                    curr_mag_code, line_ctr, line )
                                continue

                            elif not curr_mag_code[1].strip():

                                # fix magnitude code
                                curr_mag_code = "%s%s" % (
                                    curr_mag_code[0], '0')
                              
                        try:
                            # is magnitude code numeric? (mag. >= -0.9)
                            curr_mag_code_int = int(curr_mag_code)

                            if curr_mag_code_int >= 0:

                                # mag >= 0 (F2.1 w/o decimal point)
                                try:
                                    curr_mag = float('.'.join(( 
                                        curr_mag_code[0], curr_mag_code[1])))
                                except Exception:
                                    print " illegal positive numeric "\
                                        "magnitude format %s in hypocenter "\
                                        "line %s: %s" % (curr_mag_code, 
                                            line_ctr, line)
                                    continue
                            else:

                                # -1, -2, ..., -9 (-0.9 <= mag <= 0.1)
                                try:
                                    curr_mag = float('.'.join(('-0', 
                                        curr_mag_code[1])))
                                except Exception:
                                    print " illegal negative numeric "\
                                        "magnitude format %s in hypocenter "\
                                        "line %s: %s" % (curr_mag_code, 
                                            line_ctr, line)
                                    continue
                        except Exception:

                            # mag. <= -1.0, code not numeric, use letter code
                            # first char has to be letter A, B, or C
                            # second char has to be integer number

                            if curr_mag_code[0] in ('A', 'B', 'C') and \
                                curr_mag_code[1].isdigit():
                            
                                letter_code = {'A': '-1', 'B': '-2', 'C': '-3'}
                                curr_mag = float('.'.join((letter_code[
                                    curr_mag_code[0]], curr_mag_code[1])))

                            else:
                                print " illegal magnitude format %s in "\
                                    "hypocenter line %s: %s" % (curr_mag_code,
                                        line_ctr, line)
                                continue

                        mag = Magnitude()
                        if not minConf:
                            mag.publicID = QPUtils.build_resource_identifier(
                                auth_id, 'magnitude', "%s/%s" % (
                                curr_id, mag_ctr+1))
                    
                        mag.add(ev)
                        mag.mag = RealQuantity( curr_mag )
                        mag.setOriginAssociation( ori.publicID )

                        # magnitude type
                        try:
                            curr_magtype = \
                                line[mag_indices[mag_ctr]['magtype_from']:\
                                mag_indices[mag_ctr]['magtype_to']].strip()
                        except Exception:
                            curr_magtype = ''
                        
                        if curr_magtype == 'J':
                            mag.type = 'MJ'
                        elif curr_magtype.lower() == 'd':
                            mag.type = 'MD'
                        elif curr_magtype.lower() == 'v':
                            mag.type = 'MV'
                        elif curr_magtype == 'B':
                            mag.type = 'mb'
                        elif curr_magtype == 'S':
                            mag.type = 'MS'
                        else:
                            mag.type = 'unknown'

                        # source of magnitude determination
                        # mb: USGS, MS: ?, other: JMA
                        if mag.type not in ('MS', 'unknown'):

                            if mag.type == 'mb':
                                curr_magsource = JMA_USGS_AUTHORITY_ID
                            else:
                                curr_magsource = JMA_AUTHORITY_ID

                            if not minConf:
                                mag.creationInfo = CreationInfo()
                                mag.creationInfo.agencyID = curr_magsource


                ## set first as preferred magnitude
                if ev.magnitude:
                    ev.preferredMagnitudeID = ev.magnitude[0].publicID

                ## get "subsidiary information": event type
                try:
                    subsidiary = line[60].strip()

                    # valid classifications are
                    # '1': Natural earthquake
                    # '2': Insufficient number of JMA stations
                    # '3': Artificial event
                    # '4': Noise
                    # '5': Low frequency earthquake

                    # we consider '1', '2', and '5' as earthquakes

                    if subsidiary in ('1', '2', '5'):
                        ev.type = 'earthquake'

                    # comment: 'JMA:subsidiary=<subsidiary>'
                    oc = Comment("JMA:subsidiary=%s" % subsidiary)
                    ev.comment.append(oc)
                    
                except Exception:
                    pass
                        
                ## geographical region
                try:
                    curr_region_str = line[68:92].strip()

                    if curr_region_str:
                        curr_region_str_xml = saxutils.escape(curr_region_str)

                        if not minConf:
                            descr = EventDescription( 
                                curr_region_str_xml, 
                                EVENT_DESCRIPTION_REGION_NAME_STRING)
                            ev.description.append(descr)
                except Exception:
                    pass
                    
                ## origin quality
                try:
                    curr_stations_used = int(line[92:95].strip())
                    self.create_origin_quality(ori)
                    if not minConf:
                        ori.quality.usedStationCount = curr_stations_used
                except Exception:
                    pass

            elif phasesMode:

                # check if there is a JMA origin for picks
                if jma_origin is None:
                    error_str = "no JMA origin to associate phases to for "\
                        "event %s" % ev.publicID
                    raise ValueError, error_str

                # first phase type
                curr_phase_first = line[15:19].strip()

                # ignore line if empty
                if not curr_phase_first:
                    continue
                
                ## required fields
                try:
                    curr_sta_code             = line[1:7].strip()
                    curr_date_day             = int( line[13:15] )
                    curr_time_first_hours     = int( line[19:21] )
                    curr_time_first_mins      = int( line[21:23] )
                    curr_time_first_secs_int  = int( line[23:25] )
                    curr_time_first_secs_frac = line[25:27]
                    
                except Exception:
                    print " format error in phase line %s: %s" % (line_ctr, 
                        line)
                    continue

                # create pick
                pick_ctr = pick_ctr + 1
                pick_id  = line[19:27].strip()

                pick = Pick()
                if not minConf:
                    pick.publicID = QPUtils.build_resource_identifier(auth_id,
                        'event', "%s/pick/%s" % (curr_id, pick_id))
                            
                # set pick time, use year and month from event

                try:
                    curr_time_first_secs = float('.'.join((
                        str(curr_time_first_secs_int), 
                        curr_time_first_secs_frac)))
                except Exception:
                    print " illegal time format in phase line %s: %s" % (
                        line_ctr, line)
                    continue
		  
                # check if date/day given in phase line is smaller than 
                # date/day of focal time:
                # - either pick is in following month (day of focal time is at
                #   end of month)
                #   -> add one month to date/month, difference between 
                #      days >~ 25
                # - or pick time is earlier than focal time AND focal time is
                #   shortly after midnight
                #   -> no correction, difference between days = 1
                #
                # it can happen that pick time is earlier than focal time
                # strange, but we will ignore this

                timeCorrection = QPUtils.fixTimeComponents(
                    curr_time_first_hours, curr_time_first_mins, 
                    curr_time_first_secs)

                pick_time_utc = DateTime(curr_year, curr_month, curr_date_day,
                    timeCorrection['component'][0], 
                    timeCorrection['component'][1],
                    timeCorrection['component'][2]) - TimeDelta(time_delta_jst)
                                           
                pick_time_utc = QPUtils.adjustDateTime(
                    timeCorrection['increaseDelta'], pick_time_utc)

                if (curr_day - curr_date_day) > 1:

                    # add one month
                    pick_time_utc += RelativeDateTime(months=+1)
                        
                pick.time = TimeQuantity(QPDateTime.QPDateTime(pick_time_utc))

                # set waveform id
                pick.waveformID = WaveformStreamID()
                pick.waveformID.stationCode = curr_sta_code

                # preliminary: network code 'JMA'
                pick.waveformID.networkCode = JMA_AUTHORITY_ID
                
                pick.add(ev)
                
                # create arrival: phase 
                arrv = Arrival()
                arrv.pickID = pick.publicID
                arrv.phase  = Phase(curr_phase_first)
                arrv.add(jma_origin)

                ## look is second phase is given
                
                # second phase type
                curr_phase_second = line[27:31].strip()

                # ignore line if empty
                if not curr_phase_second:
                    continue
                
                ## required fields
                try:
                    curr_time_second_mins = int( line[31:33] )
                    curr_time_second_secs_int = int( line[33:35] )
                    curr_time_second_secs_frac = line[35:37]
                except Exception:
                    print " time format (seconds) error in phase line "\
                        "%s: %s" % (line_ctr, line)
                    continue

                try:
                    curr_time_second_secs = float('.'.join((str(
                        curr_time_second_secs_int), 
                        curr_time_second_secs_frac)))
                except Exception:
                    print " illegal time format in phase line %s: %s" % (
                        line_ctr, line)
                    continue

                # create pick
                pick_ctr = pick_ctr + 1
                pick_id  = "%s%s" % (str(curr_time_first_hours), 
                    line[31:37].strip())

                pick = Pick()
                if not minConf:
                    pick.publicID = QPUtils.build_resource_identifier(auth_id,
                        'event', "%s/pick/%s" % (curr_id, pick_id))
                
                # set pick time, use date from event and hours from first pick
                # of line

                # check if pick time is earlier than time of first pick if 
                # hours from first pick is used
                # -> then second pick is in following hour
                # first use date from first pick, if required, add one hour
                # get components from DateTime object of first pick
                # no correction for time zone required here!

                timeCorrection = QPUtils.fixTimeComponents(pick_time_utc.hour,
                    curr_time_second_mins, curr_time_second_secs )
                                                    
                pick_time_second_utc = DateTime(pick_time_utc.year, 
                    pick_time_utc.month, pick_time_utc.day,
                    timeCorrection['component'][0],
                    timeCorrection['component'][1],
                    timeCorrection['component'][2])
                                                 
                pick_time_second_utc = QPUtils.adjustDateTime(
                    timeCorrection['increaseDelta'], pick_time_second_utc)

                if pick_time_second_utc < pick_time_utc:

                    # add one hour
                    pick_time_second_utc += TimeDelta(1.0)
                        
                pick.time = TimeQuantity(QPDateTime.QPDateTime(
                    pick_time_second_utc))

                # set waveform id
                pick.waveformID = WaveformStreamID()
                pick.waveformID.stationCode = curr_sta_code

                # preliminary: network code 'JMA'
                pick.waveformID.networkCode = JMA_AUTHORITY_ID
                
                pick.add(ev)
                
                # create arrival: phase 
                arrv = Arrival()
                arrv.pickID = pick.publicID
                arrv.phase  = Phase(curr_phase_second)
                arrv.add(jma_origin)

            elif commentMode:

                # append to comment text string
                # comment object is created and added to Event when data 
                # block ends ('E')
                comment_str_xml = "%s %s" % (comment_str_xml, saxutils.escape(
                    line[2:].strip()))

    
    def importGSE2_0Bulletin(self, input, **kwargs):
        """
        Import earthquake catalog data in GSE2.0 Bulletin format 
        (as used, e.g., for the INGV catalog)
        
        Data example from INGV (note: rulers shown at beginning and end are 
        not part of data)

                 10        20        30        40        50        60        70        80        90        100       110       120       130
        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012

        BEGIN GSE2.0
        MSG_TYPE DATA
        MSG_ID 2008-03-21_16:15:35 ITA_NDC
        E-MAIL info@example.com
        DATA_TYPE BULLETIN GSE2.0

        EVENT 00011371
        Date       Time            Lat       Lon    Depth    Ndef Nsta Gap    Mag1  N    Mag2  N    Mag3  N  Author          ID
            rms   O.T. Error    Smajor Sminor Az        Err  mdist   Mdist     Err        Err        Err     Quality

        2008/02/16 01:22:14.9      43.935    10.289      5.1      11    6 170  Md 2.2  6  Ml 1.7  4             ITA_NDC   00011371
            0.32    +-  0.18       2.3    1.3   91    +-  2.7    0.15   0.72   +-0.3      +-0.1      +-        m i ke

        ITALY (Alpi Apuane)
        Sta    Dist   EvAz     Phase         Date       Time  TRes  Azim  AzRes  Slow  SRes Def  SNR        Amp   Per   Mag1   Mag2 Arr ID
        MAIM    0.15    98 m   Pg      2008/02/16 01:22:18.8   0.4                          T                                       00149600
        MAIM    0.15    98 m   Sg      2008/02/16 01:22:21.1   0.1                          T               273   .21 Md 1.9 Ml 1.9 00149601
        VLC     0.23    17 m   Pg      2008/02/16 01:22:20.4   0.1                          T                                       00149602
        VLC     0.23    17 m   Sg      2008/02/16 01:22:24.1  -0.1                          T                96   .19 Md 2.1 Ml 1.6 00149603
        BDI     0.26    60 m   Pg      2008/02/16 01:22:20.8   0.1                          T                                       00149604
        BDI     0.26    60 m   Sg      2008/02/16 01:22:24.5  -0.5                          T               124   .70 Md 2.0 Ml 1.7 00149605
        PII     0.27   141 m   Pg      2008/02/16 01:22:21.1  -0.0                          T                                       00149606
        PII     0.27   141 m   Sg      2008/02/16 01:22:25.2  -0.5                          T                         Md 2.0        00149607
        ERBM    0.49    10 m   Pg      2008/02/16 01:22:25.8   0.2                          T                                       00149608
        ERBM    0.49    10 m   Sg      2008/02/16 01:22:33.4   0.0                          T               120   1.3 Md 2.5 Ml 1.7 00149609
        SC2M    0.72   311 m   Pg      2008/02/16 01:22:29.2  -0.2                          T                         Md 2.4        00149610

        .

        EVENT 00011372
        Date       Time            Lat       Lon    Depth    Ndef Nsta Gap    Mag1  N    Mag2  N    Mag3  N  Author          ID
            rms   O.T. Error    Smajor Sminor Az        Err  mdist   Mdist     Err        Err        Err     Quality

        2008/02/16 02:49:56.0      43.696    10.660      9.7      12    7 169  Md 2.1  7  Ml 1.6  4             ITA_NDC   00011372
            0.52    +-  0.19       3.3    1.7   21    +-  1.8    0.10   0.69   +-0.1      +-0.2      +-        m i ke

        ITALY (Valdarno inferiore)
        Sta    Dist   EvAz     Phase         Date       Time  TRes  Azim  AzRes  Slow  SRes Def  SNR        Amp   Per   Mag1   Mag2 Arr ID
        PII     0.10   285 m   Pg      2008/02/16 02:49:59.4   0.3                          T                                       00149612
        PII     0.10   285 m   Sg      2008/02/16 02:50:00.8  -0.4                          T                         Md 2.1        00149613
        CRMI    0.24    67 m   Pg      2008/02/16 02:50:01.8  -0.0                          T                                       00149614
        CRMI    0.24    67 m   Sg      2008/02/16 02:50:05.8  -0.2                          T                45   .20 Md 1.9 Ml 1.4 00149615
        BDI     0.37   353 m   Pg      2008/02/16 02:50:03.9  -0.1                          T                                       00149616
        BDI     0.37   353 m   Sg      2008/02/16 02:50:08.9  -0.8                          T                80   .29 Md 1.9 Ml 1.8 00149617
        CSNT    0.51   116 m   Pg      2008/02/16 02:50:06.3  -0.1                          T                                       00149618
        CSNT    0.51   116 m   Sg      2008/02/16 02:50:13.3  -0.6                          T                48   .36 Md 2.2 Ml 1.7 00149619
        VLC     0.50   337 m   Pg      2008/02/16 02:50:06.4   0.1                          T                                       00149620
        VLC     0.50   337 m   Sg      2008/02/16 02:50:13.8   0.0                          T                40   .86 Md 2.0 Ml 1.5 00149621
        SEI     0.62    54 m   Pg      2008/02/16 02:50:08.8   0.5                          T                83   .32 Md 2.2        00149622
        VMG     0.69    67 m   Pg      2008/02/16 02:50:10.1   0.7                          T                12   .16 Md 2.3        00149623

        STOP

        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
        
        NOTE: the point separating two event blocks seems to be a non-standard INGV addition
                according to the standard, event blocks are separated by two blank lines

        NOTE: some INGV bulletin files have some deviations from the standard:
                (1) blank line between the two origin lines
                (2) magnitude-related fields are in the wrong columns
                (3) no blank line between last header line (DATA_TYPE BULLETIN GSE2.0) 
                    and first 'EVENT NNNNNNNN' line

        NOTE: if kwarg 'checkMessageHeader' is set to True, the header lines are not checked
                for correctness. However, there has to be at least *one* non-blank header line.

        NOTE: the 'STOP' line at the end finishes processing (entries after it are ignored),
                but is not required for correct processing
            
        correct illegal time components: NO
        
        kwargs: fieldIndices              - dictionary of positions of input fields, used if
                                            input file is non-standard, like older INGV bulletins 
                                            (if not set, use default)
                nopicks            = True - do not read in phase pick lines
                                            (default: False)
                minimumDataset     = True - only read basic information (save memory)
                                            (default: False)
                checkMessageHeader = True - check if correct header lines are at beginning of stream
                                            (default: False)
                authorityID               - authority ID used in publicID attributes
                                            (default: 'local')
                networkCode               - network code used for phase lines
                                            (default: 'XX')
                codeMapping               - dictionary of station codes with respective network
                                            codes for adding station specific network codes
                                            (if station not present, default networkCode is used)
        
        """
        
        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'minimumDataset' in kwargs and kwargs['minimumDataset']:
            minConf = True
        else:
            minConf = False

        if 'checkMessageHeader' in kwargs and kwargs['checkMessageHeader']:
            checkMessageHeader = True
        else:
            checkMessageHeader = False

        if 'authorityID' in kwargs and isinstance(
                kwargs['authorityID'], QPCore.STRING_TYPES):
            auth_id = kwargs['authorityID']
        else:
            auth_id = LOCAL_AUTHORITY_ID

        if 'networkCode' in kwargs and isinstance(
                kwargs['networkCode'], QPCore.STRING_TYPES):
            default_network_code = kwargs['networkCode']
        else:
            default_network_code = 'XX'

        if 'codeMapping' in kwargs and isinstance(kwargs['codeMapping'], dict):
            do_codeMapping = True
            codeMapping = kwargs['codeMapping']
        else:
            do_codeMapping = False

        # if input field positions are given, replace default
        if 'fieldIndices' in kwargs and isinstance(
                kwargs['fieldIndices'], dict):
            fieldIndices = kwargs['fieldIndices']
        else:

            # standard-conforming default field positions
            # NOTE: these are Python-style, i.e. first position is 
            # zero-offset, and last position is zero-offset plus one
            fieldIndices = { 
                'author_from': 104,
                'author_to': 112,
                'id_from': 114,
                'id_to': 122,
                'mag': (
                    {'magtype_from': 71, 'magtype_to': 73, 'mag_from': 73, 
                     'mag_to': 77,  'st_cnt_from': 78, 'st_cnt_to': 80, 
                     'magerr_from': 74, 'magerr_to': 77 },
                    {'magtype_from': 82, 'magtype_to': 84, 'mag_from': 84, 
                     'mag_to': 88, 'st_cnt_from': 89, 'st_cnt_to': 91, 
                     'magerr_from': 85, 'magerr_to': 88 },
                    {'magtype_from': 93, 'magtype_to': 95, 'mag_from': 95,
                     'mag_to': 99,  'st_cnt_from': 100, 'st_cnt_to': 102, 
                     'magerr_from': 96, 'magerr_to': 99 }
                    )
            }
                    
        line_ctr = 0

        startMode      = True
        headerMode     = None
        newEventMode   = None
        originMode     = None
        regionMode     = None
        phaseMode      = None
        eventEndMode   = None
        
        commentMode     = None
        comment_str_xml = ''
        
        for line in istream:

            line_ctr += 1

            # if line is blank, change mode and skip

            # startMode
            if startMode:
                if QPUtils.line_is_empty(line):
                    continue
                else:
                    startMode   = False
                    headerMode  = True
                    header_line = 0
                    
            # header mode
            if headerMode:
                
                # header block starts with BEGIN line
                # first blank line is interpreted as end of header block
                # if no blank line after header block, detect 'EVENT' line
                if QPUtils.line_is_empty(line):
                    headerMode   = False
                    newEventMode = True
                    continue
                elif line.strip().startswith(GSE2_0_LINESTART_EVENT):
                    # first event block has started without separating blank 
                    # line, don't go to next line, fall through to new event
                    # mode block
                    headerMode   = False
                    newEventMode = True
                else:
                    header_line += 1
                    if checkMessageHeader:

                        # check header lines 1 (BEGIN) and 5 (DATA_TYPE) for 
                        # correctness, ignore others
                        if (header_line == 1 and line.strip().upper() != \
                                GSE2_0_HEADER_LINE_BEGIN) or (
                            header_line == 5 and line.strip().upper() != \
                                GSE2_0_HEADER_LINE_DATA_TYPE):
                            error_str = " illegal GSE2.0 header line %s: "\
                                "%s" % (line_ctr, line)
                            raise ValueError, error_str
                        else:
                            continue
                    else:
                        continue

            # event end mode
            if eventEndMode:

                if line.strip().upper() == GSE2_0_LINESTART_STOP:

                    # end processing loop
                    break
                
                elif QPUtils.line_is_empty(line) or line.strip() == \
                        GSE2_0_EVENT_SEPARATOR:
                    continue
                else:

                    # new regular line, new data block starts
                    eventEndMode = False
                    newEventMode = True
                    
            if newEventMode:
                
                # event block starts with EVENT line
                # then the origin header lines follow: ignore them
                # first blank line is interpreted as begin of first 
                # origin block
                if QPUtils.line_is_empty(line):
                    newEventMode = False
                    originMode = True
                    origin_line = 0
                    continue

                elif line.strip().startswith(GSE2_0_LINESTART_EVENT):

                    # create event
                    ev = Event()
                    ev.add(self.eventParameters)

                    # get event id 
                    try:
                        ev_id = line[6:].strip()
                    except Exception:
                        error_str = " event id missing in EVENT line %s: "\
                            "%s" % (line_ctr, line)
                        raise ValueError, error_str

                    if not minConf:
                        ev.publicID = QPUtils.build_resource_identifier(
                            auth_id,  'event', ev_id)
                        continue

                else:
                    # ignore non-blank and non-EVENT line
                    continue
                    
            if originMode:

                # origin block consists of 2-line origin info pairs, separated
                # by blank lines
                # origin block is terminated by region info line

                # NOTE: in older INGV bulletin data sets, origin line pairs 
                # can be separated with blank line

                # blank line: just ignore
                if QPUtils.line_is_empty(line):
                    continue

                elif not QPUtils.line_is_empty(line[0]):
                    
                    # non-blank line with non-empty first column
                    # this is either 1st event line or region line which 
                    # indicates the next input block

                    # check if the first entry in line is a valid date
                    match_str = r'\d{4}/\d{2}/\d{2}\s+'
                
                    if re.match(match_str, line.strip()):
                        origin_line = 1
                    
                    else:
                        # this line is already the region line, set region 
                        # info within origin block
                        origin_line = 0
                        originMode  = False
                        regionMode  = True

                else:
                    
                    # non-blank line with empty first column: 2nd event line
                    # if current origin line is not 1, we have an error
                    # 2nd origin line cannot stand alone

                    if origin_line == 1:
                        origin_line = 2
                    else:
                        error_str = " illegal format in origin line %s: %s" % (
                            line_ctr, line)
                        raise ValueError, error_str
                
                if origin_line == 1:
                    try:
                        # require time and lat/lon
                        
                        curr_year   = int( line[0:4] )
                        curr_month  = int( line[5:7] )
                        curr_day    = int( line[8:10] )
                        
                        curr_hour   = int( line[11:13] )
                        curr_minute = int( line[14:16] )
                        curr_second = float( line[17:21].strip() )

                        curr_lat    = float( line[25:33].strip() )
                        curr_lon    = float( line[34:43].strip() )

                        # create origin, set publicID later
                        ori = Origin()

                        ori.time = TimeQuantity(QPDateTime.QPDateTime((
                            curr_year, curr_month, curr_day, curr_hour, 
                            curr_minute, curr_second)))
                        ori.latitude  = RealQuantity(curr_lat)
                        ori.longitude = RealQuantity(curr_lon)

                        ori.add(ev)

                    except Exception:
                        print " error in origin line %s: %s" % (line_ctr, line)
                        continue

                    ## optional fields
                    
                    # 23 fixf a1 fixed flag (f=fixed origin time solution, or blank)
                    time_fixed_flag = line[22:23].strip()
                    if time_fixed_flag == 'f':
                        ori.timeFixed = True
                    
                    # 45 fixf a1 fixed flag (f= fixed epicenter solution, or blank)
                    epicenter_fixed_flag = line[44:45].strip()
                    if epicenter_fixed_flag == 'f':
                        ori.epicenterFixed = True
                    
                    # 54 fixf a1 fixed flag (f= fixed depth station, d=depth phases, or blank)
                    depth_fixed_flag = line[53:54].strip()
                    if depth_fixed_flag == 'd':
                        ori.depthType = 'constrained by depth phases'
                    
                    # origin ID
                    try:    
                        ori_id = \
                            line[fieldIndices['id_from']:fieldIndices['id_to']].strip()
                    except Exception: 
                        ori_id = ev_id

                    if not minConf:
                        ori.publicID = QPUtils.build_resource_identifier(
                            auth_id, 'origin', ori_id)
                    
                    # depth
                    try:
                        curr_depth = 1000 * float(line[47:52].strip())
                        ori.depth = RealQuantity(curr_depth)
                    except Exception:
                        pass

                    if not minConf:

                        # number of used phases
                        try:    
                            used_phase_cnt = int( line[56:60].strip() )
                            self.create_origin_quality(ori)
                            ori.quality.usedPhaseCount = used_phase_cnt
                        except Exception: 
                            pass
                            
                        # number of used stations
                        try:    
                            used_sta_cnt = int( line[61:65].strip() )
                            self.create_origin_quality(ori)
                            ori.quality.usedStationCount = used_sta_cnt
                        except Exception: 
                            pass
                        
                        # azimuthal gap
                        try:    
                            azimuthal_gap = float( line[66:69].strip() )
                            self.create_origin_quality(ori)
                            ori.quality.azimuthalGap = azimuthal_gap
                        except Exception: 
                            pass

                    ## magnitudes
                    mag_arr = []
                    for mag_ctr in xrange(GSE2_0_MAGNITUDE_COUNT):

                        try:
                            curr_mag_str = \
                                line[fieldIndices['mag'][mag_ctr]['mag_from']:fieldIndices['mag'][mag_ctr]['mag_to']].strip()
                        except Exception:
                            curr_mag_str = ''

                        # something there?
                        if curr_mag_str:
                            
                            mag = Magnitude()
                            mag.add(ev)
                            mag.setOriginAssociation( ori.publicID )
                                                        
                            try:
                                mag.mag = RealQuantity(float(curr_mag_str))
                            except Exception:
                                error_str = " illegal magnitude format in "\
                                    "EVENT line %s: %s" % (line_ctr, line)
                                raise ValueError, error_str

                            # magnitude type
                            try:
                                mag.type = \
                                    line[fieldIndices['mag'][mag_ctr]['magtype_from']:fieldIndices['mag'][mag_ctr]['magtype_to']].strip()
                            except Exception:
                                mag.type = 'unknown'

                            if not minConf:

                                # public ID
                                mag.publicID = \
                                    QPUtils.build_resource_identifier(auth_id, 
                                    'magnitude', "%s/%s" % (ori_id, mag_ctr+1))
                                
                                # station count
                                try:
                                    mag.stationCount = \
                                        int(line[fieldIndices['mag'][mag_ctr]['st_cnt_from']:fieldIndices['mag'][mag_ctr]['st_cnt_to']].strip())
                                except Exception:
                                    pass

                            # fill mag_arr for later identification of magnitude instance
                            mag_arr.append(mag)

                        else:
                            mag_arr.append(None)

                    # Author: map to creationInfo.agencyID
                    try:
                        curr_locsource = \
                            line[fieldIndices['author_from']:fieldIndices['author_to']].strip()
                        
                        if curr_locsource:
                            self.create_object_creationinfo(ori)
                            ori.creationInfo.agencyID = curr_locsource
                    except Exception:
                        pass

                    # set preferred origin
                    # TODO(fab): set first origin as preferred
                    ev.preferredOriginID = ori.publicID

                    ## set first magnitude as preferred one
                    if ev.magnitude:
                        ev.preferredMagnitudeID = ev.magnitude[0].publicID

                # everything in origin line 2 is ignored in minimum 
                # configuration
                elif origin_line == 2 and (not minConf):

                    # rms - standard deviation of arrival time residuals
                    try:
                        curr_std_dev = float(line[5:10].strip())
                        self.create_origin_quality(ori)
                        ori.quality.standardError = curr_std_dev
                    except Exception:
                        pass

                    # focal time error (seconds)
                    try:    
                        ori.time.uncertainty = float(line[15:21].strip())
                    except Exception: 
                        pass

                    ## horizontal error ellipse

                    # add only if complete description is there
                    try:
                        ou = OriginUncertainty.OriginUncertainty()
                        ori.originUncertainty.append(ou)

                        ou.minHorizontalUncertainty = float( 
                            line[25:31].strip())
                        ou.maxHorizontalUncertainty = float(
                            line[32:38].strip())
                        ou.azimuthMaxHorizontalUncertainty = float(
                            line[40:43].strip())
                        ou.preferredDescription = 'uncertainty ellipse'

                    except Exception:
                        pass

                    # depth Error
                    try:    
                        ori.depth.uncertainty = 1000 * float(
                            line[49:54].strip())
                    except Exception: 
                        pass

                    # minumum distance to station (degrees)
                    try:
                        min_dist = float(line[56:62].strip())
                        self.create_origin_quality(ori)
                        ori.quality.minimumDistance = min_dist
                    except Exception:
                        pass

                    # maximum distance to station (degrees)
                    try:
                        max_dist = float(line[63:69].strip())
                        self.create_origin_quality(ori)
                        ori.quality.maximumDistance = max_dist
                    except Exception:
                        pass

                    # magnitude errors, mags from 1st origin line are 
                    # saved in mag_arr
                    for mag_ctr, curr_mag in enumerate(mag_arr):

                        if curr_mag is None:
                            continue
                        else:
                            try:
                                curr_mag.mag.uncertainty = \
                                    float(line[fieldIndices['mag'][mag_ctr]\
                                        ['magerr_from']:fieldIndices['mag']\
                                            [mag_ctr]['magerr_to']].strip())
                            except Exception:
                                pass

                    # antype -> Origin.evaluationMode, (evaluationStatus)
                    # no match for 'g' (guess) in QuakeML
                    # we map 'g' to 'manual', set evaluationStatus to 
                    # 'preliminary', and create a comment for origin
                    try:
                        curr_ori_mode = line[104:105].strip()
                        if curr_ori_mode.lower() == 'm':
                            ori.evaluationMode = 'manual'
                        elif curr_ori_mode.lower() == 'a':
                            ori.evaluationMode = 'automatic'
                        elif curr_ori_mode.lower() == 'g':
                            ori.evaluationMode = 'manual'
                            ori.evaluationStatus = 'preliminary'
                            
                            # comment: 'GSE2.0:antype=g'
                            oc = Comment("GSE2.0:antype=%s" % curr_ori_mode)
                            ori.comment.append(oc)

                    except Exception:
                        pass

                    # ignore loctype field, no match in QuakeML

                    # evtype -> Event.type, Event.typeCertainty
                    # if classification is 'unknown', we do not set the Event.type
                    # add comment to event with GSE2.0 classification
                    try:
                        curr_ev_remarks = line[108:110].strip()
                        if curr_ev_remarks.lower() == 'ke':
                            ev.type = 'earthquake'
                            ev.typeCertainty = 'known'
                        elif curr_ev_remarks.lower() == 'se':
                            ev.type = 'earthquake'
                            ev.typeCertainty = 'suspected'
                            
                        elif curr_ev_remarks.lower() == 'kr':
                            ev.type = 'rock burst'
                            ev.typeCertainty = 'known'
                        elif curr_ev_remarks.lower() == 'sr':
                            ev.type = 'rock burst'
                            ev.typeCertainty = 'suspected'
                            
                        elif curr_ev_remarks.lower() == 'ki':
                            ev.type = 'induced or triggered event'
                            ev.typeCertainty = 'known'
                        elif curr_ev_remarks.lower() == 'si':
                            ev.type = 'induced or triggered event'
                            ev.typeCertainty = 'suspected'
                            
                        elif curr_ev_remarks.lower() == 'km':
                            ev.type = 'mining explosion'
                            ev.typeCertainty = 'known'
                        elif curr_ev_remarks.lower() == 'sm':
                            ev.type = 'mining explosion'
                            ev.typeCertainty = 'suspected'
                            
                        elif curr_ev_remarks.lower() == 'kx':
                            ev.type = 'experimental explosion'
                            ev.typeCertainty = 'known'
                        elif curr_ev_remarks.lower() == 'sx':
                            ev.type = 'experimental explosion'
                            ev.typeCertainty = 'suspected'
                            
                        elif curr_ev_remarks.lower() == 'kn':
                            ev.type = 'nuclear explosion'
                            ev.typeCertainty = 'known'
                        elif curr_ev_remarks.lower() == 'sn':
                            ev.type = 'nuclear explosion'
                            ev.typeCertainty = 'suspected'
                            
                        elif curr_ev_remarks.lower() == 'ls':
                            ev.type = 'landslide'
                            ev.typeCertainty = 'known'
                            
                        # comment: 'GSE2.0:evtype=<evtype>'
                        if curr_ev_remarks:
                            oc = Comment("GSE2.0:evtype=%s" % curr_ev_remarks)
                            ev.comment.append(oc)

                    except Exception:
                        pass

                elif regionMode:

                    # change mode to phases mode
                    regionMode = False
                    phasesMode = True
                    phase_line_ctr = 0
                    
                    if not minConf:

                        ## geographical region
                        curr_region_str = line.strip()

                        if curr_region_str:
                            curr_region_str_xml = saxutils.escape(
                                curr_region_str)

                            descr = EventDescription(
                                curr_region_str_xml, 
                                EVENT_DESCRIPTION_REGION_NAME_STRING)
                            ev.description.append(descr)

            elif phasesMode:

                # 1-5 Sta a5 station code
                # 7-12 Dist f6.2 station to event distance (degrees)
                # 14-18 EvAz f5.1 event to station azimuth (degrees)
                # 20 picktype a1 type of pick (a=automatic, m=manual)
                # 21 directio
                #  n
                #  a1 direction of short period motion (c=compression,
                #  d=dilatation, or blank)
                # 22 detchar a1 detection character (i=impulsive, e=emergent,
                #  q=questionable, or blank)
                # 24-30 Phase a7 ISC phase code (P, S, pP, etc.)
                # 32-41 Date i4,a1,i2,a1,i2 arrival date (yyyy/mm/dd)
                # 43-52 Time i2,a1,i2,a1,f4.1 arrival time (hh:mm:ss.s)
                # 54-58 TRes f5.1 time residual (seconds)
                # 60-64 Azim f5.1 arrival azimuth (degrees)
                # 66-71 AzRes f6.1 azimuth residual (degrees)
                # 73-77 Slow f5.1 arrival slowness (seconds/degree)
                # 79-83 SRes f5.1 slowness residual (seconds/degree)
                # 85 tdef a1 time defining flag (T or blank)
                # 86 adef a1 azimuth defining flag (A or blank)
                # 87 sdef a1 slowness defining flag (S or blank)
                # 89-93 Snr f5.1 signal-to-noise ratio
                # 95-103 Amp f9.1 amplitude (nanometers)
                # 105-109 Per f5.2 period (seconds)
                # 111-112 mdef1 a2 magnitude type (mb, Ms, ML, MD=duration,
                #  Mn=Nuttli, M)
                # 113-116 Mag1 f4.1 magnitude
                # 118-119 mdef2 a2 magnitude type (mb, Ms, ML, MD=duration,
                #  Mn=Nuttli, M)
                # 120-123 Mag2 f4.1 magnitude
                # 125-132 ID a8 Arrival ID

                # Sta    Dist   EvAz     Phase         Date       Time  TRes  Azim  AzRes  Slow  SRes Def  SNR        Amp   Per   Mag1   Mag2 Arr ID
                # CRMI    0.24    67 m   Sg      2008/02/16 02:50:05.8  -0.2                          T                45   .20 Md 1.9 Ml 1.4 00149615

                # phase block starts with 1 line of header information
                # the following lines are phase lines
                # phase block and whole event section is terminated by 
                # blank line(s)

                phase_line_ctr += 1

                # if first line of block (header), skip
                if phase_line_ctr == 1:
                    continue

                else:

                    # if blank line, phase block has ended
                    if QPUtils.line_is_empty(line):
                        phasesMode   = False
                        eventEndMode = True

                    # if keyword argument 'nopicks' set, skip line
                    elif not ('nopicks' in kwargs and kwargs['nopicks']):

                        ##  read regular phase line
                        try:

                            # required fields: Sta Phase DateTime
                            curr_sta_code   = line[0:5].strip()
                            curr_phase_code = line[23:30].strip()

                            curr_year       = int( line[31:35] )
                            curr_month      = int( line[36:38] )
                            curr_day        = int( line[39:41] )
                        
                            curr_hour       = int( line[42:44] )
                            curr_minute     = int( line[45:47] )
                            curr_second     = float(line[48:52].strip())
                            
                        except Exception:
                            print " error in phase line %s: %s" % (line_ctr, 
                                line)
                            continue

                        # if pick id is not provided, use phase line number
                        try:
                            pick_id = line[124:132].strip()
                            if not pick_id:
                                pick_id = str(phase_line_ctr)
                                
                        except Exception:
                            pick_id = str(phase_line_ctr)

                        # create pick object and add to event
                        pick = Pick()
                        if not minConf:
                            pick.publicID = ''.join(
                                QPUtils.build_resource_identifier(auth_id, 
                                'event', "%s/pick/%s" % (ori_id, pick_id)))

                        base_time_utc = DateTime(curr_year, curr_month, 
                            curr_day, curr_hour, curr_minute, 0.0)
                                                  
                        pick_time_utc = base_time_utc + \
                            DateTimeDeltaFromSeconds(curr_second)
                        pick.time = TimeQuantity(QPDateTime.QPDateTime(
                            pick_time_utc))

                        # set waveform id
                        pick.waveformID = WaveformStreamID()
                        pick.waveformID.stationCode = curr_sta_code
                        if do_codeMapping:
                            try:
                                network_code = codeMapping[curr_sta_code]
                            except Exception:
                                network_code = default_network_code
                        else:
                            network_code = default_network_code
                        pick.waveformID.networkCode = network_code
                        pick.add(ev)

                        # create arrival object and add to origin
                        arrv = Arrival()
                        arrv.pickID = pick.publicID
                        arrv.phase = Phase(curr_phase_code)
                        arrv.add(ori)
                        
                        # optional fields: Azim Slow Dist EvAz TRes AzRes SRes Def Arr
                        
                        # OK Azim -> pick.backazimuth
                        # OK Slow -> pick.horizontalSlowness
                        
                        # OK Dist -> arrival.distance
                        # OK EvAz -> arrival.azimuth
                        # OK TRes -> arrival.timeResidual
                        # *OK Azres -> arrival.backazimuthResidual
                        # *OK SRes -> arrival.horizontalSlownessResidual
                        
                        # Def: 3 "defining" flags (TAS), ignored
                        # Arr: (legacy arrival id) is ignored
                        if not minConf:

                            pick.phaseHint = Phase(curr_phase_code)
                            
                            try:
                                pick.backazimuth = RealQuantity(
                                    QPUtils.backazimuth_from_azimuth_flat(
                                        float(line[59:64].strip())))
                            except Exception: 
                                pass

                            try:
                                # NOTE: assume that this is 
                                # *horizontal* slowness
                                pick.horizontalSlowness = RealQuantity(
                                    float(line[72:77].strip()))
                            except Exception: 
                                pass

                            # distance is in degrees
                            try:    
                                arrv.distance = float(line[6:12].strip())
                            except Exception: 
                                pass

                            try:    
                                arrv.azimuth = float(line[13:18].strip())
                            except Exception: 
                                pass

                            try:    
                                arrv.timeResidual = float(line[53:58].strip())
                            except Exception: 
                                pass
                            
                            try:    
                                arrv.backazimuthResidual = float(
                                    line[65:71].strip())
                            except Exception: 
                                pass
                            
                            try:    
                                arrv.horizontalSlownessResidual = float(
                                    line[78:83].strip())
                            except Exception: 
                                pass
                            
                            ## Amplitude

                            # optional fields: SNR Amp Per
                            try:
                                curr_amp = Amplitude(
                                    QPUtils.build_resource_identifier(auth_id,
                                    'event', "%s/amplitude/%s" % (ori_id, 
                                    pick_id)))

                                # amplitude is in nanometres, thus it is a 
                                # displacement
                                amp_value = float(line[94:103].strip()) * 1e-9
                                curr_amp.genericAmplitude = RealQuantity(
                                    amp_value)

                                curr_amp.type = 'A'
                                curr_amp.unit = 'm'
                                
                                curr_amp.pickID     = pick.publicID
                                curr_amp.waveformID = pick.waveformID
                                
                                curr_amp.add(ev)
                            except Exception:
                                curr_amp = None

                            if curr_amp is not None:
                                try:    
                                    curr_amp.snr = float(line[88:93].strip())
                                except Exception: 
                                    pass

                                try:    
                                    curr_amp.period = RealQuantity(
                                        float(line[104:109].strip()))
                                except Exception: 
                                    pass

                            ## StationMagnitude(s), optional fields: Mag1 Mag2
                            sta_mag_indices = [ 
                                {'mag_from': 112, 'mag_to': 116, 
                                 'magtype_from': 110, 'magtype_to': 112 },
                                {'mag_from': 119, 'mag_to': 123, 
                                 'magtype_from': 117, 'magtype_to': 119 } 
                            ]

                            # 1st potential station magnitude
                            for sta_mag_idx in xrange(
                                GSE2_0_STATION_MAGNITUDE_COUNT):
                                try:
                                    sta_mag = \
                                        StationMagnitude.StationMagnitude()

                                    mag_value = float(
                                        line[sta_mag_indices[sta_mag_idx]\
                                            ['mag_from']:sta_mag_indices\
                                                [sta_mag_idx]['mag_to']].strip())
                                    sta_mag.mag = RealQuantityRealQuantity(
                                        mag_value)
                                    sta_mag.type = \
                                        line[sta_mag_indices[sta_mag_idx]\
                                            ['magtype_from']:sta_mag_indices\
                                                [sta_mag_idx]['magtype_to']].strip()

                                    sta_mag.add(ori)
                                    sta_mag.waveformID = pick.waveformID

                                    if curr_amp is not None:
                                        sta_mag.stationAmplitudeID = curr_amp.publicID
                                    
                                except Exception:
                                    pass


    def importOGS_HPL(self, input, **kwargs):
        """
        Import earthquake catalog data in HPL format as used by OGS
        
        Data example from OGS (note: ruler shown below is not part of data)

                 10        20        30        40        50        60        70        80        90        100       110       120       130       140       150       160
        123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890

             9 770508 0619                                   0.49                                                                                                      2
             9 BUA                eP   0619 24.90                                                   FL   80 0.5  iS   28.80                        BUA     gg
             9 COLI               eP   0619 25.90                                                   FL   70 0.5  iS   30.00                        COLI    gg
        ^MOGGIO UDINESE (FRIULI)

            10 770508 1659  8.76 46-21.69  13- 9.51   1.62   0.78  5 16 317 1 0.12  0.3  2.1 C B/D 0.56 10  6 0.00 0.10  0  0.0  0.0  2  0.8  0.2 9  0.3  0.1          3
            10 BAD   15.6 155  96    4 1659  0.00******  2.68  0.00        0.00   0  0  0.00 0      FLD          iS   13.30  4.54 -0.23   0.8      BAD      g
            10 BUA   16.3 189  96 eP   1659 11.60  2.84  2.80  0.00  0.04  1.25   0  0  0.00 0      FLD 100 0.7  iS   13.70  4.94 -0.05   1.2      BUA     gg
            10 COLI  30.5 147  93 eP   1659 14.10  5.34  5.23  0.00  0.11  0.83   0  0  0.00 0      FLD 100 0.8  iS   18.20  9.44  0.13   0.8      COLI    gg
        ^ZAGARIE (SLOVENIA)

            11 770508 22 9 27.33 46- 5.83  15-19.11  18.07   2.26  5 61 336 1  .14  3.4  1.6 D C/D 7.15 10  6  .00  .13  0   .0   .0  1  2.3   .0 4  2.6  2.1          3
            11 LJU   61.5 264 106 eP   22 9 38.20 10.87 10.96   .00  -.09  1.35   0  0   .00 0      SLD          eS   46.90 19.57   .07   1.3      LJU     gg
            11 CEY   79.8 240 103 eP   22 9 41.50 14.17 13.99   .00   .18   .84   0  0   .00 0      SLD          eS   52.00 24.67  -.24    .8      CEY     gg
            11 TRI  128.1 250  59    4 2210   .00 32.67 21.10   .00         .00   0  0   .00 0      SLD 650 2.3  eS    5.00 37.67   .11    .7      TRI      g                                                   

        Note:
            (1) lines are very long in this format (> 200 chars)
            (2) there are localized and non-localized EQs in the catalog. 
                blocks of localized events have a starting line that begins 
                with '^' in the first column and gives the region.
                a blank line (whitespace only) follows immediately
                after that, a hypocenter line and phase lines follow 
                non-localized event blocks have the same sequence of 
                hypocenter and phase lines, but have no starting ^-line with 
                region
            (3) all lines which are not ^-lines with region info start with a 
                sequence number that takes the first 6 columns, right-adjusted
            (4) there can be comment lines after last phase line that start 
                with '*'

        correct illegal time components: NO
        
        kwargs: nopicks=True - do not read in phase pick lines
                minimumDataset=True - only read basic information (save memory)
                authorityID - authority id used in public ids, default: 'local'
                networkCode - network code used for phase lines, default: 'XX'
        
        """
        
        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input

        if 'minimumDataset' in kwargs and kwargs['minimumDataset']:
            minConf = True
        else:
            minConf = False

        if 'authorityID' in kwargs and isinstance(
                kwargs['authorityID'], QPCore.STRING_TYPES):
            auth_id = kwargs['authorityID']
        else:
            auth_id = OGS_AUTHORITY_ID

        if 'networkCode' in kwargs and isinstance(
                kwargs['networkCode'], QPCore.STRING_TYPES):
            network_code = kwargs['networkCode']
        else:
            network_code = OGS_NETWORK_CODE_DUMMY
                                
        line_ctr = 0

        newEventMode   = None
        originMode     = None
        phaseMode      = None
        skipMode       = True
        
        comment_str_xml = ''
        
        for line in istream:

            line_ctr += 1

            # check if it's a new localized event
            if line[0] == OGS_LINESTART_LOCALIZED_EVENT:

                newEventMode = True
                skipMode = False

                # get region string
                region_str_xml = saxutils.escape(line[1:].strip())
                continue

            elif line[0] == OGS_LINESTART_COMMENT:

                # comment line, skip
                continue

            else:

                if skipMode:
                    continue

                elif newEventMode:

                    # skip one blank line after region info
                    originMode   = True
                    newEventMode = False
                    continue
                    
                elif originMode:

                    # get hypocenter data

                    # create event
                    ev = Event()
                    ev.add(self.eventParameters)

                    # get event sequence number of data set
                    try:
                        ev_seq = int(line[0:6].strip())
                    except Exception:
                        error_str = " no valid sequence number in origin "\
                            "line %s: %s" % (line_ctr, line)
                        raise RuntimeError, error_str
                    
                    try:
                        
                        # require time, lat/lon
                        
                        curr_year_str = line[7:9]
                        curr_month    = int( line[9:11] )
                        curr_day      = int( line[11:13] )

                        # catalog starts in 1977
                        # make years >= 77 -> 19XX, < 77 -> 20XX
                        if int( curr_year_str ) >= OGS_YEAR_START_1900:
                            curr_year = int("%s%s" % ('19', curr_year_str))
                        else:
                            curr_year = int("%s%s" % ('20', curr_year_str))
                            
                        curr_hour   = int( line[14:16] )
                        curr_minute = int( line[16:18] )
                        curr_second = float( line[19:24].strip() )

                        # latitude and longitude are given as degrees and decimal minutes
                        curr_lat_deg = float( line[25:27].strip() )
                        curr_lat_min = float( line[28:33].strip() )
                        curr_lat     = curr_lat_deg + ( curr_lat_min / 60.0 )
                        
                        curr_lon_deg = float( line[35:37].strip() )
                        curr_lon_min = float( line[38:43].strip() )
                        curr_lon     = curr_lon_deg + ( curr_lon_min / 60.0 )
                        
                        # create origin, set publicID later
                        ori = Origin()

                        ori.time = TimeQuantity(QPDateTime.QPDateTime((
                            curr_year, curr_month, curr_day,
                            curr_hour, curr_minute, curr_second)))
                        ori.latitude  = RealQuantity( curr_lat )
                        ori.longitude = RealQuantity( curr_lon )
                        
                        ori.add(ev)

                    except Exception:
                        print " error in origin line %s: %s" % (line_ctr, line)
                        skipMode = True
                        continue

                    ## optional fields
                    
                    # depth
                    try:
                        curr_depth = 1000 * float( line[45:50].strip() )
                        ori.depth  = RealQuantity( curr_depth )
                    except Exception:
                        pass

                    ## origin/event id is not provided in HPL format
                    # get origin id from date and time, show as ISO datetime 
                    # with 2 decimal places for seconds
                    ori_id = QPUtils.mxDateTime2ISO(
                        ori.time.value.datetime, secondsdigits=2)
                    
                    if not minConf:
                        ori.publicID = QPUtils.build_resource_identifier(
                            auth_id, 'origin', ori_id)

                    ## set preferred origin
                    ev.preferredOriginID = ori.publicID
                        
                    ## magnitude
                    try:
                        curr_mag = float( line[52:57].strip() )
                        
                        mag = Magnitude()
                        mag.add(ev)
                        mag.setOriginAssociation( ori.publicID )

                        # duration magnitude (local?)
                        mag.mag  = RealQuantity( curr_mag )
                        mag.type = 'Md'

                        if not minConf:

                            mag.publicID = QPUtils.build_resource_identifier(
                                auth_id, 'magnitude', ori_id)

                            # station count
                            try:
                                mag.stationCount = int( line[125:127].strip() )
                            except Exception:
                                pass

                    except Exception:
                        pass

                    ## set first magnitude as preferred one
                    if ev.magnitude:
                        ev.preferredMagnitudeID = ev.magnitude[0].publicID
                            
                    if not minConf:
                        ev.publicID = QPUtils.build_resource_identifier(
                            auth_id, 'event', ori_id)

                        ## geographical region
                        descr = EventDescription(region_str_xml, 
                            EVENT_DESCRIPTION_REGION_NAME_STRING)
                        ev.description.append( descr )
                        
                        # number of used phases
                        try:    
                            used_phase_cnt = int(line[58:60].strip())
                            self.create_origin_quality(ori)
                            ori.quality.usedPhaseCount = used_phase_cnt
                        except Exception: 
                            pass

                        # azimuthal gap
                        try:    
                            azimuthal_gap = float(line[64:67].strip())
                            self.create_origin_quality(ori)
                            ori.quality.azimuthalGap = azimuthal_gap
                        except Exception: 
                            pass

                        # standardError (rms)
                        try:
                            curr_rms_residual_phases = float(
                                line[70:74].strip())
                            self.create_origin_quality(ori)
                            ori.quality.standardError = \
                                curr_rms_residual_phases
                        except Exception: 
                            pass
                        
                        # TODO(fab): degrees?
                        # horizontal error (km)
                        try:
                            che = float(line[74:79].strip())
                            ou = OriginUncertainty.OriginUncertainty()
                            ou.horizontalUncertainty = che
                            ou.add(ori)
                        except Exception:
                            pass

                        # depth error (km)
                        try:    
                            ori.depth.uncertainty = 1000 * float(
                                line[79:84].strip())
                        except Exception: 
                            pass
                        
                        # number of associated stations
                        try:    
                            ass_sta_cnt = int( line[99:101].strip() )
                            self.create_origin_quality(ori)
                            ori.quality.associatedStationCount = ass_sta_cnt
                        except Exception: 
                            pass

                    phaseMode      = True
                    phase_line_ctr = 0
                    originMode     = False
                    continue

                elif phaseMode:

                    ## read phase line

                    # if keyword argument 'nopicks' set, skip line
                    if not('nopicks' in kwargs and kwargs['nopicks']):

                        phase_line_ctr += 1
                        
                        # get sequence number
                        try:
                            curr_ev_seq = int( line[0:6].strip() )
                        except Exception:
                            error_str = " no valid sequence number in phase "\
                                "line %s: %s" % (line_ctr, line)
                            raise RuntimeError, error_str
                        
                        # check if there's a change in sequential number
                        # this would indicate a location line of a new non-localized event
                        # -> skip subsequent lines until next '^' localized event line 
                        if ev_seq != curr_ev_seq:
                            skipMode = True
                            continue

                        ## required: station code, phase block, arrival hour, minute, second
                        try:
                            curr_sta_code    = line[7:11].strip()
                            phase_block      = line[26:29].strip()

                            curr_hour        = int( line[31:33].strip() )
                            curr_minute      = int( line[33:35].strip() )
                            curr_second      = float( line[36:41].strip() )

                        except Exception:
                            print " error in phase line %s: %s" % (line_ctr, line)
                            continue

                        # no pick id provided: use phase line number
                        pick_id = str(phase_line_ctr)

                        # set base time (hour/minute) from which pick times are measured
                        # curr_hour and curr_minute are trusted to be in valid range
                        base_time_utc = DateTime(
                            curr_year, curr_month, curr_day, curr_hour, 
                            curr_minute, 0.0)

                        # sometimes first (P) pick seems to be invalid, 
                        # then seconds are set to 0.0, and a sequence of '*' 
                        # chars follow
                        if not (curr_second == 0.0 and \
                            line[41] == OGS_LINESTART_COMMENT):
                            
                            # create pick object and add to event
                            pick = Pick()
                            if not minConf:
                                pick.publicID = QPUtils.build_resource_identifier(
                                    auth_id, 'event', "%s/pick/%s" % (
                                        ori_id, pick_id))

                            pick_time_utc = base_time_utc + \
                                DateTimeDeltaFromSeconds(curr_second)
                            pick.time = TimeQuantity(QPDateTime.QPDateTime(
                                pick_time_utc))

                            # set waveform id
                            pick.waveformID = WaveformStreamID()
                            pick.waveformID.stationCode = curr_sta_code
                            pick.waveformID.networkCode = network_code
                            pick.add(ev)

                            # create arrival object and add to origin
                            arrv           = Arrival()
                            arrv.pickID    = pick.publicID
                            arrv.phase     = Phase(OGS_ARRIVAL_PHASE_P)
                            arrv.add(ori)

                            ## optional fields
                            
                            if not minConf:

                                pick.phaseHint = Phase(OGS_ARRIVAL_PHASE_P)

                                try:    
                                    phase_onset = phase_block[0]
                                except Exception: 
                                    phase_onset = ''

                                try:    
                                    phase_polarity = phase_block[2]
                                except Exception: 
                                    phase_polarity = ''
                            
                                # epicentral distance (km), convert to degrees 
                                # (great circle)
                                try:
                                    distance_km = float(line[12:17].strip())
                                    arrv.distance = \
                                        QPUtils.central_angle_degrees_from_distance(
                                            distance_km)
                        
                                except Exception: 
                                    pass

                                try:    
                                    arrv.azimuth = float( line[18:21].strip() )
                                except Exception: 
                                    pass

                                try:
                                    # NOTE: assume that 'angle of incidence' 
                                    # corresponds to slowness azimuth
                                    # convert to backazimuth
                                    pick.backazimuth = RealQuantity(
                                        QPUtils.backazimuth_from_azimuth_flat(
                                            float(line[22:25].strip())))
                                except Exception: 
                                    pass

                                # P phase onset (emergent/impulsive)
                                if phase_onset.lower() == 'e':
                                    pick.onset = 'emergent'
                                elif phase_onset.lower() == 'i':
                                    pick.onset = 'impulsive'

                                # P polarity
                                if phase_polarity == '+':
                                    pick.polarity = 'positive'
                                elif phase_polarity == '-':
                                    pick.polarity = 'negative'

                                # P-arrival time residual (sec)
                                try:    
                                    arrv.timeResidual = float(line[60:65].strip())
                                except Exception: 
                                    pass

                                # weight in hypocentral solution for this arrival
                                try:
                                    arrv.timeWeight = float(line[67:71].strip())
                                except Exception: 
                                    pass

                                ## duration/amplitude for magnitude
                                # QuakeML TimeWindow requires an absolute point in time for duration
                                # we use pick time of P phase
                                # measured duration goes into 'end' component of TimeWindow, 'begin' is set to zero
                                
                                # TODO(fab): what about genericAmplitude? unit?
                                amp = None
                                try:
                                    amp = Amplitude()

                                    tw = TimeWindow.TimeWindow(0.0, float(
                                        line[96:99].strip()))
                                    tw.reference   = pick.time.value
                                    amp.timeWindow = tw
                                            
                                    amp.add(ev)
                                            
                                except Exception:
                                    pass

                                if amp is not None:
                                    
                                    amp.publicID = \
                                        QPUtils.build_resource_identifier(auth_id, 
                                        'event', "%s/amplitude/%s" % (ori_id, 
                                            pick_id))
                                    
                                    amp.type = 'END'
                                    amp.unit = 's'
                                    amp.pickID = pick.publicID
                                    amp.waveformID = pick.waveformID

                                ## duration magnitude at station
                                sta_mag = None
                                try:
                                    sta_mag = StationMagnitude.StationMagnitude()
                                    sta_mag.mag = RealQuantity(float(
                                        line[100:103].strip()))

                                    sta_mag.add(ori)
                                        
                                except Exception:
                                    pass

                                if sta_mag is not None:

                                    sta_mag.type = 'Md'
                                    sta_mag.waveformID  = pick.waveformID

                                    try:    
                                        sta_mag.stationAmplitudeID = amp.publicID
                                    except Exception: 
                                        pass

                        ## S arrival
                        try:
                            phase_block = line[105:107].strip()
                            curr_second_s = float(line[110:115].strip())
                        except Exception:
                            continue

                        # no pick id provided: use phase line number
                        phase_line_ctr += 1
                        pick_id = str( phase_line_ctr )

                        # create pick object and add to event
                        pick = Pick()
                        if not minConf:
                            pick.publicID = QPUtils.build_resource_identifier(
                                auth_id,  'event', "%s/pick/%s" % (ori_id, 
                                    pick_id))

                        pick_time_utc = base_time_utc + DateTimeDeltaFromSeconds(
                            curr_second_s)
                        pick.time = TimeQuantity(
                            QPDateTime.QPDateTime(pick_time_utc))

                        # set waveform id
                        pick.waveformID = WaveformStreamID()
                        pick.waveformID.stationCode = curr_sta_code
                        pick.waveformID.networkCode = network_code
                        pick.add(ev)

                        # create arrival object and add to origin
                        arrv = Arrival()
                        arrv.pickID = pick.publicID
                        arrv.phase  = Phase(OGS_ARRIVAL_PHASE_S)
                        arrv.add(ori)
                        
                        if not minConf:

                            pick.phaseHint = Phase(OGS_ARRIVAL_PHASE_S)

                            try:    
                                phase_onset = phase_block[0]
                            except Exception: 
                                phase_onset = ''
                            
                            # S phase onset (emergent/impulsive)
                            if phase_onset.lower() == 'e':
                                pick.onset = 'emergent'
                            elif phase_onset.lower() == 'i':
                                pick.onset = 'impulsive'

                            # residual of S arrival (sec)
                            try:    
                                arrv.timeResidual = float(line[122:127].strip())
                            except Exception: 
                                pass

                            # weight in hypocentral solution for S arrival
                            try:    
                                arrv.timeWeight = float(line[130:133].strip())
                            except Exception: 
                                pass
                            
                        continue


    def exportAtticIvy(self, output, **kwargs):
        """ 
        Export catalog to format required by Roger Musson's AtticIvy code.

        One line per event (in this implementation).

        data example (note: ruler shown below is not part of data)

        0         1         2         3         4         5
        123456789012345678901234567890123456789012345678901234567890

        YYYY MM DD HH IIAABB PPPPPP LLLLLLL  EE RRR FFF WWWWKKKSSSSS
        1690  8 27 20  0 1 1  51.83   -4.38  00 4.3 0.0 1.00  0
        1727  7 19  4  0 1 1  51.57   -3.76  00 4.8 0.0 1.00 25
        1734 10 25  3 50 1 1  50.20   -0.70  00 4.1 0.0 1.00 14

        Fields: YYYY, MM, DD, HH, II    date/time components, no seconds used
                AA, BB                  ?
                PPPPPP, LLLLLLL         latitude, longitude
                EE                      horizontal error of epicenter in km, 00 if not known
                RRR                     magnitude
                FFF                     error of magnitude, 0.0 if not known
                WWWW                    weight of this location 
                                        (can have multiple locations per event)
                KKK                     hypocenter depth in km, 0 if not known
                SSSSS                   ?

        """
        
        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData(output, **kwargs)
        else:
            ostream = output

        ostream.write("%s\n" % ATTICIVY_HEADER_LINE)

        for ev in self.eventParameters.event:

            # check if event has preferred origin and coordinates, 
            # otherwise skip
            try:
                ori = ev.getPreferredOrigin()
                curr_lon = ori.longitude.value
                curr_lat = ori.latitude.value
            except Exception:
                continue

            try:
                mag = ev.getPreferredMagnitude()
                mag_value = mag.mag.value
            except Exception:
                continue

            # if origin has no depth, set depth column to zero
            if hasattr(ori, 'depth') and ori.depth is not None:
                depth_value = ori.depth.value / 1000.0
            else:
                depth_value = 0.0

            try:
                depth_value = int(ori.depth.value)
            except Exception:
                depth_value = 0

            hzErrorFound = False
            
            # look if explicit horizontal error is given 
            # in OriginUncertainty object
            # this overrides possible separate lat/lon errors
            if ori.originUncertainty:
                ou = ori.originUncertainty[0]

                if hasattr(ou, 'horizontalUncertainty'):
                    try:
                        horizontal_uncertainty_value = \
                            ou.horizontalUncertainty
                        hzErrorFound = True
                    except Exception:
                        pass

            # if no explicit horizontal error is given, compute horizontal 
            # error from lat/lon errors
            if not hzErrorFound:

                if hasattr(ori.longitude, 'uncertainty') and hasattr(
                        ori.latitude, 'uncertainty'):

                    try:
                        curr_lon_err = ori.longitude.uncertainty
                        curr_lat_err = ori.latitude.uncertainty
                        
                        # TODO(fab): use geospatial functions
                        horizontal_uncertainty_value = math.sqrt(
                            math.pow(
                                curr_lat_err * QPUtils.EARTH_KM_PER_DEGREE, 2) +
                            math.pow(curr_lon_err * math.cos(
                                curr_lat * math.pi/180.0) * \
                                    QPUtils.EARTH_KM_PER_DEGREE, 2))
                        hzErrorFound = True
                    except Exception:
                        pass


            # set horizontal error to zero, if not given
            if not hzErrorFound:
                horizontal_uncertainty_value = 0.0

            # set magnitude error to zero, if not given
            if hasattr(mag.mag, 'uncertainty') and \
                    mag.mag.uncertainty is not None:
                magnitude_uncertainty_value = mag.mag.uncertainty
            
            else:
                magnitude_uncertainty_value = 0.0

            line_arr = ( 
                '%4i' % ori.time.value.datetime.year,
                '%3i' % ori.time.value.datetime.month,
                '%3i' % ori.time.value.datetime.day,
                '%3i' % ori.time.value.datetime.hour,
                '%3i' % ori.time.value.datetime.minute,
                ' 1 1',
                '%7.2f' % ori.latitude.value,
                '%8.2f' % ori.longitude.value,
                '  %02i' % horizontal_uncertainty_value,
                ' %3.1f' % mag_value,
                ' %3.1f' % magnitude_uncertainty_value,
                ' 1.00',
                '%3i' % depth_value,
                ATTICIVY_BLANK_FIELD
            )

            ostream.write("%s\n" % ''.join(line_arr))
        
        ostream.close()


    def cut(self, polygon=None, grid=None, geometry=None, **kwargs):
        """
        Cut (= filter) catalog according to given parameter ranges.
        
        Input:
            polygon     tuple, list, numpy.array OR QPPolygon object
            grid        QPGrid object
            geometry    Shapely aggregate geometry object
        
            kwargs:     min* and max* for lat, lon, depth, time, magnitude
                        default: cutting limits are included in result
                        
                        If limit should be excluded, set
                        kwarg min*_excl=True (example: minmag_excl=True)

                        removeNaN=True: remove values that are set to 'NaN' 
                        when cutting (default: do not remove)
            
        Strategy for cutting: 
            An event is deleted if one origin/magnitude meets criterion
            
            Loop over event array (from end)
                (1) loop over origins:
                    - check if lat/lon falls into polygon: if not, break origin
                      loop, delete event, continue event loop.
                      Keep event if it falls on polygon boundary.
                      (Polygon: isInside(), QPPolygon: isInsideOrOnBoundary())
                    - if cut criterion met for lat/lon/depth/time, break origin
                      loop, delete event, continue event loop
                
                (2) loop over magnitudes: if cut criterion met, break mag loop, 
                    delete event, continue event loop
        
        """
        
        cut_params = kwargs.keys()
        
        # check if polygon is given
        if polygon is not None:
            if isinstance(polygon, QPPolygon.QPPolygon):
                poly_area = polygon
            else:
                poly_area = QPPolygon.QPPolygon(polygon)
        else:
            poly_area = None
        
        # loop over list of events in reversed order
        for curr_ev_idx in reversed(xrange(len(self.eventParameters.event))):
            
            cut_ev = False
            
            # need to go into origins?
            if     poly_area is not None \
                or grid is not None \
                or geometry is not None \
                or 'minlat' in cut_params or 'maxlat' in cut_params \
                or 'minlon' in cut_params or 'maxlon' in cut_params \
                or 'mindepth' in cut_params or 'maxdepth' in cut_params \
                or 'mintime' in cut_params or 'maxtime' in cut_params:
                
                for curr_ori in self.eventParameters.event[curr_ev_idx].origin:
                    
                    # check for polygon
                    if poly_area is not None:
                        if not poly_area.isInsideOrOnBoundary(
                            float(curr_ori.longitude.value),
                            float( curr_ori.latitude.value)):
                            
                            cut_ev = True
                            break
                        
                    # check for grid
                    if grid is not None:
                        
                        # check if grid is correct object
                        try:
                            isinstance(grid, QPGrid.QPGrid)
                        except Exception:
                            raise TypeError, \
                                'QPCatalog::cut - grid has wrong type'
                        
                        if not grid.inGrid(
                            float(curr_ori.latitude.value), 
                            float(curr_ori.longitude.value),
                            float(curr_ori.depth.value)):
                            
                            cut_ev = True
                            break

                    # check for geometry
                    if geometry is not None:
                        ev_point = shapely.geometry.Point( 
                            float(curr_ori.longitude.value),
                            float(curr_ori.latitude.value)) 
                        
                        if not (
                            geometry.contains(ev_point) or \
                            geometry.touches(ev_point)):
                            
                            cut_ev = True
                            break

                    # cut latitude
                    if ('removeNaN' in cut_params and kwargs['removeNaN'] and (
                        curr_ori.latitude.value is None or numpy.isnan(
                            curr_ori.latitude.value))):
                        
                        cut_ev = True
                        break
                    
                    else:
                        if 'minlat' in cut_params:
                            if 'minlat_excl' in cut_params and \
                                kwargs['minlat_excl']:
                                
                                if float(
                                    curr_ori.latitude.value) <= \
                                        kwargs['minlat']:
                                    cut_ev = True
                                    break
                            
                            elif float(
                                curr_ori.latitude.value) < kwargs['minlat']:
                                
                                cut_ev = True
                                break
                                    
                        if 'maxlat' in cut_params:
                            if 'maxlat_excl' in cut_params and \
                                kwargs['maxlat_excl']:
                                
                                if float(
                                    curr_ori.latitude.value) >= \
                                        kwargs['maxlat']:
                                    cut_ev = True
                                    break
                            
                            elif float(
                                curr_ori.latitude.value) > kwargs['maxlat']:
                                
                                cut_ev = True
                                break
                
                    # cut longitude
                    if ('removeNaN' in cut_params and kwargs['removeNaN'] and (
                        curr_ori.longitude.value is None or numpy.isnan(
                            curr_ori.longitude.value))):
                            
                        cut_ev = True
                        break
                    
                    else:
                        if 'minlon' in cut_params:
                            if 'minlon_excl' in cut_params and \
                                kwargs['minlon_excl']:
                                
                                if float(
                                    curr_ori.longitude.value) <= \
                                        kwargs['minlon']:
                                    cut_ev = True
                                    break
                            
                            elif float(
                                curr_ori.longitude.value) < kwargs['minlon']:
                                    
                                cut_ev = True
                                break
                                    
                        if 'maxlon' in cut_params:
                            if 'maxlon_excl' in cut_params and \
                                kwargs['maxlon_excl']:
                                
                                if float(
                                    curr_ori.longitude.value) >= \
                                        kwargs['maxlon']:
                                    cut_ev = True
                                    break
                            elif float(
                                curr_ori.longitude.value) > kwargs['maxlon']:
                                
                                cut_ev = True
                                break
                    
                    # cut depth
                    if 'removeNaN' in cut_params and kwargs['removeNaN'] and (
                        curr_ori.depth.value is None or numpy.isnan(
                            curr_ori.depth.value)):
                        
                        cut_ev = True
                        break
                    
                    else:
                        if 'mindepth' in cut_params:
                            if 'mindepth_excl' in cut_params and \
                                kwargs['mindepth_excl']:
                                
                                if float(
                                    curr_ori.depth.value) <= kwargs['mindepth']:
                                    
                                    cut_ev = True
                                    break
                            
                            elif float(
                                curr_ori.depth.value) < kwargs['mindepth']:
                                
                                cut_ev = True
                                break
                                
                        if 'maxdepth' in cut_params:
                            if 'maxdepth_excl' in cut_params and \
                                kwargs['maxdepth_excl']:
                                
                                if float(
                                    curr_ori.depth.value) >= kwargs['maxdepth']:
                                    
                                    cut_ev = True
                                    break
                            
                            elif float(
                                curr_ori.depth.value) > kwargs['maxdepth']:
                                
                                cut_ev = True
                                break
                    
                    # cut time
                    if 'mintime' in cut_params:
                        
                        mintime = QPDateTime.QPDateTime(
                            ParseDateTimeUTC(kwargs['mintime']))
                        
                        if 'mintime_excl' in cut_params and \
                            kwargs['mintime_excl']:
                            
                            if curr_ori.time.value <= mintime:
                                cut_ev = True
                                break
                        
                        elif curr_ori.time.value < mintime:
                            cut_ev = True
                            break

                    if 'maxtime' in cut_params:
                        
                        maxtime = QPDateTime.QPDateTime(
                            ParseDateTimeUTC(kwargs['maxtime']))
                        
                        if 'maxtime_excl' in cut_params and \
                            kwargs['maxtime_excl']:
                            
                            if curr_ori.time.value >= maxtime:
                                cut_ev = True
                                break
                        
                        elif curr_ori.time.value > maxtime:
                            cut_ev = True
                            break
                
                # origin loop finished    
                if cut_ev:
                    self.eventParameters.event.pop(curr_ev_idx)
                    continue
                   
            # need to go into magnitudes?
            if 'minmag' in cut_params or 'maxmag' in cut_params:

                for curr_mag in \
                    self.eventParameters.event[curr_ev_idx].magnitude:

                    if 'removeNaN' in cut_params and kwargs['removeNaN'] and (
                        curr_mag.mag.value is None or numpy.isnan(
                            curr_mag.mag.value)):
                        
                        cut_ev = True
                        break
                    
                    else:
                        if 'minmag' in cut_params:
                            
                            if 'minmag_excl' in cut_params and \
                                kwargs['minmag_excl']:
                                
                                if float(
                                    curr_mag.mag.value) <= kwargs['minmag']:
                                    
                                    cut_ev = True
                                    break
                            
                            elif float(curr_mag.mag.value) < kwargs['minmag']:
                                cut_ev = True
                                break

                        if 'maxmag' in cut_params:
                            
                            if 'maxmag_excl' in cut_params and \
                                kwargs['maxmag_excl']:
                                
                                if float(
                                    curr_mag.mag.value) >= kwargs['maxmag']:
                                    
                                    cut_ev = True
                                    break
                            
                            elif float(curr_mag.mag.value) > kwargs['maxmag']:
                                cut_ev = True
                                break    
                
                # mag loop finished
                if cut_ev:
                    self.eventParameters.event.pop(curr_ev_idx)
                    continue


    def rebin(self, binsize=DEFAULT_MAG_REBIN_BINSIZE, allorigins=True):
        
        # loop over events
        for curr_ev in self.eventParameters.event:
            
            # if allorgins=False, rebin only preferred origins, otherwise all
            if not allorigins:
                curr_ori = curr_ev.getPreferredOrigin()
                
                # rebin all magnitudes
                for curr_mag_idx in curr_ev.getMagnitudesIdx(curr_ori):
                    
                    curr_mag_value = curr_ev.magnitude[curr_mag_idx].mag.value
                    curr_ev.magnitude[curr_mag_idx].mag.value = \
                        QPUtils.rebin_float(curr_mag_value, binsize)
                
            else:
                for curr_ori in curr_ev.origin:
                    
                    # rebin all magnitudes
                    for curr_mag_idx in curr_ev.getMagnitudesIdx(curr_ori):
                        
                        curr_mag_value = \
                            curr_ev.magnitude[curr_mag_idx].mag.value
                        
                        curr_ev.magnitude[curr_mag_idx].mag.value = \
                            QPUtils.rebin_float(curr_mag_value, binsize)


    @property
    def size(self):
        """Return event count of a catalogue."""
        
        return len(self.eventParameters.event)
    
    
    def timeSpan(self):
        """
        Compute time span of events (use preferred origins).
        
        Returns a triple of time difference (in years), start time, end time
        
        """
        
        time_start = None
        time_end = None
        
        for curr_ev in self.eventParameters.event:
            curr_ori = curr_ev.getPreferredOrigin()
            curr_time = curr_ori.time.value
            
            if time_start is None:
                time_start = curr_time
                time_end = curr_time
            else:
                if curr_time < time_start:
                    time_start = curr_time
                elif curr_time > time_end:
                    time_end = curr_time
                    
        time_diff = QPDateTime.diffQPDateTime(time_end, time_start)
        
        # TODO(fab): remove magic number, account for leap year
        return (
            time_diff.days / 365.25, time_start.datetime, time_end.datetime)


    def getFmd(self, allorigins=False, **kwargs):
        """
        Compute and return frequency-magnitude distribution (FMD) object.
        
        """
        
        self.frequencyMagnitudeDistribution = \
            qpfmd.FrequencyMagnitudeDistribution( 
                self.eventParameters, **kwargs)
        
        return self.frequencyMagnitudeDistribution
    
    
    def getCumulativeDistribution(self):
        """
        Compute and return cumulative distribution object.
        
        """
        
        self.cumulativeDistribution = cumuldist.CumulativeDistribution(
            self.eventParameters)
        
        return self.cumulativeDistribution 


    def toCompact(self):
        """
        Return compact catalog object from  current catalog.
        
        """
        
        compact = QPCatalogCompact.QPCatalogCompact()
        compact.update(self.catalog)

        return compact


    def fromCompact(self, compact):
        """
        TODO(fab): Return full catalog from compact catalog.
        
        """
        
        raise NotImplementedError, \
            "compact catalog to full catalog not yet implemented"
    
    
    def origin_without_quality(self, ori):
        """Return true if origin doesn't have a quality attribute."""
        
        origin_with_quality = hasattr(ori, 'quality') and isinstance(
            ori.quality, OriginQuality)

        return not(origin_with_quality)


    def create_origin_quality(self, ori):
        """
        If origin has no quality attribute, append an empty quality attribute.
        
        """
        
        if origin_without_quality(ori):
            ori.quality = OriginQuality()


    def object_without_creationinfo(self, obj):
        """Return true if origin doesn't have a creationInfo attribute."""
        
        origin_with_creationinfo = hasattr(obj, 'creationInfo') and isinstance(
            obj.creationInfo, CreationInfo)
        
        return not(origin_with_creationinfo)


    def create_object_creationinfo(self, obj):
        """
        If origin has no creationInfo attribute, append an empty creationInfo 
        attribute.
        
        """
        
        if object_without_creationinfo(obj):
            obj.creationInfo = CreationInfo()
