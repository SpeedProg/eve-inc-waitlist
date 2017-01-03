import os, sys
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from multiprocessing import Process, JoinableQueue
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.storage.database import Base, Shipfit, InvType
from waitlist.base import db, manager

class FitModule(Base):
    __tablename__ = 'fit_module'
    fitID = Column(Integer, ForeignKey('split_fittings.id'), primary_key=True, nullable=False)
    moduleID = Column(Integer, ForeignKey('invtypes.typeID'), primary_key=True, nullable=False)
    amount = Column(Integer, default=1)
    module = relationship('InvType')

class SplitShipFit(Base):
    """
    Represents a single fit
    """
    __tablename__ = "split_fittings"
    
    id = Column(Integer, primary_key=True)
    ship_type = Column(Integer, ForeignKey("invtypes.typeID"))
    comment = Column(String(5000))
    wl_type = Column(String(10))
    created = Column(DateTime, default=datetime.utcnow)
    
    ship = relationship("InvType")
    modules = relationship('FitModule')
    
    #def get_dna(self):
    #    return "{0}:{1}".format(self.ship_type, self.modules)
    
    def __repr__(self):
        return "<Shipfit id={0} ship_type={1} modules={2} comment={3} waitlist={4}>".format(self.id, self.ship_type, self.modules, self.comment, self.waitlist.id)

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
            dbFit = SplitShipFit(id=fit.id, ship_type=fit.ship_type, comment=fit.comment, wl_type=fit.wl_type, created=fit.created)
            dbFit.waitlist = fit.waitlist
            if (fit.modules != None):
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
                        module = db.session.query(InvType).get(moduleDefArr[0])
                        if (module == None):
                            print("No Module with ID=", module.typeID)
                        dbModule = FitModule(moduleID=moduleDefArr[0], amount=moduleDefArr[1])
                        dbFit.modules.append(dbModule)
                    except ValueError as e:
                        print("Fit ID=", fit.id, " Module Def Str:", moduleDefStr)
                        raise e
                    except IndexError as ie:
                        print("Fit ID=", fit.id, " Module Def Str:", moduleDefStr)
                        raise ie
                    
            
            db.session.add(dbFit)
        
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