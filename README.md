About this tool
===============
The Wikiläum tool aims to help editors of the German Wikipedia to identify awardee candidates based on project database queries.

Sources of the tool are available under the MIT license at [bitbucket.org](https://bitbucket.org/MisterSynergy/wikilaeum.git)

Installation
============
*   Set up an account at [Wikitech-Wiki](https://wikitech.wikimedia.org).
*   Create a service group for the tool [here](https://wikitech.wikimedia.org/w/index.php?title=Special:NovaServiceGroup&amp;action=addservicegroup&amp;projectname=tools).
*   Log on to the Tool Labs console and switch to the new tool (`~$ become <YOUR TOOL NAME>`).
*   In your tool account home directory, obtain a copy of the script by cloning the bitbucket.org repository: `~$ git clone --recursive https://bitbucket.org/MisterSynergy/wikilaeum.git`. This puts a copy of the sources into a new subfolder `wikilaeum`.
*   Run the init script: `~$ sh ~/wikilaeum/tool-init.sh`. This will do most of the necessary configuration for you.
*   Initialize the tool database. Switch to your home folder and repeatedly run `~$ python3 ~/wikilaeum/daily_update.py` as long as there are more users matching criterias in the replica (project) database as in your local tool database. For efficiency reasons, not more than 500 users are queried per run. This has to be done only once in the setup phase of the tool.
*   Start the webserver: `~$ webservice start`. The tool is now publicly available at https://tools.wmflabs.org/<YOUR TOOL NAME>/index.php