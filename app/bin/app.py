from argparse import ArgumentParser

from app.lib import limitJson, openStack, test, mdpo

def duration(buffer):
    import numpy as np
    from prettytable import PrettyTable
    x = PrettyTable()
    x.field_names = ['Observer', 'R', 'AM', 'N', 'M', 'VF']
    endTimes, labels = [], []
    countLabelR, countLabelAM, countLabelN, countLabelM, countLabelVF = 0, 0, 0, 0, 0
    countEndTimeInLabelR, countEndTimeInLabelAM, countEndTimeInLabelN, countEndTimeInLabelM, countEndTimeInLabelVF = 0, 0, 0, 0, 0
    for i, json in enumerate(buffer):
        owner, data = json['owner'], json['data']
        for j, item in enumerate(data):
            endTime = item[1]
            label = item[2]
            if label == 'R':
                countEndTimeInLabelR += endTime
                countLabelR += 1
            elif label == 'VF':
                countEndTimeInLabelVF += endTime
                countLabelVF += 1
            elif label == 'AM':
                countEndTimeInLabelAM += endTime
                countLabelAM += 1
            elif label[0] == 'N':
                countEndTimeInLabelN += endTime
                countLabelN += 1
            elif label[0] == 'M':
                countEndTimeInLabelM += endTime
                countLabelM += 1
        else:
            x.add_row([owner, countLabelR, countLabelAM, countLabelN, countLabelM, countLabelVF])
            labels.append([countLabelR, countLabelAM, countLabelN, countLabelM, countLabelVF])
            endTimes.append([countEndTimeInLabelR, countEndTimeInLabelAM, countEndTimeInLabelN, countEndTimeInLabelM, countEndTimeInLabelVF])
            countLabelR, countLabelAM, countLabelN, countLabelM, countLabelVF = 0, 0, 0, 0, 0
    else:
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

def main():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    parser.add_argument('--audiolen', '-aL', required=False, default=60, help='Audio lenght')
    parser.add_argument('--sample', '-s', required=True, default='./sample', help='Sample path')
    args = parser.parse_args()
    print(args)
    
    buffer = openStack(path=args.sample)
    mdpo(buffer)
    #dataLimited = limitJson(buffer, limit=float(args.audiolen))
    #test(list(dataLimited), limit=float(args.audiolen))

if __name__ == '__main__':
    main()