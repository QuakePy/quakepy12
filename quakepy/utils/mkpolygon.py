#!/usr/bin/env python

"""
This file is part of QuakePy12.

"""



import sys
import getopt
import math

import xml.dom.ext
import xml.dom.minidom

import QPPolygon
from QPUtils import frange

## Global constants

# magnitude bins for CSEP ForecastML
MAG_MIN   =  4.0
MAG_MAX   =  9.0
MAG_DELTA =  0.1

EPSILON   = 10e-10

OUTPUT_NONE, OUTPUT_NODES, OUTPUT_GMT, OUTPUT_FORECASTML, OUTPUT_GRIDML = range(5)


def main():

  # Init defaults
  seOutput = OUTPUT_NONE
  bOutput2Standard   = True
  sOutputFilename    = ''
  bInputFromStandard = True
  sInputFilename     = ''
  
  rArea = { 'fLonLatDelta'          : 0.1,
            'fAlign'                : 0.0,
            'bIncludePointOnVertex' : False,
            'bShift'                : False,
            'fShift'                : 0.0,
            'fMinMag'               : 4.0,
            'fMaxMag'               : 9.0,
            'fDeltaMag'             : 0.1 }
  
  # If no commandline arguments given, print help and exit
  if len(sys.argv) == 1:
    PrintHelp()
    sys.exit()
    
  # Read commandline arguments
  sCmdParams = sys.argv[1:]
  opts, args = getopt.gnu_getopt( sCmdParams,
                                  'a:d:D:f:ghim:M:no:p:s:xy',
                                  ['align=', 'delta=', 'deltamag=', 'file', 'gmt',
                                  'help', 'include', 'nodes', 'minmag=', 'maxmag', 'output=',
                                  'polygon=', 'shift=', 'forecastml', 'gridml'] )

  for option, parameter in opts:
      
    if option == '-p' or option == '--polygon':
      sInputFilename = parameter
      bInputFromStandard = False

    if option == '-a' or option == '--align':
      rArea['fAlign'] = float(parameter)

    if option == '-d' or option == '--delta':
      rArea['fLonLatDelta'] = float(parameter)

    if option == '-D' or option == '--deltamag':
      rArea['fDeltaMag'] = float(parameter)
      
    if option == '-i' or option == '--include':
      rArea['bIncludePointOnVertex'] = True

    if option == '-m' or option == '--minmag':
      rArea['fMinMag'] = float(parameter)
      
    if option == '-M' or option == '--maxmag':
      rArea['fMaxMag'] = float(parameter)
      
    if option == '-s' or option == '--shift':
      rArea['bShift'] = True
      rArea['fShift'] = float(parameter)
      
    if option == '-g' or option == '--gmt':
      if seOutput != OUTPUT_NONE:
        print 'Please use only one of the following options: -n, -g, -x, -y'
        sys.exit()
      seOutput = OUTPUT_GMT

    if option == '-n' or option == '--nodes':
      if seOutput != OUTPUT_NONE:
        print 'Please use only one of the following options: -n, -g, -x, -y'
        sys.exit()
      seOutput = OUTPUT_NODES
    if option == '-x' or option == '--forecastml':
      if seOutput != OUTPUT_NONE:
        print 'Please use only one of the following options: -n, -g, -x, -y'
        sys.exit()
      seOutput = OUTPUT_FORECASTML
    if option == '-y' or option == '--gridml':
      if seOutput != OUTPUT_NONE:
        print 'Please use only one of the following options: -n, -g, -x, -y'
        sys.exit()
      seOutput = OUTPUT_GRIDML
    if option == '-o' or option == '--output':
      bOutput2Standard = False
      sOutputFilename = parameter
    if option == '-h' or option == '--help':
      PrintHelp()
      sys.exit()

  # Read polygon
  vPolygon = []
  mPolygon = [[], []]
  if bInputFromStandard:
    ftPolygon = sys.stdin
  else:
    ftPolygon = file(sInputFilename, "r")
  for line in ftPolygon:
    vValues = line.rstrip('\n').split()
    
    vValues[0] = float(vValues[0])
    vValues[1] = float(vValues[1])

    if rArea['bShift'] is True and vValues[0] < rArea['fShift']:
        vValues[0] = vValues[0] + 360.0

    vPolygon.append( [vValues[0], vValues[1]] )
    mPolygon[0].append(vValues[0])
    mPolygon[1].append(vValues[1])
    
  ftPolygon.close
  
  # Close polygon
  vPolygon.append([vPolygon[0][0], vPolygon[0][1]])

  # Store polygon
  rArea['vPolygon'] = QPPolygon.QPPolygon(vPolygon)

  # Determine extent of polygon
  rArea['fLonMin'] = round(min(mPolygon[0]) - (2* rArea['fLonLatDelta'])) - 2 + rArea['fAlign']
  rArea['fLonMax'] = round(max(mPolygon[0]) + (2* rArea['fLonLatDelta'])) + 1 + rArea['fAlign']
  rArea['fLatMin'] = round(min(mPolygon[1]) - (2* rArea['fLonLatDelta'])) - 2 + rArea['fAlign']
  rArea['fLatMax'] = round(max(mPolygon[1]) + (2* rArea['fLonLatDelta'])) + 1 + rArea['fAlign']

  # Open output
  if bOutput2Standard:
    ftOutput = sys.stdout
  else:
    ftOutput = file(sOutputFilename, "w")

  # Output grid nodes
  if seOutput == OUTPUT_NODES:
    OutputNodes(ftOutput, rArea)
    ftOutput.close()
    sys.exit()

  # Output GMT cells
  if seOutput == OUTPUT_GMT:
    OutputGMT(ftOutput, rArea)
    ftOutput.close()
    sys.exit()

  # Output to ForecastML
  if (seOutput == OUTPUT_FORECASTML) or (seOutput == OUTPUT_GRIDML):
    OutputXML(ftOutput, rArea, seOutput)
    ftOutput.close()
    sys.exit()

  # Exit if no output method defined
  print 'No output method defined. Please select one of the following options: -p, -n, -g, -x'
  print 'Exiting.'
  sys.exit()

