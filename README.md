# About
Waitlist for Eve Online targeted towards incursion groups

# License
MIT
For library licenses see licenses folder

# Requirements
* MySQL/MariaDB (for PosgresSQL the migration does not work, never tested)
* all the libraries in "requirements.txt"
* python library to connect to the choosen database
* node (optional for JS minimization)


# Installation
1. install python 3.6
2. install all the requirements by doing pip install -r requirements.txt
3. install your database connection library
4. run `python main.py` to create a default confige file
5. close the process
6. Create a an empty database-scheme in your choosen database server
7. open `config\config.cfg` in your favorite text editor
8. configure the settings in the `config.cfg`
9. run `python manager.py db upgrade` which creates the database schema
10. run `python setup_basic.py` to create needed scopes
11. execute `python create_admin.py` to create the initial admin account.
Enter the character name of your main character as account name, then enter the same name as character to associate.
When asked for more characters just press enter without entering anything.
Further admin accounts can be created over the account management on the website
12. Start the waitlist with `python main.py` and visit it to login with the character that was setup as adming in the previous step.
13. Now configure groups and permissions :)
14. Import needed static data! You can find the interface for it under `Setting`->`Static Data Import`.
The Eve Static Date Export can be found at [Eve Resources](https://developers.eveonline.com/resource/resources).
Mandatory are: typeIDs.yaml, staStations.yaml and updating systems and constellations!
The systems and constellations are updated via esi and can take quite a while.
Updating systems and constellations can fail quietly, so check the error log afterwards.
14. If you write any improvements committing code back to this project is very much appreciated!

# SSO Callback
<path to your waitlist install>/fc_sso/cb

# Configuring Waitlist Groups
There is a script called `setup_waitlists` in the base directory.
To create the 3 default waitlist groups, you can just run it with `python setup_waitlists.py`.
If you want your own customized groups, just look at the script and edit it to your need.
Currently there is no UI for setting up waitlist groups, but you can change their display name in the fleet settings.
Having an UI for this would be nice through, but I haven't gotten around to it yet.

# JS Minimization
For the minification used javascript libs are `bable` and `babili`, which are both MIT licensed.
1. Make sure [node](https://nodejs.org) is installed
2. Go to the waitlist base directory (the one containing **package.json**)
3. ```npm i```

# Usage Guide
A small [usage guide](https://speedprog.github.io/eve-inc-waitlist-docs/) can be found [here](https://speedprog.github.io/eve-inc-waitlist-docs/)
You can contribute to the guide buy forking [the guide](https://github.com/SpeedProg/eve-inc-waitlist-docs) and sending pull requests
Please edit the tex only and not the html! HTML modifications will not be accepted
