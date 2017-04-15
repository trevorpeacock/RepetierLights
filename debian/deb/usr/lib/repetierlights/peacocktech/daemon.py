#!/usr/bin/env python

import sys, os, signal

class Log:
    """file like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""
    def __init__(self, f):
        self.f = f
    def write(self, s):
        self.f.write(s)
        self.f.flush()

class Daemon:
    running=False
    def __init__(self, pidfile):
        self.pidfile=pidfile
    def start(self):
        # do the UNIX double-fork magic, see Stevens' "Advanced
        # Programming in the UNIX Environment" for details (ISBN 0201563177)
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")   #don't prevent unmounting....
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent, print eventual PID before
                #print "Daemon PID %d" % pid
                open(self.pidfile,'w').write("%d"%pid)
                sys.exit(0)
        except OSError, e:
            print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
            sys.exit(1)
        
        self.startinthread()
    #can use this to start in the current thread
    def startinthread(self):
        signal.signal(signal.SIGINT, lambda *args: self.stop())
        signal.signal(signal.SIGQUIT, lambda *args: self.stop())
        
        #change to data directory if needed
        #os.chdir("/root/data")
        #redirect outputs to a logfile
        #sys.stdout = sys.stderr = Log(open(LOGFILE, 'a+'))
        #ensure the that the daemon runs a normal user
        #os.setegid(103)     #set group first "pydaemon"
        #os.seteuid(103)     #set user "pydaemon"
        #start the user program here:
        self.running=True
        self.run()
    def run(self):
        pass
    def stop(self):
        self.running=False

