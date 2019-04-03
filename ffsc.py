from multiprocessing import Process, JoinableQueue
from typing import List, Union

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
            ConvertConsumer.convert(work[0], work[1])

    @staticmethod
    def convert(offset, limit):
        fits = db.session.query(Shipfit).limit(limit).offset(offset).all()
        for fit in fits:
            if fit.modules is not None and fit.modules != '':
                filtered_modules_string = ''
                for moduleDefStr in fit.modules.split(':'):
                    if moduleDefStr == '':
                        continue
                    try:
                        module_def_arr: List[Union[str, int], Union[str, int]] = moduleDefStr.split(';')
                        if len(module_def_arr) != 2:
                            print("Skipping Module Fit ID=", fit.id, " Module Def Str:", moduleDefStr)
                            continue
                        
                        # lets check here if that module exists
                        module_def_arr[0] = int(module_def_arr[0])
                        module_def_arr[1] = int(module_def_arr[1])
                        if module_def_arr[1] > 2147483647 or module_def_arr[1] < 0:
                            module_def_arr[1] = 2147483647
                        
                        module = db.session.query(InvType).get(module_def_arr[0])
                        if module is None:
                            print("No Module with ID=", str(module_def_arr[0]))
                            continue
                        
                        db_module = FitModule(moduleID=module_def_arr[0], amount=module_def_arr[1])
                        fit.moduleslist.append(db_module)
                        filtered_modules_string += str(module_def_arr[0])+';'+str(module_def_arr[1])+':'
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
                    print("Correcting: ", fit.modules, " -> ", filtered_modules_string)
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
    for s in range(0, numberOfFits, stepSize):
        task_queue.put((s, stepSize))
    
    # send them all the signal to break
    for _ in range(6):
        task_queue.put(None)
