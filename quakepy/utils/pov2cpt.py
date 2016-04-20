#!/usr/bin/env python

"""
This file is part of QuakePy12.

"""

import sys
import getopt
from math import floor
import re
import colorsys


def main():
  # Set defaults
  fMin = 0
  fMax = 1
  bBackgroundColor = False
  vBackgroundColor = [0, 0, 0]
  bDiscrete = False
  bExtent = False
  bFlip = False
  bForegroundColor = False
  vForegroundColor = [0, 0, 0]
  bInteger = False
  bLogScale = False
  bValuesAlreadyLog = False
  bPale = False
  bOutput2Standard = True
  vNaNColor = [0, 0, 0]
  bNaNColor = False
  sCptFilename = ''
  # Read commandline arguments
  sCmdParams = sys.argv[1:]
  opts, args = getopt.gnu_getopt(sCmdParams, 'a:b:B:d:efF:hilLn:o:p:', ['min=', 'max=', 'background=', 'discrete=', 'extend', 'flip', 'foreground=', 'help', 'integer', 'log', 'Log', 'nan=', 'output=', 'pale='])
  for option, parameter in opts:
    if option == '-a' or option == '--min':
      fMin = float(parameter)
    if option == '-b' or option == '--max':
      fMax = float(parameter)
    if option == '-B' or option == '--background':
      bBackgroundColor = True
      vRGB = re.split(r'/', parameter)
      if vRGB:
        vBackgroundColor[0] = float(vRGB[0])
        vBackgroundColor[1] = float(vRGB[1])
        vBackgroundColor[2] = float(vRGB[2])
    if option == '-d' or option == '--discrete':
      bDiscrete = True
      fNumSteps = int(parameter)
    if option == '-e' or option == '--extend':
      bExtent = True
    if option == '-f' or option == '--flip':
      bFlip = True
    if option == '-F' or option == '--foreground':
      bForegroundColor = True
      vRGB = re.split(r'/', parameter)
      if vRGB:
        vForegroundColor[0] = float(vRGB[0])
        vForegroundColor[1] = float(vRGB[1])
        vForegroundColor[2] = float(vRGB[2])
    if option == '-i' or option == '--integer':
      bInteger = True
    if option == '-l' or option == '--log':
      bLogScale = True
      bValuesAlreadyLog = True
    if option == '-L' or option == '--Log':
      bLogScale = True
      bValuesAlreadyLog = False
    if option == '-n' or option == '--nan':
      bNaNColor = True
      vRGB = re.split(r'/', parameter)
      if vRGB:
        vNaNColor[0] = float(vRGB[0])
        vNaNColor[1] = float(vRGB[1])
        vNaNColor[2] = float(vRGB[2])
    if option == '-o' or option == '--output':
      bOutput2Standard = False
      sCptFilename = parameter
    if option == '-p' or option == '--pale':
      if (float(parameter) > 1) or (float(parameter) < 0):
        print 'ERROR: Value for pale colorbar must be in the range [0,1]'
        sys.exit()
      bPale = True
      fPaleFactor = float(parameter)
    if option == '-h' or option == '--help':
      print 'Convert PovRay-colorbars (exported from GIMP) to cpt-files for GMT'
      print 'Version 1.5 [17.10.2009]'
      print 'Usage: pov2cpt.py [OPTION] povray-file'
      print '   -a, --min=<value>          minimum value on colorbar (default = 0)'
      print '   -b, --max=<value>          maximum value on colorbar (default = 1)'
      print '   -B, --background=<r/g/b>   defines the B-entry at the end of the cpt-file'
      print '   -d, --discrete=<value>     discrete colors with <value> steps (default continuous)'
      print '   -e, --extent               extent colorbar (F/B values)'
      print '   -f, --flip                 flip colorbar'
      print '   -F, --foreground=<r/g/b>   defines the F-entry at the end of the cpt-file (overrides -e)'
      print '   -h, --help                 print this information'
      print '   -i, --integer              output color values as integer'
      print '   -l, --log                  create a log10 scale from min- to max-value'
      print '   -L, --Log                  create a log10 scale from log10(min) to log10(max)'
      print '   -n, --nan=<r/g/b>          defines the N-entry at the end of the cpt-file (overrides -e)'
      print '   -o, --output=<filename>    output to file instead of stdout'
      print '   -p, --pale=<value>         create pale colorbar (multiply saturation by value)'
      sys.exit()
  sPovRayFilename = args[0]
  mColormap = ReadPovRay(sPovRayFilename)
  if bPale:
    mColormap = CreatePale(mColormap, fPaleFactor)
  if bFlip:
    mColormap = Flip(mColormap)
  if (bLogScale) and (bValuesAlreadyLog == False):
    fMin = log10(fMin)
    fMax = log10(fMax)
  mCpt = Scale(mColormap, fMin, fMax)
  if bDiscrete:
    mCpt = Discretize(mCpt, fMin, fMax, fNumSteps)
  if bLogScale:
    mCpt = RestoreZValues(mCpt)
  mCpt = PrepareForWriting(mCpt, bDiscrete)
  WriteCpt(bOutput2Standard, sCptFilename, mCpt, bExtent, bForegroundColor, vForegroundColor, bBackgroundColor, vBackgroundColor, bNaNColor, vNaNColor, bInteger)

