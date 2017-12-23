#!/bin/bash
updatetime=$(date +"%Y%m%d%H%M%S")
mkdir ${HOME}/wikilaeum-${updatetime}
cp -a ${HOME}/wikilaeum/* ${HOME}/wikilaeum-${updatetime}
cd ${HOME}/wikilaeum
git pull --all
git rev-list --format=format:'%ai' --max-count=1 `git rev-parse HEAD` > ${HOME}/commit_version_and_timestamp.txt