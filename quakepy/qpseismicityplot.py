# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import os
import datetime
import matplotlib
matplotlib.use('PS')

from pylab import *
from matplotlib import rcParams
from matplotlib.dates import MO
from matplotlib.dates import YearLocator, MonthLocator, DayLocator, \
                             WeekdayLocator, DateFormatter

#import gmt
#import subprocess

import qpplot
    

class QPSeismicityPlot( qpplot.QPPlot ):

    def __init__( self ):
        """
        catalog: QPCatalog object
        kwargs:                                             default value:
            gmt_event_symbol_type                               's'            # square
            gmt_event_symbol_size                               0.2            # cm
            gmt_event_symbol_colour                             ( 255, 0, 0 )  # red
            
            gmt_latmin                                          AUTO
            gmt_latmax                                          AUTO
            gmt_lonmin                                          AUTO
            gmt_lonmax                                          AUTO
            
            gmt_proj                                            'cyl'
            gmt_xyunits                                         'c'
            gmt_xsize                                           15.0 # cm
            gmt_ysize                                           15.0 # cm
            gmt_xshift                                          0.0
            gmt_yshift                                          0.0
            gmt_centerlon                                       0.0
            gmt_centerlat                                       0.0
            
            gmt_latgrdinc                                       -1
            gmt_longrdinc                                       -1
            
            gmt_basemaptype                                     'fancy'
            gmt_headerfontsize                                  18
            gmt_labelfontsize                                   12
            gmt_axisfontsize                                    16
            
            gmt_maintitle                                       ''
            gmt_lefttitle                                       ''
            gmt_righttitle                                      ''
            
            gmt_mapscale                                        True
            gmt_mapscalestyle                                   'f'
            
            gmt_eaxis                                           True
            gmt_elabels                                         False
            gmt_naxis                                           True
            gmt_nlabels                                         False
            gmt_saxis                                           True
            gmt_slabels                                         True
            gmt_waxis                                           True
            gmt_wlabels                                         True
        
            gmt_coastlines                                      True
            gmt_coastres                                        'f'
            gmt_coastthick                                      1.0
            gmt_countries                                       True
            gmt_countrythick                                    1.0
        
            gmt_continents                                      True
            gmt_continentfill                                   False
            gmt_continentfillcolor                              ( 200, 200, 200 )
            gmt_oceanfill                                       False
            gmt_oceanfillcolor                                  ( 100, 100, 100 )
        """
        super( QPSeismicityPlot, self ).__init__()
        
        ### ----- set GMT map defaults ----- ###
        self.gmt_event_symbol_type                  = 's'            # square
        self.gmt_event_symbol_size                  = 0.2            # cm
        self.gmt_event_symbol_colour                = ( 255, 0, 0 )  # red
        
        self.gmt_proj                               = 'cyl'
        self.gmt_xyunits                            = 'c'
        self.gmt_xsize                              = 15.0 # cm
        self.gmt_ysize                              = 15.0 # cm
        self.gmt_xshift                             = 0.0
        self.gmt_yshift                             = 0.0
        self.gmt_centerlon                          = 0.0
        self.gmt_centerlat                          = 0.0
        
        self.gmt_latgrdinc                          = -1 # no grid
        self.gmt_longrdinc                          = -1 # no grid
        
        self.gmt_basemaptype                        = 'fancy'
        self.gmt_headerfontsize                     = 18
        self.gmt_labelfontsize                      = 12
        self.gmt_axisfontsize                       = 16
        
        self.gmt_maintitle                          = ''
        self.gmt_lefttitle                          = ''
        self.gmt_righttitle                         = ''
        
        self.gmt_mapscale                           = True
        self.gmt_mapscalestyle                      = 'f'    # fancy, 'p' plain
        
        self.gmt_eaxis                              = True
        self.gmt_elabels                            = False
        self.gmt_naxis                              = True
        self.gmt_nlabels                            = False
        self.gmt_saxis                              = True
        self.gmt_slabels                            = True
        self.gmt_waxis                              = True
        self.gmt_wlabels                            = True
        
        self.gmt_coastlines                         = True
        self.gmt_coastres                           = 'h'
        self.gmt_coastthick                         = 1.0
        self.gmt_countries                          = True
        self.gmt_countrythick                       = 1.0
        # self.map_rivers                             = True
        # self.map_rivers_thickness                   = 1.0
        # self.map_rivers_colour                      = ( 0, 255, 0 )
        
        self.gmt_continents                         = True
        self.gmt_continentfill                      = False
        self.gmt_continentfillcolor                 = ( 200, 200, 200 )
        self.gmt_oceanfill                          = False
        self.gmt_oceanfillcolor                     = ( 100, 100, 100 )
        
        ### ----- set Matplotlib map defaults ----- ###
        self.mpl_event_symbol_type                  = 'rs'            # red square
        self.mpl_line_style                         = 'k-'            # black
        
        self.mpl_coastlines                         = True
        
        
    def plot_gmt( self, catalog, epsfile, **kwargs ):
        """
        plot x-axis 'longitude', y-axis 'latitude'
        """

        # get (lon, lat) pairs of events
        lon = []
        lat = []
        for curr_ev in catalog.eventParameters.event:
            try:
                lon.append( float(curr_ev.getPreferredOrigin().longitude.value) )
                lat.append( float(curr_ev.getPreferredOrigin().latitude.value) )
            except:
                pass
            
        # check if lat/lon range is given in kwargs
        if 'gmt_latmin' in kwargs:
            latmin = kwargs['gmt_latmin']
        else:
            latmin = min(lat)
            latmin = ( latmin < 0.0 and [1.05*latmin] or [0.95*latmin] )[0]
            
        if 'gmt_latmax' in kwargs:
            latmax = kwargs['gmt_latmax']
        else:
            latmax = max(lat)
            latmax = ( latmax < 0.0 and [0.95*latmax] or [1.05*latmax] )[0]
            
        if 'gmt_lonmin' in kwargs:
            lonmin = kwargs['gmt_lonmin']
        else:
            lonmin = min(lon)
            lonmin = ( lonmin < 0.0 and [1.05*lonmin] or [0.95*lonmin] )[0]
            
        if 'gmt_lonmax' in kwargs:
            lonmax = kwargs['gmt_lonmax']
        else:
            lonmax = max(lon)
            lonmax = ( lonmax < 0.0 and [0.95*lonmax] or [1.05*lonmax] )[0]
        
        # possible choices for proj (map projection) 
        #   'linear'
        #   'loglinear'
        #   'loglog' 
        #   'cyl'       - cylindrical equidistant 
        #   'npst'      - North Polar Stereographic 
        #   'spst'      - South Polar Stereographic 
        #   'lc'        - Lambert Conformal Conic 
        #   'la'        - lambert azimuthal 
        #   'merc'      - mercator 
        #   'ortho'     - Orthographic
        #   'gst'       - general stereographic.
 
        proj      = ( 'gmt_proj' in kwargs and [kwargs['gmt_proj']] or [self.gmt_proj] )[0]
        xsize     = ( 'gmt_xsize' in kwargs and [kwargs['gmt_xsize']] or [self.gmt_xsize] )[0]
        ysize     = ( 'gmt_ysize' in kwargs and [kwargs['gmt_ysize']] or [self.gmt_ysize] )[0]
        xyunits   = ( 'gmt_xyunits' in kwargs and [kwargs['gmt_xyunits']] or [self.gmt_xyunits] )[0]
        xshift    = ( 'gmt_xshift' in kwargs and [kwargs['gmt_xshift']] or [self.gmt_xshift] )[0]
        yshift    = ( 'gmt_yshift' in kwargs and [kwargs['gmt_yshift']] or [self.gmt_yshift] )[0]
        centerlon = ( 'gmt_centerlon' in kwargs and [kwargs['gmt_centerlon']] or [self.gmt_centerlon] )[0]
        centerlat = ( 'gmt_centerlat' in kwargs and [kwargs['gmt_centerlat']] or [self.gmt_centerlat] )[0]
        
        # lat/lon grid lines, tick minor/major tick marks, labels
        latgrdinc = ( 'gmt_latgrdinc' in kwargs and [kwargs['gmt_latgrdinc']] or [self.gmt_latgrdinc] )[0]
        longrdinc = ( 'gmt_longrdinc' in kwargs and [kwargs['gmt_longrdinc']] or [self.gmt_longrdinc] )[0]
        
        basemaptype         = ( 'gmt_basemaptype' in kwargs and [kwargs['gmt_basemaptype']] or [self.gmt_basemaptype] )[0]
        headerfontsize      = ( 'gmt_headerfontsize' in kwargs and [kwargs['gmt_headerfontsize']] or [self.gmt_headerfontsize] )[0]
        labelfontsize       = ( 'gmt_labelfontsize' in kwargs and [kwargs['gmt_labelfontsize']] or [self.gmt_labelfontsize] )[0]
        axisfontsize        = ( 'gmt_axisfontsize' in kwargs and [kwargs['gmt_axisfontsize']] or [self.gmt_axisfontsize] )[0]
        
        maintitle           = ( 'gmt_maintitle' in kwargs and [kwargs['gmt_maintitle']] or [self.gmt_maintitle] )[0]
        lefttitle           = ( 'gmt_lefttitle' in kwargs and [kwargs['gmt_lefttitle']] or [self.gmt_lefttitle] )[0]
        righttitle          = ( 'gmt_righttitle' in kwargs and [kwargs['gmt_righttitle']] or [self.gmt_righttitle] )[0]
        
        # map scale: mapscale mapscalestyle mapscalelatlon mapscalelength mapscalexpos mapscaleypos
        mapscale            = ( 'gmt_mapscale' in kwargs and [kwargs['gmt_mapscale']] or [self.gmt_mapscale] )[0]
        mapscalestyle       = ( 'gmt_mapscalestyle' in kwargs and [kwargs['gmt_mapscalestyle']] or [self.gmt_mapscalestyle] )[0]
    
        ## TODO
        #mapscalelatlon
        #False | specify position of map scale in lon/lat instead of x/y. 
   
        #mapscalelength
        #approx 1/5 zonal scale of plot | length of map scale in km. 
   
        #mapscalexpos
        #xsize*4/5 | x-position of map scale. 
   
        #mapscaleypos
        #ysize/10 | y-position of map scale.
        
        eaxis               = ( 'gmt_eaxis' in kwargs and [kwargs['gmt_eaxis']] or [self.gmt_eaxis] )[0]
        elabels             = ( 'gmt_elabels' in kwargs and [kwargs['gmt_elabels']] or [self.gmt_elabels] )[0]
        naxis               = ( 'gmt_naxis' in kwargs and [kwargs['gmt_naxis']] or [self.gmt_naxis] )[0]
        nlabels             = ( 'gmt_nlabels' in kwargs and [kwargs['gmt_nlabels']] or [self.gmt_nlabels] )[0]
        saxis               = ( 'gmt_saxis' in kwargs and [kwargs['gmt_saxis']] or [self.gmt_saxis] )[0]
        slabels             = ( 'gmt_slabels' in kwargs and [kwargs['gmt_slabels']] or [self.gmt_slabels] )[0]
        waxis               = ( 'gmt_waxis' in kwargs and [kwargs['gmt_waxis']] or [self.gmt_waxis] )[0]
        wlabels             = ( 'gmt_wlabels' in kwargs and [kwargs['gmt_wlabels']] or [self.gmt_wlabels] )[0]
        
        coastlines          = ( 'gmt_coastlines' in kwargs and [kwargs['gmt_coastlines']] or [self.gmt_coastlines] )[0]
        coastres            = ( 'gmt_coastres' in kwargs and [kwargs['gmt_coastres']] or [self.gmt_coastres] )[0]
        coastthick          = ( 'gmt_coastthick' in kwargs and [kwargs['gmt_coastthick']] or [self.gmt_coastthick] )[0]
        countries           = ( 'gmt_countries' in kwargs and [kwargs['gmt_countries']] or [self.gmt_countries] )[0]
        countrythick        = ( 'gmt_countrythick' in kwargs and [kwargs['gmt_countrythick']] or [self.gmt_countrythick] )[0]
        
        continents          = ( 'gmt_continents' in kwargs and [kwargs['gmt_continents']] or [self.gmt_continents] )[0]
        continentfill       = ( 'gmt_continentfill' in kwargs and [kwargs['gmt_continentfill']] or [self.gmt_continentfill] )[0]
        continentfillcolor  = ( 'gmt_continentfillcolor' in kwargs and [kwargs['gmt_continentfillcolor']] or [self.gmt_continentfillcolor] )[0]
        oceanfill           = ( 'gmt_oceanfill' in kwargs and [kwargs['gmt_oceanfill']] or [self.gmt_oceanfill] )[0]
        oceanfillcolor      = ( 'gmt_oceanfillcolor' in kwargs and [kwargs['gmt_oceanfillcolor']] or [self.gmt_oceanfillcolor] )[0]
        
        plot = gmt.GMT( latmin=latmin, latmax=latmax, lonmin=lonmin, lonmax=lonmax, proj=proj, 
                        xsize=xsize, ysize=ysize, xyunits=xyunits, xshift=xshift, yshift=yshift, 
                        centerlon=centerlon, centerlat=centerlat,
                        latgrdinc=latgrdinc,
                        longrdinc=longrdinc,
                        headerfontsize=headerfontsize,
                        labelfontsize=labelfontsize,
                        axisfontsize=axisfontsize,
                        basemaptype=basemaptype )
        
        # axes
        plot.eaxis   = eaxis
        plot.elabels = elabels 
        plot.naxis   = naxis
        plot.nlabels = nlabels 
        plot.saxis   = saxis
        plot.slabels = slabels 
        plot.waxis   = waxis
        plot.wlabels = wlabels 
        
        # titles
        plot.maintitle  = maintitle
        plot.lefttitle  = lefttitle
        plot.righttitle = righttitle
        
        # coastlines
        plot.coastlines = coastlines
        plot.coastres   = coastres
        plot.coastthick = coastthick
           
        # countries (political boundaries) 
        plot.countries    = countries
        plot.countrythick = countrythick
        
        # continents
        plot.continents          = continents
        plot.continentfill       = continentfill
        plot.continentfillcolor  = continentfillcolor
        plot.oceanfill           = oceanfill
        plot.oceanfillcolor      = oceanfillcolor
        
        ## TODO
        # rivers
        # if 'rivers' in kwargs and kwargs['rivers'] == True:
        #    pass

        # mapscale
        plot.mapscale      = mapscale
        plot.mapscalestyle = mapscalestyle
           
        # plot symbols for events
        event_symbol_type  = ( 'gmt_event_symbol_type' in kwargs and [kwargs['gmt_event_symbol_type']] or [self.gmt_event_symbol_type] )[0]
        event_symbol_size  = ( 'gmt_event_symbol_size' in kwargs and [kwargs['gmt_event_symbol_size']] or [self.gmt_event_symbol_size] )[0]
        event_symbol_color = ( 'gmt_event_symbol_color' in kwargs and [kwargs['gmt_event_symbol_color']] or [self.gmt_event_symbol_color] )[0]

        plot.basemap()
        plot.drawsymbol( lat, lon, symbol=event_symbol_type, size=event_symbol_size, color=event_symbol_color )
        
        plot.close( psfilename=epsfile )

    def plot_matplotlib( self, catalog, imgfile, **kwargs ):
        """
        plot x-axis 'longitude', y-axis 'latitude'
        """
        
        event_symbol_type  = ( 'mpl_event_symbol_type' in kwargs and [kwargs['mpl_event_symbol_type']] or [self.mpl_event_symbol_type] )[0]
        line_style         = ( 'mpl_line_style' in kwargs and [kwargs['mpl_line_style']] or [self.mpl_line_style] )[0]

        coastfile  = 'coast.tmp'
        
        # get (lon, lat) pairs
        lon = []
        lat = []
        
        for curr_ev in catalog.eventParameters.event:
            try:
                lon.append( float(curr_ev.getPreferredOrigin().longitude.value) )
                lat.append( float(curr_ev.getPreferredOrigin().latitude.value) )
            except:
                pass
            
        ax = subplot(111)
        plot( lon, lat, event_symbol_type )
            
        if 'mpl_coastlines' in kwargs and kwargs['mpl_coastlines'] == True:
           xmin, xmax = xlim()
           ymin, ymax = ylim()
           
           # GMT: pscoast, -Dh high-resolution
           # commandstr  = 'pscoast'
           # commandstr  = '/opt/gmt/bin/pscoast'
           commandstr  = '/usr/local/GMT4.2.1/bin/pscoast'
           
           #commandarg  = ''.join( ( ' -W -Jm6i -Di -R', str(xmin), '/', str(xmax), '/', str(ymin), '/', str(ymax), ' -M' ) )
           commandarg  = ''.join( ( ' -W -Jm6i -Dc -R', str(xmin), '/', str(xmax), '/', str(ymin), '/', str(ymax), ' -M' ) )
           stdout = os.system( commandstr + commandarg + " > " + coastfile )
           
           # open file for coastline
           fh = open( coastfile, 'r' )
           lines = fh.readlines()
           
           # over lines in file
           curr_seg_absc = []
           curr_seg_ord = []
           for curr_line in lines:
               
               if curr_line.startswith('#'):
                   continue
               
               elif curr_line.startswith('>'):
                   
                   # if arrays are not empty, plot segments, otherwise do nothing
                   if len( curr_seg_absc ) != 0 or len( curr_seg_ord ) != 0:
                       plot( curr_seg_absc, curr_seg_ord, line_style )
                       curr_seg_absc = []
                       curr_seg_ord = []
                   else:
                       continue
                   
               else:
                   # add lon, lat to segment
                   lon, lat = curr_line.split()
                   if lon > 180.0:
                       lon = float(lon) - 360.0
                   curr_seg_absc.append( float(lon) )
                   curr_seg_ord.append( float(lat) )
           fh.close()
           
        show()
        
        try:
            savefig( imgfile )
        except IOError, e:
            print "could not write image to file: ", e
            return None
    
