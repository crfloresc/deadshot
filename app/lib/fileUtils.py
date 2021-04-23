from contextlib import ExitStack
from os import listdir
from os.path import abspath

from app.lib.validation import bufferValidate

VALID_LABELS = [
    'AM',
    'R',
    'M',
    'M1',
    'N',
    'N1',
    'VF'
]

def getAbsdir(path, file):
    return abspath(f'{path}/{file}')

def load(path, rev, limit, ext='txt', customValidLabels=VALID_LABELS):
    result = dict()
    filespath = [getAbsdir(path, x) for x in listdir(path) if x.split('.')[-1] == ext and rev in x.split('.')]
    if not filespath:
        raise Exception('No files found')
    with ExitStack() as stack:
        filesData = [stack.enter_context(open(fname)) for fname in filespath]
        for fileBuffer in filesData:
            result.update(bufferValidate(fileBuffer, customValidLabels, limit))
    return result, len(result)
