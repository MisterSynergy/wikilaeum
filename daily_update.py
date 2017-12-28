#!/usr/bin/env python
import configparser
from itertools import chain
import mysql.connector
from os.path import expanduser
from time import gmtime, strftime
import time

# init
now_at_start = time.time()

config = configparser.ConfigParser()
with open(expanduser('~') + '/wikilaeum/config.ini') as lines:
    lines = chain(('[wikilaeum]',), lines)
    #config.read(expanduser('~') + '/wikilaeum/config.ini')
    config.read_file(lines)
for key in config['wikilaeum']:
    config['wikilaeum'][key] = config['wikilaeum'][key].replace('"', '')
    #print('{} : {}'.format(key, config['wikilaeum'][key]))
    
dbcredentials = configparser.ConfigParser()
dbcredentials.read(expanduser('~') + '/replica.my.cnf')

replica = mysql.connector.connect(host=config['wikilaeum']['replica_dewiki_analytics_host'], database=config['wikilaeum']['replica_dewiki_dbname'], user=dbcredentials['client']['user'], password=dbcredentials['client']['password'], charset='utf8mb4', collation='utf8mb4_bin')
tooldb = mysql.connector.connect(host=config['wikilaeum']['tooldb_host'], database=config['wikilaeum']['tooldb_dbname'], user=dbcredentials['client']['user'], password=dbcredentials['client']['password'], charset='utf8mb4', collation='utf8mb4_bin')

del dbcredentials

editcount_threshold = int(config['wikilaeum']['editcount_threshold'])
insertcounter_limit = int(config['wikilaeum']['insertcounter_limit'])

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

# close tooldb for now and open it later again; otherwise we risk to loose the connection
tooldb.close()

# perform update
if len(list_of_ids)>0:
    firstedit = replica.cursor()

    time_before = time.time()
    print('Perform database query to cache data about up to {:d} users (this may take a while) ...'.format(insertcounter_limit))
    select_query = 'SELECT rev_user, MIN(rev_timestamp) AS first_edit FROM revision_userindex WHERE rev_user IN ({}) GROUP BY rev_user'.format(','.join(['%s']*len(list_of_ids)))
    select_parameters = tuple(list_of_ids)
#    print('Select query: {}'.format(select_query))
#    print('Select parameters: {}'.format(select_parameters))
    firstedit.execute(select_query, params=select_parameters)
    print('This took {:d} seconds'.format(int(time.time()-time_before)))

    dbcredentials = configparser.ConfigParser()
    dbcredentials.read(expanduser('~') + '/replica.my.cnf')
    tooldb = mysql.connector.connect(host=config['wikilaeum']['tooldb_host'], database=config['wikilaeum']['tooldb_dbname'], user=dbcredentials['client']['user'], password=dbcredentials['client']['password'], charset='utf8mb4', collation='utf8mb4_bin')
    del dbcredentials

    if tooldb.is_connected()==True:
        insert = tooldb.cursor()
        for counter2, tuple2 in enumerate(firstedit.fetchall()):
            print('Inserting now ({:3d}/{:3d}): {:d} --- {}'.format(counter2+1, insertcounter_limit, tuple2[0], tuple2[1].decode('utf-8')))
            insert_query = 'INSERT INTO localuser (user_id, timestmp_first) VALUES (%(user_id)s, %(timestmp_first)s)'
            insert_parameters = { 'user_id' : int(tuple2[0]), 'timestmp_first' : tuple2[1].decode('utf-8') }
#            print('Insert query: {}'.format(insert_query))
#            print('Insert parameters: {}'.format(insert_parameters))
            try:
                insert.execute(insert_query, params=insert_parameters)
#               insert.execute('INSERT INTO localuser (user_id, timestmp_first) VALUES (%(user_id)s, %(timestmp_first)s)', { 'user_id':int(tuple2[0]), 'timestmp_first':tuple2[1].decode('utf-8') } )
                tooldb.commit()
            except (mysql.connector.errors.InterfaceError, NameError) as err:
                print(err)

        insert.close()
        tooldb.close()
    else:
        print('Lost connection to tool database')

    firstedit.close()
else:
    counter2=-1

replica.close()

file = open('./daily_update_log.txt', 'w') 
output = '{} UTC (editcount_threshold={:d}): {:d} users in dewiki, {:d} users locally, {:d} users added; update execution time: {:.2f} seconds'.format(strftime('%Y-%m-%d %H:%M:%S', gmtime()), editcount_threshold, cnt_heavyusers, cnt_localusers, counter2+1, time.time()-now_at_start)
file.write(output)
file.close() 
print(output)
