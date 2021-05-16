from bisect import bisect_left
from bokeh.plotting import figure, output_file, show
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, LabelSet, Range1d, HoverTool
from nltk import agreement
from time import process_time

class Dex(object):
    def __init__(self, sample, dataset, src=None, offset=0.150, limit=60.00, debug=False):
        self.sample = sample
        self.files = dataset
        self.src = src
        self.offset = offset
        self.limit = limit
        self.debug = debug
        # For processing
        self.data = {}
        self.agreements = {}
        self.tempAgreements = {}
        self.attemps = {}
        # For chart
        self.colormap = {}
        self.observermap = {}
        self.railmap = {}
        self.ioacolormap = {}
        self.ioarailmap = {}
        # For agree
        self.ratingtask = None

        self.__setupDicts()
        self.__process()

    def __setupDicts(self):
        val = 0.40
        self.colormap = {'VF': 'red', 'N': 'green', 'M': 'blue', 'AM': 'purple', 'R': 'black'}
        self.railmap = {'N': 0, 'M': 0.0013, 'R': 0.0026, 'VF': 0.0039, 'AM': 0.0052}
        self.ioacolormap = {'agreement': 'green', 'noAgreement': 'red'}
        self.ioarailmap = {'agreement': 0.25, 'noAgreement': 0.24}
        for k, v in self.files.items():
            val = val - 0.05
            self.data[k] = []
            self.agreements[k] = []
            self.tempAgreements[k] = []
            self.attemps[k] = []
            self.observermap[k] = val

    def __checkIntegrity(self):
        o1, o2 = (len(v) for k, v in self.agreements.items())
        print([o1, o2])
        return True if o1 == o2 else False

    def __compare(self, v1, v2, observer1, observer2, num):
        cv1, cv2 = v1.copy(), v2.copy()
        #self.data[observer1] = [tuple(_) for _ in cv1]
        #self.agreements[observer2] = [tuple(_) for e in cv1 for _ in cv2 if (abs(e[0] - _[0]) <= self.offset) and (abs(e[1] - _[1]) <= self.offset) and (e[2] == _[2])]
        #'''
        for i, event1 in enumerate(cv1):
            start1, end1, label1 = event1
            self.data[observer1].append(event1)
            #res = res + [tuple(_) for _ in cv2 if (abs(start1 - _[0]) <= self.offset) and (abs(end1 - _[1]) <= self.offset) and (label1 == _[2])]
            for j, event2 in enumerate(cv2):
                start2, end2, label2 = event2
                diffStart, diffEnd = abs(start1 - start2), abs(end1 - end2)
                if diffStart <= self.offset and diffEnd <= self.offset and label1 == label2:
                    self.agreements[observer2].append(cv2[j])
                    self.tempAgreements[observer2].append(cv2[j])
                    cv2.remove(event2)
                    break
        #self.agreements[observer2] = res
        #'''

    def __test(self, v):
        from math import floor, ceil
        cv = v.copy()
        #cv = [(0, 0.124560, 'R'), (0, 0.144560, 'VF'), (0.201564, 0.856712, 'N')]
        limit = 120
        d = 100 # 441
        last = None
        reset = False
        track = [_ for _ in range(0, int(limit) * d)]
        while cv:
            reset = False
            for i in range(0, int(limit) * d):
                if reset:
                    break
                if last:
                    ts, te, label = last
                    sts, ste = floor(ts * d), floor(te * d)
                    #print(i, sts, ste, label)
                    if i >= sts and i <= ste:
                        if track[i] != i:
                            track[i] = track[i] + label
                        else:
                            track[i] = label
                        if i == ste or i == ceil(te * d) or i == round(te * d):
                            last = None
                            reset = True
                            del cv[0]
                    if i >= ste:
                        break
                else:
                    for j, (ts, te, label) in enumerate(cv):
                        ds = i - ts * d
                        de = i - te * d
                        if i < te * d and ds >= 0 and de <= 0:
                            #if i != round(ts * d) and i > round(ts * d) and i < round(te * d):
                            #    print(ts * d, te * d, label, track[round(ts * d)])
                            if track[round(ts * d)] != label and i > 0:
                                #print(ts, te, label, '-', ts * d, te * d, '-', track[round(ts * d)], i)
                                reset = True
                                last = (ts, te, label)
                                break
                            if track[i] != i:
                                track[i] = track[i] + label
                            else:
                                track[i] = label
                            if i == floor(te * d) or i == ceil(te * d) or i == round(te * d):
                                del cv[j]
                            break
            limit = limit + 1
        print('len track', len(track))
        return track
    def __test2(self, v):
        from decimal import getcontext, ROUND_HALF_UP, Decimal
        getcontext().prec = 5
        getcontext().rounding = ROUND_HALF_UP
        pv = [(0, 0.144560, 'RVF'), (0.201564, 0.856712, 'N')] # procesed vector
        L = 1 # actually 90 seg
        MS = 1000 # constant
        d = 10 # framing in ms
        td = MS / d
        defaultLabel = 'R'
        track = [defaultLabel for _ in range(0, L * int(td))]
        for i, (st, et, label) in enumerate(pv):
            tst, tet = int(Decimal(st * td).to_integral_value()), int(Decimal(et * td).to_integral_value())
            #print(st*td, et*td)
            #print('[DEBUG]', tst, tet)
            for j in range(tst, tet):
                track[j] = label
        print(track)
    def __test3(self):
        v = [(0, 0.101870, 'R'), (0, 0.144560, 'VF'), (0.201564, 0.856712, 'N'), (0.856712, 0.900000, 'M')] # vector
        result = []
        temp = []
        indexes = []

        for i, e in enumerate(v):
            st, et, label = e
            if i > 0:
                rst, ret, rlabel = result[i - 1]
                if st < ret:
                    if st >= rst:
                        temp.append(st)
                    if et >= ret:
                        temp.append(et)
                    temp.append(rlabel + label)
            if temp:
                result.append(tuple(temp))
                indexes.append(i - 1)
                temp = []
            else:
                result.append(e)

        for i, j in enumerate(indexes):
            del result[j - i]

        print(result)
    def __test4(self):
        v = [(0, 2, 'R'), (0.5, 1.5, 'VF'), (0.75, 1.75, 'M')]
        cv = v
        ccv = []
        result = []
        debug = True

        lastCopy = None
        toAdd = []
        for i, (parentSt, parentEt, parentLab) in enumerate(cv):
            print(f'[DEBUG] parent: {(parentSt, parentEt, parentLab)}')
            print(f'[DEBUG] clone: {lastCopy}')
            if i > 0:
                for j, (childSt, childEt, childLab) in enumerate(lastCopy):
                    overlap = max(0, min(parentEt, childEt) - max(parentSt, childSt))
                    print(f'[DEBUG] child {(parentSt, parentEt, parentLab), overlap, (childSt, childEt, childLab)}')
                    if overlap > 0 and parentSt != childSt and parentEt != childEt and parentLab != childLab:
                        val1st = min(childSt, parentSt)
                        val1et = max(childSt, parentSt)
                        val1Label = childLab if parentSt > childSt else parentLab
                        val2st = max(childSt, parentSt)
                        val2et = min(childEt, parentEt)
                        val2Label = childLab + parentLab
                        val3st = min(parentEt, childEt)
                        val3et = max(parentEt, childEt)
                        val3Label = parentLab if parentEt > childEt else childLab
                        if val1st != val1et:
                            result.append((val1st, val1et, val1Label))
                        result.append((val2st, val2et, val2Label))
                        if val3st != val3et:
                            result.append((val3st, val3et, val3Label))
                        del lastCopy[j]
                        #print(result)
                        lastCopy = sorted(list(set(result + lastCopy)))
            else:
                lastCopy = cv.copy()

        lastIndex = 0
        continuity = []
        for i, (st, et, lab) in enumerate(lastCopy):
            if i > 0:
                if lastCopy[0][1] == st:
                    lastIndex = i
                    continuity.append((st, et, lab))
            else:
                continuity.append((st, et, lab))
        print(lastCopy)

