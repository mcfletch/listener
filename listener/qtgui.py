"""Qt GUI wrapper"""
import logging,os,json, pprint, math, sys
from . import pipeline, context
from . import service
from .oneshot import one_shot
try:
    from PySide import (
        QtCore, QtGui, QtWebKit
    )
except ImportError as err:
    from PyQt4 import (
        QtCore, QtGui, QtWebKit
    )
from jinja2 import Environment, FileSystemLoader
import dbus
import dbus.service
import dbus.mainloop.glib

if hasattr( QtGui,  'QtSingleApplication'):
    QtSingleApplication = QtGui.QtSingleApplication
else:
    from . import pysideqtsingleapplication
    QtSingleApplication = pysideqtsingleapplication.QtSingleApplication


HERE = os.path.dirname( __file__ )

TEMPLATE_ENVIRONMENT = Environment( loader=FileSystemLoader(os.path.join( HERE, 'templates')) )
MAIN_PAGE_TEMPLATE = TEMPLATE_ENVIRONMENT.get_template( 'main.html' )

log = logging.getLogger(__name__)

class QtPipelineGenerator( QtCore.QObject ):
    """QObject generating events from the Pipeline"""
    partial = QtCore.Signal(dict)
    final = QtCore.Signal(dict)
    level = QtCore.Signal(dict)

class JavascriptBridge( QtCore.QObject ):
    """A QObject that can process clicks"""
    js_event = QtCore.Signal(dict)
    
    @QtCore.Slot(str)
    def send_event( self, event ):
        log.info( 'Received event from javascript' )
        return self.js_event.emit( json.loads(event) )

class QtPipeline(pipeline.Pipeline):
    """Pipeline that sends messages through Qt Events"""
    @one_shot
    def events( self ):
        return QtPipelineGenerator()
    def send( self, message ):
        event = getattr( self.events, message['type'],None)
        if event:
            event.emit( message )