# ---

def RestoreZValues(mColormap):

  nLen = len(mColormap[0])
  for nCnt in range(0, nLen):
    mColormap[0][nCnt] = 10**(mColormap[0][nCnt])
  return mColormap

# ---

def CreatePale(mCpt, fPaleFactor):

  mColormap = [[], [], [], [], [], [], [], []]
  nLen = len(mCpt[0])
  for nCnt in range(0, nLen):
    mColormap[0].append(mCpt[0][nCnt])
    mHSV = colorsys.rgb_to_hsv(mCpt[1][nCnt], mCpt[2][nCnt], mCpt[3][nCnt])
    mPaleHSV = [mHSV[0], mHSV[1] * fPaleFactor, mHSV[2]]
    mRGB = colorsys.hsv_to_rgb(mPaleHSV[0], mPaleHSV[1], mPaleHSV[2])
    mColormap[1].append(mRGB[0])
    mColormap[2].append(mRGB[1])
    mColormap[3].append(mRGB[2])
  return mColormap

# ---

def Discretize(mCpt, fMin, fMax, fNumSteps):

  mData = [[], [], [], []]
  fStepSize = (fMax - fMin)/(fNumSteps)
  for nCnt in range(0, fNumSteps):
    fDataPoint = fMin + (nCnt * fStepSize)
    vColor = FindColor(mCpt, fDataPoint)
    mData[0].append(fDataPoint)
    mData[1].append(vColor[0])
    mData[2].append(vColor[1])
    mData[3].append(vColor[2])
  nLast = len(mCpt[0]) - 1
  mData[0].append(fMax)
  mData[1].append(mCpt[1][nLast])
  mData[2].append(mCpt[2][nLast])
  mData[3].append(mCpt[3][nLast])
  return mData

# ---

def FindColor(mCpt, fDataPoint):

  # Find segment
  nLen = len(mCpt[0])
  for nCnt in range(0, nLen-1):
    if (fDataPoint >= mCpt[0][nCnt]) and (fDataPoint < mCpt[0][nCnt+1]):
      # Find color
      vColor = [[], [], []]
      for nColor in range(0, 3):
        fColorMin = mCpt[nColor+1][nCnt]
        fColorDifference = mCpt[nColor+1][nCnt+1] - fColorMin
        fDataMin = mCpt[0][nCnt]
        fDataDifference = mCpt[0][nCnt+1] - fDataMin
        vColor[nColor] = (((fDataPoint - fDataMin) * fColorDifference)/fDataDifference) + fColorMin
      return vColor

# ---

def Scale(mColormap, fMin, fMax):

  fDiff = fMax - fMin
  nLen = len(mColormap[0])
  for nCnt in range(0, nLen):
    mColormap[0][nCnt] = fMin + (float(mColormap[0][nCnt]) * fDiff)
  return mColormap

# ---

def PrepareForWriting(mCpt, bDiscrete):

  mColormap = [[], [], [], [], [], [], [], []]
  nLen = len(mCpt[0])
  if bDiscrete:
    nIndexInc = 0
  else:
    nIndexInc = 1
  for nCnt in range(0, nLen-1):
    mColormap[0].append(mCpt[0][nCnt])
    mColormap[1].append(mCpt[1][nCnt])
    mColormap[2].append(mCpt[2][nCnt])
    mColormap[3].append(mCpt[3][nCnt])
    mColormap[4].append(mCpt[0][nCnt+1])
    mColormap[5].append(mCpt[1][nCnt+nIndexInc])
    mColormap[6].append(mCpt[2][nCnt+nIndexInc])
    mColormap[7].append(mCpt[3][nCnt+nIndexInc])
  return mColormap

# ---

def Flip(mColormap):

  mColormap[0].reverse()
  mColormap[0] = [1.0 - float(item) for item in mColormap[0]]
  mColormap[1].reverse()
  mColormap[2].reverse()
  mColormap[3].reverse()
  return mColormap

# ---

def IsUsed(sLine):

  if ((sLine[0] == "/") or (sLine[0] == "c") or (sLine[0] == "}")):
    return False
  else:
    return True

# ---

def ConvertLine(sLine):

  vLine = [sLine[2:9], sLine[23:30], sLine[33:40], sLine[43:50]]
  vLine[1] = float(vLine[1]) * 255;
  vLine[2] = float(vLine[2]) * 255;
  vLine[3] = float(vLine[3]) * 255;
  return vLine

