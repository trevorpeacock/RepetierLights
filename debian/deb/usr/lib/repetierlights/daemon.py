#!/usr/bin/python

import time
import peacocktech.log, peacocktech.status
import peacocktech.daemon
import peacocktech.daemon_task
import serial
import requests
import math
import glob
import time
import re

execfile('/etc/repetierLights.py')

class Arduino(object):
    def __init__(self, log, port, baud):
        super(Arduino, self).__init__()
        self.log = log
        self.port = None
        if port: self.port = port
        self.baud = baud
        self.ser = None
        try:
            self.open()
        except: pass
    def find_port(self):
        for port in glob.glob('/dev/tty[A-Za-z]*'):
            self.log(4, 'Trying Port {}'.format(port))
            try:
                s = serial.Serial(port, self.baud, timeout=0)
                time.sleep(2)
                data = s.read(1000)
                self.log(4, 'Received {}'.format([data]))
                found = re.findall(r'^repetierLights', data)
                s.close()
                if found:
                    self.log(4, 'Found Port {}'.format(port))
                    return port
            except (IOError, OSError, serial.SerialException):
                pass
            self.log(4, 'Failed Port {}'.format(port))
        self.log(3, 'No Serial Port Found')
        raise Exception('No Port Found')
    def open(self):
        if self.ser is not None: return
        if self.port is None:
            raise Exception('No Port Defined')
            port = self.find_port()
        else:
            port = self.port
        self.ser = serial.Serial(port, self.baud)
    def write(self, data):
        try:
            self.open()
            self.ser.write(data)
        except Exception as e:
            self.log(2, 'Serial Port Error {}'.format(e))
            self.close()
    def close(self):
        if self.ser is None: return
        self.ser.close()
        self.ser = None
        
def maprange(val, flow, fhi, tlow, thi):
    val = min(max(val, flow), fhi)
    val = 1.0*(val-flow) / (fhi-flow)
    return val * (thi-tlow) + tlow

class LightUpdaterTask(peacocktech.daemon_task.ScheduledTask):
    def preinit(self, arduino):
        self.arduino = arduino
        self.interval = 15
    def postinit(self, *k, **kk):
        self.execute(True)
    def execute(self, runnow):
        url = 'http://{}:{}/printer/api/{}?a=stateList&apikey={}'.format(host, port, printer, apikey)
        self.log(4, 'Fetching {}'.format(url))
        printerdata = requests.get(url).json()
        url = 'http://{}:{}/printer/api/{}?a=listPrinter&apikey={}'.format(host, port, printer, apikey)
        self.log(4, 'Fetching {}'.format(url))
        jobdata = requests.get(url).json()
        def get_led(jobdata, printerdata):
            self.log(4, 'Printer Data {}'.format(printerdata))
            self.log(4, 'Job Data {}'.format(jobdata))
            if printer not in printerdata:
                #a few bright white with a dim white, error code
                return [0, 0, 255, 0, 0, 16, 16]
            printerdata = printerdata[printer]
            temp = maprange(printerdata['heatedBed']['tempRead'], 35, 50, 0, 255)
            for extruder in printerdata['extruder']:
                temp = max(temp, maprange(extruder['tempRead'], 35, 80, 0, 255))
            temp = maprange(temp, 0, 255, 64, 0)
            if type(jobdata)!=list or len(jobdata)!=1:
                #a few bright white with a dim white, error code
                return [0, 0, 255, 0, 0, 16, 16]
            if 'done' not in jobdata[0]:
                #all dimly indicating temperature, as background so it doesn't glow
                return [42, 255, 64, temp, 255, 64, 0]
            complete = jobdata[0]['done']
            complete = math.ceil(complete * 255/100)
            if complete > 255: complete = 255
            if complete < 0: complete = 0
            #green complete bar, background indicating temp
            return [96, 255, 64, temp, 255, 16, complete]
        numbers = get_led(jobdata, printerdata)
        s = '{}\n'.format(','.join([str(int(n)) for n in numbers]))
        self.log(4, 'Sending String {}'.format(s))
        self.arduino.write(s)


class ServerD(peacocktech.daemon.Daemon):
    pausetime=0.5
    def __init__(self):
        peacocktech.daemon.Daemon.__init__(self, '/var/repetierlights/pid')
        self.log=peacocktech.log.Logger('daemon', '/var/log/repetierlights', 4)
        self.status=peacocktech.status.Status('/var/repetierlights/status')
        self.tasks=peacocktech.daemon_task.ScheduleTaskManager(self.log, self.status)
    def registertask(self, taskclass):
        self.tasks.registertask(taskclass)
    def run(self):
        self.log.log(3, 'Starting')
        self.status.update('Status', 'Starting')
        arduino = Arduino(self.log, serial_port, serial_port_baud)
        self.tasks.registertask(LightUpdaterTask, arduino)
        self.status.update('Status', 'Running')
        
        self.firstruninit()

        while self.running:
            self.tasks.loop()
            time.sleep(self.pausetime)

        self.log.log(3, 'Stopping')
        self.status.update('Status', 'Stopping')
        arduino.close()
        self.status.update('Status', 'Stopped')
        self.log.log(3, 'Stopped')

    def stop(self):
        self.log.log(3, 'Received Stop Signal')
        self.running=False

    def firstruninit(self):
        pass
    
server=ServerD()

server.start()

