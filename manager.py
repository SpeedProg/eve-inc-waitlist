# inject the lib folder before everything else
from waitlist.base import manager
from waitlist.storage.database import *

if __name__ == '__main__':
    manager.run()
