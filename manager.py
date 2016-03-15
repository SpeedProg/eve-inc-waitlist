# inject the lib folder before everything else
import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist import manager
from waitlist.storage.database import *
if __name__ == '__main__':
    manager.run()