class ListenerMain( QtGui.QMainWindow ):
    """Main application window for listener"""
    def __init__( self, *args, **named ):
        command_line_arguments = named.pop('arguments',None)
        super( ListenerMain, self ).__init__( *args, **named )
        self.context = context.Context( getattr(
            command_line_arguments,'context','default'
        ) )
        self.interpreter = self.context.interpreter('default')
        self.pipeline = QtPipeline( self.context )
        self.create_gui()
        self.create_systray()
        self.pipeline.start_listening()
        self.proxy = self.create_proxy()
    def create_proxy(self):
        """Create our DBus Service (proxy) instance"""
        return service.ListenerService(self)
    def create_gui( self ):
        self.setWindowTitle( 'Listener' )
        self.statusBar().showMessage( 'Initializing the context' )
        self.create_menus()
        
        QtWebKit.QWebSettings.globalSettings().setAttribute(
            QtWebKit.QWebSettings.DeveloperExtrasEnabled, True
        )
        self.view = QtWebKit.QWebView(self)
        self.view_frame.baseURL = 'file://'+os.path.abspath(os.path.join( HERE ))
        self.view.setHtml( self.main_view_html() )
        
        self.main_html = self.element_by_selector( 'div.main-view' )
        self.final_results = self.element_by_selector( '.final-results' )
        
        self.view_frame.javaScriptWindowObjectCleared.connect(
            self.add_gui_bridge
        )
        
        self.setCentralWidget( self.view )
        
        self.view.show()
        
        self.pipeline.events.partial.connect( self.on_partial )
        self.pipeline.events.final.connect( self.on_final )
        self.pipeline.events.level.connect( self.on_level )
    def create_systray( self ):
        self.systray = QtGui.QSystemTrayIcon()
        self.systray.setToolTip( 'Listener Voice-Coding' )
        self.systray.setIcon( QtGui.QIcon.fromTheme('media-playback-stop'))
        self.systray.show()
        self.systray.activated.connect( self.on_systray )
    
    @property
    def view_frame( self ):
        return self.view.page().mainFrame()
    def elements_by_selector( self, selector ):
        return self.view_frame.findAllElements( selector )
    def element_by_selector( self, selector ):
        return self.view_frame.findFirstElement( selector )
        
    def main_view_html( self ):
        return MAIN_PAGE_TEMPLATE.render( 
            view = self,
            HERE = os.path.abspath( HERE ),
        )
    def quit( self, *args ):
        self.pipeline.close()
        QtGui.qApp.quit()
    def create_menus( self ):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        
        chooseAction = QtGui.QAction('&Microphone', self)
        chooseAction.setStatusTip('Choose the ALSA microphone to use')
        chooseAction.triggered.connect(self.on_choose_input)
        fileMenu.addAction(chooseAction)
        
        chooseAction = QtGui.QAction('&Speaker', self)
        chooseAction.setStatusTip('Choose the ALSA speaker to use')
        chooseAction.triggered.connect(self.on_choose_output)
        fileMenu.addAction(chooseAction)
        
        testCorrection = QtGui.QAction('&Test Correction', self)
        testCorrection.triggered.connect(self.on_correction)
        fileMenu.addAction(testCorrection)
        
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), 'E&xit', self)        
        exitAction.setShortcut('Alt-F4')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.quit)
        fileMenu.addAction(exitAction)
    
    ZERO_LEVEL_AUDIO = math.log( 60 )
    FULL_LEVEL_AUDIO = math.log( 20 )
    def on_level( self, record ):
        """Interpret recording level in manner useful to user...
        
        Really need to get this to be a useful tool; basically it 
        *seems* like the pocketsphinx stuff works fine with full-volume
        input, but in noisy environments the vader won't pick up the 
        end of the utterance
        """
        intensity = math.log( abs(record['level']))
        intensity = (intensity - self.ZERO_LEVEL_AUDIO)/(self.FULL_LEVEL_AUDIO-self.ZERO_LEVEL_AUDIO)
        translated = min((1.0,max((0,intensity))))
        js = 'recording_level( %f )'%(translated,)
        self.view_frame.evaluateJavaScript(
            js
        )
    
    def on_partial( self, record ):
        for record in self.interpreter( record ):
            self.statusBar().showMessage( record['interpreted'] )
            self.proxy.send_partial( record['interpreted'], record['text'],  record['uttid'] )
    def on_final( self, record ):
        for record in self.interpreter( record ):
            js = '''add_final( %s );'''%(json.dumps( record ))
            self.view_frame.evaluateJavaScript(
                js
            )
            self.systray.showMessage( 'Recognized', record['interpreted'] , msecs=500 )
            self.proxy.send_final( record['interpreted'], record['text'],  record['uttid'] )

    def on_systray( self, reason ):
        if self.pipeline.running:
            self.pipeline.stop_listening()
            self.systray.setIcon( QtGui.QIcon.fromTheme('media-record'))
            self.systray.showMessage( "Listener", "Shut down Listener Pipeline, click to re-start" )
        else:
            self.pipeline.start_listening()
            self.systray.setIcon( QtGui.QIcon.fromTheme('media-playback-stop'))
            self.systray.showMessage( "Listener", "Restarted Listener Pipeline for %s, click to stop"%( self.context.key,) )
        return False

    @QtCore.Slot()
    def add_gui_bridge( self ):
        self.bridge = JavascriptBridge()
        self.bridge.js_event.connect( self.on_js_event )
        self.view_frame.addToJavaScriptWindowObject(
            "gui_bridge",
            self.bridge,
        )
    @QtCore.Slot()
    def on_js_event( self, event ):
        log.info( 'Received event from javascript: %s', event )
        if event['action'] == 'listen':
            record = event['record']
            if record['files']:
                for file in record['files']:
                    log.info( 'Playing file %s', file )
                    self.context.rawplay( file )
            else:
                log.error( 'No files were present: %s', pprint.pformat(event))
        else:
            log.info( 'Unrecognized action: %s', pprint.pformat( event ))
    
    def on_choose_input( self, event=None ):
        def update_input( choice ):
            self.pipeline.reset( )
        return self.on_choose_alsa_device( 'input', update_input )
    def on_choose_output( self, event=None ):
        return self.on_choose_alsa_device( 'output', None )
    
    def on_choose_alsa_device( self, key='input', updater=None ):
        current = self.context.audio_context().settings['%s_device'%(key,)]
        choices = self.context.available_alsa_devices()[key]
        current_index = 0
        for i,(label,name) in enumerate(choices):
            if name == current:
                current_index = i
        if key == 'input':
            title,label = "Choose Input Microphone", "ALSA Microphone"
        else:
            title,label = "Choose Output Speaker", "ALSA Speaker"
        item,ok = QtGui.QInputDialog.getItem(
            self,
            title,
            label,
            [l for l,name in choices],
            current=current_index,
            editable=False,
            ok=True,
        )
        if ok:
            choice = None
            for label,name in choices:
                if item == label:
                    if name != current:
                        choice = name
                        log.info( 'Chose device: %s (%s)', label, name )
                        self.pipeline.audio_context.update_settings({
                            '%s_device'%(key,): choice,
                        })
                        if updater:
                            updater( choice )
                    else:
                        log.info( 'Chose the current device, ignoring' )
    def on_correction( self, event=None ):
        from . import correction 
        dialog = QtGui.QDialog( parent = self )
        view = correction.CorrectionView( parent=dialog, text='Moo' )
        view.setGeometry(0,0,dialog.width(), dialog.height())
        view.setMinimumSize(400,200)
        #dialog.setCentralWidget( view )
        dialog.setMinimumSize(450,250)
        dialog.show()
    
def main(arguments):
    app = QtSingleApplication("Listener GUI", sys.argv)
    if app.isRunning():
        log.error("Another Listener instance is running, exiting")
        return 0
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    MainWindow = ListenerMain(arguments=arguments)
    MainWindow.show()
    app.setActivationWindow( MainWindow )
    app.exec_()
