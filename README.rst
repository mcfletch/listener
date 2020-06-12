Pocketsphinx-based Linux Voice Dictation Service
================================================


Note:
-----


    You likely want `Listener2`_

    This old repository includes the original PocketSphinx based
    implementation, the new repository includes the modern Deep Speech 
    based engine.



The basic idea is to see if `CMU Pocketsphinx`_ (a BSD-licensed continuous 
voice recognition system) can be used to create a voice dictation service 
reasonable enough to be used to drive a programmer's IDE/editor; not to 
completely eliminate the use of hands, but to augment them such that most 
identifiers and common code constructs can be dictated without touching the 
keyboard.

While editing/navigation/command and control will likely be looked at 
some time, they aren't a priority. The basic approach *should* work for any 
dictation task, it is just that the first task I want to work on is the 
one for which I need a solution.

Big Caveats:

 * This is an early stage project
 
    * See `The TODO List`_
    
    * At the moment you can use command-line tools to create a dictation context
      from your code repositories, start a qt-based `Listener` instance and 
      have that dictate into an application that listens on DBus. I've got an
      Eric IDE plugin that works as a client for that DBus service.
    
 * This project is currently English-only (and English-US keyboard only). 
   It would be nice to support other languages, but it is not a priority for me
   
 * This project is Linux-only.I am targetting modern (K)ubuntu desktops.
 
 * The use of pocketsphinx is actually somewhat incidental. While we are using 
   pocketsphinx right now, we should be able to switch out the engine for 
   another at some point with little change to the GUI and services.
   The reason I'm using Pocketsphinx is that it comes nicely packaged under 
   Ubuntu and provides pre-packaged language models for English-US dictation.

.. _`Listener2` : https://github.com/mcfletch/listener2
.. _`The TODO List`: ./TODO.rst
.. _`CMU Pocketsphinx`: http://cmusphinx.sourceforge.net/pocketsphinx

Setup
=====

This is still very much a programmers/contributors only project. That said,
these instructions *should* get you a working setup on a Kubuntu 14.04 
machine.

Dependencies::

    $ apt-get install gstreamer0.10-pocketsphinx build-essential \
        libsphinxbase1 sphinxbase-utils sphinxtrain \
        pocketsphinx-hmm-en-hub4wsj pocketsphinx-utils \
        espeak alsa-utils python-gst0.10 python-gobject-2 \
        python-sqlite build-essential
    
    # for the Qt-based GUI (Note: pyside is LGPL)
    $ apt-get install python-pyside.qtcore python-pyside.qtwebkit python-jinja2

    # for the Desktop service (uinput), currently unimplemented
    $ apt-get install python-dbus

Listener is a python library (using setuptools), use::

    $ git clone https://github.com/mcfletch/listener.git
    $ cd listener
    $ python2.7 setup.py develop --user

to install.

Executables
===========

