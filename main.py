import numpy as np
from numpy import array, append, unravel_index

from src.audacity import createLabels
from src.constants import LIMIT, OFFSET
from src.fileUtils import openStack

def selectData(buffer):
    result = []
    for json in buffer:
        owner, data = json['owner'], json['data']
        inRange = [x for x in data if x[0] <= 60]
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

def getFoundIndexesOf(parent, child):
    result = [[i, j] for i, _ in enumerate(parent) for j, v in enumerate(_['data']) if v[0] == float(child[0]) and v[1] == float(child[1])]
    return result[0] if len(result) == 1 else None

def getAgree_temp(lst):
    lstSorted = array(sorted([item[0:2] for item in lst], key=lambda v : v[1]))
    middle = lambda x: x[int(np.floor(len(x) / 4)):int(np.ceil(len(x) * 3 / 4))]
    diff = round(middle(lstSorted)[-1][-1] - middle(lstSorted)[0][1], 6)
    print(diff)
    currMin, currMax = (round(x, 6) for x in np.mean(middle(lstSorted), axis=0))
    result = []
    
    for item in lst:
        if item[1] <= currMax + OFFSET:
            result.append(item)
    return result, [currMin, currMax], diff

'''
Label order:
ex. [0.0, 1.285021, 'R', 'CF', 0, 0]
    [start, end, labelName, owner, ownerIndex, itemIndex]
'''
def splitByLabel(lst):
    lstSorted = sorted(lst, key=lambda item : item[2])
    currLabel = None
    result = []
    temp = []
    
    for item in lstSorted:
        if not currLabel:
            currLabel = item[2]
        if currLabel == item[2]:
            temp.append(item)
        else:
            currLabel = item[2]
            result.append(temp)
            temp = []
            temp.append(item)
    else:
        result.append(temp)
    return sorted(result, key=len, reverse=True)

def test(files):
    active, currStartTime, attempts, diff = True, 0, 0, OFFSET
    mainOutput, unsettledOutput, noAgreeOutput = [], [], [] # outputs
    
    temp, temp2 = [], []
    while active:
        if not files or currStartTime >= 60 or attempts == 5:
            active = False
            continue
        
        # aqui busca el start y el end de la label
        for i, json in enumerate(files):
            owner, data = json['owner'], json['data']
            if not data:
                continue
            inRange = [item + [owner] for j, item in enumerate(data) if currStartTime == item[0] or abs(currStartTime - item[0]) <= diff]
            temp += inRange
        else:
            if not temp:
                attempts += 1
                continue
            temp2 = getAgree_temp(temp)
            temp = []
        
        ####### Split array and order by label name #######
        diff = temp2[2] if temp2[2] > 0 else OFFSET
        temp2 = [splitByLabel(temp2[0]), temp2[1]] # Label segment
        currAvgSt, currAvgEt = temp2[1][0], temp2[1][1]
        minAgree = round(len(files) / 2)
        
        if __debug__:
            print('\nGet item to remove from main data: ')
        for i, labelCluster in enumerate(temp2[0]):
            currLabel, noEnoughAgree, agree = None, [], 0
            for j, item in enumerate(labelCluster):
                if not currLabel:
                    currLabel = item[2]
                if (abs(currStartTime - item[0]) >= 0 and
                        abs(currStartTime - item[0]) <= OFFSET and
                        abs(currAvgEt - item[1]) >= 0 and
                        abs(currAvgEt - item[1]) <= OFFSET):
                    agree += 1
                    noEnoughAgree.append([item[0], item[1], item[2] + '-' + item[3]])
                    if __debug__:
                        print(i, j, item, agree)
                        print(files[item[-2]]['data'][item[-1]])
                else:
                    unsettledOutput.append([item[0], item[1], item[2] + '-' + item[3]])
                ix = getFoundIndexesOf(files, item)
                if ix:
                    if __debug__:
                        print('\t', item[-3], '-', item[0:3])
                    del(files[ix[0]]['data'][ix[1]])
            else:
                if agree >= minAgree:
                    mainOutput.append([currStartTime, currAvgEt, currLabel])
                else:
                    noAgreeOutput += noEnoughAgree
        else:
            currStartTime = currAvgEt
            #print('main -\t\t', mainOutput)
            #print('unsettled -\t', unsettledOutput)
            #print('noAgree -\t', noAgreeOutput)
            print('currStartTime -\t', currStartTime)
            print()
    else:
        print('main -\t\t', mainOutput)
        print(files)
        if mainOutput:
            createLabels('mainOutput', mainOutput)
        if unsettledOutput:
            createLabels('unsettledOutput', unsettledOutput)
        if noAgreeOutput:
            createLabels('noAgreeOutput', noAgreeOutput)

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