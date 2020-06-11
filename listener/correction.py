"""Correction dialog for Listener"""
from __future__ import absolute_import
from __future__ import print_function
import sys, os
from PySide import QtCore, QtGui
HERE = os.path.dirname( __file__ )

CORRECTION_CONTEXT = 'correction'

class CorrectionView( QtGui.QWidget ):
    def __init__( self, *args, **named ):
        try:
            self.original =named.pop( 'text' )
        except KeyError as err:
            raise TypeError( "Require a 'text' parameter" )
        super( CorrectionView, self ).__init__( *args, **named )
        self.create_gui()
    def on_correction( self, text ):
        print(( u'Correction: %s'%( text, )))
    def create_gui( self ):
        """Create our GUI components and wire them up"""
        layout = QtGui.QFormLayout(parent=self)
        layout.addRow( u"Recognized Text", QtGui.QLabel( self.original ))
        layout.addRow( u"Correction", QtGui.QLineEdit( text=self.original ))
        layout.addRow( u"Interpretation", QtGui.QLineEdit( text=self.original ))
        self.setLayout( layout )
    def sizeHint( self ):
        print('Using size hint')
        return QtCore.QSize( 400,250 )
    def minimumSize( self ):
        return QtCore.QSize( 400,250 )
        
