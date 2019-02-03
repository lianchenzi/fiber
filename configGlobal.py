class globalVar:
    stop = False
    pause=False

def setStop(stop):
    globalVar.stop = stop
def getStop():
    return globalVar.stop

def setPause(pause):
    globalVar.pause = pause
def getPause():
    return globalVar.pause