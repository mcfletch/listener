import os

from setuptools import setup, find_packages
version = [
    (line.split('=')[1]).strip().strip('"').strip("'")
    for line in open(os.path.join('listener','version.py'))
    if line.startswith( '__version__' )
][0]

if __name__ == "__main__":
    setup(
        name='listener',
        version='1.0.0',
        description='listener',
        long_description='listener',
        classifiers=[
            "Programming Language :: Python",
        ],
        author='VRPlumber Consulting Inc.',
        author_email='mcfletch@vrplumber.com',
        url='http://www.vrplumber.com/programming/project/listener',
        keywords='',
        packages=find_packages(),
        include_package_data=True,
        license='BSD', # Pocketsphinx is BSD-like
        # Dev-only requirements:
        # nose
        # pychecker
        # coverage
        # globalsub
        package_data = {
            'listener': [
            ],
        },
        install_requires=[
        ],
        scripts = [
        ],
        entry_points = dict(
            console_scripts = [
                "text2wfreq=listener.text2wfreq:main",
                "listener-pipe=listener.pipeline:main",
                'listener-code-to-words-py=listener.codetowords:main',
                'listener-rawplay=listener.pipeline:rawplay',
                
                'listener-ipa-arpa-statmap=listener.ipatoarpabet:create_stat_mapping',
            ],
        ),
        zip_safe=False,
    )

