#!/bin/bash

# config
. "${HOME}/wikilaeum/config.ini"
timestmp=$(date +"%Y%m%d_%H%M%S")

# backup command
mysqldump --defaults-file="${HOME}/replica.my.cnf" --host="${tooldb_host}" "${tooldb_dbname}" > "${HOME}/${backup_savepath}tooldb_${timestmp}.sql"
