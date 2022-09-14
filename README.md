About this tool
===============
The Wikiläum tool aims to help editors of the German Wikipedia to identify awardee candidates based on project database queries.

Sources of the tool are available under the MIT license at [github.com](https://github.com/MisterSynergy/wikilaeum.git)

Installation
============
*   Set up a developer account at [Wikitech-Wiki](https://wikitech.wikimedia.org).
*   Create a tool account; see [here](https://wikitech.wikimedia.org/wiki/Portal:Toolforge/Tool_Accounts) for details.
*   Log on to the Toolforge console and switch to the new tool (`~$ become <YOUR_TOOL_NAME>`).
*   In your tool account home directory, obtain a copy of the script by cloning the github.org repository (the tool folder is unfortunately not empty):

    ~$ git init
    ~$ git remote add origin https://github.com/MisterSynergy/wikilaeum.git
    ~$ git fetch
    ~$ git checkout -t origin/master -f

*   Run the init script: `~$ sh ~/tool-init.sh`. This will do most of the necessary configuration for you.
*   Initialize the tool database. Switch to your home folder and repeatedly run `~$ python3 ~/daily_update.py` in an interactive Kubernetes environment as long as there are more users matching criterias in the replica (project) database as in your local tool database. For efficiency reasons, not more than 500 users are queried per run. This has to be done only once in the setup phase of the tool.

Update
=======
*   In case you want to pull updates from the original repository, run the update script: `~$ sh ~/tool-update.sh`