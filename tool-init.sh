#!/bin/bash

# at this point, we have already cloned https://github.com/MisterSynergy/wikilaeum.git manually before
cd ${HOME}
git rev-list --format=format:'%ai' --max-count=1 `git rev-parse HEAD` > ${HOME}/commit_version_and_timestamp.txt

# copy configuration and put user's database user name into it
if [ ! -f ${HOME}/config.ini ]; then
    cp ${HOME}/config-sample.ini ${HOME}/config.ini
    dbuser=`sed -n -e '/user/{s/.*= *//p}' ${HOME}/replica.my.cnf`
    sed -i -- s/{}/${dbuser}/g ${HOME}/config.ini
fi

# database setup
. ${HOME}/config.ini
mysql --defaults-file=${HOME}/replica.my.cnf --host=${tooldb_host} "CREATE DATABASE IF NOT EXISTS ${tooldb_dbname} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
CHECKTABLES=`mysqlshow --defaults-file=${HOME}/replica.my.cnf --host=${tooldb_host} ${tooldb_dbname} | grep -o localuser`
if [ "$CHECKTABLES" != "localuser" ]; then
    mysql --defaults-file=${HOME}/replica.my.cnf -h ${tooldb_host} ${tooldb_dbname} < ${HOME}/wikilaeum.sql
fi

# file permissions
chmod u+x ${HOME}/*.sh

# set up venv with required python packages for use in kubernetes container for the daily database updates
webservice python3.11 shell ${HOME}/container-init.sh

# create cron jobs
kubectl apply --validate=true -f ${HOME}/k8s_daily_update.yaml
kubectl apply --validate=true -f ${HOME}/k8s_backup.yaml

# start the webserver
webservice php8.2 start