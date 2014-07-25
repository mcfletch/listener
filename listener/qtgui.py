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
    def run(self):
        """Create the GStreamer Pipeline with the PocketSphinx listener"""
        self.context = context.Context( 'default' )
        self.pipeline = pipeline.Pipeline(self.context)
        self.pipeline.start_listening()
        while self.active:
            try:
                message = self.pipeline.queue.get(True,1)
            except Queue.Empty as err:
                pass 
            else:
                log.info( 'Got message: %s', message )

def main():
    logging.basicConfig( level=logging.DEBUG )
    app = QtGui.QApplication(sys.argv)
    bl = BackgroundListener()
    bl.start()
    
    MainWindow = QtGui.QMainWindow()
    MainWindow.show()
    MainWindow.setWindowTitle( 'Listener' )
    MainWindow.show()    
    
    app.exec_()

if __name__ == "__main__":
    main()
