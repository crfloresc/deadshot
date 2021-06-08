from contextlib import ExitStack
from os import chdir, listdir
from os.path import abspath, basename, normpath
from app.lib.utils import containsNumber, getAbsdir, formatLine

def dataLabelingValidate(buffer, validLabels, audioDuration, removeNumberFromLabels):
    currOwner, temp = None, []
    for line in buffer.readlines():
        lineFormated = formatLine(line)
        if len(lineFormated) != 3 or lineFormated[0] == '\\':
            continue
        if not currOwner:
            currOwner = buffer.name.split('/')[-1][0:2]
        label = lineFormated[2].replace(' ','')
        if removeNumberFromLabels:
            label = label[0] if containsNumber(label) else label
        if label in validLabels:
            start = float(lineFormated[0].replace(',','.'))
            if start >= audioDuration:
                continue
            end = float(lineFormated[1].replace(',','.'))
            temp.append((start, end, label))
    return dict({currOwner: temp})

def loadAudacityDataLabeling(path, rev, audioDuration, validLabels, removeNumberFromLabels, ext='txt'):
    sampleData = dict()
    filespath = sorted([getAbsdir(path, x) for x in listdir(path) if x.split('.')[-1] == ext and rev in x.split('.')])
    sampleName = basename(normpath(abspath(path)))
    if not filespath:
        raise Exception('No files found')
    with ExitStack() as stack:
        filesData = [stack.enter_context(open(fname)) for fname in filespath]
        for fileBuffer in filesData:
            sampleData.update(dataLabelingValidate(fileBuffer, validLabels, audioDuration, removeNumberFromLabels))
    return sampleData, f'{sampleName}-{rev}'