# ---

def ReadPovRay(sFilename):

  mData = [[], [], [], []]
  sPreviousLine = ''
  ftInput = file(sFilename, "r")
  for sLine in ftInput.readlines():
    if IsUsed(sLine):
      if (sLine != sPreviousLine):
        vDataLine = ConvertLine(sLine)
        mData[0].append(vDataLine[0])
        mData[1].append(vDataLine[1])
        mData[2].append(vDataLine[2])
        mData[3].append(vDataLine[3])
        sPreviousLine = sLine
  return mData

# ---

def WriteCpt(bOutput2Standard, sFilename, mCpt, bExtent, bForegroundColor, vForegroundColor, bBackgroundColor, vBackgroundColor, bNaNColor, vNaNColor, bInteger):

  if bOutput2Standard:
    ftOutput = sys.stdout
  else:
    ftOutput = file(sFilename, "w")
  nLen = len(mCpt[0])
  if bInteger:
    for nCnt in range(0, nLen):
      for nItem in range(1, 4):
        mCpt[nItem][nCnt] = int(mCpt[nItem][nCnt])
      for nItem in range(5, 8):
        mCpt[nItem][nCnt] = int(mCpt[nItem][nCnt])
  sColorBottom = str(mCpt[1][0]) + '\t' + str(mCpt[2][0]) + '\t' + str(mCpt[3][0])
  sColorTop    = str(mCpt[5][nLen-1]) + '\t' + str(mCpt[6][nLen-1]) + '\t' + str(mCpt[7][nLen-1])
  for nCnt in range(0, nLen):
    sLine = str(mCpt[0][nCnt]) + '\t' + str(mCpt[1][nCnt]) + '\t' + str(mCpt[2][nCnt]) + '\t' + str(mCpt[3][nCnt]) + '\t' + str(mCpt[4][nCnt]) + '\t' + str(mCpt[5][nCnt]) + '\t' + str(mCpt[6][nCnt]) + '\t' + str(mCpt[7][nCnt])
    ftOutput.write(sLine + '\n')
  if bExtent:
    sForeground = 'F\t' + sColorTop + '\n'
    sBackground = 'B\t' + sColorBottom + '\n'
  else:
    sForeground = 'F\t-\t-\t-\n'
    sBackground = 'B\t-\t-\t-\n'
  if bForegroundColor:
    if bInteger:
      sForeground ='F\t' + str(int(vForegroundColor[0])) + '\t' + str(int(vForegroundColor[1])) + '\t' + str(int(vForegroundColor[2])) + '\n'
    else:
      sForeground ='F\t' + str(vForegroundColor[0]) + '\t' + str(vForegroundColor[1]) + '\t' + str(vForegroundColor[2]) + '\n'
  if bBackgroundColor:
    if bInteger:
      sBackground ='B\t' + str(int(vBackgroundColor[0])) + '\t' + str(int(vBackgroundColor[1])) + '\t' + str(int(vBackgroundColor[2])) + '\n'
    else:
      sBackground ='B\t' + str(vBackgroundColor[0]) + '\t' + str(vBackgroundColor[1]) + '\t' + str(vBackgroundColor[2]) + '\n'
  if bNaNColor:
    if bInteger:
      sNaN = 'N\t' + str(int(vNaNColor[0])) + '\t' + str(int(vNaNColor[1])) + '\t' + str(int(vNaNColor[2])) + '\n'
    else:
      sNaN = 'N\t' + str(vNaNColor[0]) + '\t' + str(vNaNColor[1]) + '\t' + str(vNaNColor[2]) + '\n'
  else:
    sNaN = 'N\t-\t-\t-\n'
  ftOutput.write(sForeground)
  ftOutput.write(sBackground)
  ftOutput.write(sNaN)

main()


# GIMP PovRay-export example

#/* color_map file created by the GIMP */
#/* http://www.gimp.org/               */
#color_map {
#	[0.000000 color rgbt <0.128028, 0.725490, 0.128028, 0.000000>]
#	[0.168005 color rgbt <0.564014, 0.862745, 0.564014, 0.000000>]
#	[0.333333 color rgbt <1.000000, 1.000000, 1.000000, 0.000000>]
#	[0.333333 color rgbt <1.000000, 1.000000, 1.000000, 0.000000>]
#	[0.500678 color rgbt <0.996078, 0.904645, 0.538908, 0.000000>]
#	[0.668022 color rgbt <0.992157, 0.809289, 0.077816, 0.000000>]
#	[0.668022 color rgbt <0.992157, 0.809289, 0.077816, 0.000000>]
#	[0.834011 color rgbt <0.970588, 0.449304, 0.174595, 0.000000>]
#	[1.000000 color rgbt <0.949020, 0.089319, 0.271374, 0.000000>]
#} /* color_map */
