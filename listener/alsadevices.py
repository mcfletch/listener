"""Extract alsa hardware device descriptions/ids from arecord/aplay"""
from __future__ import absolute_import
from __future__ import print_function
import subprocess, re, logging, json
log = logging.getLogger( __name__ )

CARD_MATCH = re.compile(r'card (?P<card>\d+)[:].*?[[](?P<description>.*?)[]], device (?P<device>\d+)[:].*?[[](?P<device_description>.*?)[]]' )

def get_inputs( ):
    """Get alsa inputs (relies on having arecord present)"""
    output = subprocess.check_output( ['arecord','-l'] )
    cards = [line for line in output.splitlines() if line.startswith( 'card ' )]
    results = [
        ('Use Default','default'),
    ]
    for line in cards:
        match = CARD_MATCH.match( line )
        if match:
            description = '%(description)s: %(device_description)s'%match.groupdict()
            device = 'hw:%(card)s,%(device)s'%match.groupdict()
            results.append( (description,device) )
    return results 

def get_outputs( ):
    output = subprocess.check_output( ['aplay','-l'] )
    cards = [line for line in output.splitlines() if line.startswith( 'card ' )]
    results = [
        ('Use Default','default'),
    ]
    for line in cards:
        match = CARD_MATCH.match( line )
        if match:
            description = '%(description)s: %(device_description)s'%match.groupdict()
            device = 'hw:%(card)s,%(device)s'%match.groupdict()
            results.append( (description,device) )
    return results 
    

if __name__ == "__main__":
    print(json.dumps( get_inputs()))
    print(json.dumps( get_outputs()))
        
