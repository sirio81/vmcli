from libvmcli import *
from libhost import Host
from libhost import Guest
import threading


class Cluster:
    def __init__(self,conf_dir, cluster_name):
        self.name = cluster_name
        self.conf_dir = conf_dir
        options_allowed = ['host_names', 'pssh_time_out', 'bin', 'vnc_over_ssh', 'guests_shutdown_delay', 'migration_ports']
        tempdir = '/tmp/vmcli'
        config_file = os.path.join(self.conf_dir, 'clusters.conf')
        if not os.path.exists(config_file): error('clusters configuration file is missing')
        config = configparser.ConfigParser()
        config.read(config_file)
        try:
            self.global_cluster_options = dict(config.items('global'))
        except:
            error('"global" section missing or wrong. Check you configuration.')
        try:
            self.cluster_options = dict(config.items(self.name))
        except:
            error('You chose a wrong cluster')
        # Check if the option in the configuration file have been written correctly
        for option in self.cluster_options:
            if option not in options_allowed:
                error(option + ': wrong option. Check you configuration file.')
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
            os.chmod(tempdir, 0o777)
        d = os.path.join(tempdir, subprocess.getstatusoutput('whoami')[1])
        if not os.path.exists(d):
            os.makedirs(d)
        self.pssh = {
            'out': os.path.join(d, 'out'),
            'err': os.path.join(d, 'err'),
            'host_file': os.path.join(d, 'host_file'),
            'timeout' : self.cluster_options['pssh_time_out']
            }
        self.hosts = {}
        f = open(self.pssh['host_file'], 'w')
        f.write(self.cluster_options['host_names'].replace(',','\n'))
        f.close()
        self.host_names = self.cluster_options['host_names'].split(',')
        self.query_hosts()
        for host_name in self.host_names:
            self.hosts[host_name] = Host(host_name, self.global_cluster_options, self.cluster_options)


    def query_hosts(self):
        '''Contact all hosts and write output to file
        '''
        parallel_ssh = 'parallel-ssh -h {} -o {} -e {} -t {} '.format(self.pssh['host_file'], self.pssh['out'], self.pssh['err'], self.pssh['timeout'])
        os.system('[ -d {0} ] && rm -r {0}; sync'.format((self.pssh['out'])))
        os.system('[ -d {0} ] && rm -r {0}; sync'.format((self.pssh['err'])))
        cmd = ['cat /proc/cpuinfo', 'free -m', 'pgrep -fl qemu-system-x86_64 | grep -v bash', 'uptime']
        cmd = '"' + '; echo; '.join(cmd) + '"'

        cmd = parallel_ssh + cmd
        out = subprocess.getstatusoutput(cmd)
        if out[0] != 0:
            error('There has been problems collecting data from one or more hosts\n\n' + out[1])


    def show(self):
        '''
        Just show a list of the servers and their guests
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
        If no target host is given, one will be chosen.
        It returns True if the guest starts correctly,
        otherwise returns None
        '''
        
        host_name =  self.guest_find(guest_name)
        if host_name is not None:
            error('guest {} already running on {}'.format(guest_name, host_name))
            
        # Istantiante guest from configuration file
        try:
            f = open(os.path.join(self.conf_dir, 'guests', self.name, guest_name) + '.conf', 'r')
        except:
            error('Guest configuration file not readable')
        all_opt = parse_conf(f.read().strip())
        g = Guest(all_opt, self.global_cluster_options, self.cluster_options)
        
        # Search on the cluster already used resources
        if self.check_contention(g):
            error('disk or mac address already used')
            
        if to_host == 'choose':
            to_host = self.choose_host(g)
            if to_host is None:
                error('No suitable hosts found')
        else:
            if to_host not in self.hosts:
                error('Host not valid')
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
        if to_host not in self.hosts:
            error('Host not valid')
            
        g = self.hosts[host_name].guests[guest_name]
        if not self.compare_min_resources(g, to_host):
            error('Not enough resources on ' + to_host)
            
        ports = self.cluster_options['migration_ports'].split('-')
        incoming_port = random.randint(int(ports[0]),int(ports[1]))
        
        #debug(g.all_opt)
        if '-incoming' in g.all_opt:
            all_opt = g.all_opt.split('-incoming')[0].strip()
        else:
            all_opt = g.all_opt
        all_opt = all_opt + ' -incoming tcp:0:' + str(incoming_port)
        
        new_guest = Guest(all_opt, self.global_cluster_options, self.cluster_options)
        print('starting guest on new host (incoming)' + to_host)
        if new_guest.start(to_host) != 0:
            return False
        print('starting migration')
        #debug('ssh {0} \'echo "migrate -d tcp:{1}:{2}" | socat - UNIX-CONNECT:/tmp/{3}.sock\''.format(host_name, to_host, incoming_port, guest_name))
        if subprocess.getstatusoutput('ssh {0} \'echo "migrate -d tcp:{1}:{2}" | socat - UNIX-CONNECT:/tmp/{3}.sock\''.format(host_name, to_host, incoming_port, guest_name))[0] != 0:
            return False
        sleep(5)
        print('checking migration status')
        
        while True:
            #debug('ssh {0} \'echo "info migrate" | socat - UNIX-CONNECT:/tmp/{1}.sock\''.format(host_name, guest_name))
            print('...in progress')
            out = subprocess.getstatusoutput('ssh {0} \'echo "info migrate" | socat - UNIX-CONNECT:/tmp/{1}.sock\''.format(host_name, guest_name))
            if 'active' in out[1]:
                sleep (5)
            else:
                break
        
        if 'Migration status: completed' in out[1]:
            print('Migration completed')
            g.kill()
        else:
            error('failed')
        sys.exit()
        
    def check_contention(self, guest):
        '''Check if a disk, or mac address is already used on the cluster.
        Return True if it does.
        Else False'''
        
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
        if self.hosts[to_host].ram_free  < (int(guest.opt['m']) + 512):
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
        '''Remove drives options from the list'''
        clean_list = []
        for drive in drives:
            drive = drive.replace('file=', '').split(',')[0]
            clean_list.append(drive)
        return clean_list


    def clear_macs(self, macs):
        '''Remove other net options form the list'''
        clean_list = []
        for mac in macs:
            mac = mac.split('macaddr=')[1].split(',')[0]
            clean_list.append(mac)
        return clean_list


    def shutdown_guests(self):
        '''Shut down all cluster guests'''
        for host_name in self.hosts:
            t = threading.Thread(target=self.hosts[host_name].shutdown_guests())
            t.daemon = True
            t.start()
            


    def guest_find(self, guest_name):
        '''Show the host name on wich the guest is running'''
        for host_name in self.hosts:
            if self.hosts[host_name].guests is not None:
                if guest_name in self.hosts[host_name].guests:
                    return host_name
        return None


    def poweroff(self):
        '''
        Turn off power to all servers after checking the presence of any sheep proccess
        '''
        print('Checking if any guest is running')
        for host_name in self.hosts:
            if self.hosts[host_name].guests is not None:
                print('...there are still active guests, I can\'t shutdown the cluster')
                return False
                
        print('Checking sheeps status')
        parallel_ssh = 'parallel-ssh -h {} -t {} '.format(self.pssh['host_file'], self.cluster_options['pssh_time_out'])
        sheeps_status = subprocess.getstatusoutput(parallel_ssh + " 'pgrep -x sheep'")
        
        if 'SUCCESS' in sheeps_status[1] and 'FAILURE' in sheeps_status[1]:
            print('...some sheeps are alive, some are not. Fix this manually.')
            return False
            
        # If all sheeps are alive, check the recovery, then kill them.
        # Else, they are dead already, and I can shutdown the cluster
        if 'FAILURE' not in sheeps_status[1]:
            print('Cheking if recovery is running')
            for host_name in self.hosts:
                status = subprocess.getstatusoutput('ssh {} "dog node recovery"'.format(host_name))
                if status[0] != 0:
                    print('..failed')
                    return(False)
                elif len(status[1].splitlines()) != 2:
                    print('...a recovery is running. I can\'t shutdown the cluster')
                    return False
                break
        
            print('Shutting down sheepdog')
            for host_name in self.hosts:
                status = subprocess.getstatusoutput('ssh {} "dog cluster shutdown"'.format(host_name))
                if status[0] is not 0:
                    print('...failed')
                    return False
                
                break
            sleep(3)
            
            parallel_ssh = 'parallel-ssh -h {} -t {} '.format(self.pssh['host_file'], self.cluster_options['pssh_time_out'])
            sheeps_status = subprocess.getstatusoutput(parallel_ssh + " 'pgrep -x sheep'")
            
            if 'SUCCESS' in sheeps_status[1]:
                print('...cluster shutdown faile to kill all the sheeps. Fix this manually')
        
        else:
            print('... all sheeps are already dead')
            
        print('Powering off hosts')
        subprocess.getstatusoutput(parallel_ssh + " poweroff")

    def show_guests(self):
        '''Show the vnc of all cluster guests'''
        if self.global_cluster_options == 'vncviewer':
            for host_name in self.hosts:
                self.hosts[host_name].show_guests()
        elif self.global_cluster_options['vncviewer'] == 'krdc':
            guest_list = []
            for host_name in self.hosts:
                if self.hosts[host_name].guests is not None:
                    for guest_name in self.hosts[host_name].guests:
                        guest_list.append(host_name + self.hosts[host_name].guests[guest_name].opt['vnc'])
            debug('krdc ' + ' '.join(guest_list))
            #os.system('krdc ' + ' '.join(guest_list))

    def list_guests(self):
        '''Show guest name list reading file name.
        File not ending with '.conf' will be ignored'''
        clean_list = []
        rows = []
        col_status = ''
        col_guest_name = ''
        col_host_name = ''
        separator = ''
        separator_min = ' ' * 4
        name_max_len = 0
        out = ''
        try:
            l = os.listdir(os.path.join(self.conf_dir, 'guests', self.name))
        except:
            error('Guests\'s configuration folder not found')
            
        # Keep only name ending exactly with '.conf' and remove the suffix
        l.sort()
        for f in l:
            if f[-5::1] == '.conf':
                clean_list.append(f.replace('.conf', ''))

        # Adapt the column size to the longer guest name
        #|status|guest name         | host name|
        #---------------------------------------
        #|......|max_len,sep_min    |          |
        #|......|name,diff,sep_min  |          |
        
        for guest_name in clean_list:
            if len(guest_name) > name_max_len: name_max_len = len(guest_name)
        for guest_name in clean_list:
            host_name = self.guest_find(guest_name)
            status = '  ' if host_name is None else '* '
            if host_name is None: host_name = '' 
            col_guest_name = guest_name + ' ' * (name_max_len - len(guest_name)) + separator_min
            col_host_name = host_name + '\n\r'
            rows.append(status + col_guest_name + host_name)
            
        return '\n\r'.join(rows)



