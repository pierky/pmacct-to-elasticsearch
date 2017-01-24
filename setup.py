import os
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

"""
New release procedure

- edit pierky/p2es/version.py

- edit CHANGES.rst

- new files to be added to MANIFEST.in?

- python setup.py sdist

- twine upload dist/*

- git push

- edit new release on GitHub
"""

__version__ = None

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# Get proper long description for package
current_dir = dirname(abspath(__file__))
description = open(join(current_dir, "README.rst")).read()
changes = open(join(current_dir, "CHANGES.rst")).read()
long_description = '\n\n'.join([description, changes])
exec(open(join(current_dir, "pierky/p2es/version.py")).read())

# Get the long description from README.md
setup(
    name="pmacct-to-elasticsearch",
    version=__version__,

    packages=["pierky", "pierky.p2es"],
    namespace_packages=["pierky"],
    include_package_data=True,

    license="MIT",
    description="A Python script designed to read output from pmacct daemons, to process it and to store it into ElasticSearch.",
    long_description=long_description,
    url="https://github.com/pierky/pmacct-to-elasticsearch",
    download_url="https://github.com/pierky/pmacct-to-elasticsearch",

    author="Pier Carlo Chiodi",
    author_email="pierky@pierky.com",
    maintainer="Pier Carlo Chiodi",
    maintainer_email="pierky@pierky.com",

    install_requires=[
    ],

    scripts=["scripts/pmacct-to-elasticsearch"],

    keywords=['pmacct', 'NetFlow', 'accounting', 'BGP'],

    classifiers=[
        "Development Status :: 4 - Beta",

        "Environment :: Console",

        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",


        "Operating System :: POSIX",
        "Operating System :: Unix",

        "Programming Language :: Python :: 2.7",

        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
        "Topic :: System :: Networking :: Monitoring",
    ],
)
