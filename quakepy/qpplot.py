# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import datetime
import numpy
import sys

import matplotlib
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams

BACKENDS = { 'PS': { 'extension': 'eps' },
             'AGG': { 'extension': 'png' },
             'PDF': { 'extension': 'pdf' },
             'SVG': { 'extension': 'svg' }
           }

LINE_STYLES = ('k-', 'r-', 'b-', 'g-', 'k--', 'r--', 'b--', 'g--', 'k-.', 
    'r-.', 'b-.', 'g-.')
    
PLOT_COLOR_CODES = ('k', 'r', 'g', 'b')

class QPPlot( object ):
    """Base class for 2-d plots."""

    autoscale = False
    showgrid = True

    _plotLegendFont = {'size'  : 'small',
                       'style' : 'normal',
                       'family': ('serif', 'sans-serif', 'monospace')}
                       
    def __init__( self, backend='PS', xsize=6, ysize=6 ):
        rcParams['figure.figsize'] = (xsize, ysize)

        self.line_style_generator = line_style_generator()
        
        self.backend = backend
        matplotlib.use( backend )
        __import__( 'matplotlib.pyplot' )
        self.pyplot = sys.modules['matplotlib.pyplot']

        self.figure = self.pyplot.figure()
    
    def close(self):
        """Close figure to free memory."""
        self.pyplot.close(self.figure)
        
    def return_image( self, imgfile=None ):
        """Return image, either as figure object, or as image file."""

        # TODO(fab): can use file-like object here
        if imgfile is None:
            return self.figure
        elif self.backend in BACKENDS:
            print "plot for backend %s" % self.backend
            try:
                self.pyplot.savefig( "%s.%s" % ( 
                    imgfile, BACKENDS[self.backend]['extension'] ) )
                self.close()
                return True
            except IOError, e:
                print "could not write image to file: ", e
                return None
        else:
            return False
        
    def plot( self, imgfile, abscissa_in, ordinate_in, xlabel='', ylabel='', 
        **kwargs ):

        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )
    
        self.pyplot.clf()
        
        line_style = 'k-' # black solid line
        
        ax = self.figure.add_subplot(111)
        
        # basic plot: non-logarithmic
        self.pyplot.plot( abscissa_in, ordinate_in, line_style )
        self.pyplot.xlabel( xlabel )
        self.pyplot.ylabel( ylabel )
        
        return self.return_image( imgfile )
            
    def plot_vs_date( self, imgfile, abscissa_in, ordinate_in, **kwargs ):

        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )

        self.pyplot.clf()
        line_style = 'r-' # N-test - black solid line
    
        # get values for abscissa, only date part (first 10 chars)
        abscissa = []
        for absc in abscissa_in:
            absc_parts = absc[0:10].split('-')
            abscissa_date = datetime.date( 
                int(absc_parts[0]), int(absc_parts[1]), int(absc_parts[2]) )

            # TODO(fab): we need float days from 0001-01-01
            # mdates.mx2num( abscissa_date )
            abscissa.append( mdates.date2num( abscissa_date ) )
            
        # abscissa (date axis) formatting / define tick locators and formatters
        # NOTE: we expect the dates in <testDate> to be in ascending order
            
        # get difference in years
        startyear = int( mdates.num2date(abscissa[0]).strftime('%Y') )
        endyear   = int( 
            mdates.num2date(abscissa[len(abscissa)-1]).strftime('%Y') )
        yeardiff  = endyear - startyear
        
        if ( yeardiff >= 15 ):
            abscissaFmt  = mdates.DateFormatter( '%Y' )
            abscMajorLoc = mdates.YearLocator( 10, month=1, day=1 )
            abscMinorLoc = mdates.YearLocator( 2, month=1, day=1 )
        elif ( yeardiff >= 8 ):
            abscissaFmt  = mdates.DateFormatter( '%Y' )
            abscMajorLoc = mdates.YearLocator( 5, month=1, day=1 )
            abscMinorLoc = mdates.YearLocator( 1, month=1, day=1 )
        elif ( yeardiff >= 3 ):
            abscissaFmt  = mdates.DateFormatter( '%Y' )
            abscMajorLoc = mdates.YearLocator()
            abscMinorLoc = mdates.MonthLocator( (1, 4, 7, 10) )
        elif ( yeardiff >= 1 ):
            abscissaFmt  = mdates.DateFormatter( '%b %Y' )
            abscMajorLoc = mdates.MonthLocator( (1, 4, 7, 10) )
            abscMinorLoc = mdates.MonthLocator()
        else:
            # get month difference
            startmonth = int( mdates.num2date(abscissa[0]).strftime('%m') )
            endmonth   = int( 
                mdates.num2date(abscissa[len(abscissa)-1]).strftime('%m') )
            monthdiff  = endmonth - startmonth
            
            if ( monthdiff >= 6 ):
                abscissaFmt  = mdates.DateFormatter( '%b %Y' )
                abscMajorLoc = mdates.MonthLocator( (1, 3, 5, 7, 9, 11) )
                abscMinorLoc = mdates.MonthLocator()
            elif ( monthdiff >= 2 ):
                abscissaFmt  = mdates.DateFormatter( '%b %Y' )
                abscMajorLoc = mdates.MonthLocator()
                abscMinorLoc = mdates.WeekdayLocator( mdates.MO )
            elif ( monthdiff >= 1 ):
                abscissaFmt  = mdates.DateFormatter( '%b %d' )
                abscMajorLoc = mdates.WeekdayLocator( mdates.MO )
                abscMinorLoc = mdates.DayLocator()
            else:
                # all dates in the same month
                # get difference of days
                startday = int( mdates.num2date(abscissa[0]).strftime('%d') )
                endday   = int( 
                    mdates.num2date(abscissa[len(abscissa)-1]).strftime('%d') )
                daydiff  = endday - startday
                
                if ( daydiff > 10 ):
                    abscissaFmt  = mdates.DateFormatter( '%b %d' )
                    abscMajorLoc = mdates.WeekdayLocator( mdates.MO )
                    abscMinorLoc = mdates.DayLocator()
                else:
                    # range is smaller than 10 days, major tick every day
                    abscissaFmt  = mdates.DateFormatter( '%b %d' )
                    abscMajorLoc = mdates.DayLocator()
                    abscMinorLoc = mdates.NullLocator()
                            
        # get ordinate
        ordinate = map( float, ordinate_in )
            
        # check for equal array dimension
        if ( len(abscissa_in) != len(ordinate) ):
            raise IndexError, "error: data vector length mismatch"
            
        # use AUTO for ordinate formatting
        # ordinateFmt = FormatStrFormatter( '%0.3f' )
        # ax.yaxis.set_major_formatter( ordinateFmt )
                
        # determine y axis range
        ymin = 0.9 * min( ordinate )
        ymax = 1.1 * max( ordinate )
        
        #ax = subplot(111)
        ax = self.figure.add_subplot(111)
        
        self.pyplot.plot_date( abscissa, ordinate, line_style )
        self.pyplot.ylabel( 'Number of events' )
        # self.pyplot.ylabel( 'mean completeness' )
            
        # check if abscissa has only one data point: set x axis range explicitly
        # (plus / minus one day)
        if ( len( abscissa ) == 1 ):
            self.pyplot.xlim( abscissa[0]-1, abscissa[0]+1 )
            
        # set y axis range - adjust to the '0.1'-bin
        ymin = 0.1 * numpy.floor( 10.0 * ymin )
        ymax = 0.1 * numpy.ceil( 10.0 * ymax )
        
        # avoid that ymin equals ymax
        # currently this is only possible if the whole dataset is zero
        # in this case, set range to -0.1 ... 0.1
        if ( ymin == ymax ):
            ymin -= 0.1
            ymax += 0.1
            
        self.pyplot.ylim( ymin, ymax )
            
        # formatting of abscissa (date) axis
        ax.xaxis.set_major_formatter( abscissaFmt )
        ax.xaxis.set_major_locator( abscMajorLoc )
        ax.xaxis.set_minor_locator( abscMinorLoc )
            
        if ( self.autoscale == True ):
            ax.autoscale_view()
            
        labels = ax.get_xticklabels()
        self.pyplot.setp( labels, 'rotation', 30, fontsize=14 )
        #grid( self.showgrid )
        
        return self.return_image( imgfile )
    

