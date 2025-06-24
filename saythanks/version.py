#!/usr/bin/env python

# This file is part of the SayThanks project.
# It is used to retrieve the current version of the project.
import subprocess as commands

version_file = "version.txt"

'''
# This function reads the version from a file named "version_file"
# If the file does not exist, it returns "unknown"
def get_version():
    try:
        with open(version_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"
'''

#####################
# Get Version details
######################


def get_version():
    """
    Retrieve the current version of the project using git tags.

    Returns:
        str: The version string if available, otherwise "unknown".
    """
    status, version = commands.getstatusoutput("git describe --tags --long")
    if not status: 
        print("Version: " + version)
    else:
        print("git describe returned bad status!")
        print("The repo should have at least one release tag!")
        print("Please see https://help.github.com/articles/creating-releases/")
        version = "unknown"

    return version 
