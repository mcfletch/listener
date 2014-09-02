"""Correction dialog for Listener"""
import sys, os
from PySide import QtCore, QtDeclarative
HERE = os.path.dirname( __file__ )

CORRECTION_CONTEXT = 'correction'

class CorrectionView( QtDeclarative.QDeclarativeView ):
    def __init__( self, *args, **named ):
        try:
            self.original =named.pop( 'text' )
        except KeyError as err:
            raise TypeError( "Require a 'text' parameter" )
        super( CorrectionView, self ).__init__( *args, **named )
        self.setSource(QtCore.QUrl(os.path.join( HERE, 'static', 'correction.qml' )))
        self.setResizeMode(QtDeclarative.QDeclarativeView.SizeRootObjectToView)
        self.rootObject().setText( self.original )
        self.rootObject().correctionMade.connect( self.on_correction )
    def on_correction( self, text ):
        print( u'Correction: %s'%( text, ))

