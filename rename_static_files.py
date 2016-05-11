from waitlist.data.version import version
from os.path import isfile, join
from os import listdir
import os
if __name__ == '__main__':
    v = version
    basePath = "./static/js"
    onlyfiles = [f for f in listdir(basePath) if isfile(join(basePath, f))]
    for f in onlyfiles:
        os.rename(f, f.replace(".js", ""+v+".js"))
    
        basePath = "./static/css"
    onlyfiles = [f for f in listdir(basePath) if isfile(join(basePath, f))]
    for f in onlyfiles:
        os.rename(f, f.replace(".css", ""+v+".css"))