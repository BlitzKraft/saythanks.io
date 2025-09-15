#!/usr/bin/env python

# This file is part of the SayThanks project.
# It is used to retrieve the current version of the project.
import subprocess as commands
from datetime import datetime


#####################
# Get Version details
######################


def get_version():
    """
    Retrieve the current version of the project using git tags and commit date.

    Returns:
        str: The version string with date in format 'V X.X-XX MMM-DD', otherwise "unknown".
    """
    # Get version tag
    status, version = commands.getstatusoutput("git describe --tags --long")
    if not status:
        # Get the commit date
        date_status, commit_date = commands.getstatusoutput('git log -1 --format=%cd --date=short')
        if not date_status:
            # Parse the version and date
            version = version.split('-g')[0]  # Remove git hash
            # Convert date string to datetime object
            date_obj = datetime.strptime(commit_date, '%Y-%m-%d')
            # Format month as three letters and get day
            formatted_date = f"{date_obj.strftime('%b')}-{date_obj.day}"
            version = f"{version} {formatted_date}"
            print(f"Version: {version}")
        else:
            print("Warning: Could not retrieve commit date")
    else:
        print("git describe returned bad status!")
        print("The repo should have at least one release tag!")
        print("Please see https://help.github.com/articles/creating-releases/")
        version = "unknown"

    return version

version_file = "version.txt"

# Alternative simple version retrieval method (commented out)
# Deprecated in favor of git-based versioning

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
