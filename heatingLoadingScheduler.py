import sys
import re
import subprocess
from datetime import datetime, timedelta

nightStart       = '20:00'
nightEnd         = '07:00'
eveningStart     = '17:00'
normalLoadUnder  = 6.0
eveningLoadUnder = 55.0

IDLE_INT_STATE = 19

CMD_TYPE_TEST = -1
CMD_TYPE_SET = 0
CMD_TYPE_P_READ = 1
CMD_TYPE_V_READ = 2
CMD_TYPE_STATE = 3

#*/10 * * * * /path/to/your/python /path/to/your/script.py >> /path/to/your/logfile.log 2>&1
    
def loadIfUnder(minLoad):
    curLoad = getCurLoad()
    print(f"curLoad {curLoad}")
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
    command = "p4 getv -a 0x71"
    loadRaw = execP4dCmd(command, CMD_TYPE_V_READ)
    try:
        return float(int(loadRaw) * 0.004830917874396135)
    except ValueError:
        print(f"\tError: getCurLoad: [{loadRaw}] is not a valid float.")
        sys.exit(2)

def resetLoadTime():
    curLoadTime = getCurLoadTime()
    if curLoadTime != '00:00':
        setCurLoadTime('00:00', curLoadTime)

def getCurLoadTime():
    command = "p4 getp -a 0x3c"
    loadTimeMinutes = int(execP4dCmd(command, CMD_TYPE_P_READ))
    return f"{str(int(loadTimeMinutes / 60)).zfill(2)}:{str(loadTimeMinutes % 60).zfill(2)}"
    
def setCurLoadTime(newTime, prevVal=None):
    print(f"\t[{timeFrame}] Setting current load time to {newTime}", end="")
    if prevVal != None:
        print(f" (prev val [{prevVal}])")
    else:
        print("")

    intTime = int(newTime[:2])*60 + int(newTime[3:5])
    return execP4dCmd(f"p4 setp -a 0x3c -v {intTime}") # add CMD_TYPE_SET

def execP4dCmd(command, cmdType=CMD_TYPE_TEST):
    if cmdType == CMD_TYPE_TEST:
        print()
        return command

    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.stderr:
        print(f"\tError while executing p4d command: {result.stderr}")
        sys.exit(1)
        
    if cmdType == CMD_TYPE_SET:
        return None
    if cmdType == CMD_TYPE_P_READ:
        match = re.search(r'Value: (\d+) \((\d+)\)', result.stdout.rstrip())
        if match:
            return match.group(2)
        print(f"\tError: execP4Cmd failed to parse CMD_TYPE_P_READ value [{result.stdout.rstrip()}]")
        sys.exit(3)
    if cmdType == CMD_TYPE_V_READ:
        match = re.search(r' is (\d+) / ', result.stdout.rstrip())
        if match:
            return match.group(1)
        print(f"\tError: execP4Cmd failed to parse CMD_TYPE_V_READ value [{result.stdout.rstrip()}]")
        sys.exit(3)
    if cmdType == CMD_TYPE_STATE:
        match = re.search(r'(\d+) - \w+', result.stdout.splitlines()[3])
        if match:
            return match.group(1)
        print(f"\tError: execP4Cmd failed to parse CMD_TYPE_STATE value [{result.stdout.rstrip()}]")
        sys.exit(3)
    print(f"\tError: execP4Cmd: unknown command type [{cmdType}] [{command}]")
    sys.exit(4)

def isIdle():
    command = "p4 state"
    intStateRaw = execP4dCmd(command, CMD_TYPE_STATE)
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
