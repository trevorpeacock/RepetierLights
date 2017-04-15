#!/usr/bin/python

import os
import datetime, time
import peacocktech.synchronization

class Status():
    file=None
    data={}
    lastrender=time.time()
    def __init__(self, file):
        Status.file=file

    @peacocktech.synchronization.synchronized()
    def update(self, name, value=None):
        if not isinstance(name, dict): data={name:value}
        else: data=name
        change=False
        for name in data:
            if Status.data.has_key(name):
                if Status.data[name][1]!=data[name]:
                    change=True
            else:
                change=True
            Status.data[name]=(datetime.datetime.now(), data[name])
        if change or time.time()-self.lastrender>60:self.write()

    @peacocktech.synchronization.synchronized()
    def write(self):
        self.lastrender=time.time()
        text=['date: %s' % (datetime.datetime.now())]
        names=Status.data.keys()
        names.sort()
        for name in Status.data:
            if isinstance(Status.data[name][1], list) or isinstance(Status.data[name][1], tuple):
                text.append("%s: " % (name))
                for item in Status.data[name][1]:
                    text.append("    %s" % (item))
            else:
                text.append("%s: %s" % (name, Status.data[name][1]))
        file=open(Status.file, 'w')
        file.write("\n".join(text)+"\n")
        file.flush()
        os.fsync(file)

