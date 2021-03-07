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

def getFoundIndexesOf(parent, child, iA):
    result = [[i, j] for i, _ in enumerate(parent) for j, v in enumerate(_['data']) if v[0] == float(child[0]) and v[1] == float(child[1]) and iA == i]
    return result[0] if len(result) == 1 else None

def getAgree_temp(lst):
    lstSorted = array(sorted([item[0:2] for item in lst]))
    middle = lambda x: x[int(np.floor(len(x) / 4)):int(np.ceil(len(x) * 3 / 4))]
    currMin, currMax = (round(x, 6) for x in np.mean(middle(lstSorted), axis=0))
    #currStartTime, currEndTime, currLabel = None, None, None
    #lastStartTime, lastEndTime, lastLabel = None, None, None
    #agree = 0
    #diff = OFFSET
    #means = np.mean(lstSorted, axis=1)
    #result = round(np.mean(middle(means), axis=0), 6)
    result = []
    
    for item in lst:
        #print(item[1], currMax + OFFSET)
        #if 0 - item[0] >= 0 and 0 - item[0] <= OFFSET and abs(currMax - item[1]) >= 0 and abs(currMax - item[1]) <= OFFSET:
        if item[1] <= currMax + OFFSET:
            result.append(item)
    return result, [currMin, currMax]

def test(files):
    active, firstOperation = True, True
    currStartTimes, currEndTimes, currLabels = [], [], []
    currStartTime, currEndTime, currLabel = 0, None, None
    criteriaStartTime, criteriaEndTime, criteriaLabel = 0, 0, 0
    output, unsettled = [], []
    tempArr, tempData = [], []
    toDelete = []
    currItems = None
    
    temp = []
    while active:
        if not files:
            active = False
        
        # aqui busca el start y el end de la label
        for i, json in enumerate(files):
            owner, data = json['owner'], json['data']
            #lst = list(list(zip(*data)))
            #print(list(zip(*lst))[0])
            if not data:
                continue
            inRange = [item + [owner, i, j] for j, item in enumerate(data) if currStartTime == item[0] or abs(currStartTime - item[0]) <= OFFSET]
            tempArr.append(data[0][0:2])
            tempData.append({ 'owner': owner, 'data': data[0] })
            temp += inRange
        #print(list(getAgree_temp(temp)))
        print(getAgree_temp(temp))

        #######  #######
        minAgree = len(files) - 1 # @todo change
        currItems = array(tempArr)
        agreeInMax, agreeInMin, minAvg, maxAvg, attempts = 0, 0, 0, 0, 0
        iMax, jMax = unravel_index(currItems.argmax(), currItems.shape)
        currMin, currMax = currItems[i][0], np.amax(currItems)
        print(iMax, jMax, [currMin, currMax])
        if __debug__:
            print('\nGet item to remove from main data: ')
        for iA, item in enumerate(currItems):
            if currMin - item[0] >= 0 and currMin - item[0] <= OFFSET:
                agreeInMin += 1
            if currMax - item[1] >= 0 and currMax - item[1] <= OFFSET:
                agreeInMax += 1
            if currMin - item[0] >= 0 and currMin - item[0] <= OFFSET and currMax - item[1] >= 0 and currMax - item[1] <= OFFSET:
                minAvg += item[0]
                maxAvg += item[1]
                iX = getFoundIndexesOf(files, item, iA)
                if iX:
                    if __debug__:
                        print('\t', files[iX[0]]['owner'], '-', files[iX[0]]['data'][iX[1]])
                    del files[iX[0]]['data'][iX[1]]
            else:
                iX = getFoundIndexesOf(files, item, iA)
                tempStartTime = files[iX[0]]['data'][iX[1]][0]
                tempEndTime = files[iX[0]]['data'][iX[1]][1]
                tempLabel = files[iX[0]]['data'][iX[1]][2] + '-' + files[iX[0]]['owner']
                newData = [tempStartTime, tempEndTime, tempLabel]
                unsettled.append(newData)
        else:
            if minAgree >= agreeInMin:
                minAvg = round(minAvg / agreeInMin, 6)
            if minAgree >= agreeInMax:
                maxAvg = round(maxAvg / agreeInMax, 6)
            if agreeInMin < minAgree or agreeInMax < minAgree:
                minAvg, maxAvg = 0, 0
                attempts += 1
                # reinit currMax
                print('No min agree reached')
        print(agreeInMin, agreeInMax, [minAvg, maxAvg], attempts)
        print('unsettled', unsettled)
        print(files)
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