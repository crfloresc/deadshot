import numpy as np
from numpy import array, append, unravel_index

from src.constants import LIMIT, OFFSET
from src.fileUtils import openStack

def selectData(buffer):
    result = []
    for json in buffer:
        owner, data = json['owner'], json['data']
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
        owner, data = json['owner'], json['data']
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
    tempArr = []
    currItems = None

    while active:
        if not files:
            active = False
        for i, json in enumerate(files):
            owner, data = json['owner'], json['data']
            if not data:
                del(files[i])
                break
            tempArr.append(data[0][0:2])
            del(files[i]['data'][0])
        
        minAgree = 4 # @todo change
        currItems = array(tempArr)
        agree, avg = 0, 0
        initialMax = np.amax(currItems)
        i, j = unravel_index(currItems.argmax(), currItems.shape)
        print(i, j, initialMax)
        for item in currItems:
            if initialMax - item[1] >= 0 and initialMax - item[1] <= OFFSET:
                agree += 1
                avg += item[1]
        else:
            if minAgree >= agree:
                avg = round(avg / agree, 6)
            else:
                print('No min agree reached')
        print(agree, avg)
        print(list(map(max, currItems)))
        break

def test2(files):
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
            if __debug__:
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
    test(data)
    #interObserverAgreement(data)
    # output += test(data)
    #print(output)
    #paserToAudacity(output)