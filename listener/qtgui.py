"""Qt GUI wrapper"""
import sys,logging,Queue,cgi, os,json, pprint
from . import pipeline, context
try:
    from PySide import (
        QtCore, QtGui, QtWebKit
    )
except ImportError as err:
    from PyQt4 import (
        QtCore, QtGui, QtWebKit
    )
from jinja2 import Environment, FileSystemLoader

HERE = os.path.dirname( __file__ )

TEMPLATE_ENVIRONMENT = Environment( loader=FileSystemLoader(os.path.join( HERE, 'templates')) )
MAIN_PAGE_TEMPLATE = TEMPLATE_ENVIRONMENT.get_template( 'main.html' )

log = logging.getLogger(__name__)

class QtPipelineGenerator( QtCore.QObject ):
    """QObject generating events from the Pipeline"""
    partial = QtCore.Signal(dict)
    final = QtCore.Signal(dict)

class JavascriptBridge( QtCore.QObject ):
    """A QObject that can process clicks"""
    js_event = QtCore.Signal(dict)
    
    @QtCore.Slot(str)
    def send_event( self, event ):
        log.info( 'Received event from javascript' )
        return self.js_event.emit( json.loads(event) )

class QtPipeline(pipeline.Pipeline):
    """Pipeline that sends messages through Qt Events"""
    @property 
    @context.one_shot
    def events( self ):
        return QtPipelineGenerator()
    def send( self, message ):
        if message['type'] == 'partial':
            self.events.partial.emit( message )
        elif message['type'] == 'final':
            self.events.final.emit( message )

class ListenerMain( QtGui.QMainWindow ):
    """Main application window for listener"""
    def __init__( self, *args, **named ):
        super( ListenerMain, self ).__init__( *args, **named )
        self.context = context.Context( 'default' )
        self.pipeline = QtPipeline( self.context )
        self.create_gui()
        self.pipeline.start_listening()
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
        self.listener.active = False 
        QtGui.qApp.quit()
    def create_menus( self ):
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)        
        exitAction.setShortcut('Alt-F4')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.quit)
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
    
    def on_partial( self, record ):
        self.statusBar().showMessage( record['text'] )
    def on_final( self, record ):
        js = '''add_final( %s );'''%(json.dumps( record ))
        self.view_frame.evaluateJavaScript(
            js
        )
#        self.final_results.appendInside(
#            '''<li class="final-result">%s</li>'''%(cgi.escape( record['text']) )
#        )
#        element = self.final_results.lastChild()
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
    
def main():
    logging.basicConfig( level=logging.DEBUG )
    app = QtGui.QApplication(sys.argv)
    
    MainWindow = ListenerMain()
    MainWindow.show()
    
    app.exec_()

if __name__ == "__main__":
    main()
