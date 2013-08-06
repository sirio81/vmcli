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

def get_opt_value (opt, process_string):
    '''Returns the option value of a kvm process'''
    opt = opt.strip('-')
    for pair in process_string.split('-'):
        pair = pair.strip().split(' ')
        if len (pair) == 2 and opt == pair[0]:
            return pair[1]


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


#def cluster_wake_up():
    #'''
    #Turn on hosts by wake on lan
    #'''
    #for mac in subprocess.getstatusoutput('grep -v -e ^$ -e ^# ' + mac_file)[1].splitlines():
        #os.system('wakeonlan ' + mac)

    
def parser(cmd):
    '''
    Controls if the syntax of the arguments it correct.
    Retruns the corrispective function name.
    '''
        
    subjects = ['guest', 'host','cluster']
    guest_actions = ['find', 'start', 'start_and_show', 'shutdown', 'kill', 'stop', 'cont', 'info', 'migrate', 'show']
    host_actions = ['info', 'shutdown_guests']
    cluster_actions = ['info', 'show', 'poweroff', 'shutdown_guests']
    
    
    if len(cmd) < 3 or len(cmd) > 5:
        print_help()
    else:
        subject, action = cmd[1], cmd[2]
        
    if subject not in subjects:
        print('wrong key word given')
        print_help()
    if 'guest' == subject and action not in guest_actions:
        print('guest wrong key work')
        print_help()
    if 'host' == subject and action not in host_actions:
        print('host wrong key word')
        print_help()
    if 'cluster' == subject and action not in cluster_actions:
        print('cluster wrong key word')
        print_help()
    if ('guest' == subject or 'host' == subjects) and len(cmd) < 4:
        print('To little arguments')
        print_help()
    if 'migrate' == action and len(cmd) < 4:
        print('To little arguments')
        print_help()

        
        
        
