Scratchpad for Pocketsphinx-based Linux Voice Dictation
=======================================================

This repository is a work-space exploring whether pocketsphinx can be used 
to provide a voice dictation solution suitable for use in a programmer's 
editor.

Dependencies::

	apt-get install gstreamer0.10-pocketsphinx build-essential libsphinxbase1 sphinxbase-utils sphinxtrain

python library, use::

or::

	setup.py develop

(requires setuptools/distribute)

What's the Idea?
================

The basic idea is to see if CMU Pocketsphinx (a BSD-licensed continuous 
voice recognition system) can be used to create a programmer's file editor
that uses voice dictation not to eliminate use of the hands, but to allow them
to be used far less by allowing text entry. While editing/navigation/command 
and control will likely be looked at some time, they aren't a priority.

The model is (and this is just a sketch so far):

    * use Pocketsphinx running under gstreamer 
        * we could use pocketsphinx directly, but gstreamer gives us nice 
          features for pre and post-processing the audio if necessary
          however, so far those features don't actually work, at least they 
          don't seem to work wrt storing data etc.
    * record each utterance into ram-disk or the like
        * currently this is being done in the vader component
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
        * may be able to use e.g. espeak --punct -q -x --pho "Hello world!"
          to provide a guess as to the phonemes. A mapping will be required 
          to do that, see http://en.wikipedia.org/wiki/Arpabet
      * plan to allow for "upload your utterances" functionality, so that 
        a user can upload non-private utterances as voice-training data 
        (with the transcription).
    * on opening a project (git/bzr/hg repository)
        * scan the project source code and convert to dictation words
        * build a language model from that translation
        * layer the project-specific language model onto a generic natural-language model
    * apply interpretation at a higher level
        * if there are 10 possible matches, given context, which one would make the most sense?
        * apply "sounds like" filtering to get more possible matches
    * ideally, be able to switch between fine-grained models such that saying "from " would 
      trigger a switch to a new context such that a different sphinx would then process the 
      module name. This is really a fluid set, we want layers of models and the ability to 
      swap them out as context changes (e.g. when you navigate into a method, you want the 
      variables in that method to become very likely dictation targets, with class methods,
      module identifiers etc coming in behind)
        * "identifiers" 
        * classes
        * modules
        