class FMDPlot( QPPlot ):
    """This class plots a non-cumulative FMD."""

    def plot( self, imgfile, fmd, **kwargs ):

        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )
    
        self.pyplot.clf()
        
        line_style = 'ks' # black squares without line segments
        
        ax = self.figure.add_subplot(111)

        # non-cumulative
        self.pyplot.semilogy( fmd[0, :], fmd[1, :], line_style )

        self.pyplot.xlabel( 'Magnitude' )
        self.pyplot.ylabel( 'Number of Events' )

        return self.return_image( imgfile )


class FMDPlotCumulative( QPPlot ):
    """This class plots a cumulative frequency-magnitude 
    distribution with optional G-R fit."""

    def plot( self, imgfile, fmd, fit=None, normalized=False, **kwargs ):

        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )
    
        self.pyplot.clf()
        
        line_style_cumul = 'ks' # black squares without line segments
        
        ax = self.figure.add_subplot(111)

        # cumulative
        self.pyplot.semilogy( fmd[0, :], fmd[2, :], line_style_cumul )

        # G-R fit
        if fit is not None:
            line_style_fit = self.line_style_generator.next()
            self.pyplot.semilogy( fit[0, :], fit[1, :], line_style_fit )

        self.pyplot.xlabel( 'Magnitude' )
        
        if normalized is False:
            self.pyplot.ylabel( 'Number of Events' )
        else:
            self.pyplot.ylabel( 'Number of Events/year' )

        return self.return_image( imgfile )


