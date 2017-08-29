# About
Incursion Targets Waitlist for Eve Online

# License
MIT
For library licenses see licenses folder

# Requirements
* MySQL/MariaDB (maybe PosgresSQL works too, never tested)
* all the libraries in "requirements.txt"
* python library to connect to the choosen database
* node (optional for JS minimization)


# Installation
1. install python 3.6
2. install all the requirements by doing pip install -r requirements.txt
3. install your database connection library
4. run `python waistlist.py`
5. close the process
6. open `config\config.cfg` in your favorite text editor
7. configure the settings in there
8. Create a an empty database-scheme in your choosen database server
9. run `python manager.py upgrade` which creates the database schema
10. run `python setup_basic.py` to create needed scopes
11. execute `python create_admin.py` to create the initial admin account.
Further admin accounts can be created over the account management on the website
12. Visit the website with the admin account and configure groups and permissions :)
13. If you write any improvements committing code back to this project is very much appreciated!

# JS Minimization
1. Make sure [node](https://nodejs.org) is installed
2. Go to the waitlist base directory (the one containing **package.json**)
3. ```npm i```
