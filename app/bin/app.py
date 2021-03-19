from argparse import ArgumentParser
import numpy as np
from app.lib import limitJson, openStack, test, mdpo, load, shot

def compare(v1, v2, offset=0.150, debug=False):
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
                print(diffStart, diffEnd, diffStart >= 0, diffEnd >= 0, diffEnd <= offset, e1[2] == e2[2])
            if diffStart >= 0 and diffStart <= offset and diffEnd >= 0 and diffEnd <= offset and e1[2] == e2[2]:
                if debug: print(diffStart, diffEnd, e1[2])
                yPlot[i] = round(e2[0])
                agree += 1
                va1[i] += 1
                cv2.remove(e2)
    return agree/len(cv1)*100, [agree, len(cv1)], va1, xPlot, yPlot

def getArgs():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    parser.add_argument('--audiolen', '-aL', required=False, default=60, help='Audio lenght')
    parser.add_argument('--sample', '-s', required=True, default='./sample', help='Sample path')
    return parser.parse_args()

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

def test(x, y):
    from sklearn.metrics import cohen_kappa_score
    from nltk import agreement
    import pingouin as pg
    import pandas as pd
    formatted = [[1,i,x[i]] for i in range(len(x))] + [[2,i,y[i]] for i in range(len(y))]
    ratingtask = agreement.AnnotationTask(data=formatted)
    data = pd.DataFrame(data={'x':x, 'y':y})
    kappa = ratingtask.kappa() # cohen_kappa_score(x, y)
    cronbach = pg.cronbach_alpha(data=data)
    alpha = ratingtask.alpha()
    pi = ratingtask.pi()
    return kappa, cronbach, alpha, pi

def showMetrics(v1, v2, ioa):
    kappa, cronbach, alpha, pi = test(v1, v2)
    print('*** METRICS ***')
    print('Exact IOA: {}%'.format(round(ioa, 4)))
    print('Cronbach\'s alpha: {}% {} - {}'.format(round(cronbach[0] * 100, 4), cronbach[1][0], cronbach[1][1]))
    print('Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4)))
    print('Krippendorff\'s alpha: {}%'.format(round(alpha * 100, 4)))
    print('Scott\'s pi: {}%'.format(round(pi * 100, 4)))

def main():
    args = getArgs()
    print(args)
    
    buffer, bLen = load(path=args.sample)
    mdpo(buffer)
    if bLen == 3:
        v1, v2 = ((k, v) for k, v in buffer.items())
        ioa, attemps, assest, x, y = compare(v1[1], v2[1])
        kappa, cronbach, alpha, pi = test(x, y)
        print('{}, attemps: {}'.format(v1[0], attemps))
        showMetrics(x, y, ioa)
        print('Assest: {}'.format(assest))
        print('Observer 1: {}\nObserver 2: {}\n'.format(x, y))
        
        ioa, attemps, assest, x, y = compare(v2[1], v1[1])
        test(x, y)
        print('{}, attemps: {}'.format(v2[0], attemps))
        showMetrics(x, y, ioa)
        print('Assest: {}'.format(assest))
        print('Observer 1: {}\nObserver 2: {}\n'.format(x, y))

if __name__ == '__main__':
    main()