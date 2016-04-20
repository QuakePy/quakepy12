# -*- coding: utf-8 -*-

"""
The QuakePy package
http://www.quakepy.org

----------------------------------------------------------------------
Copyright (C) 2007-2013 by Fabian Euchner and Danijel Schorlemmer     
                                                                      
This program is free software; you can redistribute it and/or modify  
it under the terms of the GNU General Public License as published by  
the Free Software Foundation; either version 2 of the License, or     
(at your option) any later version.                                   
                                                                      
This program is distributed in the hope that it will be useful,       
but WITHOUT ANY WARRANTY; without even the implied warranty of        
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
GNU General Public License for more details.                          
                                                                      
You should have received a copy of the GNU General Public License     
along with this program; if not, write to the                         
Free Software Foundation, Inc.,                                       
59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             
----------------------------------------------------------------------
"""

__version__  = '$Id$'
__revision__ = '$Revision$'
__author__   = "Fabian Euchner <fabian@fabian-euchner.de>, "\
               "Danijel Schorlemmer <ds@gfz-potsdam.de>"
__license__  = "GPL"

import sys

from quakepy import QPCore
from quakepy import QPDateTime
from quakepy import QPElement

from quakepy.datamodel import MomentTensor
from quakepy.datamodel import FocalMechanism
from quakepy.datamodel import WaveformStreamID
from quakepy.datamodel import Amplitude
from quakepy.datamodel import StationMagnitudeContribution
from quakepy.datamodel import Magnitude
from quakepy.datamodel import StationMagnitude
from quakepy.datamodel import OriginUncertainty
from quakepy.datamodel import Arrival
from quakepy.datamodel import Origin
from quakepy.datamodel import Pick
from quakepy.datamodel import CompositeTime
from quakepy.datamodel import DataUsed
from quakepy.datamodel import EventDescription
from quakepy.datamodel import Comment
from quakepy.datamodel import ResourceReference
from quakepy.datamodel import RealQuantity
from quakepy.datamodel import SourceTimeFunction
from quakepy.datamodel import Tensor
from quakepy.datamodel import CreationInfo
from quakepy.datamodel import NodalPlanes
from quakepy.datamodel import PrincipalAxes
from quakepy.datamodel import TimeQuantity
from quakepy.datamodel import TimeWindow
from quakepy.datamodel import ConfidenceEllipsoid
from quakepy.datamodel import Phase
from quakepy.datamodel import OriginQuality
from quakepy.datamodel import IntegerQuantity

