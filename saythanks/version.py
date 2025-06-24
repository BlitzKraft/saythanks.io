#!/usr/bin/env python

version_file = "version.txt"

# This function reads the version from a file named "version_file"
# If the file does not exist, it returns "unknown"
def get_version():
    try:
        with open(version_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

