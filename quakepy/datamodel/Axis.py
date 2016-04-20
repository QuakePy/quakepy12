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

from quakepy.datamodel import RealQuantity

class Axis(QPCore.QPPublicObject):
    """
    QuakePy: Axis
    """


    # <!-- UML2Py start -->
    addElements = QPElement.QPElementList((

            QPElement.QPElement('azimuth', 'azimuth', 'element', RealQuantity.RealQuantity, 'complex'),

            QPElement.QPElement('plunge', 'plunge', 'element', RealQuantity.RealQuantity, 'complex'),

            QPElement.QPElement('length', 'length', 'element', RealQuantity.RealQuantity, 'complex'),
    ))
    # <!-- UML2Py end -->
    def __init__(self, 
        azimuth=None,
        plunge=None,
        length=None,
        **kwargs ):
        super(Axis, self).__init__(**kwargs)
        self.elements.extend(self.addElements)

        self.azimuth = azimuth
        self.plunge = plunge
        self.length = length

        self._initMultipleElements()
