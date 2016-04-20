# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

import qpplot

class CumulativeDistribution( object ):
    def __init__( self, evpar ):
        
        # over events and preferred origins
        curr_cd = []
        
        for curr_ev in evpar.event:
            
            curr_ori_time = curr_ev.getPreferredOrigin().time.value.datetime
            
            # append timestamp to list
            curr_cd.append( curr_ori_time )
        
        # sort list and add consecutive number
        self.cd = [ [ curr_cd_val.strftime('%Y-%m-%dT%H:%M:%S'), 
            str(curr_cd_idx+1) ] for curr_cd_idx, curr_cd_val in enumerate( 
            sorted( curr_cd ) ) ]
        del curr_cd
        
        
    def plot( self, imgfile=None, **kwargs ):
        return qpplot.QPPlot().plot_vs_date( imgfile, 
            [ curr_data[0] for curr_data in self.cd ], 
            [ curr_data[1] for curr_data in self.cd ],
            **kwargs )
    
def main():
    pass
    
if __name__ == '__main__':
    main()
