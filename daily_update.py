from os.path import expanduser
from time import gmtime, strftime, time
from configparser import ConfigParser
from typing import Optional

from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import InterfaceError


class Config:
    def __init__(self):
        self.config = ConfigParser(delimiters='=')

        with open(
            f'{expanduser("~")}/config.ini',
            mode='r',
            encoding='utf8'
        ) as file_handle:
            config_str = file_handle.read()
        
        self.config.read_string(f'[wikilaeum]\n{config_str}')

        for key in self.config['wikilaeum']:
            self.config['wikilaeum'][key] = self.config['wikilaeum'][key].replace('"', '')

    def get_config(self, key:str) -> str:
        if key not in self.config['wikilaeum']:
            return ''

        return self.config['wikilaeum'][key]


class DatabaseCursor:
    def __init__(self, host:str, database:str, autocommit:bool=False) -> None:
        self.connection = MySQLConnection(
            host=host,
            database=database,
            option_files=f'{expanduser("~")}/replica.my.cnf',
            autocommit=autocommit
        )
        self.cursor = self.connection.cursor()

    def __enter__(self) -> MySQLCursor:
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()


class ReplicaCursor(DatabaseCursor):
    def __init__(self) -> None:
        super().__init__(
            host=CONFIG.get_config('replica_dewiki_analytics_host'),
            database=CONFIG.get_config('replica_dewiki_dbname')
        )


class ToolDatabaseCursor(DatabaseCursor):
    def __init__(self) -> None:
        super().__init__(
            host=CONFIG.get_config('tooldb_host'),
            database=CONFIG.get_config('tooldb_dbname'),
            autocommit=True
        )


def query_mediawiki(query:str) -> list[tuple]:
    with ReplicaCursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


def query_tool_database(query:str) -> list[tuple]:
    with ToolDatabaseCursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


def query_new_heavyusers(user_ids:list[int]) -> dict[int, str]:
    time_start = time()

    print(f'Perform database query to cache data about {len(user_ids):d} users' \
          ' (this may take a while) ...')

    query = f"""SELECT
  actor_user,
  MIN(rev_timestamp) AS first_edit
FROM
  revision_userindex
    JOIN actor_revision ON rev_actor=actor_id
WHERE
  actor_user IN ({",".join([ str(user_id) for user_id in user_ids ])})
GROUP BY
  actor_user"""

    query_result = query_mediawiki(query)
    print(f'This took {int(time()-time_start):d} seconds')
    
    result = {}
    for tpl in query_result:
        result[tpl[0]] = tpl[1].decode('utf8')

    return result


def insert_user_id(cursor:MySQLCursor, user_id:int, first_edit:str) -> int:
    query = f"""INSERT INTO
  localuser (user_id, timestmp_first)
VALUES
  ({user_id:d}, {first_edit})"""

    try:
        cursor.execute(query)
    except (InterfaceError, NameError) as exception:
        print(exception)
        return 0

    return 1


def insert_user_ids(user_ids:list[int]) -> int:
    if len(user_ids) == 0:
        return 0

    new_heavyusers = query_new_heavyusers(user_ids)

    added_cnt = 0
    with ToolDatabaseCursor() as cursor:
        for user_id, first_edit in new_heavyusers.items():
            print(f'Inserting now ({added_cnt+1:3d}/{len(user_ids):3d}):' \
                  f' {user_id:d} --- {first_edit}')

            added_cnt += insert_user_id(cursor, user_id, first_edit)

    return added_cnt


def query_heavyusers(limit:int) -> list[int]:
    query = f"""SELECT user_id FROM user WHERE user_editcount>={limit}"""
    query_result = query_mediawiki(query)

    user_ids = [ user_id_tuple[0] for user_id_tuple in query_result ]

    print(f'Found {len(user_ids):d} users with more than {limit:d} edits in replica database')

    return user_ids


def query_localusers() -> list[int]:
    query = 'SELECT user_id FROM localuser'
    query_result = query_tool_database(query)

    user_ids = [ user_id_tuple[0] for user_id_tuple in query_result ]

    print(f'Found {len(user_ids):d} users in local database')

    return user_ids


def evaluate_user_ids_to_update(heavyusers:list[int], localusers:list[int], \
                                limit:Optional[int]=None) -> list[int]:
    user_ids = [ user_id for user_id in heavyusers if user_id not in localusers ]

    print(f'{len(user_ids):d} users need to be added')

    if limit is not None and limit < len(user_ids):
        user_ids = user_ids[:limit]
        print(f'{len(user_ids):d} users will be added (set by limit of {limit})')

    return user_ids


def make_output(output:str) -> None:
    with open(f'{expanduser("~")}/daily_update_log.txt', mode='w', encoding='utf8') as file_handle:
        file_handle.write(output)

    print(output)


def main() -> None:
    # init
    now_at_start = time()
    
    editcount_threshold = int(CONFIG.get_config('editcount_threshold'))
    insert_limit = int(CONFIG.get_config('insertcounter_limit'))

    # read database entries
    heavyusers = query_heavyusers(editcount_threshold)
    localusers = query_localusers()

    # prepare update
    user_ids = evaluate_user_ids_to_update(heavyusers, localusers, limit=insert_limit)

    # perform update
    added_cnt = insert_user_ids(user_ids)

    make_output(f'{strftime("%Y-%m-%d %H:%M:%S", gmtime())} UTC (editcount_threshold=' \
        f'{editcount_threshold:d}): {len(heavyusers):d} users in dewiki, {len(localusers):d} ' \
        f'users locally, {added_cnt:d} users added; update execution time: ' \
        f'{time()-now_at_start:.2f} seconds')


CONFIG = Config()


if __name__=='__main__':
    main()
