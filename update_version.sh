#!/bin/bash

# -----------------------------------------------------------------------------
# DEPRECATED: This script is no longer used, as version.txt is not required.
# It was previously used to fetch the latest git tags from the upstream
# repository and write the current version to version.txt.
# -----------------------------------------------------------------------------
# This script is kept for reference only and does not perform any actions.
git fetch upstream --tags
git describe --tags > version.txt
