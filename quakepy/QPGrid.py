# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import cStringIO
import pyRXP

from quakepy import QPElement
from quakepy import QPCore
from quakepy import QPPolygon


ROOT_ELEMENT_NAME = 'QPGrid'
ROOT_ELEMENT_AXIS = "/%s" % ROOT_ELEMENT_NAME

PACKAGE_ELEMENT_NAME = 'grid'
ANNOTATION_ELEMENT_NAME = 'annotation'

STATIONS_ATTRIBUTE_NAME = 'stations'

PMC_STATIONS_ELEMENT_NAME = 'QPStations'
PMC_STATION_ELEMENT_NAME = 'QPStation'


class Cell(QPCore.QPObject):
    """
    QuakePy: Cell
    """

    addElements = QPElement.QPElementList((
        QPElement.QPElement('lat', 'lat', 'attribute', float, 'basic'),
        QPElement.QPElement('lon', 'lon', 'attribute', float, 'basic')
    ))
    
    def __init__(self, **kwargs):
        super(Cell, self).__init__(**kwargs)
        
        self.elements.extend(self.addElements)
        self._initMultipleElements()


class DefaultCellDimension(QPCore.QPObject):
    """
    QuakePy: DefaultCellDimension
    """

    addElements = QPElement.QPElementList((
        QPElement.QPElement('latRange', 'latRange', 'attribute', float, 'basic'),
        QPElement.QPElement('lonRange', 'lonRange', 'attribute', float, 'basic')
    ))
    
    def __init__(self, **kwargs):
        super(DefaultCellDimension, self).__init__(**kwargs)
        
        self.elements.extend(self.addElements)
        self._initMultipleElements()


class DepthLayer(QPCore.QPObject):
    """
    QuakePy: DepthLayer
    """

    addElements = QPElement.QPElementList((
        QPElement.QPElement( 'min', 'min', 'attribute', float, 'basic' ),
        QPElement.QPElement( 'max', 'max', 'attribute', float, 'basic' ),
        QPElement.QPElement( 'at', 'at', 'attribute', float, 'basic' ),
        QPElement.QPElement( 'cell', 'cell', 'element', Cell, 'multiple' )
    ))
    
    def __init__(self, **kwargs):
        super(DepthLayer, self).__init__(**kwargs)
        
        self.elements.extend(self.addElements)
        self._initMultipleElements()


class Grid(QPCore.QPObject):
    """
    QuakePy: Grid
    """

    addElements = QPElement.QPElementList((
        QPElement.QPElement('defaultCellDimension', 'defaultCellDimension', 
            'element', DefaultCellDimension, 'complex'),
        QPElement.QPElement('depthLayer', 'depthLayer', 'element', DepthLayer, 'multiple')
    ))
    
    def __init__(self, **kwargs):
        super(Grid, self).__init__(**kwargs)
        
        self.elements.extend(self.addElements)
        self._initMultipleElements()
        

