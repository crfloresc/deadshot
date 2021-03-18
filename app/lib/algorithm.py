import numpy as np

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
    '''
    
    '''
    mean = []
    for k, v in result.items():
        for kk, vv in v.items():
            if kk == 'm':
                if not vv:
                    continue
                mean.append(vv)
    
    #print(np.mean(mean, axis=0))
    return result

def fragmentBuffer(buffer, start, diff):
    fragment = []
    for k, v in buffer.items():
        if not v:
            continue
        fragment += [event + [k] for event in v if start == event[0] or abs(start - event[0]) <= diff]
    return fragment

def shot(buffer, limit=60, maxAttempts=5):
    active, currStartTime, attempts, diff = True, 0, 0, 0.160
    
    fragment, temp2 = [], []
    while active:
        if not buffer or currStartTime >= limit or attempts == maxAttempts:
            break
        
        # aqui busca el start y el end de la label
        fragment = fragmentBuffer(buffer, currStartTime, diff)
        
        if not fragment:
            attempts += 1
            continue
        temp2 = proto(fragment)
        fragment = []
        print(temp2.get('R')['approved'])
        
        # remove events approved from main buffer
        for k, v in buffer.items():
            for i, event in enumerate(v):
                foo, bar = ((x[0:2], x[-1]) for x in temp2.get('R')['approved'])
                if event in foo and k == bar:
                    print(event)
        break
        
        ####### Split array and order by label name #######
        '''diff = temp2[2] if temp2[2] > 0 else OFFSET
        temp2 = [splitByLabel(temp2[0]), temp2[1]] # Label segment
        currAvgSt, currAvgEt = temp2[1][0], temp2[1][1]
        minAgree = ceil(len(buffer) / 2)'''