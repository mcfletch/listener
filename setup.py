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
        license='MIT',
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
            ],
        ),
        zip_safe=False,
    )

