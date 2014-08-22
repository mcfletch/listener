import os, urlparse

class SourceDescription( object ):
    def __init__( self, url ):
        self.url = urlparse.urlparse( url )
    @property 
    def continuous( self ):
        return self.url.scheme in ('alsa','pulse')
    def gst_fragment( self ):
        if self.url.scheme in ('file',''):
            source = [
                'filesrc',
                    'name=source',
                    'location=%s'%(self.url.path,),
                '!',
            ]
            name = os.path.basename( self.url.path )
            if name.endswith( '.opus' ):
                source += [
                    'opusdec',
                    '!',
                ]
            elif name.endswith( '.raw' ):
                source += [
                    'audioparse',
                        'width=16','depth=16',
                        'signed=true',
                        'rate=8000',
                        'channels=1',
                        '!',
                ]
            elif name.endswith( '.wav' ):
                source += [
                    'wavparse',
                        '!',
                ]
            else:
                raise ValueError(
                    "Unknown source type: %s"%( name, )
                )
            return source 
        elif self.url.scheme == 'alsa':
            return [
                'alsasrc', 
                    'name=source', 
                    'device=%s'%(self.url.netloc),
                    #'device=hw:2,0', # setting somewhere or other...                
                '!',
            ]
        elif self.url.scheme == 'pulse':
            return [
                'pulsesrc',
                    'name=source',
                    'device=%s'%(self.url.netloc),
                '!',
            ]
        else:
            raise ValueError(
                "Unsupported source protocol (file/alsa only at the moment): %r"%(
                    self.url.scheme,
                )
            )
