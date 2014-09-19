TODO Items for Listener
=======================

* Voice dictation accurracy is pretty lousy
    
    * we are *not* getting the N-best results from pocketsphinx, so we 
      wind up just having to accept the result we got or explicitly 
      try to fix it
    
    * we don't have any access to words not in the corpus, and it is 
      essentially impossible to convince the dictation to recognize 
      a new combination of words, for instance, you basically cannot 
      get the recognizer to recognize ",comma" at the start of an 
      utterance, though it recognizes it perfectly well elsewhere
      
    * likely this needs to be correction/training fixes, and in 
      particular likely need to have *every* utterance
      (and its correction) saved in order to update the auto-extracted
      language model with real-world usage
    
    * tokenizer needs to be updated to produce utterances closer to what 
      the interpreter now allows (e.g. dunder new dunder is now sufficient,
      don't need a lot of no-space statements).

* Interpretation needs a lot more finesse

    * need to be able to create separate utterances from an original
    
    * need to have facilities for command-and-control operation
    
    * need to have context-aware interpretation aware (i.e. only apply in HTML context)
    
    * still seeing bugs where e.g. numbers aren't getting their space preserved when 
      next to text `this 3that` instead of `this 3 that`
    
    * need a way to say `spell out three` so that we can get the non-numeric representation

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

    * type A  B  C 
    
    * type ARABIC LETTER REH (unicodedata db search for name)
    
    * type GREEK CAPITAL LETTER PI
    
    * 1, 2, 3
    
    * Delete/Backspace
    
    * Navigation (Home, End, Left, Right, Word Left, Word Right, Up, Down, etc)
    
    * Unicode support requires ~16,000 words, many of them short/simple and likely 
      to be too close to english words, need to do some experimentation there or see 
      if we want a wholely different pipeline for "typing" context

* Provide correct-that behaviour
    
    * will need to recognize `correct that`, switch 
      to the GUI window (or do it in a global pop-up)
      and then use dictation *or* typing context
      
        * the Listener application itself will activate the context
          and let the speech service know we are in-focus...
    
    * also need `undo that`, `scratch that`, etc.
    
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

    * defaults to `default` so out of the box it is system/pulseaudio controlled

* Move the `uinput` device into a (system) DBus service with access 
  control to only allow `console` users to access it (access control file 
  already written, but packaging is needed)
  
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
    
* Audio/Hardware/User Training [defer]

    * add utterance to training set (they are already stored)
    
    * trigger to re-train the audio model
    
    * eventualy allow for "upload your audio" mechanism
    
* IDE/Editor Interface

    * DBus interface for an editor to provide rich interface for speech
    
        * Activation events (speech-focus)
        
            * GUI tells speech daemon it is active
            
            * And in which context it is active
        
        * Context Definition and Corpus definition
        
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
    
    * Prototype in Eric5 for Python editing

        * on opening a project (git/bzr/hg repository)
        
            * scan the project source code and convert to dictation words
            
            * build a language model from that translation
            
            * layer the project-specific language model onto a 
              generic natural-language model

* GUI Controls/Setup

    * Eliminate use of HTML control, i.e. create native Qt controls for 
      everything
    
    * Contexts

        * Switch contexts
    
        * Add directory to context 
        
        * Context delete
        
        * Recompile context (should be automatic)
    
    * Edit dictionary/context words 
    
        * Define "actions" based on dictated words
        
            * Maybe allow for ways to recognize the results, or do we just 
              record the result of each one in statements in our language 
              model?
            
        * Edit punctuation rules for given dictation words/phrases
        
        * Add corrected word to dictionary 

    * Export/Import settings for use on another machine (and backup/restore)
    
        * Requires differentiating between auto-generated and user-edited 
          information

    * Choice of input/output ALSA devices
    
    * Potentially a "restore volume" mechanism, though that might be best 
      provided at the platform/desktop level

    * System tray icon for bringing up the GUI
    
    * Raw-file playout is currently happening in the GUI thread

* Email Interface Prototype

    * parse a user's (sent) email to get an idea of how they normally speak
    
    * create a context from their contacts' names (guessed pronunciation)

* Investigate whether we could use e.g. laptop mikes to do noise cancelling 
  (i.e. subtract the signals such that the delta between the boom-mic and the 
  ambient mic is what we feed to pocketsphinx)

.. _Opus: http://www.opus-codec.org/
