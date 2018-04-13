# afchat

This package contains utilities for interacting with chat
services (hipchat ahd slack).

***This software is provided for research purposes only. Use at own risk.***

## Development

### Clone Repo

Via ssh:

    git clone git@github.com:pnwairfire/afchat.git

or http:

    git clone https://github.com/pnwairfire/afchat.git

### Install Dependencies

Run the following to install required python packages as well
as useful dev packages:

    pip install -r requirements.txt
    pip install -r requirements-dev.txt

### Setup Environment

To import afchat in development, you'll have to add the repo
root directory to the search path. Some of the scripts bin do
this automatically.

## Installation

### Installing With pip

First, install pip (with sudo if necessary):

    apt-get install python-pip

Then, to install, for example, v1.2.6, use the following (with sudo if
necessary):

    pip install --extra-index https://pypi.airfire.org/simple afchat==1.0.0

If you get an error like    ```AttributeError: 'NoneType' object has no attribute 'skip_requirements_regex```, it means you need in upgrade pip.  One way to do so is with the following:

    pip install --upgrade pip

## Usage:

Run each script with the `-h` option to see its usage.
