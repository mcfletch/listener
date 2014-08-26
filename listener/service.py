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
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import traceback
from . import context,oneshot

MAINLOOP = None

class ContextService( dbus.service.Object ):
    """Service controlling a particular listener context"""
    DBUS_NAME = 'com.vrplumber.listener.context'
    DBUS_PATH = '/com/vrplumber/listener/context'
    
    @classmethod
    def bus_name( cls, key='default' ):
        return dbus.service.BusName(
            '%s.%s'%(cls.DBUS_NAME,key), 
            bus=dbus.SessionBus()
        )
    @classmethod 
    def bus_path( cls, key='default' ):
        return '%s/%s'%(cls.DBUS_PATH,key) 
    
    def __init__( self, key='default' ):
        self.key = key
        dbus.service.Object.__init__(
            self, self.bus_name(self.key), 
            self.bus_path( self.key )
        )
    @property
    def name( self ):
        return self.bus_name( self.key )
    @oneshot.one_shot
    def context( self ):
        return context.Context( self.key )
    
    @dbus.service.method(
        DBUS_NAME,
    )
    def delete( self ):
        self.context.delete()
        for location in self.locations():
            conn = locations[0]
            self.remove_from_connection( conn )
        return True
    @dbus.service.method(
        DBUS_NAME,
        in_signature='s',
    )
    def import_project( self, path ):
        """Import a project from the given path"""
        # iterate project importing files from the path...

class ListenerService( dbus.service.Object ):
    """Overall per-session listener service"""
    DBUS_NAME = 'com.vrplumber.listener'
    DBUS_PATH = '/com/vrplumber/listener'
    def __init__( self ):
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH )
        self._context_proxies = {}
    @property
    def context_proxies( self ):
        new_proxies = {}
        for working in context.Context.keys():
            if working not in self._context_proxies:
                new_proxies[working] = ContextService( working )
            else:
                new_proxies[working] = self._context_proxies.pop( working )
        self._context_proxies.empty()
        self._context_proxies.update( new_proxies )
        return self._context_proxies
    @dbus.service.method(
        DBUS_NAME,
    )
    def contexts( self ):
        """Lists the contexts currently defined in the service
        
        Returns the bus-names of the sub-contexts that can be used 
        to instantiate them, currently you *must* call this method 
        """
        return [
            proxy.name.get_name()
            for (name,proxy) in sorted(self.context_proxies.items())
        ]
    @dbus.service.method(
        DBUS_NAME,
        in_signature='s',
    )
    def context( self, key ):
        proxy = self.context_proxies.get( key )
        if proxy:
            return proxy.name.get_name()
        return None
    @dbus.service.method(
        DBUS_NAME,
        in_signature='s',
    )
    def create_context( self, key ):
        proxy = self.context_proxies.get( key )
        if proxy:
            return False
        c = context.Context( key )
        return ContextService.bus_name( key ).get_name()
    
    
#    def context( self, key ):
#        """Retrieve reference to the given listening context raise AttributeError on failure"""
#    def create_context( self, key, parent=None ):
#        try:
#            return self.context( key )
#        except AttributeError as err:
#            context = Context( self, key, parent )
#            return context
#
#class Context( object ):
#    def __init__( self, service, key, parent=None ):
#        """Create a new listening context based on the parent context"""
#    def add_phrase( self, phrase, recording=None, phonetic=None ):
#        """Add a (corrected) phrase to the context"""
#    def add_word( self, word, phonetic=None ):
#        """Add a single word to the context"""
#    def phrases( self ):
#        """Generate the set of (trained) phrases"""
    
def main():
    """Start up the listener Daemon, should be a DBus "service"
    
    This should be an on-demand service eventually, that is, when you 
    request a com.vrplumber.Listener.Uinput you should instantiate one
    and/or get the running one.
    """
    global MAINLOOP
    DBusGMainLoop(set_as_default=True)
    
    service = ListenerService()
    
    MAINLOOP = gobject.MainLoop()
    MAINLOOP.run()

if __name__ == "__main__":
    main()
