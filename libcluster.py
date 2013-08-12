from libvmcli import *
from libhost import Host
from libhost import Guest

#import subprocess
#import os
#import sys

class Cluster:
    def __init__(self,config_file):
        self.hosts = {}
        config = configparser.ConfigParser()
        config.read(config_file)
        self.cluster_options = dict(config.items('cluster'))
        f = open(self.cluster_options['pssh_host_file'], 'w')
        f.write(self.cluster_options['host_names'].replace(',','\n'))
        f.close()
        self.host_names = self.cluster_options['host_names'].split(',')
        self.query_hosts()
        for host_name in self.host_names:
            self.hosts[host_name] = Host(host_name, self.cluster_options)
        
        #hosts = {}
        #for host_name in self.host_names:
            #self.hosts[host_name] = Host(self, host_name)
        
    def query_hosts(self):
        '''Contact all hosts and write output to file
        '''
        parallel_ssh = 'parallel-ssh -h {} -o {} -e {} -t {} '.format(self.cluster_options['pssh_host_file'], self.cluster_options['pssh_out_dir'], self.cluster_options['pssh_err_dir'], self.cluster_options['pssh_time_out'])
        os.system('[ -d {0} ] && rm -r {0}; sync'.format((self.cluster_options['pssh_out_dir'])))
        os.system('[ -d {0} ] && rm -r {0}; sync'.format((self.cluster_options['pssh_err_dir'])))
        cmd = ['cat /proc/cpuinfo', 'free -m', 'pgrep -fl qemu-system-x86_64 | grep -v bash', 'uptime']
        cmd = '"' + '; echo; '.join(cmd) + '"'

        cmd = parallel_ssh + cmd
        out = subprocess.getstatusoutput(cmd)
        if out[0] != 0:
            error('There has been problems collecting data from one or more hosts\n\n' + out[1])

    ###def find_guest(self,guest_name):
        ###pass
    ###def migrate(self, guest_name, host_name):
        ###pass
        
        
    def show(self):
        '''
        Just show the server and the guests
        '''
        host_names = list(self.hosts)
        host_names.sort()
        out = ''
        for host_name in host_names:
            out += '\n' + host_name + '\n'
            guest_names = []
            if self.hosts[host_name].guests is not None:
                guest_names = list(self.hosts[host_name].guests)
                guest_names.sort()
                out += '\t' + ' '.join(guest_names)
        return out
        
    def info(self):
        '''
        Show all hosts info
        '''
        # Sort the host names in alphabetical order
        host_names = list(self.hosts)
        host_names.sort()
        out = ''
        for host_name in host_names:
            out += '\n' + 'server:' + host_name + '\n'
            out += self.hosts[host_name].info()
        return out
        
    
    def start_guest(self, guest_name, to_host='choose'):
        '''It calls the guest method to start the guest but it checks first if
        the target host has the necessary resources.
        If not target host is given, one will be chosen.
        It returns the host host name if the guest starts corretly,
        otherwise returns None'''

        host_name =  self.guest_find(guest_name)
        if host_name is not None:
            error('guest {} already running on {}'.format(guest_name, host_name))
            
        # Istantiante guest from configuration file
        try:
            #totest
            f = open(os.path.join(self.cluster_options['conf'], 'guests', guest_name) + '.conf', 'r')
        except:
            error('Gest configuration file not readable')
        all_opt = parse_conf(f.read().strip())
        g = Guest(all_opt, self.cluster_options)
        
        # Search on the cluster already used resources
        if self.check_contention(g):
            error('disk or mac address already used')
            
        if to_host == 'choose':
            to_host = self.choose_host(g)
            if to_host is None:
                error('No suitable hosts found')
        else:
            if not self.compare_min_resources(g, to_host):
                error('Not enough resources on ' + to_host)

        if g.start(to_host) == 0:
            if self.hosts[to_host].guests is None:
                self.hosts[to_host].guests = {}
            self.hosts[to_host].guests[guest_name] = g
            return True
        else:
            error('Failed to start guest ' + g.name)
            
    def migrate_guest(self, guest_name, to_host):
        host_name = self.guest_find(guest_name)
        if to_host == host_name:
            error('Can\'t migrate on the same host')
            
        g = self.hosts[host_name].guests[guest_name]
        if not self.compare_min_resources(g, to_host):
            error('Not enough resources on ' + to_host)
            
        ports = self.cluster_options['migration_ports'].split('-')
        incoming_port = random.randint(int(ports[0]),int(ports[1]))
        
        debug(g.all_opt)
        if '-incoming' in g.all_opt:
            all_opt = g.all_opt.split('-incoming')[0].strip()
            debug(all_opt)
        else:
            all_opt = g.all_opt
        all_opt = all_opt + ' -incoming tcp:0:' + str(incoming_port)
        
        new_guest = Guest(all_opt, self.cluster_options)
        debug('starting guest on new host (incoming)' + to_host)
        if new_guest.start(to_host) != 0:
            return False
        debug('starting migration')
        debug('ssh {0} \'echo "migrate -d tcp:{1}:{2}" | socat - UNIX-CONNECT:/tmp/{3}.sock\''.format(host_name, to_host, incoming_port, guest_name))
        if subprocess.getstatusoutput('ssh {0} \'echo "migrate -d tcp:{1}:{2}" | socat - UNIX-CONNECT:/tmp/{3}.sock\''.format(host_name, to_host, incoming_port, guest_name))[0] != 0:
            return False
        sleep(5)
        debug('check migration status')
        debug('ssh {0} \'echo "info migrate" | socat - UNIX-CONNECT:/tmp/{1}.sock\''.format(host_name, guest_name))
        out = subprocess.getstatusoutput('ssh {0} \'echo "info migrate" | socat - UNIX-CONNECT:/tmp/{1}.sock\''.format(host_name, guest_name))
        debug(out)
        
        if 'Migration status: completed' in out[1]:
            print('Migration competed')
            g.kill()
        else:
            error('failed')
        sys.exit()
        
    def check_contention(self, guest):
        '''Check if a disk, or mac address is already used on the cluster.
        Return host_name if it does.
        Else None'''
        
        #Check fro drives
        if 'drive' in guest.opt:
            all_drives = []
            for host_name in self.hosts:
                if self.hosts[host_name].guests is not None:
                    for guest_name in self.hosts[host_name].guests:
                        if guest_name != guest.name:
                            all_drives += self.hosts[host_name].guests[guest_name].opt['drive']
            all_drives = self.clear_drives(all_drives)
            
            for drive in self.clear_drives(guest.opt['drive']):
                if drive in all_drives:
                    print(drive, 'already used')
                    return True
            
        
        # Check for mac
        if 'net' in guest.opt:
            if 'macaddr' in ' '.join(guest.opt['net']):
                all_macs = []
                for host_name in self.hosts:
                    if self.hosts[host_name].guests is not None:
                        for guest_name in self.hosts[host_name].guests:
                            if guest_name != guest.name:
                                if 'net' in self.hosts[host_name].guests[guest_name].opt:
                                    for net in self.hosts[host_name].guests[guest_name].opt['net']:
                                        if 'macaddr' in net:
                                            all_macs.append(net)
            all_macs = self.clear_macs(all_macs)
        
            guest_macs = []
            for net in guest.opt['net']:
                if 'macaddr' in net:
                    guest_macs.append(net)
            guest_macs = self.clear_macs(guest_macs)
            for mac in guest_macs:
                if mac in all_macs:
                    print(mac, 'already used')
                    return True

        return False
        
    
    def compare_min_resources(self, guest, to_host):
        '''Check if host has enough resources to run the guest.
        Return True/False'''
        if self.hosts[to_host].cpu_cores < int(guest.opt['smp']):
            return False
        if self.hosts[to_host].ram_free  < (int(guest.opt['m']) + 256):
            return False
        return True
            
    def choose_host(self, guest):
        '''Finds the host with more free resources on the cluster.
        Returns the host name or None'''
        discarded = set()
        suitable_host_names = set(list(self.hosts))
        for host_name in suitable_host_names:
            if not self.compare_min_resources(guest, host_name):
                discarded.add(host_name)
        suitable_host_names = suitable_host_names.difference(discarded)
        if len(suitable_host_names) > 0:
            best = 0
            chosen = ''
            for host_name in suitable_host_names:
                if self.hosts[host_name].ram_free > best:
                    best = self.hosts[host_name].ram_free
                    chosen = host_name
            return chosen
        return None
    
    def clear_drives(self, drives):
        clean_list = []
        for drive in drives:
            drive = drive.replace('file=', '').split(',')[0]
            clean_list.append(drive)
        return clean_list

    def clear_macs(self, macs):
        clean_list = []
        for mac in macs:
            mac = mac.split('macaddr=')[1].split(',')[0]
            clean_list.append(mac)
        return clean_list


    def shutdown_guests(self):
        for host_name in self.hosts:
            self.hosts[host_name].shutdown_guests()
            
    def guest_find(self, guest_name):
        for host_name in self.hosts:
            if self.hosts[host_name].guests is not None:
                if guest_name in self.hosts[host_name].guests:
                    return host_name
        return None
                
            
    def poweroff(self):
        '''
        Turn off power to all servers after checking the presence of any sheep proccess
        '''
        parallel_ssh = 'parallel-ssh -h {} -t {} '.format(self.cluster_options['pssh_host_file'], self.cluster_options['pssh_time_out'])
        status = (subprocess.getstatusoutput(parallel_ssh + " 'pgrep -x sheep'"))
        if 'SUCCESS' not in status[1]:
            print('No sheep processes found. Hosts will be powered off')
            (subprocess.getstatusoutput(parallel_ssh + " poweroff"))
            return True
        else:
            sheeps = []
            for sheep in status[1].splitlines():
                if 'SUCCESS' in sheep:
                    sheeps.append(sheep.split()[3])
            print('Sheep daemon is still alive in: ', ' '.join(sheeps))
            print('All sheep processes have to be down before powring off all the hosts!')
            return False
    
    def show_guests(self):
        for host_name in self.hosts:
            debug('host_name: ' + host_name)
            self.hosts[host_name].show_guests()
            
