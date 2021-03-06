import os
from contextlib import ExitStack

FILE = '../../Downloads/SS/CF003_Labels.txt'
DIRNAME = './labels'
VALID_LABELS = [
    'AM',
    'R',
    'M1',
    'N1',
    'VF'
]
OFFSET = 0.150 # in ms
LIMIT = 4.00 # minutes @todo: change

def formatLine(line):
    cleanLinebreak = line.split('\n')[0:1]
    return cleanLinebreak[0].split('\t')

def validate(file):
    result = {
        'owner': file.name.split('/')[-1][0:2],
        'data': [],
    }
    for line in file.readlines():
        lineFormated = formatLine(line)
        label = lineFormated[2]
        if label in VALID_LABELS:
            start = float(lineFormated[0].replace(',','.'))
            end = float(lineFormated[1].replace(',','.'))
            result['data'] += [[start, end, label]]
    return result

def openStack():
    result = []
    filespath = [os.path.abspath(DIRNAME + '/' + x) for x in os.listdir(DIRNAME)]
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in filespath]
        for file in files:
            result += [validate(file)]
    return result

def openFiles():
    with open(FILE, 'r') as file:
        for line in file.readlines():
            lineFormated = formatLine(line)
            if lineFormated[2] in VALID_LABELS:
                start = float(lineFormated[0]) + OFFSET
                end = float(lineFormated[1]) + OFFSET
                print(start, ' - ', end)

def selectData(buffer):
    result = []
    for json in buffer:
        owner = json['owner']
        data = json['data']
        inRange = [x for x in data if x[0] <= LIMIT]
        result.append({
            'owner': owner,
            'data': inRange
        })
    return result

def interObserverAgreement(data):
    startTimes = []
    endTimes = []
    labels = []
    for json in data:
        owner = json['owner']
        data = json['data']
        startTime = [x[0] for x in data]
        endTime = [x[1] for x in data]
        label = [x[2] for x in data]
        startTimes.append({
            'owner': owner,
            'startTimes': startTime
        })
        endTimes.append({
            'owner': owner,
            'endTimes': endTime
        })
        labels.append({
            'owner': owner,
            'labels': label
        })
    for i, startTime in enumerate(startTimes):
        currTime = None
        currList = startTime['startTimes']
        while True:
            for dataTime in currList:
                if currTime == None:
                    print('NONE')
                    currTime = dataTime
                    del(startTimes[i]['startTimes'][0])
                print(i, currTime, dataTime)
                #currList.remove(currTime)
            break
        print(currList)
    print(startTimes)

def test(files):
    active, firstOperation = True, True
    currStartTimes, currEndTimes, currLabels = [], [], []
    currStartTime, currEndTime, currLabel = None, None, None
    criteriaStartTime, criteriaEndTime, criteriaLabel = 0, 0, 0
    output = []

    while active:
        for i, json in enumerate(files):
            owner, data = json['owner'], json['data']
            lst = list(list(zip(*data)))
            if not lst:
                active = False
                break
            currStartTimes, currEndTimes, currLabels = lst
            if firstOperation:
                currStartTime, currEndTime, currLabel = list(zip(*lst))[0]
                firstOperation = False
            else:
                startTimeEval = currStartTime - currStartTimes[0]
                endTimeEval = currEndTime - currEndTimes[0]
                labelEval = currLabel == currLabels[0]
                criteriaPassed = False
                if startTimeEval >= 0 and startTimeEval <= OFFSET:
                    criteriaStartTime += 1
                    criteriaPassed = True
                else: criteriaPassed = False
                if endTimeEval >= 0 and endTimeEval <= OFFSET:
                    criteriaEndTime += 1
                    criteriaPassed = True
                else: criteriaPassed = False
                if labelEval:
                    criteriaLabel += 1
                    criteriaPassed = True
                else: criteriaPassed = False

                if criteriaPassed:
                    currStartTime = round((currStartTime + currStartTimes[0]) / 2, 8)
                    currEndTime = round((currEndTime + currEndTimes[0]) / 2, 8)
            print(owner)
            print(i, currStartTimes)
            print(i, currEndTimes)
            print(i, currLabels)
            print(currStartTime, currEndTime, currLabel)
            del(files[i]['data'][0])
        firstOperation = True
        output.append([currStartTime, currEndTime, currLabel])
    return output

if __name__ == '__main__':
    output = []
    buffer = openStack()
    data = selectData(buffer)
    #interObserverAgreement(data)
    output += test(data)
    print(output)
    #paserToAudacity(output)