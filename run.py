'''
run.py

Container for Nike+ run objects
'''

RUN_FORMAT_STRING = 'Run(dist={distance}, dur={duration}, pace={0}, ' \
    'startTime={startTime})'

class Run(object):
    def __init__(self, distance, duration=None, startTime=None, howFelt=None,
        weather=None, terrain=None):
        self.distance = distance
        self.duration = duration
        self.pace = duration / distance
        self.startTime = startTime
        self.howFelt = howFelt
        self.weather = weather
        self.terrain = terrain

    def __str__(self):
        return RUN_FORMAT_STRING.format(self.getPaceAsString(), **vars(self))

    def getPaceAsString(self):
        return "{:.0f}'{:.0f}\"/mile".format(*divmod(self.pace, 60)) #we round

def test():
     run = Run(24.2, 7200, 125412354)
     print run

if __name__ == '__main__':
    test()
