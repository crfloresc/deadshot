from contextlib import ExitStack
from os import listdir
from os.path import abspath

from app.constants import VALID_LABELS
from app.lib.validation import validate, bufferValidate

def getAbsdir(path, file):
    return abspath(f'{path}/{file}')

def load(path, customValidLabels=VALID_LABELS):
    result = dict()
    filespath = [getAbsdir(path, x) for x in listdir(path)]
    with ExitStack() as stack:
        filesData = [stack.enter_context(open(fname)) for fname in filespath]
        for fileBuffer in filesData:
            result.update(bufferValidate(fileBuffer, customValidLabels))
    return result, len(result)

def openStack(path):
    '''
    @deprecated
    '''
    result = []
    filespath = [getAbsdir(path, x) for x in listdir(path)]
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in filespath]
        for file in files:
            result += [validate(file)]
    return result