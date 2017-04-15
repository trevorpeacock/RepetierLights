#!/usr/bin/python

import os
import datetime
import peacocktech.synchronization

#@peacocktech.synchronization.synchronized()
#def _log(line):
#    Logger.file.write(line)
##    print line
#    Logger.file.flush()
#    os.fsync(Logger.file)

class Logger():
    file=None
    level=3
    levels={1:'Emergency', 2:'Warnings', 3:'Messages', 4:'Debug', 5:'Verbose'}
    def __init__(self, module, file, level=None):
        self.module=module
        if level: Logger.level=level
        if not Logger.file: Logger.file=open(file, 'a')

    @peacocktech.synchronization.synchronized()
    def _log(self, line):
        Logger.file.write(line)
#        print line
        Logger.file.flush()
        os.fsync(Logger.file)

    def log(self, level, message, module=None):
        if not module: module=self.module
        if level<=Logger.level:
            line="%s %s: %s: %s\n" %(datetime.datetime.now().ctime(), module, Logger.levels[level], message)
            self._log(line)

    def __call__(self, *a, **b):
        self.log(*a, **b)

