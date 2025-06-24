#!/usr/bin/env python

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
## Get Version details
######################
import subprocess as commands

def get_version():

    status, version = commands.getstatusoutput ("git describe --tags --long")
    if not status: 
        print ("Version: " + version)
    else: 
        print("git describe returned bad status!")
        print("The repo should have at least one release tag!")
        print("Please see https://help.github.com/articles/creating-releases/")
        version = "unknown"

    return version 
