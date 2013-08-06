#!/usr/bin/python3

from libcluster import Cluster
from libguest import Guest
from time import sleep
from docopt import docopt
import sys


h = '''
Usage:
  vmcli.py [--config=<path>] guest find <guest_name>
  vmcli.py [--config=<path>] guest start <guest_name> [<host_name>]
  vmcli.py [--config=<path>] guest start_and_show <guest_name> [<host_name>]
  vmcli.py [--config=<path>] guest shutdown <guest_name>
  vmcli.py [--config=<path>] guest kill <guest_name>
  vmcli.py [--config=<path>] guest stop <guest_name>
  vmcli.py [--config=<path>] guest cont <guest_name>
  vmcli.py [--config=<path>] guest info <guest_name>
  vmcli.py [--config=<path>] guest migrate <guest_name> <host_name>
  vmcli.py [--config=<path>] guest show <guest_name>
  vmcli.py [--config=<path>] host info <host_name>
  vmcli.py [--config=<path>] host shutdown_guests <host_name>
  vmcli.py [--config=<path>] cluster info
  vmcli.py [--config=<path>] cluster show
  vmcli.py [--config=<path>] cluster poweroff
  vmcli.py [--config=<path>] cluster shutdown_guests
  
Options:
  -h --help     Show this screen.
  --version     Show version.
'''

if __name__ == '__main__':
    arg = docopt(h, version='0.8')
    #print(arg)
    #sys.exit()

    
    config_file = 'etc/vmcli.conf' if arg['--config'] is None else arg['--config']
    c = Cluster(config_file)
    
    if arg['guest']:
        if arg['find']:
            print(c.guest_find(arg['<guest_name>']))
        elif arg['start'] or arg['start_and_show']:
            if arg['<host_name>']:
                host_name = arg['<host_name>']
            else:
                host_name = 'choose'
            c.start_guest(arg['<guest_name>'], host_name)
            if arg['start_and_show']:
                host_name = c.guest_find(arg['<guest_name>'])
                c.hosts[host_name].guests[arg['<guest_name>']].show()
        elif arg['shutdown']:
            host_name = c.guest_find(arg['<guest_name>'])
            c.hosts[host_name].guests[arg['<guest_name>']].shutdown()
        elif arg['kill']:
            host_name = c.guest_find(arg['<guest_name>'])
            c.hosts[host_name].guests[arg['<guest_name>']].kill()
        elif arg['stop']:
            host_name = c.guest_find(arg['<guest_name>'])
            c.hosts[host_name].guests[arg['<guest_name>']].stop()
        elif arg['cont']:
            host_name = c.guest_find(arg['<guest_name>'])
            c.hosts[host_name].guests[arg['<guest_name>']].cont()
        elif arg['migrate']:
            c.migrate_guest(arg['<guest_name>'], arg['<host_name>'])
        elif arg['info']:
            host_name = c.guest_find(arg['<guest_name>'])
            print(c.hosts[host_name].guests[arg['<guest_name>']].info())
        elif arg['show']:
            host_name = c.guest_find(arg['<guest_name>'])
            print('Guest not found') if host_name is None else c.hosts[host_name].guests[arg['<guest_name>']].show()
    elif arg['host']:
        if arg['info']:
            print(c.hosts[arg['<host_name>']].info())
        elif arg['shutdown_guests']:
            c.hosts[arg['<host_name>']].shutdown_guests()
    elif arg['cluster']:
        if arg['info']:
            print(c.info())
        if arg['show']:
            print(c.show())
        if arg['poweroff']:
            c.poweroff()
        if arg['shutdown_guests']:
            c.shutdown_guests()
        

