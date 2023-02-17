#!/bin/bash
cd ${HOME}
git pull --all
git rev-list --format=format:'%ai' --max-count=1 `git rev-parse HEAD` > ${HOME}/commit_version_and_timestamp.txt

# file permissions
chmod u+x ${HOME}/*.sh