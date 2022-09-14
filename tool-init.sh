#!/bin/bash

# clone repo and evaluate commit properties
#git clone https://github.com/MisterSynergy/wikilaeum.git # this needs to be done manually before
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
mysql --defaults-file=${HOME}/replica.my.cnf -h ${tooldb_host} "CREATE DATABASE IF NOT EXISTS ${tooldb_dbname} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
mysql --defaults-file=${HOME}/replica.my.cnf -h ${tooldb_host} ${tooldb_dbname} < ${HOME}/wikilaeum.sql

# create cron jobs
(crontab -l ; echo "15 3 * * 1 sh ${HOME}/db_backup.sh") | crontab -
#(crontab -l ; echo "20 3 * * */1 python3 ${HOME}/daily_update.py") | crontab -

# set up kubernetes container for the daily database updates
chmod u+x ${HOME}/container-init.sh
webservice --backend=kubernetes python3.9 shell ${HOME}/container-init.sh

kubectl delete cronjob.batch/wikilaeum.dailyupdate
kubectl apply --validate=true -f ${HOME}/k8s_daily_update.yaml