# -----

def PrintHelp():
  print 'Generates various area files for CSEP testing'
  print '  Version 0.4 (26.11.2008), $Revision: 130 $'
  print 'Usage: mkpolygon.py [OPTION]'
  print '  Set polygon'
  print '   -p, --polygon=<filename>  Import polygon from file instead of stdin'
  print '  Select output method'
  print '   -g, --gmt                 Output cells for use with GMT (psxy)'
  print '   -n, --nodes               Output list of nodes'
  print '   -x, --forecastml          Output ForecastML template'
  print '   -y, --gridml              Output GridML file'
  print '  Special options'
  print '   -a, --align=<value>       Fraction of a degree to align the lon/lat nodes to (default: 0.0)'
  print '   -d, --delta=<value>       Set delta value for lon/lat gridding (default: 0.1)'
  print '   -D, --deltamag=<value>    Set delta magnitude for ForecastML (default: 0.1)'
  print '   -i, --include             Includes nodes on polygon vertices (default: not included)'
  print '   -m, --minmag=<value>      Set minimum magnitude for ForecastML (default: 4)'
  print '   -M, --maxmag=<value>      Set maximum magnitude for ForecasTML (default: 9)'
  print '   -s, --shift=<value>       Shift all values below <value> by 360 degrees for polygons crossing'
  print '                             the -180/180 longitude line (default: 0.0)'
  print '   -h, --help                print this information'
  print '   -o, --output=<filename>   Output to file instead of stdout'

