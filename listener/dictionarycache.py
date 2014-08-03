"""SQLite DB with Word - ArpaBet correspondences"""
import sqlite3
import os
import logging
from .oneshot import one_shot
log = logging.getLogger( __name__ )

class DictionaryDB( object ):
    def __init__( self, context ):
        self.context = context 
    
    @one_shot
    def filename( self ):
        return self.context.dictionary_file + '.sqlite' 
    
    @one_shot
    def connection( self ):
        if not os.path.exists( self.filename ):
            return self.initialize(sqlite3.connect( self.filename ))
        return sqlite3.connect( self.filename )
    
    DATABASE_CREATION = [
    """CREATE TABLE IF NOT EXISTS dictionary( word text NOT NULL, arpa text, ipa text )""",
    """CREATE INDEX IF NOT EXISTS dictionary_words ON dictionary( word )""",
    """CREATE INDEX IF NOT EXISTS dictionary_arpa ON dictionary( arpa )""",
    """CREATE INDEX IF NOT EXISTS dictionary_ipa ON dictionary( ipa )""",
    ]
    
    def dictionary_iterator( self, dictionary_file ):
        for i,line in enumerate(open(dictionary_file)):
            word,description = line.strip().split('\t',1)
            if word.endswith(')'):
                word = word.rsplit('(',1)[0]
            yield word,description

    def initialize( self, connection ):
        log.warn( 'Creating dictionary cache, may take a few seconds' )
        cursor = connection.cursor()
        for statement in self.DATABASE_CREATION:
            cursor.execute( statement )
        cursor.close()
        self.add_dictionary_file( self.context.dictionary_file )
        log.warn( 'Dictionary cache created' )
        return connection
    
    def add_dictionary_file( self, dictionary_file ):
        connection = self.connection
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO dictionary( word, arpa ) VALUES (?,?)",
            self.dictionary_iterator( dictionary_file ),
        )
        connection.commit()
    
    def have_words( self, *words ):
        """For each word in word, report all arpa values for them"""
        cursor = self.connection.cursor()
        results = {}
        for word in words:
            results[word] = []
            cursor.execute( 
                "SELECT arpa from dictionary where word LIKE ?",
                [word],
            )
            for row in cursor.fetchall():
                results[word].append( row[0] )
        return results
    
    

def main():
    from . import context 
    c = context.Context('default')
    db = DictionaryDB( c )
    print db.have_words( 'abductee','two','too','to' )
    db.connection.close()