class QPGrid(QPCore.QPObject):

    gridParameter = { 
        'lonDelta': 0.1,
        'latDelta': 0.1,
        'lonAlign': 0.0,
        'latAlign': 0.0,
        'includePointOnBoundary': True,
        'shift': True  
    }

    def __init__(self, input=None, **kwargs):
        super(QPGrid, self).__init__(**kwargs)

        # set element axis
        self.setElementAxis(ROOT_ELEMENT_AXIS)

        if input is not None:
            if isinstance(input, QPCore.STRING_TYPES):
                istream = QPUtils.getQPDataSource(input)
            else:
                istream = input
            
            self.readXML(istream)

    
    def readXML(self, input, **kwargs ):

        if isinstance(input, QPCore.STRING_TYPES):
            istream = QPUtils.getQPDataSource(input, **kwargs)
        else:
            istream = input
            
        # get whole content of stream at once
        lines = istream.read()
        
        # check if it is XML
        if not lines.startswith('<?xml'):
            raise IOError, 'QPGrid::readXML - input stream is not XML'
            
        tree = pyRXP.Parser().parse(lines)
        
        if tree[QPCore.POS_TAGNAME] != ROOT_ELEMENT_NAME:
            raise TypeError, 'input stream is not of QPGrid type'
        
        # NOTE: annotation element is not read from XML
        for child in tree[QPCore.POS_CHILDREN]:
            
            # possible child elements: grid
            if child[QPCore.POS_TAGNAME] == PACKAGE_ELEMENT_NAME:
              
                # QPGrid can only contain one single grid element
                # check if grid already existing
                if hasattr(self, PACKAGE_ELEMENT_NAME):
                    raise TypeError, \
                        'only single occurrence of grid element allowed'
                
                self.grid = Grid(parentAxis=self.elementAxis,
                    elementName=PACKAGE_ELEMENT_NAME)
                                                
                self.grid.fromXML(child, self.elements)

        if not hasattr(self, PACKAGE_ELEMENT_NAME):
            raise TypeError, 'no grid tag found'


    def writeXML(self, output, **kwargs):

        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData(output, **kwargs)
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
                self.toXML(ROOT_ELEMENT_NAME, curr_stream)
                streamSuccess = True
            except:
                streamSuccess = False
                print "error in StringIO self.toXML()"

            if streamSuccess is True:
                try:
                    QPUtils.xmlPrettyPrint(curr_stream, ostream)
                    return
                except:
                    print "error in xmlPrettyPrint()"

        # write to output stream w/o pretty print
        # fallback if prettify has not succeeded
        try:
            self.toXML(ROOT_ELEMENT_NAME, ostream)
        except:
            raise IOError, "error in self.toXML()"
    
    
    def toXML(self, tagname, stream):

        stream.write(QPCore.XML_DECLARATION)
        stream.writelines(['<', tagname, 
            ' xmlns="%s">' % QPCore.XML_NAMESPACE_QUAKEPY])
        
        if hasattr(self, ANNOTATION_ELEMENT_NAME) and \
            self.annotation is not None:
            self.annotation.toXML(ANNOTATION_ELEMENT_NAME, stream)
            
        if hasattr(self, PACKAGE_ELEMENT_NAME) and self.grid is not None:
            self.grid.toXML(PACKAGE_ELEMENT_NAME, stream)
            
        # NOTE: this is not a typical element of QPGrid
        # should later be placed somewhere else
        if hasattr(self, STATIONS_ATTRIBUTE_NAME) and \
            self.stations is not None:
            stream.writelines("<%s>" % PMC_STATIONS_ELEMENT_NAME)
            for sta in self.stations:
                sta.toXML(PMC_STATION_ELEMENT_NAME, stream)
            stream.writelines("</%s>" % PMC_STATIONS_ELEMENT_NAME)
            
        stream.writelines(['</', tagname, '>'])
        return True


    def writeNodes(self, output):

        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData(output)
        else:
            ostream = output
            
        for curr_cell in self.grid.depthLayer[0].cell:
            ostream.writelines([str(curr_cell.lon), "\t",  str(curr_cell.lat),
                "\n"])


    def writeCells(self, output):

        if isinstance(output, QPCore.STRING_TYPES):
            ostream = QPUtils.writeQPData(output)
        else:
            ostream = output

        for curr_cell in self.grid.depthLayer[0].cell:
            
            ostream.writelines( [ str(curr_cell.lon - 0.5 * self.gridParameter['lonDelta']), "\t",
                                  str(curr_cell.lat - 0.5 * self.gridParameter['latDelta']), "\n" ] )
            ostream.writelines( [ str(curr_cell.lon - 0.5 * self.gridParameter['lonDelta']), "\t",
                                  str(curr_cell.lat + 0.5 * self.gridParameter['latDelta']), "\n" ] )
            ostream.writelines( [ str(curr_cell.lon + 0.5 * self.gridParameter['lonDelta']), "\t",
                                  str(curr_cell.lat + 0.5 * self.gridParameter['latDelta']), "\n" ] )
            ostream.writelines( [ str(curr_cell.lon + 0.5 * self.gridParameter['lonDelta']), "\t",
                                  str(curr_cell.lat - 0.5 * self.gridParameter['latDelta']), "\n" ] )
            ostream.writelines( [ str(curr_cell.lon - 0.5 * self.gridParameter['lonDelta']), "\t",
                                  str(curr_cell.lat - 0.5 * self.gridParameter['latDelta']), "\n" ] )
            ostream.writelines( [ '>', "\n" ] )
    

    def setGridParameter(self, param):
    
        # update gridParameter dictionary
        for key in param.keys():
            self.gridParameter[key] = param[key]

    
    def setupBox(self, lonmin, lonmax, latmin, latmax, depthmin, depthmax):

        self.grid = Grid(parentAxis=self.elementAxis, 
            elementName=PACKAGE_ELEMENT_NAME)
        
        # depth layer
        dl = DepthLayer()
        dl.add(self.grid)
        
        if depthmax == depthmin:
            dl.at = depthmax
        else:
            dl.min = depthmin
            dl.max = depthmax

        # over lon
        for curr_lon in QPUtils.frange(lonmin, lonmax, 
            self.gridParameter['lonDelta']):

            # over lat
            for curr_lat in QPUtils.frange(latmin, latmax, 
                self.gridParameter['latDelta']):

                curr_cell = Cell()
                curr_cell.add(dl)
                
                curr_cell.lon = curr_lon
                curr_cell.lat = curr_lat

        return True


    def setupPolygon(self, polygon, depthmin, depthmax):
        """
        polygon must be of type QPPolygon, createNodes() should already be 
            called on polygon
        if node list is empty, call polygon.createNodes() from constructor
        """

        if not isinstance(polygon, QPPolygon.QPPolygon):
            raise TypeError, \
                'wrong type for parameter polygon, must be QPPolygon'

        nodes = self._createNodes(polygon)

        self.grid = Grid(parentAxis=self.elementAxis,
            elementName=PACKAGE_ELEMENT_NAME)
        
        # depth layer
        dl = DepthLayer()
        dl.add(self.grid)

        if depthmax == depthmin:
            dl.at = depthmax
        else:
            dl.min = depthmin
            dl.max = depthmax

        # loop over nodes of polygon
        for curr_node in nodes:
            
            curr_cell = Cell()
            curr_cell.add(dl)
            
            curr_cell.lon = curr_node[0]
            curr_cell.lat = curr_node[1]

        return True

    
    def inGridCell(self, lat, lon, depth):
        
        # depthLayer bin 0...30 km: depth  0 km is inside bin
        #                           depth 30 km is outside bin
        #
        # returns ( foundLat, foundLon, foundDepthMin, foundDepthMax ) or None
    
        for curr_depth_layer in self.grid.depthLayer:
            if depth >= curr_depth_layer.min and depth < curr_depth_layer.max:

                # look for cell
                for curr_cell in curr_depth_layer.cell:
                    
                    latMin = curr_cell.lat - 0.5 * \
                        self.grid.defaultCellDimension.latRange
                    latMax = curr_cell.lat + 0.5 * \
                        self.grid.defaultCellDimension.latRange
                    lonMin = curr_cell.lon - 0.5 * \
                        self.grid.defaultCellDimension.lonRange
                    lonMax = curr_cell.lon + 0.5 * \
                        self.grid.defaultCellDimension.lonRange
                    
                    if lat >= latMin and lat < latMax and lon >= lonMin and \
                        lon < lonMax:
                        return (curr_cell.lat, curr_cell.lon, 
                            curr_depth_layer.min, curr_depth_layer.max)
         
        # depthLayer or cell not found
        return None
            
            
    def inGrid(self, lat, lon, depth):
        
        if self.inGridCell(lat, lon, depth) is None:
            return False
        else:
            return True

    
    def _createNodes(self, polygon):

        polygon.getExtent(self.gridParameter['lonDelta'], 
            self.gridParameter['latDelta'], self.gridParameter['lonAlign'],
            self.gridParameter['latAlign'])

        nodes = []
        
        # loop over the grid
        for fLon in QPUtils.frange(polygon.lonMin, polygon.lonMax, 
            self.gridParameter['lonDelta']):
            
            for fLat in QPUtils.frange(polygon.latMin, polygon.latMax, 
                self.gridParameter['latDelta']):

                if self.gridParameter['includePointOnBoundary'] is True:

                    # check if point is in polygon or on boundary
                    if polygon.isInsideOrOnBoundary(fLon, fLat):
                        
                        # Create nodes
                        nodes.append([fLon, fLat])
                else:
                    
                    # check if point in polygon
                    if polygon.isInside(fLon, fLat):

                        # Create nodes
                        nodes.append([fLon, fLat])

        if self.gridParameter['shift'] is True:

            for nCnt in xrange(len(nodes)):
                if nodes[nCnt][0] > 180.0:
                    nodes[nCnt][0] = nodes[nCnt][0] - 360.0

        return nodes