def CreateNodes(rArea):
  mNodes = [[], []]
  
  # Loop over the grid
  for fLon in frange(rArea['fLonMin'], rArea['fLonMax'], rArea['fLonLatDelta']):
    for fLat in frange(rArea['fLatMin'], rArea['fLatMax'], rArea['fLonLatDelta']):

      if rArea['bIncludePointOnVertex']:

        # Check if point is in polygon or on vertex
        if (rArea['vPolygon'].isInside(fLon, fLat)) or (rArea['vPolygon'].isOnVertex(fLon, fLat)):
            
          # Create nodes
          mNodes[0].append(fLon)
          mNodes[1].append(fLat)
      else:
          
        # Check if point in polygon
        if (rArea['vPolygon'].isInside(fLon, fLat)):
          # Create nodes
          mNodes[0].append(fLon)
          mNodes[1].append(fLat)

  if rArea['bShift'] is True:
    nLen = len( mNodes[0] )
    for nCnt in xrange( 0, nLen ):
      if mNodes[0][nCnt] > 180.0:
        mNodes[0][nCnt] = mNodes[0][nCnt] - 360.0
          
  return mNodes

def OutputNodes(ftOutput, rArea):
  mNodes = CreateNodes(rArea)
  nLen = len(mNodes[0])
  for nCnt in xrange(0, nLen):
    sLine = str(mNodes[0][nCnt]) + '\t' + str(mNodes[1][nCnt])
    ftOutput.write(sLine + '\n')

def OutputGMT(ftOutput, rArea):
  mNodes = CreateNodes(rArea)
  nLen = len(mNodes[0])
  fInc = rArea['fLonLatDelta']/2
  for nCnt in xrange(0, nLen):
    sLine = str(mNodes[0][nCnt] - fInc) + '\t' + str(mNodes[1][nCnt] - fInc)
    ftOutput.write(sLine + '\n')
    sLine = str(mNodes[0][nCnt] + fInc) + '\t' + str(mNodes[1][nCnt] - fInc)
    ftOutput.write(sLine + '\n')
    sLine = str(mNodes[0][nCnt] + fInc) + '\t' + str(mNodes[1][nCnt] + fInc)
    ftOutput.write(sLine + '\n')
    sLine = str(mNodes[0][nCnt] - fInc) + '\t' + str(mNodes[1][nCnt] + fInc)
    ftOutput.write(sLine + '\n')
    sLine = str(mNodes[0][nCnt] - fInc) + '\t' + str(mNodes[1][nCnt] - fInc)
    ftOutput.write(sLine + '\n')
    ftOutput.write('>\n')

