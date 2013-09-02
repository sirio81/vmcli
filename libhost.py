from libvmcli import *
from libguest import Guest


class Host:
    def __init__(self, name, global_cluster_options, cluster_options):
        self.guests = {}
        self.name = name
        self.global_cluster_options = global_cluster_options
        self.cluster_options = cluster_options
        d = os.path.join('/tmp/vmcli', subprocess.getstatusoutput('whoami')[1])
        self.pssh = {
            'out': os.path.join(d, 'out'),
            'err': os.path.join(d, 'err'),
            'host_file': os.path.join(d, 'host_file'),
            'timeout' : self.cluster_options['pssh_time_out']
            }
        processes = self.guest_processes()
        if processes is None:
            self.guests = None
        else:
            for process in processes:
                g = Guest(process, self.global_cluster_options, self.cluster_options)
                g.host_name = self.name
                self.guests[g.opt['name']] = g
        
        try:
            f = open(os.path.join(self.pssh['out'],self.name), 'r')
        except:
            error('Impossible to retreive info for ' + self.name)
        
        all_info = f.read()
        f.close()
        
        # Find CPU name
        for line in all_info.splitlines():
            if 'model name' in line:
                self.cpu_name = line.split(': ')[1]
                break
            
        # Find core number
        self.cpu_cores = 0
        for line in all_info.splitlines():
            if 'processor' in line:
                self.cpu_cores += 1
                
        #Find total mem
        for line in all_info.splitlines():
            if 'Mem:    ' in line:
                self.ram_total = int(re.sub(' +', ' ', line).split()[1])

        # Find mem used by guests
        self.ram_guests = 0
        if self.guests is not None:
            for guest_name in self.guests:
                self.ram_guests += int(self.guests[guest_name].opt['m'])

        self.ram_free = self.ram_total - self.ram_guests
        if self.ram_free < 0:
            self.ram_free = 0

        # Find actual cached memeory
        self.ram_free = self.ram_total - self.ram_guests

        # Show uptime
        for line in all_info.splitlines():
            if 'load average:' in line:
                self.uptime = line.strip()


    def info(self):
        info = '''
        Cpu: {0}
        Cores: {1}
        Ram Total: {2}
        Ram Guests: {3}
        Running Guests: {4}
        Uptime: {5}
        '''
        guest_names = sorted(list(self.guests)) if self.guests is not None else None
        return info.format(self.cpu_name, self.cpu_cores, self.ram_total, self.ram_guests, guest_names, self.uptime)


    def guest_processes(self):
        '''Read the host info file and returns a list of qemu processes'''
        out = subprocess.getstatusoutput('grep {} {}'.format(self.cluster_options['bin'], os.path.join(self.pssh['out'], self.name)))
        if out[0] == 0:
            processes = []
            for process in out[1].splitlines():
                process = process.split('qemu-system-x86_64 ')[1].strip()
                processes.append(process)
            return processes
        else:
            return None


    def shutdown_guests(self):
        '''
        Shutdown all the guests of a specific host
        '''
        if self.guests is not None:
            for guest_name in self.guests:
                self.guests[guest_name].shutdown()
                print('Shutting down', guest_name, 'on', self.name)
                sleep(int(self.cluster_options['guests_shutdown_delay']))
        else:
            print('No guests running on', self.name)
            return False


    def show_guests(self):
        ''' Show vnc of all the running guests on this host'''
        ssh_br_cmd = 'ssh -fN {} '.format(self.name)
        viewer = self.global_cluster_options['vncviewer']
        host_name = self.name
        
        if self.guests is None:
            print('No guests running on', self.name)
            return 1
        
        # Create ssh bridge
        if self.cluster_options['vnc_over_ssh'] == 'true':
            host_name = 'localhost'
            bridges = []
            for guest_name in self.guests:
                port = 5900 + int(self.guests[guest_name].opt['vnc'].replace(':',''))
                bridges.append('-L {0}:localhost:{0}'.format(port))
            ssh_br_cmd = ssh_br_cmd + ' '.join(bridges)
            subprocess.getstatusoutput('pkill -f --exact "{}"'.format(ssh_br_cmd))
            os.system(ssh_br_cmd)
        
        if self.global_cluster_options['vncviewer'] != 'vncviewer':
            guest_list = []
            for guest_name in self.guests:
                guest_list.append(host_name + self.guests[guest_name].opt['vnc'])
            
        cmd = viewer + ' ' + ' '.join(guest_list)
        os.system(cmd + ' &')
        
        return 0

            
            