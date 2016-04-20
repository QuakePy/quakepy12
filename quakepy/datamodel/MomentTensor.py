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

from quakepy.datamodel import DataUsed
from quakepy.datamodel import Comment
from quakepy.datamodel import ResourceReference
from quakepy.datamodel import RealQuantity
from quakepy.datamodel import SourceTimeFunction
from quakepy.datamodel import Tensor
from quakepy.datamodel import CreationInfo

class MomentTensor(QPCore.QPPublicObject):
    """
    QuakePy: MomentTensor
    """


    # <!-- UML2Py start -->
    addElements = QPElement.QPElementList((
        QPElement.QPElement('publicID', 'publicID', 'attribute', unicode, 'basic'),

            QPElement.QPElement('derivedOriginID', 'derivedOriginID', 'element', unicode, 'basic'),

            QPElement.QPElement('momentMagnitudeID', 'momentMagnitudeID', 'element', unicode, 'basic'),

            QPElement.QPElement('scalarMoment', 'scalarMoment', 'element', RealQuantity.RealQuantity, 'complex'),

            QPElement.QPElement('tensor', 'tensor', 'element', Tensor.Tensor, 'complex'),
        QPElement.QPElement('variance', 'variance', 'element', float, 'basic'),
        QPElement.QPElement('varianceReduction', 'varianceReduction', 'element', float, 'basic'),
        QPElement.QPElement('doubleCouple', 'doubleCouple', 'element', float, 'basic'),
        QPElement.QPElement('clvd', 'clvd', 'element', float, 'basic'),
        QPElement.QPElement('iso', 'iso', 'element', float, 'basic'),

            QPElement.QPElement('greensFunctionID', 'greensFunctionID', 'element', unicode, 'basic'),

            QPElement.QPElement('filterID', 'filterID', 'element', unicode, 'basic'),

            QPElement.QPElement('sourceTimeFunction', 'sourceTimeFunction', 'element', SourceTimeFunction.SourceTimeFunction, 'complex'),

            QPElement.QPElement('methodID', 'methodID', 'element', unicode, 'basic'),
        QPElement.QPElement('category', 'category', 'element', unicode, 'enum'),
        QPElement.QPElement('inversionType', 'inversionType', 'element', unicode, 'enum'),

            QPElement.QPElement('creationInfo', 'creationInfo', 'element', CreationInfo.CreationInfo, 'complex'),
        QPElement.QPElement('dataUsed', 'dataUsed', 'element', DataUsed.DataUsed, 'multiple'),
        QPElement.QPElement('comment', 'comment', 'element', Comment.Comment, 'multiple'),
    ))
    # <!-- UML2Py end -->
    def __init__(self, publicID=None, 
        **kwargs):
        super(MomentTensor, self).__init__(publicID, **kwargs)
        self.elements.extend(self.addElements)

        # publicID has not been set in parent class
        if self.publicID is None:
            self.publicID = self.createPublicID(self.__class__.__name__, **kwargs)

        self._initMultipleElements()
