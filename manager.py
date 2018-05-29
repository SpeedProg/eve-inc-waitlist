# inject the lib folder before everything else
from waitlist import manager
from waitlist.storage.database import *

if __name__ == '__main__':
    manager.run()