class Event(QPCore.QPPublicObject):
    """
    QuakePy: Event
    """


    # <!-- UML2Py start -->
    addElements = QPElement.QPElementList((
        QPElement.QPElement('publicID', 'publicID', 'attribute', unicode, 'basic'),

            QPElement.QPElement('preferredOriginID', 'preferredOriginID', 'element', unicode, 'basic'),

            QPElement.QPElement('preferredMagnitudeID', 'preferredMagnitudeID', 'element', unicode, 'basic'),

            QPElement.QPElement('preferredFocalMechanismID', 'preferredFocalMechanismID', 'element', unicode, 'basic'),
        QPElement.QPElement('type', 'type', 'element', unicode, 'enum'),
        QPElement.QPElement('typeCertainty', 'typeCertainty', 'element', unicode, 'enum'),

            QPElement.QPElement('creationInfo', 'creationInfo', 'element', CreationInfo.CreationInfo, 'complex'),
        QPElement.QPElement('focalMechanism', 'focalMechanism', 'element', FocalMechanism.FocalMechanism, 'multiple'),
        QPElement.QPElement('amplitude', 'amplitude', 'element', Amplitude.Amplitude, 'multiple'),
        QPElement.QPElement('magnitude', 'magnitude', 'element', Magnitude.Magnitude, 'multiple'),
        QPElement.QPElement('stationMagnitude', 'stationMagnitude', 'element', StationMagnitude.StationMagnitude, 'multiple'),
        QPElement.QPElement('origin', 'origin', 'element', Origin.Origin, 'multiple'),
        QPElement.QPElement('pick', 'pick', 'element', Pick.Pick, 'multiple'),
        QPElement.QPElement('description', 'description', 'element', EventDescription.EventDescription, 'multiple'),
        QPElement.QPElement('comment', 'comment', 'element', Comment.Comment, 'multiple'),
    ))
    # <!-- UML2Py end -->
    def __init__(self, publicID=None, 
        **kwargs):
        super(Event, self).__init__(publicID, **kwargs)
        self.elements.extend(self.addElements)

        # publicID has not been set in parent class
        if self.publicID is None:
            self.publicID = self.createPublicID(self.__class__.__name__, **kwargs)

        self._initMultipleElements()


    def getPreferredOriginIdx(self):
        if (not hasattr(self, 'origin')) or len(self.origin) == 0:
            return None
        elif len(self.origin) == 1:
            return 0
        else:
            for curr_ori_idx, curr_ori in enumerate(self.origin):
                if self.preferredOriginID == curr_ori.publicID:
                    return curr_ori_idx
                
        # no origin found
        raise IndexError, "Event::getPreferredOriginIdx - origin not found"
    
    
    def getPreferredOrigin( self ):
        idx = self.getPreferredOriginIdx()
        if idx is not None:
            return self.origin[idx]
        else:
            raise IndexError, "Event::getPreferredOrigin - origin not found"
    
    
    def getPreferredMagnitudeIdx( self ):
        if (not hasattr(self, 'magnitude')) or len( self.magnitude ) == 0:
            return None
        elif len( self.magnitude ) == 1:
            return 0
        else:
            for curr_mag_idx, curr_mag in enumerate( self.magnitude ):
                if self.preferredMagnitudeID == curr_mag.publicID:
                    return curr_mag_idx
                
        # no magnitude found
        raise IndexError, "Event::getPreferredMagnitudeIdx - magnitude not found"
    
    
    def getPreferredMagnitude( self ):
        idx = self.getPreferredMagnitudeIdx()
        if idx is not None:
            return self.magnitude[idx]
        else:
            raise IndexError, "Event::getPreferredMagnitude - magnitude not found"
    
    
    def getPreferredFocalMechanismIdx( self ):
        if ( not hasattr( self, 'focalMechanism' ) ) or len( self.focalMechanism ) == 0:
            return None
        elif len( self.focalMechanism ) == 1:
            return 0
        else:
            for curr_fm_idx, curr_fm in enumerate( self.focalMechanism ):
                if self.preferredFocalMechanismID == curr_fm.publicID:
                    return curr_fm_idx
                
        # no focalMechanism found
        raise IndexError, "Event::getPreferredFocalMechanismIdx - focalMechanism not found"
    
    
    def getPreferredFocalMechanism( self ):
        idx = self.getPreferredFocalMechanismIdx()
        if idx is not None:
            return self.focalMechanism[idx]
        else:
            raise IndexError, "Event::getPreferredFocalMechanism - focalMechanism not found"


    def getOriginIdx(self, ori):
        """
        input: ori, can either be Origin instance or publicID of origin
        """
        if not isinstance(ori, Origin.Origin):
            lookForInstance = False
        else:
            lookForInstance = True

        for curr_ori_idx, curr_ori in enumerate(self.origin):
            if lookForInstance:
                if ori == curr_ori:
                    return curr_ori_idx

            else:
                if ori == curr_ori.publicID:
                    return curr_ori_idx

        return None


    def getOrigin(self, ori):
        """
        input: ori, can either be Origin instance or publicID of origin
        """
        ori_idx = self.getOriginIdx(ori)
        if ori_idx is not None:
            return self.origin[ori_idx]
        else:
            return None
    
    
    def getMagnitudesIdx(self, ori):
        mag_idx = []

        for curr_mag_idx, curr_mag in enumerate( self.magnitude ):
            if curr_mag.originID == ori.publicID:
                mag_idx.append( curr_mag_idx )
        return mag_idx
    
    
    def getMagnitudes( self, ori ):
        magnitudes = []
        
        for mag in self.magnitude:
            if mag.originID == ori.publicID:
                magnitudes.append( mag )
        return magnitudes
