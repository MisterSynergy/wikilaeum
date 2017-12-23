#!/bin/bash

# make a folder for the sql backups
mkdir ${HOME}/backup

# clone repo and evaluate commit properties
#git clone --recursive https://bitbucket.org/MisterSynergy/wikilaeum.git # this needs to be done manually before
cd ${HOME}/wikilaeum
git rev-list --format=format:'%ai' --max-count=1 `git rev-parse HEAD` > ${HOME}/wikilaeum/commit_version_and_timestamp.txt

# copy configuration and put user's database user name into it
if [ ! -f ${HOME}/wikilaeum/config.ini ]; then
    cp ${HOME}/wikilaeum/config-sample.ini ${HOME}/wikilaeum/config.ini
    dbuser=`sed -n -e '/user/{s/.*= *//p}' ${HOME}/replica.my.cnf`
    sed -i -- s/{}/${dbuser}/g ${HOME}/wikilaeum/config.ini
fi

# create symbolic links in the home directory
ln -isf ${HOME}/wikilaeum/public_html/ ${HOME}
ln -isf ${HOME}/wikilaeum/tool-update.sh ${HOME}

# database setup
. ${HOME}/wikilaeum/config.ini
mysql --defaults-file=${HOME}/replica.my.cnf -h ${tooldb_host} "CREATE DATABASE IF NOT EXISTS ${tooldb_dbname} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
mysql --defaults-file=${HOME}/replica.my.cnf -h ${tooldb_host} ${tooldb_dbname} < ${HOME}/wikilaeum/wikilaeum.sql

# create cron jobs
(crontab -l ; echo "15 3 * * 1 sh ${HOME}/wikilaeum/db_backup.sh") | crontab -
(crontab -l ; echo "20 3 * * */1 python3 ${HOME}/wikilaeum/daily_update.py") | crontab -