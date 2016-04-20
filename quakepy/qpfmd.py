# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import numpy

from mx.DateTime import DateTime

import qpplot

DEFAULT_BINSIZE = 0.1
DEFAULT_MC_METHOD = 'maxCurvature'

MC_METHODS = ( 'userDefined', 'maxCurvature', 'minMagnitude' )
MIN_EVENTS_GR = 100

class FrequencyMagnitudeDistribution( object ):
    """This class describes the FMD of an EQ catalog.
    """
    def __init__( self, evpar, binsize=DEFAULT_BINSIZE, Mc=DEFAULT_MC_METHOD,
        Mstart=None, Mend=None, minEventsGR=MIN_EVENTS_GR, time_span=None, 
        **kwargs ):
        """Computes FMD."""
        
        self.binsize = binsize
        self.Mstart = Mstart
        self.Mend = Mend

        self._setMc( Mc )
        self.minEventsGR = minEventsGR

        if time_span is not None:
            self.timeSpan = time_span

        # get list of magnitudes from events
        magnitudes = []
        time_start = None
        time_end = None

        for ev_ctr, curr_ev in enumerate( evpar.event ):
            magnitudes.append( curr_ev.getPreferredMagnitude().mag.value )
            
            if time_span is None:
                curr_time = curr_ev.getPreferredOrigin().time.value.datetime

                if ev_ctr == 0:
                    time_start = curr_time
                    time_end = curr_time
                elif curr_time < time_start:
                    time_start = curr_time
                elif curr_time > time_end:
                    time_end = curr_time

        if time_span is None:
            # compute time span of events in years
            cat_time_span = time_end - time_start
            self.timeSpan = cat_time_span.days / 365.25
        
        self.update( magnitudes, binsize )

    def update( self, magnitudes, binsize=DEFAULT_BINSIZE ):
        """Update FMD computation."""

        # sort list of magnitudes, ascending order
        self.magnitudes_sorted = numpy.array( sorted( magnitudes ) )
        
        # create array of magnitude bins
        # Mmin/Mmax:
        # (1) provided by user
        # (2) automatically from range of magnitudes:
        #     Mmin is smallest mag minus binsize
        #     Mmax is largest mag plus one binsize, plus additional margin 
        #     if required
        if self.Mstart is not None:
            mag_start = self.Mstart
        else:
            mag_start = self.magnitudes_sorted[0] - self.binsize

        if self.Mend is not None:
            mag_end = self.Mend
        else:
            mag_end = self.magnitudes_sorted[-1] + self.binsize

        mag_bin_count = int( numpy.ceil( ( mag_end - mag_start ) / binsize ) )
        hist_n, hist_bins = numpy.histogram( self.magnitudes_sorted, 
            mag_bin_count, (mag_start, mag_end) )

        # combine fmd output
        # row 0: M bin values, 
        # row 1: histogram numbers,
        # row 2: cumulated histogram numbers
        self.fmd = numpy.vstack( ( hist_bins[:-1], hist_n, 
            hist_n[::-1].cumsum()[::-1] ) )

        self.computeGR()

    def computeGR( self ):
        """Compute Gutenberg-Richter statistics."""

        # set completeness magnitude
        if self.McMethod == 'minMagnitude':
            self.Mc = self.magnitudes_sorted[0]
        
        elif self.McMethod == 'maxCurvature':

            # get largest value from non-cumulative FMD
            # left edge of bin
            max_frequency_idx = numpy.argmax( self.fmd[1, :] )
            self.Mc = self.fmd[0, max_frequency_idx]
        
        # select only events with magnitudes above completeness
        sel = ( self.magnitudes_sorted[:] >= self.Mc )
        self.magAboveCompleteness = self.magnitudes_sorted[sel.T]
        
        # abscissae for G-R fit, magnitudes above completeness
        sel = ( self.fmd[0, :] >= self.Mc )
        magnitudes_fit = self.fmd[0, sel.T]
        
        self.GR = {}
        self.GR['mag_fit'] = magnitudes_fit
        self.GR['magCtr'] = len( self.magAboveCompleteness )
        self.GR['timeSpan'] = self.timeSpan
        self.GR['binsize'] = self.binsize
        self.GR['Mmin'] = self.magAboveCompleteness[0]
        self.GR['Mmean'] = self.magAboveCompleteness.mean()
    
        if len( self.magAboveCompleteness ) >= self.minEventsGR:
            gr = computeGutenbergRichter( self.magAboveCompleteness, 
                magnitudes_fit, self.binsize, self.timeSpan, self.GR )

        else:
            gr = {'bValue': numpy.nan, 'aValue': numpy.nan, 
                  'aValueNormalized': numpy.nan, 'StdDev': numpy.nan, 
                  'fit': None, 'fitNormalized': None}

        self.GR.update(gr)

    def plot( self, imgfile=None, normalize=False, **kwargs ):
        """Create FMD plot."""
        if 'fmdtype' in kwargs and kwargs['fmdtype'] == 'cumulative':
            ordinate = self.fmd[2, :]
        else:
            ordinate = self.fmd[1, :]

        if normalize is True:
            ordinate = ordinate / self.timeSpan
            ordinate_fit = self.GR['fitNormalized']
        else:
            ordinate_fit = self.GR['fit']

        if ordinate_fit is not None and \
            len(self.GR['mag_fit']) == len(ordinate_fit):
            fit = numpy.vstack( ( self.GR['mag_fit'], ordinate_fit ) )
        else:
            fit = None

        return qpplot.FMDPlotCombined().plot( imgfile, self.fmd, fit, 
            **kwargs )
            
    def _setMc( self, Mc ):
        """Set completeness magnitude method."""
        try:
            self.Mc = float( Mc )
            self.McMethod = 'userDefined'
        except ValueError:
            self.Mc = None
            self.McMethod = Mc
            
        if self.McMethod not in MC_METHODS:
            error_msg = "illegal Mc method: %s" % self.McMethod
            raise ValueError, error_msg


