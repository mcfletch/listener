#! /usr/bin/env python
"""Stupid script to build up a language model from *my* projects"""
import os, logging
from subprocess import check_call

log = logging.getLogger(__name__)


def main(context='python'):
    check_call(['listener-context-delete', '--context', context])
    for project in [
        '~/OpenGL-dev/pyopengl',
        '~/OpenGL-dev/openglcontext',
        '~/OpenGL-dev/twitch',
        '~/OpenGL-dev/simpleparse',
        '~/OpenGL-dev/pyvrml97',
        '~/pylive/vcs2eric',
        '~/pylive/twistedsnmp',
        '~/pylive/starpy',
        '~/blog-dev/blog',
        '~/runsnake-dev/coldshot',
        '~/runsnake-dev/runsnakerun',
        '~/runsnake-dev/squaremap',
    ]:
        directory = os.path.expanduser(project)
        if os.path.exists(directory):
            log.info('Importing project: %s', project)
            check_call(
                ['listener-context-from-project', '--context', context, directory]
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
