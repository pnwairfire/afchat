from setuptools import setup, find_packages

from afchat import __version__

setup(
    name='afchat',
    version=__version__,
    license='GPLv3+',
    author='Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=find_packages(),
    scripts=[
        'bin/hcarch',
        'bin/hcarch2log',
        'bin/sarch',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.5",
        "Operating System :: POSIX",
        "Operating System :: MacOS"
    ],
    url='https://github.com/pnwairfire/afchat',
    description='Utilities for interacting with chat services',
    install_requires=[
        "afscripting==1.0.0",
        "requests==2.11.1"
    ],
    dependency_links=[
        "https://pypi.smoke.airfire.org/simple/afscripting/",
    ]
)
