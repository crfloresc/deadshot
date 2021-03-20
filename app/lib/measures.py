import numpy as np
from prettytable import PrettyTable
from nltk import agreement

def hasNumber(s):
    return any(char.isdigit() for char in s)

class Measures(object):
    def __init__(self, buffer, offset=0.150, metric='label', header=None):
        self.table = PrettyTable()
        self.files = buffer
        self.offset = offset
        self.ratingtask = None
        self.header = header if header else ['Observer']
        self.tableBody = []
        self.countLabels = []
        self.nIntervals = 0
        
        if metric == 'label':
            self.__checkLabels()
            self.__metricForLabel()
        elif metric == 'start':
            print('START')
            self.__metricForStart()
        else:
            raise NotImplementedError('Metric no supported')
    
    def __checkLabels(self):
        labels = [np.unique(sorted([e[2] for e in v]), axis=0) for v in self.files.values()]
        labelsSanitized = [[v[0] if hasNumber(v) else v for v in h] for h in labels]
        labelsLen = np.array([len(item) for item in labelsSanitized])
        sameLabels = np.all(labelsLen == labelsLen[0])
        self.nIntervals = labelsLen[0]
        if not sameLabels:
            raise NotImplementedError('Labels doesnt match')
    
    def __setTableHeader(self):
        labels = np.unique(sorted([e[2] for events in self.files.values() for e in events]), axis=0)
        labelsSanitized = [v[0] if hasNumber(v) else v for v in labels]
        self.header += labelsSanitized
    
    def __metricForLabel(self):
        intervals, labels = [], []
        currLabel, count = None, 0
        
        for k, v in self.files.items():
            owner, labelTrack = k, sorted(v, key=lambda v : v[2])
            for event in labelTrack:
                label = event[2]
                if not currLabel:
                    currLabel = label
                if currLabel != label:
                    intervals.append(count)
                    currLabel = None
                    count = 1
                    continue
                count += 1
            else:
                intervals.append(count)
                currLabel = None
                count = 0
            self.tableBody += [[owner] + intervals]
            self.countLabels.append(intervals)
            intervals = []
        formatted = [[i + 1, j, cc] for i, c in enumerate(self.countLabels) for j, cc in enumerate(c)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)
    
    def __compareTwoVecs(self, v1, v2, debug=False):
        v1, v2 = v1[1], v2[1]
        if not v1 or not v2:
            return None
        cv1, cv2 = v1.copy(), v2.copy()
        start, end, agree = None, None, 0
        va1 = [0 for v in cv1]
        
        xPlot, yPlot = [], [-1 for v in cv1]
        for i, e1 in enumerate(cv1):
            xPlot.append(round(e1[0]))
            for e2 in cv2:
                diffStart, diffEnd = abs(e1[0] - e2[0]), abs(e1[1] - e2[1])
                if i == 2 and debug:
                    print(e1, e2)
                    print(diffStart, diffEnd, diffStart >= 0, diffEnd >= 0, diffEnd <= self.offset, e1[2] == e2[2])
                if diffStart >= 0 and diffStart <= self.offset and diffEnd >= 0 and diffEnd <= self.offset and e1[2] == e2[2]:
                    if debug: print(diffStart, diffEnd, e1[2])
                    yPlot[i] = round(e2[0])
                    agree += 1
                    va1[i] += 1
                    cv2.remove(e2)
        return agree/len(cv1)*100, [agree, len(cv1)], va1, xPlot, yPlot
    
    def __metricForStart(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        self.__compareTwoVecs(v1, v2)
        formatted = [[i + 1, j, cc] for i, c in enumerate(self.countLabels) for j, cc in enumerate(c)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)
    
    def showTable(self):
        if metric != 'label':
            raise NotImplementedError('This method has been implemented for your current metric')
        self.__setTableHeader()
        self.table.field_names = self.header
        for row in self.tableBody:
            self.table.add_row(row)
        print(self.table)
    
    def totDur(self, printRes=True):
        if metric != 'label':
            raise NotImplementedError('This method has been implemented for your current metric')
        sums = np.sum(self.countLabels, axis=1)
        shorterDur, longerDur = np.min(sums), np.max(sums)
        totalDur = shorterDur / longerDur
        if printRes:
            print('Total duration is: {}%'.format(round(totalDur, 4) * 100))
        return totalDur
    
    def mdpo(self, printRes=True):
        '''Mean duration per occurrence (mdpo)
        
        Parameters
        ----------
        files : arr
            The files to get percent of mdpo
        
        Raises
        ------
        NotImplementedError
            If no match numbers label between files.
        
        Returns
        -------
        list
            a list of strings of mdpo
        
        References
        ----------
        https://www.youtube.com/watch?v=JUFh-dNGYwo
        '''
        if metric != 'label':
            raise NotImplementedError('This method has been implemented for your current metric')
        shortersDur = np.min(self.countLabels, axis=0)
        longersDur = np.max(self.countLabels, axis=0)
        sumDurIoas = np.sum(shortersDur / longersDur)
        mdpo = sumDurIoas / self.nIntervals
        if printRes:
            print('Mean duration per occurrence is: {}%'.format(round(mdpo, 4) * 100))
        return mdpo
    
    def kappa(self, printRes=True):
        kappa = self.ratingtask.kappa()
        if printRes:
            print('Cohen\'s Kappa: {}%'.format(round(kappa, 4) * 100))
        return kappa
    
    def alpha(self, printRes=True):
        alpha = self.ratingtask.alpha()
        if printRes:
            print('Krippendorff\'s alpha: {}%'.format(round(alpha, 4) * 100))
        return alpha
    
    def pi(self, printRes=True):
        pi = self.ratingtask.pi()
        if printRes:
            print('Scott\'s pi: {}%'.format(round(pi, 4) * 100))
        return pi

def graph(x, y):
    # https://plotly.com/python/parallel-coordinates-plot/
    import plotly.express as px
    df = px.data.iris()
    fig = px.parallel_coordinates(df, color="species_id", labels={"species_id": "Species",
                "sepal_width": "Sepal Width", "sepal_length": "Sepal Length",
                "petal_width": "Petal Width", "petal_length": "Petal Length", },
                color_continuous_scale=px.colors.diverging.Tealrose,
                color_continuous_midpoint=2)
    fig.show()