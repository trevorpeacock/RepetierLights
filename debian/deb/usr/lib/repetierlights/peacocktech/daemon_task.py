import datetime, random
from cStringIO import StringIO
import sys
import traceback

class ScheduledTask(object):
    interval=0 #default
    checkinterval=1 #default
    captureoutput=True
    def __init__(self, taskmanager, log, status, *k, **kk):
        self.preinit(*k, **kk)
        self.taskmanager=taskmanager
        self.logobject=log
        self.status=status
        self.module=self.__class__.__name__

        self.nextrun=datetime.datetime.now()
        if self.interval: self.nextrun=datetime.datetime.now()+datetime.timedelta(microseconds=random.randint(1, int(1000000*self.interval)))
        
        self.nextcheck=datetime.datetime.now()
        if self.checkinterval: self.nextcheck=datetime.datetime.now()+datetime.timedelta(microseconds=random.randint(1, int(1000000*self.checkinterval)))
        self.postinit(*k, **kk)
    def preinit(self, *k, **kk):
        pass
    def postinit(self, *k, **kk):
        pass
    def log(self, level, message):
        self.logobject.log(level, message, self.module)
    def check(self): #run a check to see if the task must be run now
        return False
    def docheck(self):
        if datetime.datetime.now()>self.nextcheck:
            self.nextcheck=datetime.datetime.now()+datetime.timedelta(microseconds=int(1000000*self.checkinterval))
            return self.check()
        return False
    #returns true if ran, false if not
    def run(self):
        runnow=self.docheck()
        if self.interval==0:
            if runnow:
                self.doexecute(runnow)
                return True
            return False
        if runnow or datetime.datetime.now()>self.nextrun:
            self.doexecute(runnow)
            return True
        return False
    def doexecute(self, runnow=None):
        if self.captureoutput: 
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
        try:
            self.execute(runnow)
        except:
            raise
        finally:
            if self.captureoutput: 
                sys.stdout = old_stdout
                s=mystdout.getvalue()
                if len(s):
                    self.log(4, "Execute Function Output:\n"+s)        
            self.nextrun=datetime.datetime.now()+datetime.timedelta(microseconds=int(1000000*self.interval))
    def execute(self, runnow=None):
        pass

class ScheduleTaskManager(object):
    def __init__(self, log, status, captureoutput=None):
        self.log=log
        self.status=status
        self.captureoutput=captureoutput
        self.tasks=[]
        self.failcount={}
    def registertask(self, taskclass, *j, **k):
        task=taskclass(self, self.log, self.status, *j, **k)
        self.tasks.append(task)
        return task
    def loop(self):
        try:
            for task in self.tasks:
                if task not in self.failcount: self.failcount[task]={'lastfail':0,'failcount':0}
                try:
                    if self.captureoutput is not None: task.captureoutput=self.captureoutput
                    if task.run():
                        #if ran OK, then increment run count
                        self.failcount[task]['lastfail']+=1
                        self.failcount[task]['failcount']=0
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    self.log.log(2, "Exception running task "+task.__class__.__name__+":\n" +
                                 "".join(traceback.format_exception(exc_type, exc_value,
                                                          exc_traceback)))
                    self.failcount[task]['failcount']+=1
                    self.failcount[task]['lastfail']=0
                    if self.failcount[task]['failcount']>=3:
                        self.log.log(1, "Task ""%s"" failed too many times. Removing from schedule" %(task.__class__.__name__))
                        self.tasks.remove(task)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.log(2, "Exception in main loop:\n" +
                         "".join(traceback.format_exception(exc_type, exc_value,
                                                  exc_traceback)))
        
