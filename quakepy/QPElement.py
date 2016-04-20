# -*- coding: utf-8 -*-
"""
This file is part of QuakePy12.

"""

class QPElementList(list):
    pass


class QPElement(object):
    """
    QuakePy: QPElement

    defines characteristics of attributes a class derived from QPObject has
    """
    
    def __init__(self, varname, xmlname, xmltype, pytype, vartype, 
        parentaxis=None, parenttype=None):

        if varname is not None:
            self.varname = varname
        else:
            error_str = "QPElement constructor: varname must not be None"
            raise ValueError, error_str

        if xmlname is not None:
            self.xmlname = xmlname
        else:
            error_str = "QPElement constructor: xmlname must not be None"
            raise ValueError, error_str

        if xmltype is not None:
            self.xmltype = xmltype
        else:
            error_str = "QPElement constructor: xmltype must not be None"
            raise ValueError, error_str

        if pytype is not None:
            self.pytype = pytype
        else:
            error_str = "QPElement constructor: pytype must not be None"
            raise ValueError, error_str

        if vartype is not None:
            self.vartype = vartype
        else:
            error_str = "QPElement constructor: vartype must not be None"
            raise ValueError, error_str

        self.parentaxis = parentaxis
        self.parenttype = parenttype
