#!/usr/bin/env python
import configparser
import mysql.connector
from os.path import expanduser
from time import gmtime, strftime
import time

# init
config = configparser.ConfigParser()
config.read(expanduser('~') + '/wikilaeum/config.ini')
dbcredentials = configparser.ConfigParser()
dbcredentials.read(expanduser('~') + '/replica.my.cnf')

now_at_start = time.time()
editcount_threshold = int(config['editcount_threshold'])
insertcounter_limit = int(config['insertcounter_limit'])

replica = mysql.connector.connect(host=config['replica_dewiki_analytics_host'], database=config['replica_dewiki_dbname'], user=dbcredentials['client']['user'], password=dbcredentials['client']['password'], charset='utf8mb4', collation='utf8mb4_bin')
tooldb = mysql.connector.connect(host=config['tooldb_host'], database=config['tooldb_dbname'], user=dbcredentials['client']['user'], password=dbcredentials['client']['password'], charset='utf8mb4', collation='utf8mb4_bin')

del dbcredentials
del config

# read database entries
heavyusers = replica.cursor()
heavyusers.execute('SELECT user_id FROM user WHERE user_editcount>=%(editcount_threshold)s', {'editcount_threshold':editcount_threshold})
heavyusers_result = heavyusers.fetchall()
print('Found {:d} users with more than {:d} edits in replica database'.format(heavyusers.rowcount, editcount_threshold))
cnt_heavyusers = heavyusers.rowcount
heavyusers.close()

localusers = tooldb.cursor()
localusers.execute('SELECT user_id FROM localuser')
localusers_result = localusers.fetchall()
print('Found {:d} users in local database'.format(localusers.rowcount))
cnt_localusers = localusers.rowcount
localusers.close()

# prepare update
needsupdate = [item for item in heavyusers_result if item not in localusers_result]
print('{:d} users need to be added'.format(len(needsupdate)))

list_of_ids = []
for counter, tuple1 in enumerate(needsupdate):
    if counter>=insertcounter_limit:
        break;
    list_of_ids.append(tuple1[0])

# perform update
if len(list_of_ids)>0:
    firstedit = replica.cursor()
    insert = tooldb.cursor()

    print('Perform database query (may take a while) ...')
    firstedit.execute('SELECT rev_user, MIN(rev_timestamp) AS first_edit FROM revision_userindex WHERE rev_user IN ({}) GROUP BY rev_user'.format(','.join(['%s'] * len(list_of_ids))), tuple(list_of_ids) )
    for counter2, tuple2 in enumerate(firstedit.fetchall()):
        print('Inserting now ({:3d}/{:3d}): {:d} --- {}'.format(counter2+1, insertcounter_limit, tuple2[0], tuple2[1].decode('utf-8')))
        insert.execute('INSERT INTO localuser (user_id, timestmp_first) VALUES (%(user_id)s, %(timestmp_first)s)', { 'user_id':tuple2[0] , 'timestmp_first':tuple2[1].decode('utf-8') } )
        tooldb.commit()

    firstedit.close()
    insert.close()
else:
    counter2=-1

replica.close()
tooldb.close()

file = open('./daily_update_log.txt', 'w') 
output = '{} UTC (editcount_threshold={:d}): {:d} users in dewiki, {:d} users locally, {:d} users added; update execution time: {:.2f} seconds'.format(strftime('%Y-%m-%d %H:%M:%S', gmtime()), editcount_threshold, cnt_heavyusers, cnt_localusers, counter2+1, time.time()-now_at_start)
file.write(output)
file.close() 
print(output)
