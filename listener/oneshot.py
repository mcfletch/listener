from functools import wraps
import logging
log = logging.getLogger( __name__ )

def one_shot( func ):
    """Only calculate once for each instance"""
    key = '_' + func.__name__
    @property
    @wraps( func )
    def cached( self ):
        if not hasattr( self, key ):
            setattr( self, key, func(self))
        return getattr( self, key )
    @cached.setter
    @wraps(func)
    def cached( self, value ):
        setattr( self, key, value )
        return value
    return cached