class FMDPlotCombined( QPPlot ):
    """This class plots a non-cumulative and cumulative frequency-magnitude 
    distribution with optional G-R fit."""

    def plot( self, imgfile, fmd, fit=None, normalized=False, **kwargs ):

        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )
    
        self.pyplot.clf()
        
        line_style = 'bo'       # blue circles without line segments
        line_style_cumul = 'ks' # black squares without line segments
        
        ax = self.figure.add_subplot(111)

        # cumulative
        self.pyplot.semilogy( fmd[0, :], fmd[2, :], line_style_cumul )
    
        # non-cumulative
        self.pyplot.semilogy( fmd[0, :], fmd[1, :], line_style )

        # G-R fit
        if fit is not None:
            line_style_fit = self.line_style_generator.next()
            self.pyplot.semilogy( fit[0, :], fit[1, :], line_style_fit )

        self.pyplot.xlabel( 'Magnitude' )
        
        if normalized is False:
            self.pyplot.ylabel( 'Number of Events' )
        else:
            self.pyplot.ylabel( 'Number of Events/year' )

        return self.return_image( imgfile )

class FMDPlotCombinedMulti( QPPlot ):
    """This class plots a non-cumulative and cumulative frequency-magnitude 
    distribution with multiple optional G-R fits."""

    _plotLegend = {'style'        : 0,
                   'borderpad'    : 1.0,
                   'borderaxespad': 1.0,
                   'markerscale'  : 5.0,
                   'handletextpad': 0.5,
                   'handlelength' : 2.0,
                   'labelspacing' : 0.5}
                   
    def plot( self, imgfile, fmd, fits=None, normalized=False, **kwargs ):

        """
        Input:
            fmd         QuakePy FMD object
            fits        list of dicts for each G-R fit
                        {'data': numpy array with abscissa and ordinate,
                         'label': "label text",
                         'activity': (a, b)}
        """
        
        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )
    
        self.pyplot.clf()
        
        line_style = 'bo'       # blue circles without line segments
        line_style_cumul = 'ks' # black squares without line segments
        
        ax = self.figure.add_subplot(111)

        # cumulative
        self.pyplot.semilogy( fmd[0, :], fmd[2, :], marker='D',
            markeredgecolor='black', markeredgewidth=2,
            markerfacecolor='white', linestyle='' )
    
        # non-cumulative
        self.pyplot.semilogy( fmd[0, :], fmd[1, :], marker='^',
            markeredgecolor='blue', markeredgewidth=2,
            markerfacecolor='white', linestyle='' )

        # G-R fit
        if fits is not None:
            for fit in fits:
                line_style_fit = self.line_style_generator.next()
                self.pyplot.semilogy( fit['data'][0, :], fit['data'][1, :], 
                    line_style_fit, label=fit['label'] )

        self.pyplot.legend(loc=self._plotLegend['style'],
            markerscale=self._plotLegend['markerscale'],
            borderpad=self._plotLegend['borderpad'],
            borderaxespad=self._plotLegend['borderaxespad'],
            handletextpad=self._plotLegend['handletextpad'],
            handlelength=self._plotLegend['handlelength'],
            labelspacing=self._plotLegend['labelspacing'],
            prop=FontProperties(
            size=self._plotLegendFont['size'],
            style=self._plotLegendFont['style'],
            family=self._plotLegendFont['family'][1]))
                        
        self.pyplot.xlabel( 'Magnitude' )
        
        if normalized is False:
            self.pyplot.ylabel( 'Number of Events' )
        else:
            self.pyplot.ylabel( 'Number of Events/year' )

        return self.return_image( imgfile )
        
