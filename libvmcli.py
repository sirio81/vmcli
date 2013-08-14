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

def print_help():
    print('''
    Posizione argomenti
    0     1     2    3
    vmcli guest find <guest name>
    vmcli guest start <guest name> [host]
    vmcli guest start_and_show <guest name> [host]
    vmcli guest shutdown <guest name>
    vmcli guest kill <guest name>
    vmcli guest stop <guest name>
    vmcli guest cont <guest name>
    vmcli guest info <guest name>
    vmcli guest migrate <guest name> <to-host>
    vmcli guest show <guest name>
    vmcli host info <host name>
    vmcli host shutdown_guests <host name>
    vmcli cluser info
    vmcli cluser show
    vmcli cluser poweroff
    vmcli clusert shutdown_guests
    ''')
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

