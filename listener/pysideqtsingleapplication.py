"""Implementation of QtSingleApplication for Pyside

Released under the BSD 2-clause license by:

    http://stackoverflow.com/users/763305/user763305

Here:

    http://stackoverflow.com/questions/12712360/qtsingleapplication-for-pyside-or-pyqt
"""
from __future__ import absolute_import
import logging
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

log = logging.getLogger(__name__)


class QtSingleApplication(QApplication):

    messageReceived = Signal(unicode)

    def __init__(self, id, *argv):

        super(QtSingleApplication, self).__init__(*argv)
        self._id = id
        self._activationWindow = None
        self._activateOnMessage = False

        # Is there another instance running?
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._id)
        self._isRunning = self._outSocket.waitForConnected()

        if self._isRunning:
            # Yes, there is.
            self._outStream = QTextStream(self._outSocket)
            self._outStream.setCodec('UTF-8')
        else:
            # No, there isn't.
            self._outSocket = None
            self._outStream = None
            self._inSocket = None
            self._inStream = None
            self._server = QLocalServer()
            self._server.listen(self._id)
            self._server.newConnection.connect(self._onNewConnection)

    def isRunning(self):
        return self._isRunning

    def id(self):
        return self._id

    def activationWindow(self):
        return self._activationWindow

    def setActivationWindow(self, activationWindow, activateOnMessage=True):
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self):
        if not self._activationWindow:
            log.info("No registered ActivationWindow")
            return
        # Unfortunately this *doesn't* do much of any use, as it won't
        # bring the window to the foreground under KDE... sigh.
        self._activationWindow.setWindowState(
            self._activationWindow.windowState() & ~Qt.WindowMinimized
        )
        self._activationWindow.raise_()
        self._activationWindow.activateWindow()

    def sendMessage(self, msg, msecs=5000):
        if not self._outStream:
            return False
        self._outStream << msg << '\n'
        if not self._outSocket.waitForBytesWritten(msecs):
            raise RuntimeError("Bytes not written within %ss" % (msecs / 1000.0))

    def _onNewConnection(self):
        if self._inSocket:
            self._inSocket.readyRead.disconnect(self._onReadyRead)
        self._inSocket = self._server.nextPendingConnection()
        if not self._inSocket:
            return
        self._inStream = QTextStream(self._inSocket)
        self._inStream.setCodec('UTF-8')
        self._inSocket.readyRead.connect(self._onReadyRead)
        if self._activateOnMessage:
            self.activateWindow()

    def _onReadyRead(self):
        while True:
            msg = self._inStream.readLine()
            if not msg:
                break
            log.info("Message received")
            self.messageReceived.emit(msg)
