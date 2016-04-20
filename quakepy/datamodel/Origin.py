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

from quakepy.datamodel import OriginUncertainty
from quakepy.datamodel import Arrival
from quakepy.datamodel import CompositeTime
from quakepy.datamodel import Comment
from quakepy.datamodel import ResourceReference
from quakepy.datamodel import RealQuantity
from quakepy.datamodel import CreationInfo
from quakepy.datamodel import TimeQuantity
from quakepy.datamodel import ConfidenceEllipsoid
from quakepy.datamodel import Phase
from quakepy.datamodel import OriginQuality
from quakepy.datamodel import IntegerQuantity

class Origin(QPCore.QPPublicObject):
    """
    QuakePy: Origin
    """


    # <!-- UML2Py start -->
    addElements = QPElement.QPElementList((
        QPElement.QPElement('publicID', 'publicID', 'attribute', unicode, 'basic'),

            QPElement.QPElement('time', 'time', 'element', TimeQuantity.TimeQuantity, 'complex'),

            QPElement.QPElement('longitude', 'longitude', 'element', RealQuantity.RealQuantity, 'complex'),

            QPElement.QPElement('latitude', 'latitude', 'element', RealQuantity.RealQuantity, 'complex'),

            QPElement.QPElement('depth', 'depth', 'element', RealQuantity.RealQuantity, 'complex'),
        QPElement.QPElement('depthType', 'depthType', 'element', unicode, 'enum'),
        QPElement.QPElement('timeFixed', 'timeFixed', 'element', bool, 'basic'),
        QPElement.QPElement('epicenterFixed', 'epicenterFixed', 'element', bool, 'basic'),

            QPElement.QPElement('referenceSystemID', 'referenceSystemID', 'element', unicode, 'basic'),

            QPElement.QPElement('methodID', 'methodID', 'element', unicode, 'basic'),

            QPElement.QPElement('earthModelID', 'earthModelID', 'element', unicode, 'basic'),

            QPElement.QPElement('quality', 'quality', 'element', OriginQuality.OriginQuality, 'complex'),
        QPElement.QPElement('type', 'type', 'element', unicode, 'enum'),
        QPElement.QPElement('region', 'region', 'element', unicode, 'basic'),
        QPElement.QPElement('evaluationMode', 'evaluationMode', 'element', unicode, 'enum'),
        QPElement.QPElement('evaluationStatus', 'evaluationStatus', 'element', unicode, 'enum'),

            QPElement.QPElement('creationInfo', 'creationInfo', 'element', CreationInfo.CreationInfo, 'complex'),
        QPElement.QPElement('originUncertainty', 'originUncertainty', 'element', OriginUncertainty.OriginUncertainty, 'multiple'),
        QPElement.QPElement('arrival', 'arrival', 'element', Arrival.Arrival, 'multiple'),
        QPElement.QPElement('compositeTime', 'compositeTime', 'element', CompositeTime.CompositeTime, 'multiple'),
        QPElement.QPElement('comment', 'comment', 'element', Comment.Comment, 'multiple'),
    ))
    # <!-- UML2Py end -->
    def __init__(self, publicID=None, 
        **kwargs):
        super(Origin, self).__init__(publicID, **kwargs)
        self.elements.extend(self.addElements)

        # publicID has not been set in parent class
        if self.publicID is None:
            self.publicID = self.createPublicID(self.__class__.__name__, **kwargs)

        self._initMultipleElements()
    
    
    def getArrivalsIdx(self, pick):
        arr_idx = []
        
        for curr_arr_idx, curr_arr in enumerate(self.arrival):
            if curr_arr.pickID == pick.publicID:
                arr_idx.append(curr_arr_idx)
        return arr_idx
    
    
    def getArrivals(self, pick):
        arrivals = []
        
        for arr in self.arrival:
            if arr.pickID == pick.publicID:
                arrivals.append(arr)
        return arrivals
