# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import cStringIO
import pyRXP

# internal includes
from QPCore import *
from QPUtils import *

POS_TAGNAME, POS_ATTRS, POS_CHILDREN = range(3)

# forward declarations

class QPAnnotation( object ):

    XML_NS = 'http://quakepy.org/xmlns/annotation/1.0'

    def __init__( self, **kwargs ):
        """
        the class attributes correspond to the Dublin Core elements
        although all Dublin Core elements are optional and can be repeated,
        we allow multiple occurrence only for creator, subject, source, and bibliographicCitation
        """
        self.creator   = []
        self.publisher = []
        self.subject   = []
        self.source    = []
        self.rights    = []

        self.bibliographicCitation = []
        self.comment               = []

        self.coverageTemporal = {}
        self.coverageSpatial  = {}

        self.observationTimeInterval = {}
        self.processParameters       = {}
        
        self.setProperty( **kwargs )
        
    # ------------------------------------------------------------------------

    def writeXML( self, output, **kwargs ):

        if isinstance( output, basestring ):
            ostream = writeQPData( output, **kwargs )
        else:
            ostream = output

        if 'prettyPrint' in kwargs and kwargs['prettyPrint'] is False:
            prettyPrint = False
        else:
            prettyPrint = True
            
        if prettyPrint is True:

            # serialize to string stream
            try:
                curr_stream = cStringIO.StringIO()
                curr_stream.write( '<?xml version="1.0" encoding="utf-8"?>' )
                self.toXML( 'QPAnnotation', curr_stream )
                streamSuccess = True
            except:
                streamSuccess = False
                print "QPAnnotation::writeXML - error in StringIO self.toXML()"

            if streamSuccess is True:
                try:
                    xmlPrettyPrint( curr_stream, ostream )
                    return
                except:
                    print "QPAnnotation::writeXML - error in xmlPrettyPrint()"

        # write to output stream w/o pretty print
        # fallback if prettify has not succeeded
        try:
            ostream.write( '<?xml version="1.0" encoding="utf-8"?>' )
            self.toXML( 'QPAnnotation', ostream )
            
        except:
            raise IOError, "QPAnnotation::writeXML - error in self.toXML()"
    
    # ------------------------------------------------------------------------
    
    def toXML( self, tagname, stream ):

        stream.writelines( [ '<a:', tagname,
        ' xmlns:a="', self.XML_NS,
        '" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:gml="http://www.opengis.net/gml">' ] )
        
        # dc:title
        if hasattr( self, 'title' ) and self.title is not None:
            stream.writelines( [ '<dc:title>', self.title, '</dc:title>' ] )
            
        # dc:creator (multi)
        if len( self.creator ) > 0:
            for cr in self.creator:
                stream.writelines( [ '<dc:creator>', cr, '</dc:creator>' ] )
          
        # dc:publisher (multi)
        if len( self.publisher ) > 0:
            for pu in self.publisher:
                stream.writelines( [ '<dc:publisher>', pu, '</dc:publisher>' ] )
            
        # dc:date
        if hasattr( self, 'date' ) and self.date is not None:
            stream.writelines( 
                [ '<dc:date>', mxDateTime2ISO( self.date, showtime=False ), 
                 '</dc:date>' ] )
            
        # dc:identifier
        if hasattr( self, 'identifier' ) and self.identifier is not None:
            stream.writelines( 
                [ '<dc:identifier>', self.identifier, '</dc:identifier>' ] )
            
        # dc:rights (multi)
        if len( self.rights ) > 0:
            for ri in self.rights:
                stream.writelines( [ '<dc:rights>', ri, '</dc:rights>' ] )
            
        # dc:subject (multi)
        if len( self.subject ) > 0:
            for su in self.subject:
                stream.writelines( [ '<dc:subject>', su, '</dc:subject>' ] )
            
        # dc:source (multi)
        if len( self.source ) > 0:
            for so in self.source:
                stream.writelines( [ '<dc:source>', so, '</dc:source>' ] )

        # dcterms:bibliographicCitation  (multi)
        if len( self.bibliographicCitation ) > 0:
            for bc in self.bibliographicCitation:
                stream.writelines( [ '<dcterms:bibliographicCitation>', bc,
                                     '</dcterms:bibliographicCitation>' ] )
        
        # comment (multi)
        if len( self.comment ) > 0:
            for co in self.comment:
                stream.writelines( [ '<a:comment>', co, '</a:comment>' ] )
        
        # version
        if hasattr( self, 'version' ) and self.version is not None:
            stream.writelines( [ '<a:version>', self.version, '</a:version>' ] )
            
        # acknowledgment
        if hasattr( self, 'acknowledgment' ) and self.acknowledgment is not None:
            stream.writelines( 
                [ '<a:acknowledgment>', self.acknowledgment, 
                 '</a:acknowledgment>' ] )
            
        # dc:coverage
        if ( len( self.coverageTemporal ) > 0 ) or ( 
            len( self.coverageSpatial ) > 0 ):
          
            stream.write( '<dc:coverage>' )
            
            #   temporal
            if (     ( self.coverageTemporal['starttime'] is not None ) 
                 and ( self.coverageTemporal['endtime'] is not None )):
                
                # only a point in time is given
                if self.coverageTemporal['starttime'] == \
                    self.coverageTemporal['endtime']:
                  
                    stream.writelines( 
                        [ '<gml:validTime><gml:TimeInstant><gml:TimePosition>', 
                        mxDateTime2ISO( self.coverageTemporal['starttime'] ), 
                        '</gml:TimePosition></gml:TimeInstant></gml:validTime>' ] )
                
                # a time range is given
                else:
                    stream.writelines( 
                        [ '<gml:validTime><gml:TimePeriod>',
                        '<gml:begin>',
                        mxDateTime2ISO( self.coverageTemporal['starttime'] ),
                        '</gml:begin>',
                        '<gml:end>',
                        mxDateTime2ISO( self.coverageTemporal['endtime'] ),
                        '</gml:end>',
                        '</gml:TimePeriod></gml:validTime>' ] )
            
            # spatial 
            if (      ( self.coverageSpatial['latmin'] is not None ) 
                 and  ( self.coverageSpatial['lonmin'] is not None )
                 and  ( self.coverageSpatial['latmax'] is not None )
                 and  ( self.coverageSpatial['lonmax'] is not None ) ):
              
                stream.writelines( 
                    [ '<gml:boundedBy>',
                    '<gml:Envelope srsName="urn:EPSG:geographicCRS:4326">',
                    '<gml:lowerCorner>',
                    str( self.coverageSpatial['lonmin'] ), ' ', 
                    str( self.coverageSpatial['latmin'] ),
                    '</gml:lowerCorner>',
                    '<gml:upperCorner>',
                    str( self.coverageSpatial['lonmax'] ), ' ', 
                    str( self.coverageSpatial['latmax'] ),
                    '</gml:upperCorner>',
                    '</gml:Envelope>',
                    '</gml:boundedBy>' ] )

            # boundary polygon
            if self.coverageSpatial['boundary'] is not None:
              
                stream.writelines( 
                    [ '<a:boundary>',
                    '<gml:Polygon srsName="urn:EPSG:geographicCRS:4326">',
                    '<gml:exterior>',
                    '<gml:linearRing>',
                    '<gml:posList>' ] )

                for curr_vertex_idx, curr_vertex in enumerate(
                    self.coverageSpatial['boundary'] ):

                    if curr_vertex_idx < len( 
                        self.coverageSpatial['boundary'] )-1:
                        
                        stream.writelines( 
                            [str(curr_vertex[0]), ' ', str(curr_vertex[1]), ' ' ])
                    else:
                        # last vertex

                        # check if polygon is closed
                        if curr_vertex == self.coverageSpatial['boundary'][0]:
                            stream.writelines( 
                                [str(curr_vertex[0]), ' ', str(curr_vertex[1])])
                        else:
                            # polygon is not closed, duplicate first entry
                            stream.writelines( 
                                [ str(curr_vertex[0]), ' ', str(curr_vertex[1]), 
                                 ' ' ] )
                            
                            stream.writelines(
                                [ str(self.coverageSpatial['boundary'][0][0]), 
                                ' ', str(self.coverageSpatial['boundary'][0][1])])
                    
                stream.writelines( [ '</gml:posList>',
                                     '</gml:linearRing>',
                                     '</gml:exterior>',
                                     '</gml:Polygon>',
                                     '</a:boundary>' ] )
                                     
            stream.write( '</dc:coverage>' )

        # observationTimeInterval
        if len( self.observationTimeInterval ) > 0:
          
            stream.write( '<a:observationTimeInterval>' )
            
            if (     ( self.observationTimeInterval['starttime'] is not None )
                 and ( self.observationTimeInterval['endtime'] is not None )):
                
                stream.writelines( 
                    [ '<gml:validTime><gml:TimePeriod>',
                     '<gml:begin>',
                     mxDateTime2ISO( self.observationTimeInterval['starttime'] ),
                     '</gml:begin>',
                     '<gml:end>',
                     mxDateTime2ISO( self.observationTimeInterval['endtime'] ),
                     '</gml:end>',
                     '</gml:TimePeriod></gml:validTime>' ] )

            stream.write( '</a:observationTimeInterval>' )

        # processParameters
        if len( self.processParameters ) > 0:

            stream.write( '<a:processParameters>' )
            
            if self.processParameters['maxStationCnt'] is not None:
                
                stream.writelines( 
                    [ '<a:maxStationCnt>',
                    str( self.processParameters['maxStationCnt'] ),
                    '</a:maxStationCnt>' ] )

            stream.write( '</a:processParameters>' )
            
        stream.writelines( [ '</a:', tagname, '>' ] )
        return True

    # ------------------------------------------------------------------------

    def setProperty( self, **kwargs ):
        """
        set annotation properties
        dates are mx.DateTime instances
        """
        
        # title
        if ( 'title' in kwargs ) and ( kwargs['title'] is not None ):
            self.title = kwargs['title']
            
        # creator
        if ( 'creator' in kwargs ) and ( kwargs['creator'] is not None ):
            self.creator = kwargs['creator']
            
        # publisher
        if ( 'publisher' in kwargs ) and ( kwargs['publisher'] is not None ):
            self.publisher = kwargs['publisher']
            
        # rights
        if ( 'rights' in kwargs ) and ( kwargs['rights'] is not None ):
            self.rights = kwargs['rights']
            
        # subject
        if ( 'subject' in kwargs ) and ( kwargs['subject'] is not None ):
            self.subject = kwargs['subject']
            
        # source
        if ( 'source' in kwargs ) and ( kwargs['source'] is not None ):
            self.source = kwargs['source']

        # dcterms:bibliographicCitation
        if ( 'bibliographicCitation' in kwargs ) and ( 
            kwargs['bibliographicCitation'] is not None ):
            
            self.bibliographicCitation = kwargs['bibliographicCitation']
            
        # comment
        if ( 'comment' in kwargs ) and ( kwargs['comment'] is not None ):
            self.comment = kwargs['comment']

        # date of program execution / resource publishing date
        if ( 'date' in kwargs ) and ( kwargs['date'] is not None ):
            self.date = kwargs['date']
        
        # temporal coverage / point in time for completeness computation
        if ( 'starttime' in kwargs ) and ( kwargs['starttime'] is not None ):
            self.coverageTemporal['starttime'] = kwargs['starttime']
        if ( 'endtime' in kwargs ) and ( kwargs['endtime'] is not None ):
            self.coverageTemporal['endtime'] = kwargs['endtime']
        
        # spatial coverage / grid boundaries
        if ( 'latmin' in kwargs ) and ( kwargs['latmin'] is not None ):
            self.coverageSpatial['latmin'] = kwargs['latmin']
        if ( 'latmax' in kwargs ) and ( kwargs['latmax'] is not None ):
            self.coverageSpatial['latmax'] = kwargs['latmax']
        if ( 'lonmin' in kwargs ) and ( kwargs['lonmin'] is not None ):
            self.coverageSpatial['lonmin'] = kwargs['lonmin']
        if ( 'lonmax' in kwargs ) and ( kwargs['lonmax'] is not None ):
            self.coverageSpatial['lonmax'] = kwargs['lonmax']

        if ( 'boundary' in kwargs ) and ( kwargs['boundary'] is not None ):
            self.coverageSpatial['boundary'] = kwargs['boundary']
            
        # observationTimeInterval
        if ( 'observationStartTime' in kwargs ) and ( 
            kwargs['observationStartTime'] is not None ):
            
            self.observationTimeInterval['starttime'] = kwargs['observationStartTime']
        
        if ( 'observationEndTime' in kwargs ) and ( 
            kwargs['observationEndTime'] is not None ):
            
            self.observationTimeInterval['endtime'] = kwargs['observationEndTime']

        # process parameters
        # maxStationCnt
        if ( 'maxStationCnt' in kwargs ) and ( 
            kwargs['maxStationCnt'] is not None ):
            
            self.processParameters['maxStationCnt'] = kwargs['maxStationCnt']
        
        return True