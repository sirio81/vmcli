#!/usr/bin/python3

from libvmcli import error
from libcluster import Cluster
from libguest import Guest
from time import sleep
from docopt import docopt
import sys
import os


h = '''
Usage:
  vmcli.py --cluster=<name> guest find <guest_name>
  vmcli.py --cluster=<name> guest start <guest_name> [<host_name>]
  vmcli.py --cluster=<name> guest start_and_show <guest_name> [<host_name>]
  vmcli.py --cluster=<name> guest shutdown <guest_name>
  vmcli.py --cluster=<name> guest kill <guest_name>
  vmcli.py --cluster=<name> guest stop <guest_name>
  vmcli.py --cluster=<name> guest cont <guest_name>
  vmcli.py --cluster=<name> guest info <guest_name>
  vmcli.py --cluster=<name> guest list
  vmcli.py --cluster=<name> guest migrate <guest_name> <host_name>
  vmcli.py --cluster=<name> guest show <guest_name>
  vmcli.py --cluster=<name> host info <host_name>
  vmcli.py --cluster=<name> host list_running_guests <host_name>
  vmcli.py --cluster=<name> host shutdown_guests <host_name>
  vmcli.py --cluster=<name> host show_guests <host_name>
  vmcli.py --cluster=<name> cluster info
  vmcli.py --cluster=<name> cluster show
  vmcli.py --cluster=<name> cluster show_guests
  vmcli.py --cluster=<name> cluster poweroff
  vmcli.py --cluster=<name> cluster shutdown_guests
  vmcli.py  [-h | --help]
  vmcli.py  [--verions]
    
Options:
  -h --help         Show this screen.
  --version         Show version.
  --cluster=name    Choose the cluster to use
  --conf=path       Change path of the main configuration directory [default: /etc/vmcli]
'''


if __name__ == '__main__':
    arg = docopt(h, version='0.9.0')
    
    if os.path.isdir('conf'):
        conf_path = 'conf'
    elif os.path.isdir('~/.vmcli'):
        conf_path = '~/.vmcli'
    elif os.path.isdir('/etc/vmcli'):
        conf_path = '/etc/vmcli'
    else:
        error('No configuration available')
        
        
    c = Cluster(conf_path, arg['--cluster'])

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
        elif arg['list']:
            print(c.list_guests())
    elif arg['host']:
        if arg['<host_name>'] not in c.hosts:
            error('Host not valid')
        if arg['info']:
            print(c.hosts[arg['<host_name>']].info())
        elif arg['list_running_guests']:
            c.hosts[arg['<host_name>']].list_running_guests()
        elif arg['show_guests']:
            c.hosts[arg['<host_name>']].show_guests()
        elif arg['shutdown_guests']:
            c.hosts[arg['<host_name>']].shutdown_guests()
    elif arg['cluster']:
        if arg['info']:
            print(c.info())
        if arg['show']:
            print(c.show())
        if arg['show_guests']:
            print(c.show_guests())
        if arg['poweroff']:
            c.poweroff()
        if arg['shutdown_guests']:
            c.shutdown_guests()
        

