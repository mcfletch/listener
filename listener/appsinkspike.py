#! /usr/bin/env python
"""Spike test for using an app-sink to get raw data"""
import sys, os, logging
import pygst
pygst.require("0.10")
import gst
import gobject
import numpy
from numpy.fft import fft, fftfreq

log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )

def main(filename=os.path.join( HERE, '../tests/fixtures/hello_world.wav' )):
    gobject.threads_init()
    pipeline_command = [
        'filesrc',
            'location=%s'%(filename,),
            '!',
        'decodebin2', '!',
        'audioconvert', '!',
        'audioresample', '!',
        'audio/x-raw-int,width=16,depth=16,channels=1,rate=8000', '!',
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
        # TODO: why doesn't on_new_buffer give us the 
        # gst.Buf object? here we're using the last-buffer, 
        # but that's not thread-safe
        buf = appsink.get_property('last-buffer')
        buf = numpy.frombuffer( buf.data, numpy.int16 )
        # Example of doing something on the data, though 
        # in a real app you'd combine the data on longer 
        # time-scales such that you would see patterns 
        # at the phoneme scale I suppose
        raw = fft( buf )
        frequencies = raw[:int(len(raw)/2)]
        mags = numpy.round(numpy.absolute( frequencies ),0).astype('i')
        #max_bucket = (len(raw)/2-1)/(len(raw)/8000.)
        
        freqs = fftfreq( len(buf), d=(1/8000.))[:len(mags)]
        mapped = zip([int(x) for x in mags],[int(y) for y in freqs])
        mapped = sorted(mapped)
        mapped = mapped[-10:]
        for mag,freq in mapped:
            print '%s - %s'%(freq, mag)
        print
    app.connect('new-buffer',on_new_buffer )

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    mainloop = gobject.MainLoop()
    def on_message(bus, message):
        if message.type == gst.MESSAGE_EOS:
            pipeline.set_state(gst.STATE_NULL)
            mainloop.quit()
    bus.connect( "message", on_message )

    pipeline.set_state(gst.STATE_PAUSED)
    pipeline.set_state(gst.STATE_PLAYING)
    mainloop.run()

if __name__ == "__main__":
    main( *sys.argv[1:] )