class FMDPlotRecurrence( QPPlot ):
    """This class plots a cumulative FMD that is truncated at Mmax."""

    _plotLegend = {'style'        : 0,
                   'borderpad'    : 1.0,
                   'borderaxespad': 1.0,
                   'markerscale'  : 5.0,
                   'handletextpad': 0.5,
                   'handlelength' : 2.0,
                   'labelspacing' : 0.5}
                
    def plot( self, imgfile, occurrence, fmd=None, fits=None, normalized=True,
        **kwargs ):
        """Plot cumulative occurrence rate vs. magnitude.

        Input:
            occurrence        3xN numpy array with magnitudes in row 0, 
                              min occurrence rates in row 1,
                              max occurrence rates in row 2
                              
            fmd               cumulative FMD
                              2xN numpy array with magnitudes in row 0,
                              cumulative eq number in row 1
        """
        if 'backend' in kwargs and kwargs['backend'] != self.backend:
            self.__init__( backend=kwargs['backend'] )
    
        self.pyplot.clf()
        
        line_style_min = 'g--' # green dashed line
        line_style_max = 'b--' # blue dashed line
        line_style_fit_ml = 'r-' # red solid line
        
        ax = self.figure.add_subplot(111)

        self.pyplot.semilogy( occurrence[0, :], occurrence[1, :], 
            line_style_min, label="min slip rate" )
        self.pyplot.semilogy( occurrence[0, :], occurrence[2, :], 
            line_style_max, label="max slip rate" )

        if fmd is not None:
            self.pyplot.semilogy( fmd[0, :], fmd[2, :], marker='D',
                markeredgecolor='black', markeredgewidth=2,
                markerfacecolor='white', linestyle='' )
                
        if fits is not None:
            for fit in fits:
                self.pyplot.semilogy( fit['data'][0, :], fit['data'][1, :], 
                    line_style_fit_ml, label=fit['label'] )
            

        self.pyplot.legend(loc=self._plotLegend['style'],
            markerscale=self._plotLegend['markerscale'],
            borderpad=self._plotLegend['borderpad'],
            borderaxespad=self._plotLegend['borderaxespad'],
            handletextpad=self._plotLegend['handletextpad'],
            handlelength=self._plotLegend['handlelength'],
            labelspacing=self._plotLegend['labelspacing'],
            prop=FontProperties(
            size=self._plotLegendFont['size'],
            style=self._plotLegendFont['style'],
            family=self._plotLegendFont['family'][1]))
        
        self.pyplot.xlabel( 'Magnitude' )
        
        if normalized is False:
            self.pyplot.ylabel( 'Number of Events' )
        else:
            self.pyplot.ylabel( 'Number of Events/year' )
            
        return self.return_image( imgfile )
        
        
def line_style_generator():
    """Generator that walks through a sequence of color codes and line styles
    for matplotlib. When reaching the end of the list, start at the 
    beginning again.
    """
    while (True): 
        for style in LINE_STYLES: 
            yield style
            
def color_code_generator():
    """Generator that walks through a sequence of color codes for matplotlib.
    When reaching the end of the color code list, start at the beginning again.
    """
    while (True):
        for code in PLOT_COLOR_CODES:
            yield code
