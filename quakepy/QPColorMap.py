# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import colorsys
import matplotlib

import numpy

# internal includes

from QPUtils import *

# forward declarations

class QPColorMap( object ):

    def __init__( self ):
        """
        create color map object from povray data

        """
        pass

    # ------------------------------------------------------------------------

    def importPovray( self, sFilename, **kwargs ):

        # Create data source
        if sFilename is not None:
            dsInput = getQPDataSource(sFilename)
        else:
            raise IOError, "File not found"
        self.sColormapName = os.path.basename(os.path.abspath(sFilename))

        # Plain import
        self.mData = [[], [], [], []]
        sPreviousLine = ''
        for sLine in dsInput:
            if self._isUsed(sLine):
                if (sLine != sPreviousLine):
                    vDataLine = self._convertLine(sLine)
                    self.mData[0].append(vDataLine[0])
                    self.mData[1].append(vDataLine[1])
                    self.mData[2].append(vDataLine[2])
                    self.mData[3].append(vDataLine[3])
                    sPreviousLine = sLine

        # Change saturation
        if ('saturation' in kwargs.keys()) and (kwargs['saturation'] is not None):
            self.saturation(float(kwargs['saturation']))

        # Flip colormap
        if ('flip' in kwargs.keys()) and (kwargs['flip'] is True):
            self.flip()

        #if (bLogScale) and (bValuesAlreadyLog == False):
        #    fMin = log10(fMin)
        #    fMax = log10(fMax)

        # Create discrete colors steps instead of interpolated colors
        if ('discretize' in kwargs.keys()) and (kwargs['discretize'] is not None):
            fNumSteps = int((kwargs['discretize']))
            self.bDiscretize = True
            self.discretize(fNumSteps)
        else:
            self.bDiscretize = False

        #if bLogScale:
        #    mCpt = RestoreZValues(mCpt)

        # Specify color values for NaN values and values outside the range
        if ('ncolor' in kwargs.keys()) and (kwargs['ncolor'] is not None):
            self.vNColor = kwargs['ncolor']
        else:
            self.vNColor = ['-', '-', '-']
        if ('fcolor' in kwargs.keys()) and (kwargs['fcolor'] is not None):
            self.vFColor = kwargs['fcolor']
        else:
            self.vFColor = ['-', '-', '-']
        if ('bcolor' in kwargs.keys()) and (kwargs['bcolor'] is not None):
            self.vBColor = kwargs['bcolor']
        else:
            self.vBColor = ['-', '-', '-']
        if ('extend' in kwargs.keys()) and (kwargs['extend'] is True):
            self.vFColor = self._maxColor()
            self.vBColor = self._minColor()

    # -----------------------------------------------------------------------

    def _isUsed(self, sLine):

        if ((sLine[0] == "/") or (sLine[0] == "c") or (sLine[0] == "}")):
            return False
        else:
            return True

    # -----------------------------------------------------------------------

    def _convertLine(self, sLine):

        vLine = [sLine[2:9], sLine[23:30], sLine[33:40], sLine[43:50]]
        vLine[1] = float(vLine[1])
        vLine[2] = float(vLine[2])
        vLine[3] = float(vLine[3])
        return vLine

    # -----------------------------------------------------------------------

    def _minColor(self):
        return [self.mData[1][0], self.mData[2][0], self.mData[3][0]]

    # -----------------------------------------------------------------------

    def _maxColor(self):
        return [self.mData[1][-1], self.mData[2][-1], self.mData[3][-1]]

    # -----------------------------------------------------------------------

    def saturation(self, fSaturationFactor):

        nLen = len(self.mData[0])
        for nCnt in xrange(0, nLen):
            mHSV = colorsys.rgb_to_hsv(self.mData[1][nCnt], self.mData[2][nCnt], self.mData[3][nCnt])
            mRGB = colorsys.hsv_to_rgb(mHSV[0], mHSV[1] * fSaturationFactor, mHSV[2])
            self.mData[1][nCnt] = mRGB[0]
            self.mData[2][nCnt] = mRGB[1]
            self.mData[3][nCnt] = mRGB[2]

    # -----------------------------------------------------------------------

    def flip(self):

        self.mData[0].reverse()
        self.mData[0] = [1.0 - float(item) for item in self.mData[0]]
        self.mData[1].reverse()
        self.mData[2].reverse()
        self.mData[3].reverse()

    # -----------------------------------------------------------------------

    def scale(self, fMin, fMax):

        fDiff = fMax - fMin
        nLen = len(self.mData[0])
        for nCnt in xrange(0, nLen):
            self.mData[0][nCnt] = fMin + (float(self.mData[0][nCnt]) * fDiff)

    # -----------------------------------------------------------------------

    def discretize(self, fNumSteps):

        mDiscreteData = [[], [], [], []]
        #nLen = len(self.mData[0])
        fMin = self.mData[0][0]
        fMax = self.mData[0][-1]
        fStepSize = (fMax - fMin)/(fNumSteps)
        for nCnt in xrange(0, fNumSteps):
            fDataPoint = fMin + (nCnt * fStepSize)
            vColor = self._findColor(fDataPoint)
            mDiscreteData[0].append(fDataPoint)
            mDiscreteData[1].append(vColor[0])
            mDiscreteData[2].append(vColor[1])
            mDiscreteData[3].append(vColor[2])
        mDiscreteData[0].append(fMax)
        mDiscreteData[1].append(self.mData[1][-1])
        mDiscreteData[2].append(self.mData[2][-1])
        mDiscreteData[3].append(self.mData[3][-1])
        self.mData = mDiscreteData

    # -----------------------------------------------------------------------

    def _findColor(self, fDataPoint):

        # Find segment
        nLen = len(self.mData[0])
        for nCnt in xrange(0, nLen-1):
            if (fDataPoint >= self.mData[0][nCnt]) and (fDataPoint < self.mData[0][nCnt+1]):
            # Find color
                vColor = [[], [], []]
                for nColor in xrange(0, 3):
                    fColorMin = self.mData[nColor+1][nCnt]
                    fColorDifference = self.mData[nColor+1][nCnt+1] - fColorMin
                    fDataMin = self.mData[0][nCnt]
                    fDataDifference = self.mData[0][nCnt+1] - fDataMin
                    vColor[nColor] = (((fDataPoint - fDataMin) * fColorDifference)/fDataDifference) + fColorMin
                return vColor

    # -----------------------------------------------------------------------

    def importCPT( self, filename, **kwargs ):
        """
        based on gmtColormap(), from Matplotlib Cookbook on scipy.org
        http://www.scipy.org/Cookbook/Matplotlib/Loading_a_colormap_dynamically
        """

        # Create data source
        if filename is not None:
            lines = getQPDataSource( filename ).readlines()
        else:
            raise IOError, "File not found"
        
        self.sColormapName = os.path.basename( os.path.abspath( filename ) )

        # Plain import
        self.mData = [ [], [], [], [] ]
        self.bDiscretize = False
        
        # default: RGB color model
        colorModel = "RGB"

        for l in lines:

            ls = l.split()

            if l[0] == "#":

                if ls[-1] == "HSV":
                    colorModel = "HSV"

                continue

            if ls[0] == "B":
                self.vBColor = [ ls[1], ls[2], ls[3] ]
            elif ls[0] == "F":
                self.vFColor = [ ls[1], ls[2], ls[3] ]
            elif ls[0] == "N":
                self.vNColor = [ ls[1], ls[2], ls[3] ]

            else:
                self.mData[0].append( float( ls[0] ) )
                self.mData[1].append( float( ls[1] ) )
                self.mData[2].append( float( ls[2] ) )
                self.mData[3].append( float( ls[3] ) )
                xtemp = float( ls[4] )
                rtemp = float( ls[5] )
                gtemp = float( ls[6] )
                btemp = float( ls[7] )

        self.mData[0].append( xtemp )
        self.mData[1].append( rtemp )
        self.mData[2].append( gtemp )
        self.mData[3].append( btemp )

        xMin = float( self.mData[0][0] )
        xMax = float( self.mData[0][-1] )
        
        for idx in xrange( len( self.mData[0] ) ):
        
            if colorModel == "HSV":
                    rr, gg, bb = colorsys.hsv_to_rgb( self.mData[1][idx] / 360.0,
                                                      self.mData[2][idx],
                                                      self.mData[3][idx] )
                    self.mData[1][idx] = rr
                    self.mData[2][idx] = gg
                    self.mData[3][idx] = bb
                
            if colorModel == "RGB":
                self.mData[1][idx] = self.mData[1][idx] / 255.0
                self.mData[2][idx] = self.mData[2][idx] / 255.0
                self.mData[3][idx] = self.mData[3][idx] / 255.0
            
            self.mData[0][idx] = ( self.mData[0][idx] - xMin ) / ( xMax - xMin )

        # B, F, N values
        for curr_arr in ( self.vBColor, self.vFColor, self.vNColor):

            if curr_arr[0] != '-':

                if colorModel == "HSV":

                    rr, gg, bb = colorsys.hsv_to_rgb( float(curr_arr[0]) / 360.0,
                                                      float(curr_arr[1]),
                                                      float(curr_arr[2]) )

                    curr_arr[0] = rr
                    curr_arr[1] = gg
                    curr_arr[2] = bb

                if colorModel == "RGB":

                    curr_arr[0] = float(curr_arr[0]) / 255.0
                    curr_arr[1] = float(curr_arr[1]) / 255.0
                    curr_arr[2] = float(curr_arr[2]) / 255.0

    
    def exportCPT(self, sFilename, **kwargs):

        if ('integer' in kwargs.keys()) and (kwargs['integer'] is True):
            bInteger = True
        else:
            bInteger = False

        # Scale colormap to target values
        fMin = 0
        fMax = 1
        if ('min' in kwargs.keys()) and (kwargs['min'] is not None):
            fMin = float((kwargs['min']))
        if ('max' in kwargs.keys()) and (kwargs['max'] is not None):
            fMax = float((kwargs['max']))
        self.scale(fMin, fMax)

        # Prepare data for writing
        mColormap = [[], [], [], [], [], [], [], []]
        nLen = len(self.mData[0])
        if self.bDiscretize:
            nIndexInc = 0
        else:
            nIndexInc = 1
        for nCnt in xrange(0, nLen-1):
            mColormap[0].append(self.mData[0][nCnt])
            mColormap[1].append(self.mData[1][nCnt] * 255)
            mColormap[2].append(self.mData[2][nCnt] * 255)
            mColormap[3].append(self.mData[3][nCnt] * 255)
            mColormap[4].append(self.mData[0][nCnt+1])
            mColormap[5].append(self.mData[1][nCnt+nIndexInc] * 255)
            mColormap[6].append(self.mData[2][nCnt+nIndexInc] * 255)
            mColormap[7].append(self.mData[3][nCnt+nIndexInc] * 255)

        # Open output file
        ftOutput = file(sFilename, "w")

        # Convert all numbers to integers
        nLen = len(mColormap[0])
        if bInteger:
            for nCnt in xrange(0, nLen):
                for nItem in xrange(1, 4):
                    mColormap[nItem][nCnt] = int(mColormap[nItem][nCnt])
                for nItem in xrange(5, 8):
                    mColormap[nItem][nCnt] = int(mColormap[nItem][nCnt])
        sFLine = 'F\t' + self._convertSpecialValues(self.vFColor, bInteger)
        sBLine = 'B\t' + self._convertSpecialValues(self.vBColor, bInteger)
        sNLine = 'N\t' + self._convertSpecialValues(self.vNColor, bInteger)

        # Write colormap values
        for nCnt in xrange(0, nLen):
            sLine = str(mColormap[0][nCnt]) + '\t' + str(mColormap[1][nCnt]) \
                + '\t' + str(mColormap[2][nCnt]) + '\t' + \
                str(mColormap[3][nCnt]) + '\t' + str(mColormap[4][nCnt]) + \
                '\t' + str(mColormap[5][nCnt]) + '\t' + \
                str(mColormap[6][nCnt]) + '\t' + str(mColormap[7][nCnt])
            ftOutput.write(sLine + '\n')

        # Write special values
        ftOutput.write(sFLine)
        ftOutput.write(sBLine)
        ftOutput.write(sNLine)

    # -----------------------------------------------------------------------

    def _convertSpecialValues(self, vColor, bInteger):

        if (vColor[0] == '-'):
            sLine = '-\t-\t-\n'
        else:
            if bInteger:
                sLine = str(int(vColor[0] * 255)) + '\t' + str(int(vColor[1] * 255)) + '\t' + str(int(vColor[2] * 255)) + '\n'
            else:
                sLine = str(vColor[0] * 255) + '\t' + str(vColor[1] * 255) + '\t' + str(vColor[2] * 255) + '\n'
        return sLine

    # -----------------------------------------------------------------------

    def loadPreset( self, name ):
        """
        load Povray preset
        """
        pass

    # ------------------------------------------------------------------------

    def getMatplotlib(self, **kwargs ):
        """
        return colormap for Matplotlib
        """

        if ('name' in kwargs) and (kwargs['name'] is not None):
            sName = kwargs['name']
        else:
            sName = self.sColormapName
        if ('size' in kwargs) and (kwargs['size'] is not None):
            nSize = int(kwargs['size'])
        else:
            nSize = 256

        red   = []
        blue  = []
        green = []
        for nCnt in xrange(len(self.mData[0])):
            red.append([self.mData[0][nCnt], self.mData[1][nCnt], self.mData[1][nCnt]])
            green.append([self.mData[0][nCnt], self.mData[2][nCnt], self.mData[2][nCnt]])
            blue.append([self.mData[0][nCnt], self.mData[3][nCnt], self.mData[3][nCnt]])
        
        colorDict = {"red": red, "green": green, "blue": blue}
        colorMap = matplotlib.colors.LinearSegmentedColormap(sName, colorDict, nSize)
        
        if (self.vFColor[0] != '-'):
            colorMap.set_over((self.vFColor[0], self.vFColor[1], self.vFColor[2]))
        if (self.vBColor[0] != '-'):
            colorMap.set_under((self.vBColor[0], self.vBColor[1], self.vBColor[2]))
        if (self.vNColor[0] != '-'):
            colorMap.set_bad((self.vNColor[0], self.vNColor[1], self.vNColor[2]))
        return colorMap

    # ------------------------------------------------------------------------
