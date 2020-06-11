"""DBus "service" for Listener

Provides a mechanism by which code running as the current user 
(namely the listener service) can send messages.

    context setup (i.e. create new language models)
    
        add projects to context 
        
        create new contexts
        
        modify/edit dictionaries
        
        correction process
        
    context choice (switch current context)
    
    sample/training playback
    
    microphone selection enabling/disabling, etc
    
    uinput (keyboard simulation)

We will want to use permission restrictions such that only console 
users can access the uinput service. (There's a sample conf started
for that).

Will (eventually) want the pipelines to run in the Listener service 
and the uinput service to run in a separate service.
    
The code in this module is BSD licensed (as is the rest of listener).

Note: this module loads python-dbus, which on PyPI and in it's source 
distribution declares itself to be MIT licensed, but the FAQ for which 
declares to be a dual license AFL/GPL license.
"""
from __future__ import absolute_import
import dbus
import dbus.service


class ListenerService(dbus.service.Object):
    """Overall per-session listener service"""

    DBUS_NAME = 'com.vrplumber.listener'
    DBUS_PATH = '/com/vrplumber/listener'

    def __init__(self, mainwindow):
        self.target = mainwindow
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)
        self.pipeline = PipelineService(self.target)
        self.context = ContextService(self.target)

    @dbus.service.method(DBUS_NAME,)
    def contexts(self):
        """Lists the contexts currently defined in the service
        
        Returns the bus-names of the sub-contexts that can be used 
        to instantiate them, currently you *must* call this method 
        """
        from . import context

        return context.Context.keys()

    @dbus.service.signal('%s.results' % (DBUS_NAME,), signature='sss')
    def send_partial(self, interpreted, text, uttid):
        return interpreted

    @dbus.service.signal('%s.results' % (DBUS_NAME,), signature='sss')
    def send_final(self, interpreted, text, uttid):
        return interpreted


class PipelineService(dbus.service.Object):
    # current pipeline manipulation...
    DBUS_NAME = 'com.vrplumber.listener.pipeline'
    DBUS_PATH = '/com/vrplumber/listener/pipeline'

    def __init__(self, pipeline):
        self.target = pipeline
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)

    @dbus.service.method(DBUS_NAME)
    def start(self):
        """Start up pipeline for current context"""
        return self.target.pipeline.start_listening()

    @dbus.service.method(DBUS_NAME)
    def stop(self):
        """Shut down pipeline for current context"""
        return self.target.pipeline.stop_listening()

    @dbus.service.method(DBUS_NAME)
    def pause(self):
        """Pause listening (block pipeline)"""
        return self.target.pipeline.pause_listening()

    @dbus.service.method(DBUS_NAME)
    def reset(self):
        """Reset/restart the pipeline"""
        return self.target.pipeline.reset()


class ContextService(dbus.service.Object):
    """Service controlling a particular listener context"""

    # Note: this seems to be "interface name", and apparently
    # needs to be different for each class?
    DBUS_NAME = 'com.vrplumber.listener.context'
    DBUS_PATH = '/com/vrplumber/listener/context'

    def __init__(self, target):
        self.target = target
        self.key = target.context.key
        bus_name = dbus.service.BusName(self.DBUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, self.DBUS_PATH)

    @property
    def context(self):
        return self.target.context

    @dbus.service.method(DBUS_NAME,)
    def delete(self):
        return self.context.delete()

    @dbus.service.method(
        DBUS_NAME, in_signature='s',
    )
    def integrate_project(self, path):
        """Import a project from the given path"""
        return self.context.integrate_project(path)