'''
i = 0
vl = len(v)
while i < vl and False:
    if i + 1 < vl:
        A, B = v[i], v[i + 1]
        #print(f'[DEBUG] A: {A}, B: {B}')
        #print(subtractRanges(A, B))
        ranges = subtractRanges(A, B)
        if ranges[-1]:
            v.remove(A)
            v.remove(B)
            i = -1
            for e1 in ranges:
                for j, e2 in enumerate(e1):
                    if e2:
                        v.insert(0, e2)
        vl = len(v)
        v = sorted(v)
        #print(f'[DEBUG] i: {i}, vl: {vl}')
        #print(f'[DEBUG-END] vectors: {v}')
    i += 1

#print(f'[INFO] -- {v}')


v = [(0, 2, 'R'), (0.5, 1.5, 'VF'), (0.75, 1.75, 'M'), (1, 2, 'R'), (1, 3, 'AM'), (4, 5, 'N'), (4.5, 5, 'M'), (4.9, 7, 'MM'), (7.1, 7.5, 'DD'), (6.5, 7.3, 'AA')]
usedKeys = []
def getKeys(v, n=2):
    return sorted(list(set([e[-1] for e in v if e[-1] not in usedKeys])))[0:n]
keys = getKeys(v)
currV = [e for e in v if e[-1] in keys]
inQueue = (e for e in v if e[-1] not in keys)

print(f'[DEBUG] start: {currV}')

def isSame(v1, v2):
    return True if v1[0] == v2[0] and v1[1] == v2[1] and v1[2] == v2[2] else False

result = []
lastCopy = currV.copy()
used = []
i = 0
unfinished = True
while unfinished:
    pe = lastCopy[i]
    for j, ce in enumerate(lastCopy):
        if isSame(pe, ce):
            continue
        (pst, pet, pl), (cst, cet, cl) = pe, ce
        overlap = max(0, min(pet, cet) - max(pst, cst))
        if overlap > 0:
            print(f'main: {pe}, child: {ce}')
            print(f'[DEBUG] prop overlap: {overlap}')
            st1 = min(cst, pst)
            et1 = max(cst, pst)
            l1 = cl if pst > cst else pl
            st2 = max(cst, pst)
            et2 = min(cet, pet)
            l2 = cl + pl
            st3 = min(pet, cet)
            et3 = max(pet, cet)
            l3 = pl if pet > cet else cl
            down, mid, up = (st1, et1, l1), (st2, et2, l2), (st3, et3, l3)
            used.append(ce)
            del lastCopy[i]
            del lastCopy[j - 1]
            if st1 == et1:
                down = []
            else:
                down = [down]
            if st3 == et3:
                up = []
            else:
                up = [up]
            lastCopy = lastCopy + down + [mid] + up
            lastCopy = sorted(lastCopy)
            i = 0
            #print(f'[DEBUG] props: {down, mid, up}')
            print(f'[DEBUG] -- {lastCopy}')
            print()
    i += 1
    if i == len(lastCopy):
        unfinished = False
        result.append(lastCopy)
        i = 0
        usedKeys.append(keys)
print(f'[INFO] -- {lastCopy}')
for j, (childSt, childEt, childLab) in enumerate(lastCopy):
    overlap = max(0, min(parentEt, childEt) - max(parentSt, childSt))
    if overlap > 0 and parentSt != childSt and parentEt != childEt and parentLab != childLab:
        val1st = min(childSt, parentSt)
        val1et = max(childSt, parentSt)
        val1Label = childLab if parentSt > childSt else parentLab
        val2st = max(childSt, parentSt)
        val2et = min(childEt, parentEt)
        val2Label = childLab + parentLab
        val3st = min(parentEt, childEt)
        val3et = max(parentEt, childEt)
        val3Label = parentLab if parentEt > childEt else childLab
        if val1st != val1et:
            result.append((val1st, val1et, val1Label))
        result.append((val2st, val2et, val2Label))
        if val3st != val3et:
            result.append((val3st, val3et, val3Label))
        del lastCopy[j]
        lastCopy = sorted(list(set(result + lastCopy)))
lastEvent = v[0]
toAdd = []
newDict = {}
k = 0
for i, e in enumerate(v):
    if i > 0:
        overlap = max(0, min(e[1], lastEvent[1]) - max(e[0], lastEvent[0]))
        if overlap > 0:
            toAdd.append(e)
            #print(f'last -> {lastEvent}, current -> {e}')
        else:
            toAdd.append(lastEvent)
            newDict[k] = tuple(sorted(toAdd))
            lastEvent = e
            toAdd = []
            k += 1
else:
    toAdd.append(lastEvent)
    newDict[k] = tuple(sorted(toAdd))
    lastEvent = None
    toAdd = []
    k = 0

a = []
for k, v in newDict.items():
    for i, e in enumerate(v):
        lastEvent = e
        if i == 0:
            pass
        val1st = min(childSt, parentSt)
        val1et = max(childSt, parentSt)
        val1Label = childLab if parentSt > childSt else parentLab
        val2st = max(childSt, parentSt)
        val2et = min(childEt, parentEt)
        val2Label = childLab + parentLab
        val3st = min(parentEt, childEt)
        val3et = max(parentEt, childEt)
        val3Label = parentLab if parentEt > childEt else childLab
    print(k, v)
'''

    def __process(self, debug=True):
        from timeit import timeit
        t = process_time()
        data1, data2 = ((k, v) for k, v in self.files.items())
        o1, v1 = data1
        o2, v2 = data2
        if not v1 or not v2:
            raise Exception('v1 or v2 not present')

        self.__compare(v1, v2, o1, o2, 1)
        self.__compare(v2, v1, o2, o1, 2)
        if not self.__checkIntegrity():
            print(self.agreements)
            raise Exception('There are difference between two observers')
        elapsed_time = process_time() - t
        print(elapsed_time)
        self.__test4()
        #track1 = self.__test(v1)
        #track2 = self.__test(v2)
        #self.__ratingtask(track1, track2)
        #print(self.ratingtask.kappa())
        #import edit_distance
        #ref = [row[-1] for row in v1]
        #hyp = [row[-1] for row in v2]
        #sm = edit_distance.SequenceMatcher(a=ref, b=hyp)
        #print('ratio', sm.ratio())

    def __ratingtask(self, v1, v2):
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)

    def graphBrokenBarh(self, title=None, tools=None):
        pass
        if not title:
            title = 'IOA of {} - Observer 1 vs. Observer 2'.format(self.sample)
        if not tools:
            tools = 'wheel_zoom, pan, save, reset,'
        p = figure(title=title, tools=tools, y_range=Range1d(bounds=(0, 1)), x_range=(0, 60), sizing_mode='stretch_both')

        # Draw all events
        for i, (k, v) in enumerate(self.data.items()):
            for j, e in enumerate(v):
                start, end, label = e
                diff = abs(end - start)
                observer, color, rail = self.observermap[k], self.colormap[label], self.railmap[label]
                #data = {'x': [start, start + diff], 'y': [observer + rail, observer + rail], 'start': [start, start], 'end': [end, end], 'label': [label, label]}
                data = {'x': [start], 'y': [observer + rail], 'start': [start], 'end': [end], 'label': [label]}
                source = ColumnDataSource(data=data)
                if j == 0: # only for draw observer label
                    observerLabel = Label(x=start, y=observer, text=k, x_offset=-30, render_mode='canvas')
                    p.add_layout(observerLabel)
                #p.line(x='x', y='y', name=label, line_color=color, line_width=6, source=source)
                p.hbar(y='y', height=0.007, left='start', right='end', name=label, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7, source=source)

        # Only for draw legend colors
        for k, v in self.colormap.items():
            p.line(0, 0, line_color=v, legend_label=k, line_width=6)

        result = {'agreement': [], 'noAgreement': []}
        lastStart, lastEnd = 0, 0
        z1, z2 = 0, 0
        for i, (v1, v2) in enumerate(zip(*self.agreements.values())):
            start1, end1, label1 = v1
            start2, end2, label2 = v2
            newStart, newEnd = start2 if start1 > start2 else start1, end2 if end1 < end2 else end1
            if lastStart - newStart < 0:
                result['agreement'].append((z1, z2))
                result['noAgreement'].append((z2, newStart))
                z1, z2 = newStart, newEnd
            else:
                z2 = newEnd
            lastStart = newEnd
        else:
            result['agreement'].append((z1, z2))
            result['noAgreement'].append((z2, self.limit))

        # draw temp agreement bars
        '''railmap = {'ZZ': 0.21, 'XX': 0.19}
        for k, v in self.agreements.items():
            for e in v:
                start, end, label = e
                diff = abs(end - start)
                p.line([start, start + diff], [railmap[k], railmap[k]], line_color='green', line_alpha=0.8, line_width=6)'''

        # draw agreement bar and annotation
        for k, v in result.items():
            for (start, end) in v:
                color, rail = self.ioacolormap.get(k), self.ioarailmap.get(k)
                if k == 'noAgreement':
                    p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color=color))
                #p.line([start, start + abs(end - start)], [y, y], line_color=color, line_alpha=0.8, line_width=6)
                p.hbar(y=rail, height=0.007, left=start, right=end, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7)

        # add observers names
        '''citation = Label(x=70, y=500, x_units='screen', y_units='screen',
                 text=self.__kappa(0.87), render_mode='css',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)
        p.add_layout(citation)'''

        # Notation
        p.line([0, self.limit], [0.33, 0.33], line_color='gray', line_width=1, line_alpha=0.2)
        p.line([0, self.limit], [0.28, 0.28], line_color='gray', line_width=1, line_alpha=0.2)

        ticks = [i for i in range(0, int(self.limit) + 1) if i % 2 == 0]
        node_hover_tool = HoverTool(names=['VF', 'R', 'N', 'M', 'AM'], tooltips=[('label', '@label'), ('start', '@start'), ('end', '@end')])

        p.add_tools(node_hover_tool)
        p.legend.title = 'Etiquetas'
        p.xaxis.axis_label = 'Timeline'
        p.yaxis.axis_label = 'Observer'
        #p.legend.click_policy = 'hide'
        p.xaxis.ticker = ticks
        p.ygrid.grid_line_dash = [6, 4]
        p.xaxis.bounds = (0, 90)
        p.x_range.min_interval = 7
        #show(p)

    def __kappa(self):
        if not self.ratingtask:
            return None
        kappa = self.ratingtask.kappa()
        return 'Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4))

    def saveMetrics(self):
        filename = '{0}/output/metrics.txt'.format(self.src)
        with open(filename, 'a') as out:
            out.write('Observer {0}\n'.format(self.observer + 1))
            out.write('{0}, attemps: {1}\n'.format(self.oName, self.attemps))
            #out.write('Cohen\'s Kappa: {0}%\n'.format(round(self.kappa(printRes=False) * 100, 4)))
