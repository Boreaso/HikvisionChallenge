import sys
import logging

TIME = 0.5


def main():
    fn = sys.argv[1]
    MT = 0
    with open(fn) as f:
        lines = f.readlines()
        for line in lines:
            t = float(line.split(' ')[-2])
            MT = max(t, MT)
            if float(t) > TIME:
                logging.warning('TLE.')
    logging.warning('max time: {}'.format(MT))


if __name__ == '__main__':
    main()
