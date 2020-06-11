"""Utility functions for processing source-code directories into vocabularies"""
from __future__ import absolute_import
from . import tokenizer, ipatoarpabet
from ._bytes import as_unicode
import logging, traceback, os, subprocess, re

log = logging.getLogger(__name__)
DEFAULT_FILENAME_REGEX = '^.*[.](py[xw23]?|htm[l]?|kid)$'

coding_match = re.compile(r'coding[:=]\s*(?P<encoding>[-\w.]+)', re.U | re.I)
# Handling of non-utf-8 encoding schemes...
def text_converter(lines):
    """Convert lines to appropriate format if we find a magic coding statement"""
    encoding = 'ascii'
    for line in lines[:2]:
        match = coding_match.search(line)
        if match:
            encoding = match.group('encoding')
    return [as_unicode(line, encoding) for line in lines]


def iter_translated_lines(files, working_context, **tokenizer_params):
    parser = tokenizer.Tokenizer(working_context.dictionary_cache, **tokenizer_params)
    for filename in files:
        log.info('Translating: %s', filename)
        lines = text_converter(open(filename).readlines())
        try:
            yield parser(lines)
        except Exception:
            log.error('Unable to translate: %s\n%s', filename, traceback.format_exc())
            continue


def iter_unmapped_words(translated, working_context):
    unmapped = set()
    all_words = set()
    for line in translated:
        all_words |= set(line)
    log.info('Checking %s words for transcriptions', len(all_words))
    transcriptions = working_context.transcriptions(sorted(all_words))
    for word, arpa in transcriptions.items():
        if not arpa:
            unmapped.add(word)
    log.info('%s words unmapped', len(unmapped))
    for word in unmapped:
        possible = ipatoarpabet.translate(word)
        for i, pron in enumerate(possible):
            yield word, pron


def get_project_files(directory):
    """Retrieve all files checked into a source-code project"""
    if os.path.exists(os.path.join(directory, '.git')):
        files = subprocess.check_output(['git', 'ls-files'], cwd=directory,)
        files = [os.path.join(directory, f) for f in files.splitlines() if f.strip()]
    elif os.path.exists(os.path.join(directory, '.bzr')):
        files = subprocess.check_output(
            ['bzr', 'ls', '--recursive', '--versioned', directory],
        )
        files = [os.path.join(directory, f) for f in files.splitlines() if f.strip()]
    elif os.path.exists(os.path.join(directory, '.hg')):
        files = [
            [x[6:].strip()]
            for x in subprocess.check_output(['hg', 'manifest', directory])
            .read()
            .splitlines()
            if x[6:].strip()
        ]
    else:
        files = []

        def visit(path, subdirs, files):
            files.extend([os.path.join(directory, path, file) for file in files])

    return files


def get_filtered_files(directory, pattern=DEFAULT_FILENAME_REGEX):
    """Given a vcs directory, list the checked-in python files
    
    pattern -- regex for matching or string (glob matching)
    """
    if not hasattr(pattern, 'match'):
        pattern = re.compile(pattern, re.I | re.U)
    return [name for name in get_project_files(directory) if pattern.match(name)]
