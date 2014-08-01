"""DBus "service" for Listener

Provides a mechanism by which code running as the current user 
(namely the listener service) can send messages.  Currently this 
is just to allow for running uinput "type on the keyboard" style 
messages, but eventually should allow for:

    context setup/switches (i.e. create new language models)
    
    training
    
    ???

We will want to use permission restrictions such that only console 
users can access the service. (There's already a sample conf created 
for that).

Will (eventually) want all of the pipeline etc. to run in the service,
though possibly as two separate processes, one running on the system 
bus (uinput) and the other on the session bus (listener itself).
    
The code in this module is BSD licensed (as is the rest of listener).

But Note: this module loads python-dbus, which on PyPI declares itself
to be MIT licensed, but the FAQ for which declares to be a dual license 
AFL/GPL license.

Licensing should be reviewed, and notices posted that if you use 
this script you may be further restricted than the rest of the package.
"""
import dbus
from . import uinputdriver

class UInputService( object ):
    # one shot property to get the uinput and wait for initialization
    def run_input_string( self, input_string ):
        self.uinput.run_input_string( input_string )

class ListenerService( object ):
    def context( self, key ):
        """Retrieve reference to the given listening context raise AttributeError on failure"""
    def create_context( self, key, parent=None ):
        try:
            return self.context( key )
        except AttributeError as err:
            context = Context( self, key, parent )
            return context

class Context( object ):
    def __init__( self, service, key, parent=None ):
        """Create a new listening context based on the parent context"""
    def add_phrase( self, phrase, recording=None, phonetic=None ):
        """Add a (corrected) phrase to the context"""
    def add_word( self, word, phonetic=None ):
        """Add a single word to the context"""
    def phrases( self ):
        """Generate the set of (trained) phrases"""
    
def main():
    """Start up the listener Daemon, should be a DBus "service"
    
    This should be an on-demand service eventually, that is, when you 
    request a com.vrplumber.Listener.Uinput you should instantiate one
    and/or get the running one.
    """
