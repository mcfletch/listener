#! /usr/bin/env python
"""Spike test for using an app-sink to get raw data"""
import sys, os, logging, pprint, time
import pygst
pygst.require("0.10")
import gst
import gobject
import Queue
import numpy
from numpy.fft import fft
from listener import sourcedescription

log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )

def main(url):
    gobject.threads_init()
    source = sourcedescription.SourceDescription(url)
    pipeline_command = source.gst_fragment() + [
        'audioconvert', '!',
        'audioresample', '!',
        'audio/x-raw-int,width=16,depth=16,channels=1,rate=8000', '!',
        #'autoaudiosink',
        'appsink',
            'name=app',
            'enable-last-buffer=true',
            'emit-signals=true',
            'sync=true',
    ]
    command = " ".join( pipeline_command )
    pipeline = gst.parse_launch(command)
    app = pipeline.get_by_name( 'app' )
    def on_new_buffer( appsink ):
        buf = appsink.get_property('last-buffer')
        buf = numpy.frombuffer( buf.data, numpy.int16 )
        #print( fft( buf ))
        #print( buf )
        return False
    app.connect('new-buffer',on_new_buffer )

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    source.EOS = False
    mainloop = gobject.MainLoop()
    def on_message(bus, message):
        if message.type == gst.MESSAGE_EOS:
            source.EOS = True
            pipeline.set_state(gst.STATE_NULL)
            mainloop.quit()
    bus.connect( "message", on_message )

    pipeline.set_state(gst.STATE_PAUSED)
    pipeline.set_state(gst.STATE_PLAYING)
    mainloop.run()

if __name__ == "__main__":
    filename = os.path.abspath(
        os.path.join( HERE, '../tests/fixtures/hello_world.wav' )
    )
    main( 'file://'+filename )
