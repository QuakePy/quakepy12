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

from quakepy.datamodel import NodalPlane

class NodalPlanes(QPCore.QPPublicObject):
    """
    QuakePy: NodalPlanes
    """


    # <!-- UML2Py start -->
    addElements = QPElement.QPElementList((

            QPElement.QPElement('nodalPlane1', 'nodalPlane1', 'element', NodalPlane.NodalPlane, 'complex'),

            QPElement.QPElement('nodalPlane2', 'nodalPlane2', 'element', NodalPlane.NodalPlane, 'complex'),
        QPElement.QPElement('preferredPlane', 'preferredPlane', 'attribute', int, 'basic'),
    ))
    # <!-- UML2Py end -->
    def __init__(self, 
        nodalPlane1=None,
        nodalPlane2=None,
        preferredPlane=None,
        **kwargs ):
        super(NodalPlanes, self).__init__(**kwargs)
        self.elements.extend(self.addElements)

        self.nodalPlane1 = nodalPlane1
        self.nodalPlane2 = nodalPlane2
        self.preferredPlane = preferredPlane

        self._initMultipleElements()
