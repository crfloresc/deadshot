from argparse import ArgumentParser

from app.lib import limitJson, openStack, test

def main():
    parser = ArgumentParser(description='Arguments being passed to the program')
    parser.add_argument('--audiolen', '-aL', required=False, default=60, help='Audio lenght')
    args = parser.parse_args()
    print(f'audiolen is {args.audiolen}')
    
    buffer = openStack()
    dataLimited = limitJson(buffer, limit=float(args.audiolen))
    test(list(dataLimited))

if __name__ == '__main__':
    main()