"""Qt GUI wrapper"""
import sys,logging,Queue
from . import pipeline, context
try:
    from PySide import QtCore, QtGui
except ImportError as err:
    from PyQt4 import QtCore, QtGui
log = logging.getLogger(__name__)

class BackgroundListener(QtCore.QThread):
    """Need a command to re-train based on recordings-to-date:
    
    """
    active = True
    loading = True
    def run(self):
        """Create the GStreamer Pipeline with the PocketSphinx listener"""
        self.context = context.Context( 'default' )
        self.loading = False
        self.pipeline = pipeline.Pipeline(self.context)
        self.pipeline.start_listening()
        while self.active:
            try:
                message = self.pipeline.queue.get(True,1)
            except Queue.Empty as err:
                pass 
            else:
                log.info( 'Got message: %s', message )

class ListenerMain( QtGui.QMainWindow ):
    """Main application window for listener"""
    def __init__( self, *args, **named ):
        super( ListenerMain, self ).__init__( *args, **named )
        self.listener = BackgroundListener()
        self.listener.start()
        self.create_gui()
    def create_gui( self ):
        self.setWindowTitle( 'Listener' )
        self.statusBar().showMessage( 'Initializing the context' )
        self.create_menus()
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
                
def main():
    logging.basicConfig( level=logging.DEBUG )
    app = QtGui.QApplication(sys.argv)
    
    MainWindow = ListenerMain()
    MainWindow.show()
    
    app.exec_()

if __name__ == "__main__":
    main()