def OutputXML(ftOutput, rArea, seOutput):
  # Init variables
  nBins  = 0
  mNodes = CreateNodes(rArea)
  nLen   = len(mNodes[0])

  # Init constants
  DEPTH_MIN           =  0.0
  DEPTH_MAX           = 30.0
  LAST_MAG_BIN_OPEN   =  1
  BIN_NULL_VALUE      =  0.0

  # Create document
  xmlDocument = xml.dom.minidom.Document()
  if (seOutput == OUTPUT_FORECASTML):

    # Namespace
    elCSEPForecast = xmlDocument.createElementNS("http://www.scec.org/xml-ns/csep/forecast/0.1", "CSEPForecast")
    xmlDocument.appendChild(elCSEPForecast)

    # Add <forecastData>
    elForecastData = xmlDocument.createElement("forecastData")
    elForecastData.setAttribute("publicID", "smi:org.scec/csep/forecast/1")
    elCSEPForecast.appendChild(elForecastData)

    # Add <modelName>
    elModelName = xmlDocument.createElement("modelName")
    text = xmlDocument.createTextNode("unknown")
    elModelName.appendChild(text)
    elForecastData.appendChild(elModelName)

    # Add <version>
    elVersion = xmlDocument.createElement("version")
    text = xmlDocument.createTextNode("1.0")
    elVersion.appendChild(text)
    elForecastData.appendChild(elVersion)

    # Add <author>
    elAuthor = xmlDocument.createElement("author")
    text = xmlDocument.createTextNode("CSEP")
    elAuthor.appendChild(text)
    elForecastData.appendChild(elAuthor)

    # Add <issueDate>
    elIssueDate = xmlDocument.createElement("issueDate")
    text = xmlDocument.createTextNode("2005-06-18T10:30:00Z")
    elIssueDate.appendChild(text)
    elForecastData.appendChild(elIssueDate)

    # Add <forecastStartDate>
    elForecastStartDate = xmlDocument.createElement("forecastStartDate")
    text = xmlDocument.createTextNode("2008-01-01T00:00:00Z")
    elForecastStartDate.appendChild(text)
    elForecastData.appendChild(elForecastStartDate)

    # Add <forecastEndDate>
    elForecastEndDate = xmlDocument.createElement("forecastEndDate")
    text = xmlDocument.createTextNode("2013-01-01T00:00:00Z")
    elForecastEndDate.appendChild(text)
    elForecastData.appendChild(elForecastEndDate)

    # Add <defaultMagBinDimension>
    elDefaultMagBinDimension = xmlDocument.createElement("defaultMagBinDimension")
    text = xmlDocument.createTextNode(str(rArea['fDeltaMag']))
    elDefaultMagBinDimension.appendChild(text)
    elForecastData.appendChild(elDefaultMagBinDimension)

    # Add <lastMagBinOpen>
    elLastMagBinOpen = xmlDocument.createElement("lastMagBinOpen")
    text = xmlDocument.createTextNode(str(LAST_MAG_BIN_OPEN))
    elLastMagBinOpen.appendChild(text)
    elForecastData.appendChild(elLastMagBinOpen)
  else:

    # Namespace
    elCSEPGrid = xmlDocument.createElementNS("http://www.scec.org/xml-ns/csep/grid/0.1", "CSEPGrid")
    xmlDocument.appendChild(elCSEPGrid)

    # Add <grid>
    elGrid = xmlDocument.createElement("grid")
    elCSEPGrid.appendChild(elGrid)

  # Add <defaultCellDimension>
  elDefaultCellDimension = xmlDocument.createElement("defaultCellDimension")
  elDefaultCellDimension.setAttribute("lonRange", str(rArea['fLonLatDelta']))
  elDefaultCellDimension.setAttribute("latRange", str(rArea['fLonLatDelta']))

  if (seOutput == OUTPUT_FORECASTML):
    elForecastData.appendChild(elDefaultCellDimension)
  else:
    elGrid.appendChild(elDefaultCellDimension)

  # Add depth layer
  elDepthLayer = xmlDocument.createElement("depthLayer")
  elDepthLayer.setAttribute("min", str(DEPTH_MIN))
  elDepthLayer.setAttribute("max", str(DEPTH_MAX))

  if (seOutput == OUTPUT_FORECASTML):
    elForecastData.appendChild(elDepthLayer)
  else:
    elGrid.appendChild(elDepthLayer)

  mNodes = CreateNodes(rArea)
  nLen = len(mNodes[0])

  for nCnt in xrange(0, nLen):

    # create <cell>
    elCell = xmlDocument.createElement("cell")
    elCell.setAttribute("lon", str(mNodes[0][nCnt]))
    elCell.setAttribute("lat", str(mNodes[1][nCnt]))
    elDepthLayer.appendChild(elCell)
    if seOutput == OUTPUT_FORECASTML:

      # Add magnitude bins
      for fMag in frange(rArea['fMinMag'], rArea['fMaxMag'], rArea['fDeltaMag']):
        nBins += 1

        # create <bin>
        elBin = xmlDocument.createElement("bin")
        elBin.setAttribute("m", str(fMag))
        text = xmlDocument.createTextNode(str(BIN_NULL_VALUE))
        elBin.appendChild(text)
        elCell.appendChild(elBin)

  xml.dom.ext.PrettyPrint(xmlDocument, ftOutput)

main()
