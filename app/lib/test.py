import numpy as np
from math import ceil
from numpy import array, append, unravel_index

from app.lib.audacity import createLabels
from app.constants import OFFSET

def getFoundIndexesOf(parent, child):
    result = [[i, j] for i, _ in enumerate(parent) for j, v in enumerate(_['data']) if v[0] == float(child[0]) and v[1] == float(child[1])]
    return result[0] if len(result) == 1 else None

def proto(lst):
    while True:
        testLst = sorted([item for item in lst], key=lambda v : (v[2], -v[1]))
        last = None
        avg, a = 0, []
        for i, item in enumerate(testLst):
            if item[2] != 'R':
                continue
            if i == 3:
                continue
            a.append(item[0:2])
            if not last:
                last = item[1]
                #print(last, item)
                continue
            '''div = 0
            if last >= item[1]:
                div = last / item[1]
                print(last, item[1], div, item)
            else:
                div = item[1] / last
                print(last, item[1], div, item)
            if div <= 1 + OFFSET:
                print(div)'''
        m = None
        approved = 0
        if a:
            m = np.mean(a, axis=0)
            print(m)
        for item in a:
            #print(item[1], item[1] <= m[1] + 0.150, item[1] >= m[0] + 0.150)
            offsetStart = abs(item[0] - m[0])
            offsetEnd = abs(item[1] - m[1])
            if offsetStart >= 0 and offsetStart <= 0.160 and offsetEnd >= 0 and offsetEnd <= 0.160:
                print('setted', item)
                approved += 1
            else:
                print('unsetted', item)
        if approved >= round(len(a) / 2) + 1:
            break

def getAgree_temp(lst):
    lstSorted = array(sorted([item[0:2] for item in lst], key=lambda v : v[1]))
    middle = lambda x: x[int(np.floor(len(x) / 4)):int(np.ceil(len(x) * 3 / 4))]
    diff = round(middle(lstSorted)[-1][-1] - middle(lstSorted)[0][1], 6)
    currMin, currMax = (round(x, 6) for x in np.mean(middle(lstSorted), axis=0))
    result = []
    #print([item for item in lst])
    #print(np.min([item[0:2] for item in lst]), np.max([item[0:2] for item in lst]))
    #print(np.min([item[0:2] for item in lst]) / np.max([item[0:2] for item in lst]) * 100)
    ecpiIOA = [round(len(lst) / item[1] * 100, 6) for item in lst]
    proto(lst)
    #print([item[1] for item in lst], len(lst))
    #print(ecpiIOA)
    
    for item in lst:
        if item[1] <= currMax + OFFSET:
            result.append(item)
    return result, [currMin, currMax], diff

'''
Label order:
ex. [0.0, 1.285021, 'R', 'CF']
    [start, end, labelName, owner]
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
    env, testPrint = 'development0', 0
    
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
        minAgree = ceil(len(files) / 2)
        
        if __debug__ and env == 'development' and testPrint == 0:
            print('offset -\t', diff)
            print('currStartTime -\t', currStartTime)
            print('currAvgEt -\t', currAvgEt)
            print('\nGet item to remove from main data: ')
        for i, labelCluster in enumerate(temp2[0]):
            currLabel, noEnoughAgree, agree = None, [], 0
            for j, item in enumerate(labelCluster):
                if not currLabel:
                    currLabel = item[2]
                if (abs(currStartTime - item[0]) >= 0 and
                        abs(currStartTime - item[0]) <= diff and
                        abs(currAvgEt - item[1]) >= 0 and
                        abs(currAvgEt - item[1]) <= diff):
                    agree += 1
                    noEnoughAgree.append([item[0], item[1], item[2] + '-' + item[3]])
                    if __debug__ and env == 'development' and testPrint == 0:
                        print('\t', 'approved', i, j, item, agree)
                else:
                    unsettledOutput.append([item[0], item[1], item[2] + '-' + item[3]])
                ix = getFoundIndexesOf(files, item)
                if ix:
                    if __debug__ and env == 'development' and testPrint == 0:
                        print('\t', item[-3], '-', item)
                    del(files[ix[0]]['data'][ix[1]])
            else:
                if agree >= minAgree:
                    mainOutput.append([currStartTime, currAvgEt, currLabel])
                else:
                    noAgreeOutput += noEnoughAgree
        else:
            currStartTime = currAvgEt
            if __debug__ and env == 'development' and testPrint == 0:
                print('main -\t\t', mainOutput)
                print('unsettled -\t', unsettledOutput)
                print('noAgree -\t', noAgreeOutput)
                print('currStartTime -\t', currStartTime)
                print()
        testPrint += 1
    else:
        if __debug__ and env == 'development' and testPrint == 0:
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