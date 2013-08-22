import sys
import subprocess
import os
import configparser
import re
from time import sleep
import random

def debug(msg):
    print(msg)

def error(msg=''):
    print(msg)
    sys.exit(1)

def parse_conf(conf):
    '''Remove all comments (also in-line) and empty rows
    Returns a single line string
    '''
    clean_conf = ''
    for line in conf.splitlines():
        line = line.strip()
        if not re.search(r'^#',line):
            if '#' in line:
                clean_conf = ' '.join((clean_conf, line.split()[0]))
            else:
                clean_conf = ' '.join((clean_conf, line))
    return(re.sub(r' +', ' ', clean_conf).strip())

