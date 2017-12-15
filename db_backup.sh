#!/bin/bash

# config
. "${HOME}/public_html/wikilaeum/config.ini"
timestmp=$(date +"%Y%m%d_%H%M%S")

# backup command
mysqldump --defaults-file="${HOME}/replica.my.cnf" --host="${tooldb_host}" "${tooldb_dbname}" > "${backup_savepath}tooldb_${timestmp}.sql"
