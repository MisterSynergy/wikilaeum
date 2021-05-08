#!/usr/bin/env python
from os.path import expanduser
from time import gmtime, strftime, time
from configparser import ConfigParser
from itertools import chain

from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import InterfaceError


class DatabaseCursor:
    def __init__(self, host:str, database:str, autocommit:bool=False) -> None:
        self.connection = MySQLConnection(
            host=host,
            database=database,
            option_files=expanduser('~') + '/replica.my.cnf',
            charset='utf8mb4',
            collation='utf8mb4_bin',
            autocommit=autocommit
        )
        self.cursor = self.connection.cursor()


    def __enter__(self):
        return self.cursor


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()


class ReplicaCursor(DatabaseCursor):
    def __init__(self, host:str, database:str) -> None:
        super().__init__(
            host=host,
            database=database
        )


class ToolDatabaseCursor(DatabaseCursor):
    def __init__(self, host:str, database:str) -> None:
        super().__init__(
            host=host,
            database=database,
            autocommit=True
        )


def query_mediawiki(host:str, database:str, query:str) -> list:
    with ReplicaCursor(host, database) as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


def query_tool_database(host:str, database:str, query:str) -> list:
    with ToolDatabaseCursor(host, database) as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


def read_config() -> ConfigParser: # TODO: tidy
    config = ConfigParser()

    #config.read(expanduser('~') + '/wikilaeum/config.ini')
    with open(expanduser('~') + '/wikilaeum/config.ini', mode='r', encoding='utf8') as lines:
        lines = chain(('[wikilaeum]',), lines)
        config.read_file(lines)

    for key in config['wikilaeum']:
        config['wikilaeum'][key] = config['wikilaeum'][key].replace('"', '')

    return config


def query_new_heavyusers(host:str, database:str, user_ids:list, limit:int) -> list:
    time_start = time()

    print('Perform database query to cache data about up to {:d} users' \
          ' (this may take a while) ...'.format(limit))

    query = """SELECT
  actor_user,
  MIN(rev_timestamp) AS first_edit
FROM
  revision_userindex
    JOIN actor_revision ON rev_actor=actor_id
WHERE
  actor_user IN ({user_ids_concatenated})
GROUP BY
  actor_user""".format(user_ids_concatenated=','.join([ str(user_id) for user_id in user_ids ]))

    result = query_mediawiki(host, database, query)

    print('This took {duration:d} seconds'.format(duration=int(time()-time_start)))

    return result


def insert_user_id(cursor:MySQLCursor, user_id:str, first_edit:str) -> int:
    query = """INSERT INTO
  localuser (user_id, timestmp_first)
VALUES
  ({user_id}, {first_edit})""".format(user_id=user_id, first_edit=first_edit)

    try:
        cursor.execute(query)
    except (InterfaceError, NameError) as exception:
        print(exception)
        return 0

    return 1


def insert_user_ids(replica_host:str, replica_database:str, tool_host:str, tool_db:str, \
                    user_ids:list, limit:int) -> int:
    if len(user_ids) == 0:
        return 0

    new_heavyusers = query_new_heavyusers(replica_host, replica_database, user_ids, limit)

    added_cnt = 0
    with ToolDatabaseCursor(tool_host, tool_db) as cursor:
        for tpl in new_heavyusers:
            user_id = str(tpl[0])
            first_edit = tpl[1].decode('utf8')

            print('Inserting now ({added_cnt:3d}/{limit:3d}): {user_id} --- {first_edit}'.format(
                added_cnt=added_cnt+1,
                limit=limit,
                user_id=user_id,
                first_edit=first_edit
            ))

            added_cnt += insert_user_id(cursor, user_id, first_edit)

    return added_cnt


def query_heavyusers(host:str, database:str, limit:int) -> list:
    query = """SELECT user_id FROM user WHERE user_editcount>={limit}""".format(limit=limit)
    result = query_mediawiki(host, database, query)

    print('Found {cnt:d} users with more than {limit:d} edits in replica database'.format(
        cnt=len(result),
        limit=limit
    ))

    return result


def query_localusers(host:str, database:str, ) -> list:
    query = 'SELECT user_id FROM localuser'
    result = query_tool_database(host, database, query)

    print('Found {cnt:d} users in local database'.format(cnt=len(result)))

    return result


def evaluate_user_ids_to_update(heavyusers:list, localusers:list, limit:int) -> list:
    user_ids = [ int(user_id[0]) for user_id in heavyusers if user_id not in localusers ]
    print('{cnt:d} users need to be added'.format(cnt=len(user_ids)))

    if limit < len(user_ids):
        user_ids = user_ids[:limit]
        print('{cnt:d} users will be added (set by limit of {limit})'.format(
            cnt=len(user_ids),
            limit=limit
        ))

    return user_ids


def make_output(output:str) -> None:
    with open('./daily_update_log.txt', mode='w', encoding='utf8') as file_handle:
        file_handle.write(output)

    print(output)


def main() -> None:
    # init
    now_at_start = time()
    config = read_config()

    editcount_threshold = int(config['wikilaeum']['editcount_threshold'])
    insert_limit = int(config['wikilaeum']['insertcounter_limit'])

    # read database entries
    heavyusers = query_heavyusers(
        config['wikilaeum']['replica_dewiki_analytics_host'],
        config['wikilaeum']['replica_dewiki_dbname'],
        editcount_threshold
    )
    localusers = query_localusers(
        config['wikilaeum']['tooldb_host'],
        config['wikilaeum']['tooldb_dbname']
    )

    # prepare update
    user_ids = evaluate_user_ids_to_update(heavyusers, localusers, insert_limit)

    # perform update
    added_cnt = insert_user_ids(
        config['wikilaeum']['replica_dewiki_analytics_host'],
        config['wikilaeum']['replica_dewiki_dbname'],
        config['wikilaeum']['tooldb_host'],
        config['wikilaeum']['tooldb_dbname'],
        user_ids,
        insert_limit
    )

    make_output('{timestmp} UTC (editcount_threshold={editcount_threshold:d}):' \
        ' {cnt_heavyusers:d} users in dewiki, {cnt_localusers:d} users locally,' \
        ' {added_cnt:d} users added; update execution time: {time_consumed:.2f}' \
        ' seconds'.format(
        timestmp=strftime('%Y-%m-%d %H:%M:%S', gmtime()),
        editcount_threshold=editcount_threshold,
        cnt_heavyusers=len(heavyusers),
        cnt_localusers=len(localusers),
        added_cnt=added_cnt,
        time_consumed=time()-now_at_start
    ))


if __name__=='__main__':
    main()
