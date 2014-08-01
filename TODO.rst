TODO Items for Listener
=======================

The model is (and this is just a sketch so far):

    * use Pocketsphinx running under gstreamer 
    
        * we could use pocketsphinx directly, but gstreamer gives us nice 
          features for pre and post-processing the audio if necessary
          however, so far those features don't actually work, at least they 
          don't seem to work wrt storing data etc.

    * record each utterance into ram-disk (or disk)
    
        * currently this is being done in the vader component
          and is just being dumped to home directory rather than ram disk
    
    * provide "correct that" style training/grammar updates
    
        * use the already-uttered sound-file to do the training
        * train acousticly *and* update language model 
        * acoustic training relies on have a reliable transcription
        * transcription requires that each "word" be in the dictionary with 
          phonetic translation
          
            * when new words are encountered we will need to help the user 
              convert them to phonetics (preferably without their needing to 
              work with the phonetic alphabet in the normal case, but allowing 
              them to see what is being used and override/fix it when necessary)
            * code is written to allow for use of espeak phonetic output to 
              produce loose ARPABet translations
        
        * plan to allow for "upload your utterances" functionality, so that 
          a user can upload non-private utterances as voice-training data 
          (with the transcription).
    
    * on opening a project (git/bzr/hg repository)
        * scan the project source code and convert to dictation words
        * build a language model from that translation
        * layer the project-specific language model onto a generic natural-language model
    
    * similarly, allow for e.g. "read my mail" functionality so that we can parse a 
      user's (sent) email to get an idea of how they normally speak
    
    * apply interpretation at a higher level
    
        * if there are 10 possible matches, given context, which one would make the most sense?
        * apply "sounds like" filtering to get more possible matches? (hopefully not required)
        
    * ideally, be able to switch between fine-grained models such that saying "from " would 
      trigger a switch to a new context such that a different sphinx would then process the 
      module name. This is really a fluid set, we want layers of models and the ability to 
      swap them out as context changes (e.g. when you navigate into a method, you want the 
      variables in that method to become very likely dictation targets, with class methods,
      module identifiers etc coming in behind)
      
        * "identifiers" 
        * classes
        * modules
    
    * possibly figure out how to include the "context" in the model when processing hmms,
      such that sphinx could see context as a known-state value in the HMM?
    
    * Recording level is *very* important for pocketsphinx; 
      too loud and you'll have an infinitely long 
      utterance where every bit of background is considered speech; too soft 
      and you'll just get random junk where only the loudest bits of speech 
      are processed.
      
        * Need to provide volume control as part of the setup/checking,
          possibly even include a "say nothing for a moment, now say this" setup 
          so that we can dynamically adjust to messy environments
