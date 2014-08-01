TODO Items for Listener
=======================

* Provide meta-context which relates to the voice service itself

    * `start listening`
    
    * `stop listening`
    
    * `undo that`, `retry that` -- undo last utterance, continue dictating
    
    * `correct that` -- edit the text or interpretation of the last operation

* Provide spelling/correcting/typing context/actions

    * A, B, C
    
    * 1, 2, 3
    
    * Delete/Backspace
    
    * Navigation (Home, End, Left, Right, Word Left, Word Right, Up, Down, etc)

* Provide correct-that behaviour
    
    * will need to recognize `correct that`, switch 
      to the GUI window (or do it in a global pop-up)
      and then use dictation *or* typing context
      
        * the Listener application itself will activate the context
          and let the speech service know we are in-focus...
    
    * during correction, we need to analyze each word for 
      presence in the dictionary and do ARPABet translations 
      if the word is not present, possibly requiring an 
      interaction with the user
    
    * we would really be better to have the user correct to 
      full pronunciation: "all caps H T M L end caps cap builder"
      and then *also* "what should have been typed" (interpretation)

    * so we would have two different text fields, "what was said" and 
      "what we interpreted it as" and the user might edit one, but not 
      the other
      
    * should have button to "retrain" (add to the training repository)
      for each utterance (and particularly when correcting)

* Language model recompilation (unstarted)

* Audio training (started, but never tested)

* Move the `uinput` device into a DBus service with access control to 
  only allow `console` users to access it

* Separate out the "hardware/audio context" from the language model 
  context. If we are on the same hardware we likely want to use and 
  modify/train the same hardware context regardless of which app is 
  currently active 

* Language Model Contexts

    * Language model contexts need to be able to chain to parents such that 
      the context has a corpus which has higher priority than the corpus 
      provided by the parent (e.g. every word and ngram from corpus N gets 
      N*counts) such that if we are in a very specific context (such as a 
      single module) we get a *very* high probability of recognizing names 
      from that context.

    * Add word to dictionary (with ARPABet translations via espeak)
    
        * `listener.ipatoarpabet`
        
        * try N ARPABet translations against the recorded speech to find 
          out which one(s) recognize the actual speech, if none do, we can't 
          recognize it properly...
    
    * Remove word from dictionary
    
    * Context interpretations/actions
    
        * word-sequences with special meaning or non-phonetic pronunciation
        
        * macros, special meanings (e.g. `dunder` for `__name__`)
        
        * spacings (e.g. around parens, commas, etc)
        
        * words that can be run-together, so an identifier of "open_that" could 
          be said "open that" and be recognized
    
* Audio/Hardware/User Training

    * add utterance to training set (they are already stored)
    
    * trigger to re-train the audio model
    
    * eventualy allow for "upload your audio" mechanism
    
* IDE/Editor Interface

    * DBus interface for an editor to provide rich interface for speech
    
        * Activation events (speech-focus)
        
            * GUI tells speech daemon it is active
            
            * And in which context it is active
        
        * Context Definition and Corpus definition
        
            * Automated scanning of codebase to extract phrases and words,
              likely with a base set for each language; potentially producing 
              many possible word-sets for a given identifier where how it would 
              be said is ambiguous
              
                * this has a spike-test in `listener/codetowords.py`
        
            * API for dictionary manipulation
            
                * is the word in the dictionary?
                
                * how could I say `identifier`
                
                * add this to dictionary 
        
        * Rich editing
        
            * undo/redo markers, potentially multi-level corrections
        
        * Vocal tooltip (show partial recognitions over/under current editing cursor)
        
        * Recognition event registration (user said words, you interpret them)?
        
        * Start speech event, Stop speech event (for undo/correction)
        
    * Generic "non-speech-aware" mechanisms
    
        * Possibly X-based for now (window focus, etc), need a Wayland
          story as well
        
        * Uinput driver for typing into arbitrary windows 
    
    * Prototype in either Atom or Eric5 for Python editing

        * on opening a project (git/bzr/hg repository)
        
            * scan the project source code and convert to dictation words
            
            * build a language model from that translation
            
            * layer the project-specific language model onto a 
              generic natural-language model

* GUI Bits

    * Export/Import settings for use on another machine (and backup/restore)
    
        * Requires differentiating between auto-generated and user-edited 
          information

    * Recording level monitoring
    
    * Choice of input/output ALSA devices
    
    * Potentially a "restore volume" mechanism, though that might be best 
      provided at the platform/desktop level

    * System tray icon for bringing up the GUI

* Email Interface Prototype

    * parse a user's (sent) email to get an idea of how they normally speak
    
    * create a sub-context from their contacts' names (guessed pronunciation)