def computeGutenbergRichter( magnitudes, magnitudes_fit, binsize, 
    timeSpan=None, gr=None ):
    """This function computes Gutenberg-Richter a, b parameters, and the
    standard deviation of b.
    Adapted from the ZMAP function calc_bmemag:

    % Calculate the minimum and mean magnitude, length of catalog
    nLen = length(vMag);
    fMinMag = min(vMag);
    fMeanMag = mean(vMag);
    
    % Calculate the b-value (maximum likelihood)
    fBValue = (1/(fMeanMag-(fMinMag-(fBinning/2))))*log10(exp(1));
    
    % Calculate the standard deviation 
    fStdDev = (sum((vMag-fMeanMag).^2))/(nLen*(nLen-1));
    fStdDev = 2.30 * sqrt(fStdDev) * fBValue^2;
    
    % Calculate the a-value
    fAValue = log10(nLen) + fBValue * fMinMag;

    Input: 
        magnitudes      numpy array of sorted magnitudes (already cut at completeness
                        magnitude value)
        magnitudes_fit  magnitude array on which the fit is computed            
        binsize         size of magnitude bins
        timeSpan        time span of events in years (for normalizing a value to 
                        annual rate)

    Returns dict gr.
    """

    if gr is None:
        gr = {}
        gr['mag_fit'] = magnitudes_fit
        gr['magCtr'] = len( magnitudes )
        gr['timeSpan'] = timeSpan
        gr['binsize'] = binsize
        gr['Mmin'] = magnitudes[0]
        gr['Mmean'] = magnitudes.mean()
    
    gr['bValue'] = numpy.log10( numpy.e ) / ( gr['Mmean'] - ( 
        gr['Mmin'] - 0.5 * binsize ) )
    gr['aValue'] = numpy.log10( gr['magCtr'] ) + gr['bValue'] * gr['Mmin']

    gr['StdDev'] = 2.3 * numpy.power( gr['bValue'], 2 ) * numpy.sqrt( sum( 
        numpy.power( ( magnitudes - gr['Mmean'] ), 2 ) ) / ( 
            gr['magCtr'] * ( gr['magCtr'] - 1 ) ) )

    # compute curve for G-R fit
    gr['fit'] = numpy.power( 10, 
        ( ( -gr['bValue'] * magnitudes_fit ) + gr['aValue'] ) )

    if timeSpan is not None:
        gr['aValueNormalized'] = gr['aValue'] - numpy.log10(timeSpan)
        gr['fitNormalized'] = numpy.power( 10, 
            ( ( -gr['bValue'] * magnitudes_fit ) + gr['aValueNormalized'] ) )

    return gr
