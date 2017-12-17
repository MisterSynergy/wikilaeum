About this tool
===============
The Wikiläum tool aims to help editors of the German Wikipedia to identify awardee candidates based on project database queries.

Sources of the tool are available under the MIT license.

Installation
============
* Set up an account at [Wikitech-Wiki](https://wikitech.wikimedia.org)
* Create a service group for the tool [here](https://wikitech.wikimedia.org/w/index.php?title=Special:NovaServiceGroup&amp;action=addservicegroup&amp;projectname=tools).
* Log on to the Tool Labs console and switch to the new tool (`become $toolname`)
* In your tool account home directory, obtain a copy of the script by cloning the bitbucket.org repository:
    $ git clone --recursive https://bitbucket.org/MisterSynergy/wikilaeum.git
* Update config files:
** Copy `~/wikilaeum/config-sample.ini` to `~/wikilaeum/config.ini` and adjust it so that your database user from `~/replica.my.cnf` appears in the beginning of the value with the key `tooldb_dbname`
** all other configuration should already be set up properly; in case something does not work as expected, there is config in the following files: `~/wikilaeum/daily_update.py`, `~/wikilaeum/db_backup.sh`, `~/wikilaeum/public_html/Database.php`, and `~/wikilaeum/public_html/index.php`
* Run the init script:
* Create an empty tool database ([how to](https://wikitech.wikimedia.org/wiki/Help:Tool_Labs/Database#User_databases)) for the tool; you find your database credentials in `~/replica.my.cnf` and need the database user name (like `s12345`) at this point.
    $ sql local
    MariaDB [(none)]> CREATE DATABASE IF NOT EXISTS `s53600__wikilaeum` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
    Query OK, 1 row affected (0.04 sec)
    MariaDB [(none)]> exit
    Bye
  Please replace the demo database user name (the part before '__wikilaeum') with yours. You do not need to set up tables, the tool will do that for you.
* Install cronjobs; for daily updates and backups
    $ crontab -e
  Add the following two jobs:
    15 3 * * 1 sh /data/project/<YOUR TOOL NAME>/db_backup.sh
    20 3 * * */1 python3 /data/project/<YOUR TOOL NAME>/daily_update.py
* Initialize the tool database. Switch to your home folder and repeatedly run
    python3 daily_update.py
  as long as there are more users matching criterias in the replica (project) database as in your local tool database. For efficiency reasons, not more than 250 users are queried per run. This has to be done only once in the setup phase of the tool.
* Start the webserver:
    $ webservice start
  The tool is now publicly available at https://tools.wmflabs.org/<YOUR TOOL NAME>/index.php
