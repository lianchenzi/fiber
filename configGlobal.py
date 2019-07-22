class globalVar:
    stop = False
    pause=False
    down=True

def setStop(stop):
    globalVar.stop = stop
def getStop():
    return globalVar.stop

def setPause(pause):
    globalVar.pause = pause
def getPause():
    return globalVar.pause


def setDown(down):
    globalVar.down = down
def getDown():
    return globalVar.down