import numpy as np
from math import ceil
from numpy import array, append, unravel_index

from app.lib.audacity import createLabels
from app.constants import OFFSET

def getFoundIndexesOf(parent, child):
    result = [[i, j] for i, _ in enumerate(parent) for j, v in enumerate(_['data']) if v[0] == float(child[0]) and v[1] == float(child[1])]
    return result[0] if len(result) == 1 else None

def proto(lst, offset=0.160):
    if not lst:
        return None
    cluster = sorted([item for item in lst], key=lambda v : (v[2], -v[1]))
    approved, dropped, pending = [], [], []
    last, label = None, None
    result = {}
    while cluster:
        arr, m, newM = [], [], []
        agree = 0
        
        # Search a labels cluster with the same label ordered by endTime and label
        for i, item in enumerate(cluster):
            if not label:
                label = item[2]
            if item[2] != label:
                continue
            if not last:
                last = item
            arr.append(item)
            m.append(item[0:2])
        m = np.mean(m, axis=0)
        #offset = abs((last[1] - last[0]) - (m[1] - m[0]))
        
        # 
        for i, item in enumerate(arr):
            offsetStart = abs(item[0] - m[0])
            offsetEnd = abs(item[1] - m[1])
            if offsetStart >= 0 and offsetStart <= offset and offsetEnd >= 0 and offsetEnd <= offset:
                #print('approved', item)
                if len(arr) > 1:
                    approved.append(item)
                else:
                    pending.append(item)
                newM.append(item[0:2])
                agree += 1
            else:
                #print('pending', item)
                pending.append(item)
        
        # Check for agreement and cleanup
        if agree >= round(len(arr) / 2) + 1:
            result.update({ label: {
                'approved': approved,
                'dropped': dropped,
                'pending': pending,
                'm': list(np.mean(newM, axis=0)) if approved else []
                } })
            cluster = [i for i in cluster if i not in approved and i not in pending]
            dropped = []
        else:
            dropped.append(last)
            del cluster[cluster.index(last)]
        approved, pending, last, label = [], [], None, None
    
    # New mean per cluster
    mean = []
    for k, v in result.items():
        for kk, vv in v.items():
            if kk == 'm':
                if not vv:
                    continue
                mean.append(vv)
    
    #print(np.mean(mean, axis=0))
    print(result)
    print('LAST')

def getAgree_temp(lst):
    lstSorted = array(sorted([item[0:2] for item in lst], key=lambda v : v[1]))
    middle = lambda x: x[int(np.floor(len(x) / 4)):int(np.ceil(len(x) * 3 / 4))]
    diff = round(middle(lstSorted)[-1][-1] - middle(lstSorted)[0][1], 6)
    currMin, currMax = (round(x, 6) for x in np.mean(middle(lstSorted), axis=0))
    result = []
    proto(lst)
    
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

def test(files, limit=60, maxAttempts=5):
    active, currStartTime, attempts, diff = True, 0, 0, OFFSET
    mainOutput, unsettledOutput, noAgreeOutput = [], [], [] # outputs
    env = 'production'
    
    temp, temp2 = [], []
    while active:
        if not files or currStartTime >= limit or attempts == maxAttempts:
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
        
        if __debug__ and env == 'development':
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
                    if __debug__ and env == 'development':
                        print('\t', 'approved', i, j, item, agree)
                else:
                    unsettledOutput.append([item[0], item[1], item[2] + '-' + item[3]])
                ix = getFoundIndexesOf(files, item)
                if ix:
                    if __debug__ and env == 'development':
                        print('\t', item[-3], '-', item)
                    del(files[ix[0]]['data'][ix[1]])
            else:
                if agree >= minAgree:
                    mainOutput.append([currStartTime, currAvgEt, currLabel])
                else:
                    noAgreeOutput += noEnoughAgree
        else:
            currStartTime = currAvgEt
            if __debug__ and env == 'development':
                print('main -\t\t', mainOutput)
                print('unsettled -\t', unsettledOutput)
                print('noAgree -\t', noAgreeOutput)
                print('currStartTime -\t', currStartTime)
                print()
    else:
        if __debug__ and env == 'development':
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