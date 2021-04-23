from argparse import ArgumentParser
from app.lib import Dex, load

def getArgs():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    parser.add_argument('--limit', '-aL', required=False, default=60, help='Audio lenght')
    parser.add_argument('--sample', '-sp', required=True, default='./sample', help='Sample path')
    parser.add_argument('--rev', '-r', required=True, help='Revision of file')
    parser.add_argument('--offset', '-do', required=False, default=0.150, help='Offset')
    return parser.parse_args()

def main():
    args = getArgs()
    limit, offset = float(args.limit), float(args.offset)

    buffer, bLen = load(path=args.sample, rev=args.rev, limit=limit)
    if bLen == 2:
        dex = Dex(buffer, src=args.sample, offset=offset, limit=limit)
        dex.graphBrokenBarh()
    else:
        raise NotImplementedError('Only accepted two observers')

if __name__ == '__main__':
    main()
