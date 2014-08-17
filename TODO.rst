TODO Items for Listener
=======================

* Voice dictation accurracy is pretty lousy
    
    * with a `listener-context-from-project` we get reasonable accurracy
      picking up words that are in the project, but there are a *lot* 
      of stray "junk" words showing up in between the words spoken
      
      * this *might* just be a volume issue?
      
      * investigate whether there are knobs to reduce this when dealing with 
        non-transcription modes of operation
    
    * we are *not* getting the N-best results from pocketsphinx, so we 
      wind up just having to accept the result we got or explicitly 
      try to fix it 

* Vocabulary Hinting, Commands and Actions

    * open-quote -> 'space' + " + 'no space after'
    
    * close-quote -> " + maybe space after
    
    * "context commands" -> change interpretation context until an 
      exit from that context
      
    * needs to feed into statistical model (HMM) for the tokenizer to 
      decide how to split up "run together" words...

* Language model recompilation

    * is now (loosely) working 
    
    * need to use a *lot* more repositories in initial word-set
    
    * probably should just directly generate N-grams while processing the 
      files, as all we do is feed them to the language-model compilation 
      process
    
    * .vocab files *must* include all words in the vocabulary, we should 
      likely put our words in without use of fake statements


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

* Audio training http://cmusphinx.sourceforge.net/wiki/tutorialadapt

    * Provide an explicit training process to start
    
        * User reads prepared corpus
        
        * Preferably we run a *very* tightly limited language model that 
          *just* recognizes the words in each sentence so that we can detect
          that the user is reading each word (provide visual feedback that 
          the user's words were recognized)
        
        * Preferably be able to let the user pause/rest while doing the reading 
          such that they don't have to constantly re-start the sentence 
        
    * Once we have the prepared corpus, run the audio training process (started)
    
    * Allow for user's utterances to be used as further training data
    
        * Basically as the user uses the system, record the audio such that they 
          can train automatically going forward...
          
        * investigate whether we could encode with e.g. Opus_ to compress the 
          results (especially if we're going to save-by-default for every 
          corrected sentance)

* Use `alsadevices` to let user choose which input and output devices to use 

    * store that in audio-context storage
    
    * gui control, preferably one that is populated on interaction to allow 
      for plugging in new hardware
    
    * defaults to `default` so out of the box it is system/pulseaudio controlled

* Move the `uinput` device into a (system) DBus service with access 
  control to only allow `console` users to access it (access control file 
  already written, but packaging is needed)
  
* Move the audio pipes and context management into a Session DBus service
  to decouple it and make it easy for other processes to access it

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
    
    * GUI for per-app context editing
    
    * Potentially a "restore volume" mechanism, though that might be best 
      provided at the platform/desktop level

    * System tray icon for bringing up the GUI
    
    * Eliminate use of HTML control, i.e. create native Qt controls for 
      everything
    
    * Raw-file playout is currently happening in the GUI thread

* Email Interface Prototype

    * parse a user's (sent) email to get an idea of how they normally speak
    
    * create a context from their contacts' names (guessed pronunciation)

* Investigate whether we could use e.g. laptop mikes to do noise cancelling 
  (i.e. subtract the signals such that the delta between the boom-mic and the 
  ambient mic is what we feed to pocketsphinx)

.. _Opus: http://www.opus-codec.org/
