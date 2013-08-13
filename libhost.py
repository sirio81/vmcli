from libvmcli import *
from libguest import Guest


class Host:
    def __init__(self, name, cluster_options):
        self.guests = {}
        self.name = name
        self.cluster_options = cluster_options
        d = os.path.join('/tmp/vmcli', os.getlogin())
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
                g = Guest(process, self.cluster_options)
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
                
        #Find active guest names
        self.name_guests = []
        for line in all_info.splitlines():
                if 'qemu-system-x86_64' in line:
                    self.name_guests.append(get_opt_value('-name', line))
                    
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
        return info.format(self.cpu_name, self.cpu_cores, self.ram_total, self.ram_guests, self.name_guests, self.uptime)
        
    def guest_processes(self):
        '''Reads the host's info file and creates new istances for all running 
        guests and append them to the host's dictionary.
        Returns True if at least one guest has benn found.'''
        out = subprocess.getstatusoutput('grep {} {}'.format(self.cluster_options['bin'], os.path.join(self.pssh['out'], self.name)))
        if out[0] == 0:
            processes = []
            for process in out[1].splitlines():
                process = process.split('qemu-system-x86_64 ')[1].strip()
                processes.append(process)
            return processes
        else:
            return None
        #subprocess.getstatusoutput( "grep -rw {} {} | grep -w 'name {}'".format(kvm, pssh['out_dir'], name))
        #for guest_name in Fixlist_da_info_file:
            #self.add_guest(guest_name)
        #print(out[1])

    def check_used_resource(self, resource_name):
        '''Returns True if the resource is already used'''
        pass
    
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
        if self.guests is not None:
            for guest_name in self.guests:
                self.guests[guest_name].show()
                sleep(1)
            return 0
        else:
            print('No guests running on', self.name)
            return 1
            
            