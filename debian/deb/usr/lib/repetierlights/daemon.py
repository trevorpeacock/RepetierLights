#!/usr/bin/python

import time
import peacocktech.log, peacocktech.status
import peacocktech.daemon
import peacocktech.daemon_task
import serial
import requests

execfile('/etc/repetierLights.py')

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
        printerdata = requests.get(url).json()[printer]
        url = 'http://{}:{}/printer/api/{}?a=listPrinter&apikey={}'.format(host, port, printer, apikey)
        self.log(4, 'Fetching {}'.format(url))
        jobdata = requests.get(url).json()
        def get_led(jobdata, printerdata):
            self.log(4, 'Printer Data {}'.format(printerdata))
            self.log(4, 'Job Data {}'.format(jobdata))
            temp = maprange(printerdata['heatedBed']['tempRead'], 20, 45, 0, 255)
            for extruder in printerdata['extruder']:
                temp = max(temp, maprange(extruder['tempRead'], 35, 80, 0, 255))
            temp = maprange(temp, 0, 255, 80, 0)
            if type(jobdata)!=list or len(jobdata)!=1:
                return [0, 255, 255, 0, 0, 16, 128]
            if 'done' not in jobdata[0]:
                return [42, 255, 64, temp, 128, 16, 255]
            complete = jobdata[0]['done']
            complete = int(complete * 255/100)
            if complete > 255: complete = 255
            if complete < 0: complete = 0
            return [96, 255, 64, temp, 128, 16, complete]
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
        arduino = serial.Serial('/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_A4139363931351A05142-if00')
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

