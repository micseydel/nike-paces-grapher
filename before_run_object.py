#!/usr/bin/env python
#nike.py

'''
Module for examining Nike+ data.
Last modified 13 May 2011

TODO:
    add bargraph as well as paces
    create a Run object

'''

from sys import exit
import os
import urllib
from time import localtime
import xml.dom.minidom

import matplotlib.pyplot as plot
from numpy import mean, std, polyfit
from PIL import Image

PROG_DIR = os.path.join(os.path.expanduser('~'), '.pynike/')
if not os.path.isdir(PROG_DIR): os.mkdir(PROG_DIR)

MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

STREAM = 'http://nikerunning.nike.com/nikeplus/v1/services/widget/' \
    'get_public_run_list.jsp?userID=%s'

HOW_FELT = ['', 'Awesome', 'Sluggish', 'So-so', 'Injured']
WEATHER = ['', 'Sunny', 'Rainy', 'Cloudly', 'Snowy']
TERRAIN = ['', 'Road', 'Treadmill', 'Trail', 'Track']

class Run(object):
    pass

class Nike(object):
    def __init__(self, my_id):
        self.my_id = my_id
        filename = self.getFile()
        if not filename:
            exit(0)
        file_path = os.path.join(PROG_DIR, filename)
        content = open(file_path).read()

        dom = xml.dom.minidom.parseString(content)
        self.handlePlusService(dom)

    def getFile(self):
        'robust filename getter; looks for previous months if necessary'
        year, month_num, day = localtime()[:3]
        month = MONTHS[month_num]
        filename = '%i%s%i.xml' % (day, month, year)
        file_path = os.path.join(PROG_DIR, filename)
        if not os.path.isfile(file_path):
            print "Downloading XML file..."
            try:
                page = urllib.urlopen(STREAM % self.my_id)
                content = page.read()
                page.close()
                with open(file_path, 'w') as f:
                    f.write(content)

            except IOError:
                print "Could not download file, looking for old file..."
                for i in xrange(12):
                    month = MONTHS[month_num - i]
                    files = filter(lambda x: month in x, os.listdir('.'))
                    if not files: continue
                    filename = files[-1]

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
        'convert a pace to a '
        return "%i'%02i\"/mile" % divmod(pace, 60) #we round

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
        runs = runList[0].getElementsByTagName('run')

        self.distances = []
        self.durations = []
        for index, run in enumerate(runs):
            #converting to miles
            dist_string = self.getText(run.getElementsByTagName('distance'))
            distance = float(dist_string) / 1.609
            self.distances.append(distance)
            #converting to seconds
            dur_string = self.getText(run.getElementsByTagName('duration'))
            duration = int(dur_string) / 1000
            self.durations.append(duration)

        paces = [dur/dist for dist,dur in zip(self.distances, self.durations)]
        self.paces = paces[49:] # truncate old runs

    def prepPacesGraph(self):
        'changes plot to have the paces data; does nothing more'
        plot.plot([None] + self.paces)

        #best fit, linear
        m, b = polyfit(range(len(self.paces)), self.paces, 1)
        plot.plot([None] + [m*x + b for x in xrange(len(self.paces))])

        plot.xlabel("Run Number")
        plot.ylabel("Pace")
        plot.title("Corrected Data")

        plot.axis([0, self.totalRuns - 49, 480, 360])

        #show between 8'00"/mi and 7'00"/mi with 15 second ticks
        yticks = range(360, 481, 30)
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
        plot.show()
    
    def printSummary(self):
        'print a summary of the runs'
        print "Total runs: %i" % self.totalRuns
        print "Total distance: %.2f miles" % self.totalDistance
        print "Total duration: %i:%02i:%02i hours" % self.duration
        print

        summary = zip(xrange(49, self.totalRuns), self.distances, self.paces)
        for index, distance, pace in summary:
            minutes, seconds = divmod(pace, 60)
            pace = self.paceToString(pace)
            print "%2i)  %.4s miles  in %3i:%02i minutes  (%s)" % (
                index + 1, distance, minutes, seconds, pace)

        print
        print "Average pace overall:", self.paceToString(mean(self.paces))

if __name__ == '__main__':
    nike = Nike('1148796416')
    nike.printSummary()
    nike.showPacesGraph()
