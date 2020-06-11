import os

from setuptools import setup, find_packages

version = [
    (line.split('=')[1]).strip().strip('"').strip("'")
    for line in open(os.path.join('listener', 'version.py'))
    if line.startswith('__version__')
][0]

if __name__ == "__main__":
    setup(
        name='listener',
        version=version,
        description='listener',
        long_description='listener',
        classifiers=[
            "Programming Language :: Python",
            "Environment :: X11 Applications :: Qt",
            "Environment :: Console",
            "License :: OSI Approved :: BSD License",
            "Natural Language :: English",
            "Operating System :: POSIX :: Linux",
            "Topic :: Multimedia :: Sound/Audio :: Speech",
        ],
        author='VRPlumber Consulting Inc.',
        author_email='mcfletch@vrplumber.com',
        url='https://github.com/mcfletch/listener',
        keywords='Speech, Pocketsphinx, GUI',
        packages=find_packages(),
        include_package_data=True,
        license='BSD',  # Pocketsphinx is BSD-like
        install_requires=[],
        scripts=[],
        entry_points=dict(
            console_scripts=[
                "listener-pipe=listener.pipeline:main",
                'listener-code-to-words-py=listener.cli:code_to_words',
                'listener-missing-words=listener.cli:missing_words',
                'listener-arpa-guess=listener.cli:arpabet_guess',
                'listener-context-from-project=listener.cli:context_from_project',
                'listener-contexts=listener.cli:context_keys',
                'listener-context-delete=listener.cli:delete_context',
                'listener-qt=listener.cli:qt_gui',
                'listener-dictionary-lookup=listener.cli:dictionary_lookup',
                'listener-dictionary-subset=listener.cli:subset_dictionary',
                'listener-dictionary-import=listener.cli:import_words',
                'listener-rawplay=listener.pipeline:rawplay',
                'listener-ipa-arpa-statmap=listener.ipatoarpabet:create_stat_mapping',
                'listener-uinput-device=listener.uinputdriver:main',
                'listener-uinput-rebuild-mapping=listener.uinputdriver:rebuild_mapping',
                'listener-install-lm-tools=listener.context:install_lm_tools',
            ],
        ),
        zip_safe=False,
    )
