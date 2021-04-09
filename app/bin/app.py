from argparse import ArgumentParser
import numpy as np
import seaborn as sns
import pandas as pd
from app.lib import Measures, load
from prettytable import PrettyTable

class Dex(object):
    def __init__(self, buffer, observer, src=None, showAttemps=True, offset=0.150, debug=False):
        self.table = PrettyTable()
        self.files = buffer
        self.offset = offset
        self.debug = debug
        self.ratingtask = None
        self.assest = None
        self.comp1, self.comp2 = None, None
        self.observer = observer
        self.dv1 = None
        self.dv2 = None
        self.showAttemps = showAttemps
        self.src = src
        
        if observer == 0:
            self.__observer1()
        elif observer == 1:
            self.__observer2()
        else:
            raise NotImplementedError('Only supported 2 observers')
    
    def __observer1(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        ioa, attemps, self.assest, self.comp1, self.comp2, self.dv1, self.dv2 = self.__compare(v1[1], v2[1])
        if self.showAttemps:
            print('\n{}, attemps: {}'.format(v1[0], attemps))
        self.__test(self.comp1, self.comp2)
    
    def __observer2(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        ioa, attemps, self.assest, self.comp1, self.comp2, self.dv1, self.dv2 = self.__compare(v2[1], v1[1])
        if self.showAttemps:
            print('\n{}, attemps: {}'.format(v2[0], attemps))
        self.__test(self.comp1, self.comp2)
    
    def __compare(self, v1, v2):
        if not v1 or not v2:
            return None
        cv1, cv2 = v1.copy(), v2.copy()
        start, end, agree = None, None, 0
        va1 = [0 for v in cv1]
        
        bars1, bars2 = [], [-1 for v in cv1]
        xPlot, yPlot = [], [-1 for v in cv1]
        for i, e1 in enumerate(cv1):
            xPlot.append(round(e1[0]))
            bars1.append(e1[1] - e1[0])
            for e2 in cv2:
                diffStart, diffEnd = abs(e1[0] - e2[0]), abs(e1[1] - e2[1])
                if i == 2 and self.debug:
                    print(e1, e2)
                    print(diffStart, diffEnd, diffStart >= 0, diffEnd >= 0, diffEnd <= self.offset, e1[2] == e2[2])
                if diffStart >= 0 and diffStart <= self.offset and diffEnd >= 0 and diffEnd <= self.offset and e1[2] == e2[2]:
                    if self.debug: print(diffStart, diffEnd, e1[2])
                    yPlot[i] = round(e1[0])
                    bars2[i] = e2[1] - e2[0]
                    agree += 1
                    va1[i] += 1
                    cv2.remove(e2)
                    break
        return agree/len(cv1)*100, [agree, len(cv1)], va1, xPlot, yPlot, bars1, bars2
    
    def __test(self, v1, v2):
        from sklearn.metrics import cohen_kappa_score
        from nltk import agreement
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)
    
    def graphGroupedBarplot(self):
        import matplotlib.pyplot as plt
        barWidth = 0.25
        r1 = np.arange(len(self.dv1))
        r2 = [x + barWidth for x in r1]
        plt.bar(r1, self.dv1, color='#7f6d5f', width=barWidth, edgecolor='white', label='var1')
        plt.bar(r2, self.dv2, color='#557f2d', width=barWidth, edgecolor='white', label='var2')
        plt.savefig('{0}{1}_groupedbarplot.png'.format(self.src, self.observer + 1))
        plt.clf()
    
    def graphDensityPlot(self):
        import matplotlib.pyplot as plt
        sns.set(style="darkgrid")
        fig = sns.kdeplot(self.dv1, shade=True, color='r')
        fig = sns.kdeplot(self.dv2, shade=True, color='b')
        plt.savefig('{0}{1}_densityplot.png'.format(self.src, self.observer + 1))
        plt.clf()
    
    def graphDensityChart(self):
        import matplotlib.pyplot as plt
        plt.rcParams['figure.figsize'] = 12, 8
        sns.set(style='whitegrid')
        data = pd.DataFrame({
            'a': self.dv1,
            'b': self.dv2
        })
        data = pd.melt(data, var_name='observers', value_name='value')
        sns.kdeplot(data=data, x='value', hue='observers', fill=True, common_norm=False, alpha=0.6, palette='viridis')
        plt.savefig('{0}{1}_densitychart.png'.format(self.src, self.observer + 1))
        plt.clf()
    
    def graphHeatmap(self):
        import matplotlib.pyplot as plt
        df = pd.DataFrame({ 'a': self.dv1, 'b': self.dv2 })
        sns.heatmap(df)
        plt.savefig('{0}{1}_heatmap.png'.format(self.src, self.observer + 1))
        plt.clf()
    
    def graphSpaghettiPlot(self):
        import matplotlib.pyplot as plt
        df = pd.DataFrame({ 'x': [i for i, v in enumerate(self.dv1)], 'y1': self.dv1, 'y2': self.dv2 })
        plt.style.use('seaborn-darkgrid')
        palette = plt.get_cmap('Set1')
        num = 1
        for column in df.drop('x', axis=1):
            num += 1
            plt.plot(df['x'], df[column], marker='', color=palette(num), linewidth=1, alpha=0.9, label=column)
        plt.legend(loc=2, ncol=1)
        plt.title('Observer {0} - '.format(self.observer + 1), loc='left', fontsize=12, fontweight=0, color='orange')
        plt.xlabel('Time')
        plt.ylabel('Delta')
        plt.savefig('{0}{1}_spaghettiplot.png'.format(self.src, self.observer + 1))
        plt.clf()
    
    def graphLollipopPlot(self):
        import matplotlib.pyplot as plt
        # Create a dataframe
        df = pd.DataFrame({ 'group': [i for i, v in enumerate(self.dv1)], 'value1': self.dv1, 'value2': self.dv2 })
        # Reorder it following the values of the first value:
        ordered_df = df.sort_values(by='value1')
        my_range = range(1, len(df.index) + 1)
        # The horizontal plot is made using the hline function
        plt.hlines(y=my_range, xmin=ordered_df['value1'], xmax=ordered_df['value2'], color='grey', alpha=0.4)
        plt.scatter(ordered_df['value1'], my_range, color='skyblue', alpha=1, label='value1')
        plt.scatter(ordered_df['value2'], my_range, color='green', alpha=0.4 , label='value2')
        plt.legend()
        # Add title and axis names
        plt.yticks(my_range, ordered_df['group'])
        plt.title('Comparison of the value 1 and the value 2', loc='left')
        plt.xlabel('Value of the variables')
        plt.ylabel('Group')
        plt.savefig('{0}{1}_lollipopplot.png'.format(self.src, self.observer + 1))
        plt.clf()
    
    def showAssest(self):
        print('Assest: {}'.format(self.assest))
    
    def showComparation(self):
        print('Observer 1: {}\nObserver 2: {}\n'.format(self.comp1, self.comp2))
    
    def showTable(self):
        print(self.table)
    
    def kappa(self, printRes=True):
        kappa = self.ratingtask.kappa()
        if printRes:
            print('Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4)))
        return kappa
    
    def kalpha(self, printRes=True):
        alpha = self.ratingtask.alpha()
        if printRes:
            print('Krippendorff\'s alpha: {}%'.format(round(alpha * 100, 4)))
        return alpha
    
    def spi(self, printRes=True):
        pi = self.ratingtask.pi()
        if printRes:
            print('Scott\'s pi: {}%'.format(round(pi * 100, 4)))
        return pi

def graph():
    import seaborn as sns
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Create a dataset
    data = np.array([
        [0.58191293, 0.49939776, 0.58191293, 0.58191293, 0.58191293, 0.58191293, 0.58191293, 0.58191293, 0.58191293, 0.58191293],
        [0.49939776, 0.58191293, 0.58191293, 0.58191293, 0.58191293, 0.49939776, 0.58191293, 0.58191293, 0.49939776, 0.58191293]])
    #data = np.random.random((2,10))
    #print(data)
    df = pd.DataFrame(data, columns=["a","b","c","d","e","f","g","h","i","j"])
    # plot a heatmap with annotation
    sns.heatmap(df, annot=True, annot_kws={"size": 7}, cbar=False)
    plt.show()

def getArgs():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    parser.add_argument('--audiolen', '-aL', required=False, default=60, help='Audio lenght')
    parser.add_argument('--sample', '-s', required=True, default='./sample', help='Sample path')
    return parser.parse_args()

def main():
    args = getArgs()
    print(args)
    
    buffer, bLen = load(path=args.sample)
    #graph()
    if bLen == 2:
        # Observer 1
        dex = Dex(buffer, observer=0, showAttemps=False, src=args.sample)
        #dex.showAssest()
        #dex.kappa()
        #dex.kalpha()
        #dex.spi()
        #dex.showComparation()
        dex.graphGroupedBarplot()
        dex.graphDensityPlot()
        dex.graphDensityChart()
        dex.graphHeatmap()
        dex.graphSpaghettiPlot()
        dex.graphLollipopPlot()
        
        # Observer 2
        dex = Dex(buffer, observer=1, showAttemps=False)
        #dex.showAssest()
        #dex.kappa()
        #dex.kalpha()
        #dex.spi()
        #dex.showComparation()
    else:
        raise NotImplementedError('Only accepted two observers')
    '''z = Measures(buffer, metric='label')
    z.showTable()
    z.mdpo()
    z.kappa()
    z.alpha()
    z.pi()'''

if __name__ == '__main__':
    main()
