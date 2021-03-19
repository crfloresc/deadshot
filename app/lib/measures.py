import numpy as np
from prettytable import PrettyTable

class Measures(object):
    def __init__(self, files, mode='mdpo', header=None):
        self.table = PrettyTable()
        self.files = files
        self.mode = mode
        self.header = header if header else ['Observer']
        self.body = []
        self.countLabels = []
        self.nIntervals = 0
        
        self._checkIsSameHeader()
        self._setHeader()
        self._process()
    def _checkIsSameHeader(self):
        cluster = [sorted(v, key=lambda v : v[2]) for k, v in self.files.items()]
        columnLabelCluster = [np.array(labelTrack)[:,2] for labelTrack in cluster]
        preHeaderCluster = [np.unique(v, axis=0) for v in columnLabelCluster]
        headerCluster = [[v[0] if any(char.isdigit() for char in v) else v for v in item] for item in preHeaderCluster]
        headerClusterLen = np.array([len(item) for item in headerCluster])
        isSameHeader = np.all(headerClusterLen == headerClusterLen[0])
        if not isSameHeader:
            raise NotImplementedError('Header doesnt match')
    def _setHeader(self):
        preHeader = [v[0] if any(char.isdigit() for char in v) else v for v in np.unique(sorted([e[2] for events in self.files.values() for e in events]), axis=0)]
        self.nIntervals = len(preHeader)
        self.header += preHeader
    def _process(self):
        intervals, labels = [], []
        currLabel = None
        count = 0
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
            self.body += [[owner] + intervals]
            self.countLabels.append(intervals)
            intervals = []
    def showTable(self):
        self.table.field_names = self.header
        for row in self.body:
            self.table.add_row(row)
        print(self.table)
    def totDur(self, printRes=True):
        sums = np.sum(self.countLabels, axis=1)
        shorterDur, longerDur = np.min(sums), np.max(sums)
        totalDur = shorterDur / longerDur * 100
        if printRes:
            print('Total duration is:', totalDur)
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
        shortersDur = np.min(self.countLabels, axis=0)
        longersDur = np.max(self.countLabels, axis=0)
        sumDurIoas = np.sum(shortersDur / longersDur)
        mdpo = sumDurIoas / self.nIntervals * 100
        if printRes:
            print('Mean duration per occurrence is:', mdpo)

def mdpo(buffer):
    x = PrettyTable()
    z = Measures(buffer)
    z.showTable()
    z.mdpo()
    
    
    header = ['Observer']
    header += [v[0] if any(char.isdigit() for char in v) else v for v in np.unique(sorted([e[2] for events in buffer.values() for e in events]), axis=0)]
    intervals, labels = [], []
    currLabel = None
    count = 0
    body = []
    for k, v in buffer.items():
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
        body += [[owner] + intervals]
        labels.append(intervals)
        intervals = []
    
    x.field_names = header
    for row in body:
        x.add_row(row)
    print(x)
    # Total duration
    sums = np.sum(labels, axis=1)
    shorterDur, longerDur = np.min(sums), np.max(sums)
    totalDur = shorterDur / longerDur * 100
    print('Total duration is:', totalDur)
    
    # Mean duration per occurrence
    shortersDur, longersDur = np.min(labels, axis=0), np.max(labels, axis=0)
    sumDurIoas = np.sum(shortersDur / longersDur)
    mdpo = sumDurIoas / len(labels[0]) * 100
    print('Mean duration per occurrence is:', mdpo)