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


class TimeWindow(QPCore.QPPublicObject):
    """
    QuakePy: TimeWindow
    """


    # <!-- UML2Py start -->
    addElements = QPElement.QPElementList((
        QPElement.QPElement('begin', 'begin', 'element', float, 'basic'),
        QPElement.QPElement('end', 'end', 'element', float, 'basic'),
        QPElement.QPElement('reference', 'reference', 'element', QPDateTime.QPDateTime, 'basic'),
    ))
    # <!-- UML2Py end -->
    def __init__(self, 
        begin=None,
        end=None,
        reference=None,
        **kwargs ):
        super(TimeWindow, self).__init__(**kwargs)
        self.elements.extend(self.addElements)

        self.begin = begin
        self.end = end
        self.reference = reference

        self._initMultipleElements()