`listener-context-from-project --context=<name> /path/to/project`

    Uses word extraction to generate a language model (from Python files)
    based on a git checkout.  Creates a new context <name>. With this 
    done you should be able to dictate code as in the project using 
    listener-qt (note: currently you will *not* see the actual code 
    when dictating, you will see commands such as "cap" and "no-space".

`listener-qt --context=<name>`

    Launches the (not-very-useful) Qt Listener GUI. You can dictate and see 
    the results of each dictation. You can also click a button to review the 
    raw audio captured for each utterance. Runs the code from `listener-pipe`
    in a background thread and uses Qt messages to communicate.  Eventually 
    the code from `listener-pipe` should be moved to a DBus service.
    
    Note: this will download a *large* language model on first run. Currently
    that's done *before* the GUI starts, so the process will just seem to hang.

`listener-context-delete --context=<name>`

    Delete a context and all associated data.

`listener-code-to-words-py *.py`

    Attempts to do a code-to-words translation (for building a language model)
    Writes .py.dictation files next to the source files for manual review 
    in order to improve the translations.

`listener-missing-words *.py`

    Performs code-to-words translations and reports all words/tokens not in 
    the default dictionary. This is mostly for use in improving the 
    code to words code.
    
`listener-pipe`

    Attempt to setup a gstreamer pipeline using a downloaded language model 
    that matches the hub4wsj package. 
    The pipeline will store the raw audio of utterances into 
    `~/.config/listener/default/recordings` 
    and print out the partial and final results to the console.

    Note: this will download a *large* language model on first run. Currently
    that's done *before* anything else, so expect a hang.

`listener-rawplay <filename>`

    Plays a raw audio file as output by the listener-pipe into the 
    recording directory (to allow the user to review the content before 
    adding it to their training data-set)

`listener-arpa-guess <words>`

    Prints out the best-guess ARPABet definition for the incoming words,
    these are the things you need to add to a '.dict' file for pocketsphinx,
    generated by extracting correspondences between espeak and the CMU 
    dictionary project data-files.

`listener-uinput-device`

    Test case that tries to do a uinput "send keys like" operation,
    operates at the Linux kernel uinput level, so should work with 
    any environment (in theory it could even work on a console, though 
    I have not tried that).

Internal Utilities 
------------------

These just modify (json) structures that are part of the code-base that 
provide lookup tables used by the code.
    
`listener-uinput-rebuild-mapping`

    Rebuilds the mapping from character to keystrokes. Currently this 
    just reads a kernel header and applies some hand-coded keyboard 
    mappings for a US-english keyboard. Eventually should use users 
    local xkb mappings (including compose keys) to properly map characters.

`listener-ipa-arpa-statmap`

    Re-extract IPA -> ARPABet statistical map, should the algorithm 
    be improved

License
=======

`Listener`'s code is licensed under the BSD license (as is Pocketsphinx). 
You have accepted the licenses for the Ubuntu/Debian packages used by 
installing them above. 

Note that when combined with other software `Listener` may fall under 
more restrictive licenses.

    © 2014, Copyright by VRPlumber Consulting Inc. and the Contributors;
    All Rights Reserved.

    Permission to use, copy, modify, and distribute this software 
    and its documentation for any purpose and without fee or royalty
    is hereby granted, provided that the above copyright notice appear
    in all copies and that both the copyright notice and this 
    permission notice appear in supporting documentation or portions 
    thereof, including modifications, that you make.

    THE AUTHOR VRPlumber Consulting Inc. and the Contributors 
    DISCLAIMS ALL WARRANTIES WITH REGARD
    TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF 
    MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE 
    LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY 
    DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, 
    WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS 
    ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR 
    PERFORMANCE OF THIS SOFTWARE!

`Listener` includes copies of:

    * jQuery v2.1.1 | (c) 2005, 2014 jQuery Foundation, Inc. | 
      http://jquery.org/license
    
    * Pure v0.5.0
      Copyright 2014 Yahoo! Inc. All rights reserved.
      Licensed under the BSD License.
      https://github.com/yui/pure/blob/master/LICENSE.md
    
    * normalize.css v1.1.3 | MIT License | http://git.io/normalize
      Copyright (c) Nicolas Gallagher and Jonathan Neal

	* pysideqtsingleapplication | BSD 2-Clause License
	  http://stackoverflow.com/questions/12712360/qtsingleapplication-for-pyside-or-pyqt

`Listener` will download the following software/models when run:

    * `CMU HUB4 Language Model`_ -- which provides a few extra files that 
      are needed to update/modify the acoustic model over the files distributed 
      in the Ubuntu repository
    
    * `CMU CLM TK`_ -- which provides the command line tools required to 
      update a language model for use with Sphinx

.. _`CMU HUB4 Language Model`: https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4WSJ%20Acoustic%20Model/hub4wsj_sc_8k.tar.gz/download
.. _`CMU CLM TK`: https://downloads.sourceforge.net/project/cmusphinx/cmuclmtk/0.7/cmuclmtk-0.7.tar.gz?r=&ts=1407260026&use_mirror=hivelocity
