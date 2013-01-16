#!/usr/bin/env python
#nike.py

'''
Module for examining Nike+ data.
Last modified 8 October 2011

TODO:
    add bargraph as well as paces
        bargraph for days, and for runs
    create a Run object
    add option for start date as well as start run
    add re-download feature for when you've already looked a run for a day
    support multiple figures

'''

from sys import exit
import os
import urllib
from time import localtime, strptime
import xml.dom.minidom

import matplotlib.pyplot as plot
from numpy import mean, std, polyfit
from PIL import Image

from run import Run

PROG_DIR = os.path.join(os.path.expanduser('~'), '.pynike/')
if not os.path.isdir(PROG_DIR): os.mkdir(PROG_DIR)

MONTHS = ('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

STREAM = 'http://nikerunning.nike.com/nikeplus/v1/services/widget/' \
    'get_public_run_list.jsp?userID=%s'

HOW_FELT = ('', 'Awesome', 'Sluggish', 'So-so', 'Injured')
WEATHER = ('', 'Sunny', 'Rainy', 'Cloudly', 'Snowy')
TERRAIN = ('', 'Road', 'Treadmill', 'Trail', 'Track')

class Nike(object):
    printSummaryFormatString = "{:2})  {:4.2f} miles  in {:3.0f}:{:02.0f} " \
        "minutes  ({})"
    def __init__(self, my_id, startRun=0, forceDownload=False):
        self.startRun = startRun
        self.my_id = my_id

        filename = self.getFile(forceDownload)
        if not filename:
            exit(0)
        file_path = os.path.join(PROG_DIR, filename)
        content = open(file_path).read()

        dom = xml.dom.minidom.parseString(content)
        self.handlePlusService(dom)

    def getFile(self, forceDownload):
        'robust filename getter; looks for previous months if necessary'
        year, month_num, day = localtime()[:3]
        month = MONTHS[month_num]
        filename = '{}{}{}.xml'.format(day, month, year)
        file_path = os.path.join(PROG_DIR, filename)
        if not os.path.isfile(file_path) or forceDownload:
            print "Downloading XML file..."
            try:
                page = urllib.urlopen(STREAM % self.my_id)
                content = page.read()
                page.close()
                with open(file_path, 'w') as f:
                    f.write(content)

            except IOError:
                print "Could not download file, looking for old file in",
                print PROG_DIR
                for month in (MONTHS[month_num - i] for i in xrange(12)):
                    files = filter(lambda x: month in x, os.listdir(PROG_DIR))
                    if not files: continue
                    filename = files[-1]
                    break

                try:
                    print "Using", filename
                except NameError:
                    print "It appears no file has been downloaded before!"
                    return

        else:
            print "Opening XML file downloaded earlier today..."

        return filename

    def getText(self, nodelist):
        'get the text from a nodelist'
        rc = []
        for node in nodelist:
            for subNode in node.childNodes:
                rc.append(subNode.data.strip())
        return ''.join(rc)

    def getLength(self, num1, num2):
        'get the difference in length (digits) between two numbers'
        return len(str(num1)) - len(str(num2))

    def paceToString(self, pace):
        'convert a floating point pace to a string'
        return "{:.0f}'{:02.0f}\"/mile".format(*divmod(pace, 60)) #we round

    def handlePlusService(self, plusService):
        runListSummary = plusService.getElementsByTagName('runListSummary')[0]
        runList = plusService.getElementsByTagName('runList')

        self.handleRunListSummary(runListSummary)
        self.handleRunList(runList)

    def handleRunListSummary(self, runListSummary):
        raw_runs = runListSummary.getElementsByTagName('runs')
        self.totalRuns = int(self.getText(raw_runs))

        distance = runListSummary.getElementsByTagName('distance')
        self.totalDistance = float(self.getText(distance)) / 1.609

        duration = runListSummary.getElementsByTagName('duration')
        duration = int(self.getText(duration)) / 1000 #now in seconds
        hours = duration / 3600
        minutes = duration / 60 % 60
        seconds = duration % minutes
        self.duration = (hours, minutes, seconds)

    def handleRunList(self, runList):
        self.runs = []
        run_nodes = runList[0].getElementsByTagName('run')

        for run in run_nodes:
            #converting to miles
            dist_string = self.getText(run.getElementsByTagName('distance'))
            dist = float(dist_string) / 1.609
            #converting to seconds
            dur_string = self.getText(run.getElementsByTagName('duration'))
            dur = int(dur_string) / 1000
            #get the startTime
            startTime = self.getText(run.getElementsByTagName('startTime'))
            startTime = strptime(startTime[:-6], '%Y-%m-%dT%H:%M:%S')
            #get Nike+ run info
            howFelt = self.getText(run.getElementsByTagName('howFelt'))
            if howFelt: howFelt = int(howFelt)
            weather = self.getText(run.getElementsByTagName('weather'))
            if weather: weather = int(weather)
            terrain = self.getText(run.getElementsByTagName('terrain'))
            if terrain: terrain = int(terrain)
            #make the run object
            run_obj = Run(dist, dur, startTime, howFelt, weather, terrain)
            self.runs.append(run_obj)
        
        self.runs = self.runs[self.startRun:]
        self.paces = [run.pace for run in self.runs]

    def prepPacesGraph(self):
        'changes plot to have the paces data; does nothing more'
        plot.plot([None] + self.paces)

        #best fit, linear
        m, b = polyfit(range(len(self.paces)), self.paces, 1)
        plot.plot([None] + [m*x + b for x in xrange(len(self.paces))])

        plot.title("Paces")
        plot.xlabel("Run Number")
        plot.ylabel("Pace")

        #this makes the axis self.paces wide, and 
        plot.axis([0,len(self.paces), 510, 390])
        #show between 8'00"/mi and 6'00"/mi with 30 second ticks
        yticks = range(390, 511, 30)
        #map the time/mile pace to the raw numbers
        plot.yticks(yticks, map(self.paceToString, yticks))

    def savePacesGraph(self, as_type='png'):
        'saves the image of the paces graph'
        self.prepPacesGraph()
        plot.savefig("example.png")
        if as_type in ('jpg', 'jpeg'):
            im = Image.open("example.png")
            im.save("example.jpg")
            os.remove('example.png')

    def showPacesGraph(self):
        'show the paces graph'
        self.prepPacesGraph()
        plot.draw() #show()
    
    def printSummary(self):
        'print a summary of the runs'
        print "Total runs: {}".format(self.totalRuns)
        print "Total distance: {:.2f} miles".format(self.totalDistance)
        print "Total duration: {}:{:02}:{:02} hours".format(*self.duration)
        print

        for index, run in enumerate(self.runs, self.startRun):
            minutes, seconds = divmod(run.duration, 60)
            pace = self.paceToString(run.pace)
            print self.printSummaryFormatString.format(
                index + 1, run.distance, minutes, seconds, pace)

        print
        print "Average pace overall:", self.paceToString(mean(self.paces))

    def prepDistancesDaysGraph(self):
        days = {}
        for run in self.runs:
            day = run.startTime[:3]
            if day in days:
                days[day] += run.distance
            else:
                days[day] = run.distance
        
        for day in sorted(days.keys()):
            print '{2}/{3:02} {0:.2f} miles'.format(days[day], *day)

        plot.figure(2)

        plot.title('Miles on days')
        plot.xlabel('Date')
        plot.ylabel('Miles')

        xLocations = [x + 0.25 for x in xrange(len(days.values()))]
        plot.bar(xLocations, days.values(), width=0.5)

        xticksLabels = ['{1}/{2}'.format(*day) for day in sorted(days.keys())]
        plot.xticks([x + 0.25 for x in xLocations], xticksLabels)

    def showDistancesDaysGraph(self):
        self.prepDistancesDaysGraph()
        plot.draw() #show()

if __name__ == '__main__':
    nike = Nike('1148796416', startRun=49)
    nike.printSummary()

    nike.showPacesGraph()
    nike.showDistancesDaysGraph()
    plot.show()
