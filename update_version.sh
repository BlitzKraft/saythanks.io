#!/bin/bash

git fetch upstream --tags
git describe --tags > version.txt

