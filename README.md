# About
Incursion Targets Waitlist for Eve Online

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
14. If you write any improvements committing code back to this project is very much appreciated!

# JS Minimization
1. Make sure [node](https://nodejs.org) is installed
2. Go to the waitlist base directory (the one containing **package.json**)
3. ```npm i```
