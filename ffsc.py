import os, sys
from multiprocessing import Process, JoinableQueue
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.storage.database import Shipfit, InvType, FitModule
from waitlist.base import db, manager


if __name__ == '___main__':
    manager.run()

class ConvertConsumer(Process):
    def __init__(self, tasks, name):
        Process.__init__(self)
        self.__tasks = tasks
        self.name = name

    def run(self):
        while True:
            work = self.__tasks.get()
            if work is None:
                break
            self.convert(work[0], work[1])
    
    def convert(self, offset, limit):
        fits = db.session.query(Shipfit).limit(limit).offset(offset).all()
        for fit in fits:
            if (fit.modules != None and fit.modules != ''):
                filtered_modules_string = ''
                for moduleDefStr in fit.modules.split(':'):
                    if (moduleDefStr == ''):
                        continue
                    try:
                        moduleDefArr = moduleDefStr.split(';')
                        if (len(moduleDefArr) != 2):
                            print("Skipping Module Fit ID=", fit.id, " Module Def Str:", moduleDefStr)
                            continue
                        
                        # lets check here if that module exists
                        moduleDefArr[0] = int(moduleDefArr[0])
                        moduleDefArr[1] = int(moduleDefArr[1])
                        if moduleDefArr[1] > 2147483647 or moduleDefArr[1] < 0:
                            moduleDefArr[1] = 2147483647
                        
                        module = db.session.query(InvType).get(moduleDefArr[0])
                        if (module == None):
                            print("No Module with ID=", str(moduleDefArr[0]))
                            continue
                        
                        dbModule = FitModule(moduleID=moduleDefArr[0], amount=moduleDefArr[1])
                        fit.moduleslist.append(dbModule)
                        filtered_modules_string += str(moduleDefArr[0])+';'+str(moduleDefArr[1])+':'
                    except ValueError as e:
                        print("Fit ID=", str(fit.id), " Module Def Str:", moduleDefStr)
                        raise e
                    except IndexError as ie:
                        print("Fit ID=", str(fit.id), " Module Def Str:", moduleDefStr)
                        raise ie
                
                if filtered_modules_string == '' or filtered_modules_string == '::':
                    filtered_modules_string = ':'
                else:
                    filtered_modules_string += ':'
                if fit.modules != filtered_modules_string:
                    fit.modules = filtered_modules_string
        
        db.session.commit()
        db.session.close()


if __name__ == '__main__':
    consumer_threads = []
    task_queue = JoinableQueue(maxsize=100)
    for i in range(6):
        t = ConvertConsumer(task_queue, "dec"+str(i))
        t.start()
        consumer_threads.append(t)
    
    numberOfFits = db.session.query(Shipfit).count()
    stepSize = 1000
    for s in xrange(0, numberOfFits, stepSize):
        task_queue.put((s, stepSize))
    
    # send them all the signal to break
    for _ in range(6):
            task_queue.put(None)
    

'''
maybe to this whole thing directly in SQL
but writing it might be a real pain,
it should increase the speed A LOT through, I would guess
DELIMITER $$

DROP PROCEDURE IF EXISTS `insert_csv` $$
CREATE PROCEDURE `insert_csv`(_list MEDIUMTEXT)
BEGIN

DECLARE _next TEXT DEFAULT NULL;
DECLARE _nextlen INT DEFAULT NULL;
DECLARE _value TEXT DEFAULT NULL;

iterator:
LOOP
  -- exit the loop if the list seems empty or was null;
  -- this extra caution is necessary to avoid an endless loop in the proc.
  IF LENGTH(TRIM(_list)) = 0 OR _list IS NULL THEN
    LEAVE iterator;
  END IF;

  -- capture the next value from the list
  SET _next = SUBSTRING_INDEX(_list,',',1);

  -- save the length of the captured value; we will need to remove this
  -- many characters + 1 from the beginning of the string 
  -- before the next iteration
  SET _nextlen = LENGTH(_next);

  -- trim the value of leading and trailing spaces, in case of sloppy CSV strings
  SET _value = TRIM(_next);

  -- insert the extracted value into the target table
  INSERT INTO t1 (c1) VALUES (_next);

  -- rewrite the original string using the `INSERT()` string function,
  -- args are original string, start position, how many characters to remove, 
  -- and what to "insert" in their place (in this case, we "insert"
  -- an empty string, which removes _nextlen + 1 characters)
  SET _list = INSERT(_list,1,_nextlen + 1,'');
END LOOP;

END $$

DELIMITER ;
'''