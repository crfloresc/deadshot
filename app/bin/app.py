from app.lib import Deadshot, loadAudacityDataLabeling
from argparse import ArgumentParser
from json import load as jsonload
from scipy.io import wavfile

def getArgs():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    #parser.add_argument('--audioPath', '-a', required=False, help='Audio file path')
    #parser.add_argument('--audioDurationH', '-aDh', required=False, help='Audio duration')
    #parser.add_argument('--labelPath', '-sp', required=True, help='Audacity\'s label path')
    #parser.add_argument('--rev', '-r', required=True, help='Revision of file')
    #parser.add_argument('--offset', '-do', required=False, default=0.150, help='Offset')
    parser.add_argument('--config', '-c', required=True, help='Path of config file in json')
    return parser.parse_args()

def main():
    args = getArgs()

    # Load config from json
    with open(args.config) as jsonDataFile:
        config = jsonload(jsonDataFile)

    # Check if there present test audio fragment duration
    if config.get('test_audioFragmentDuration'):
        t = config.get('test_audioFragmentDuration')
    # Check if there present audio file path
    if config.get('audioFilePath'):
        sampleRate, data = wavfile.read(config.get('audioFilePath'))
        lenData = len(data)
        t = lenData / sampleRate

    # Raise an error, bad config file
    if not t:
        raise Exception('Bad config file, no audio file/duration <audioFilePath>')
    if not config.get('audacityDataLabelingFilePath'):
        raise Exception('Bad config file, no audacity data labeling file <audacityDataLabelingFilePath>')
    if not config.get('rev'):
        raise Exception('Bad config file, no revision of data <rev>')
    if not config.get('labels'):
        raise Exception('Bad config file, no custom labels <labels>')
    if not config.get('offset'):
        raise Exception('Bad config file, no valid offset <offset>')
    if not config.get('outputPath'):
        raise Exception('Bad config file, no output path <outputPath>')
    if not config.get('labelColors'):
        raise Exception('Bad config file, no label colors <labelColors>')

    # Validation errors
    if len(config.get('labels')) != len(config.get('labelColors')):
        raise Exception('Your labels and label colors is different!')

    # Load data from audacity data labeling file
    sampleData, sampleName = loadAudacityDataLabeling(
        path=config.get('audacityDataLabelingFilePath'),
        rev=config.get('rev'),
        audioDuration=t,
        validLabels=config.get('labels'),
        removeNumberFromLabels=config.get('removeNumberFromLabels'))

    # Check if there are two observers in data
    if len(sampleData) == 2:
        app = Deadshot(
            sampleName,
            sampleData,
            config.get('labels'),
            config.get('outputPath'),
            config.get('labelColors'),
            padding=config.get('padding'),
            framing=config.get('framing'),
            offset=config.get('offset'),
            t=t)
        app.graph()
    else:
        raise NotImplementedError('Only accepted two observers')

if __name__ == '__main__':
    main()
