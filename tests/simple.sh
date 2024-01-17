#!/bin/bash

set -ex

# snapd should get activated
snap list
# wait for snapd to be operational
snap wait system seed.loaded
# install a snap
snap install test-snapd-tools
# run an app from that snap
/var/lib/snapd/snap/bin/test-snapd-tools.cmd sh -c 'echo foo'
# remove the snap
snap remove test-snapd-tools
