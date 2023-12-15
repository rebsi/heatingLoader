import sys
import subprocess
from datetime import datetime, timedelta

nightStart       = '20:00'
nightEnd         = '07:00'
eveningStart     = '17:00'
normalLoadUnder  = 6.0
eveningLoadUnder = 55.0

IDLE_INT_STATE = 3

#*/10 * * * * /path/to/your/python /path/to/your/script.py >> /path/to/your/logfile.log 2>&1
    
def loadIfUnder(minLoad):
    curLoad = getCurLoad()
    if curLoad >= minLoad:
        resetLoadTime()
        return

    # curent time rounded up to 10min (+10min offset)
    current_time = datetime.now().time()
    minutes_remaining = 10 - (current_time.minute % 10) + 10
    rounded_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=minutes_remaining)).time()
    
    print(f"\t[{timeFrame}] Required load {minLoad}; current load {curLoad}")
    setCurLoadTime(rounded_time.strftime("%H:%M"))

def getCurLoad():
    command = "echo 00" # TODO fix command!
    loadRaw = execP4dCmd(command)
    try:
        return float(loadRaw)
    except ValueError:
        print(f"\tError: getCurLoad: [{loadRaw}] is not a valid float.")
        sys.exit(2)

def resetLoadTime():
    curLoadTime = getCurLoadTime()
    if curLoadTime != '00:00':
        setCurLoadTime('00:00', curLoadTime)

def getCurLoadTime():
    command = "echo 12:00" # TODO fix command!
    return execP4dCmd(command)
    
def setCurLoadTime(newTime, prevVal=None):
    print(f"\t[{timeFrame}] Setting current load time to {newTime}", end="")
    if prevVal != None:
        print(f" (prev val [{prevVal}])")
    else:
        print("")

    command = "echo TODO SET LOAD TIME" # TODO fix command!
    return execP4dCmd(command)

def execP4dCmd(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.stderr:
        print(f"\tError while executing p4d command: {result.stderr}")
        sys.exit(1)
        
    return result.stdout.rstrip()

def isIdle():
    command = "echo 3" # TODO fix command!
    intStateRaw = execP4dCmd(command)
    try:
        intState = int(intStateRaw)
        if (intState != IDLE_INT_STATE):
            return False
        return True
    except ValueError:
        print(f"\tError: isIdle: [{intStateRaw}] is not a valid int.")
        sys.exit(2)


current_time = datetime.now().time()
#current_time = datetime.strptime("17:31:49.076132", "%H:%M:%S.%f").time()
print(datetime.now())

if (not isIdle()):
    timeFrame = 'HEATING'
    resetLoadTime()
elif current_time >= datetime.strptime(nightStart, '%H:%M').time():
    timeFrame = 'Night'
    resetLoadTime()
elif current_time <= datetime.strptime(nightEnd, '%H:%M').time():
    timeFrame = 'Night'
    resetLoadTime()
elif current_time >= datetime.strptime(eveningStart, '%H:%M').time():
    timeFrame = 'Evening'
    loadIfUnder(eveningLoadUnder)
else:
    timeFrame = 'Day'
    loadIfUnder(normalLoadUnder)

