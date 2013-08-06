from libvmcli import *

class Guest:
    def __init__(self, all_opt, cluster_options):
        self.cluster_options = cluster_options
        self.all_opt = all_opt
        self.opt = self.parse_opt(all_opt)
        self.host_name = None
        self.name = self.opt['name']

        #self.status = self.status(self):
        #if self.status == 'down':
            #all_opt = 'fix: fa file di configurazione'
        #else:
            #all_opt = 'fix: da processo qemu'
        #self.parse_opt(self,all_opt):

    def parse_opt(self, all_opt):
        '''Take a string with the whole qemu commands and creates a dictionary
        with the option name as key. It's value will be a list because many
        options may be repeated (i.e. -drive).'''
        opt = []
        opt_b = []
        d = {}
        repeatable_options = ['drive', 'net', 'chardev', 'iscsi', 'bt']
        all_opt = all_opt[1:-1]
        for e in all_opt.split(' -'):
            pair = e.split()
            if pair[0] in repeatable_options:
                opt_b.append(pair)
                continue
            elif len(pair) == 1:
                pair.append(None)
            opt.append(pair)
        opt = dict(opt)
        for c in opt_b:
            if c[0] not in opt:
                opt[c[0]] = []
            opt[c[0]].append(c[1]) 
        return opt

        
    def status():
        '''Returns guest status reading target host info file
        Return 'up', 'down', 'paused' '''
        pass
    
    ###fix: DEVE ESSERE RICHIAMATA SOLO QUANDO NON CI SONO GUEST CON LO STESSO NOME CHE GIRANO.
    ### questo implica usare l'oggetto cluster
    def start(self, to_host):
        '''Simply starts the qemu process on the target host.
        No controls are made. They are demand to higher classes.
        Retruns True if ssh exit with 0 status'''
        out = subprocess.getstatusoutput('ssh {0} "{1} {2}"'.format(to_host, self.cluster_options['bin'], self.all_opt))
        if out[0] == 0: 
            self.host_name = to_host
        else:
            print('ERROR: ', out[1])
        return out[0]
        
        
    def shutdown(self):
        '''Shutdown the guest'''
        #print('ssh {0} "echo system_powerdown | socat - UNIX-CONNECT:/tmp/{1}.sock"'.format(self.host_name, self.name))
        out = subprocess.getstatusoutput('ssh {0} "echo system_powerdown | socat - UNIX-CONNECT:/tmp/{1}.sock"'.format(self.host_name, self.name))
        #print(out[1])
        return out[0]
        
    def show(self):
        if self.cluster_options['vnc_over_ssh'] == 'true':
            port = 5900 + int(self.opt['vnc'].replace(':','').split(',')[0])
            os.system('pkill -f --exact "ssh -fN {0} -L {1}:localhost:{1}"'.format(self.host_name, port))
            os.system('ssh -fN {0} -L {1}:localhost:{1}'.format(self.host_name, port))
            os.system('vncviewer {}{} &'.format('localhost', self.opt['vnc']))
        else:
            print('vncviewer {}{} &'.format(self.host_name, self.opt['vnc']))
            os.system('vncviewer {}{} &'.format(self.host_name, self.opt['vnc']))
            
    def kill(self):
        subprocess.getstatusoutput('ssh {0} \'pkill -f "name {1}"\''.format(self.host_name, self.name))
        sleep(2)
        subprocess.getstatusoutput('ssh {0} \'pkill -9 -f "name {1}"\''.format(self.host_name, self.name))
        sleep(1)
        return subprocess.getstatusoutput('ssh {0} \'pgrep -f "name {1}"\''.format(self.host_name, self.name))[0]
        
    def stop(self):
        return subprocess.getstatusoutput('ssh {0} "echo stop | socat - UNIX-CONNECT:/tmp/{1}.sock"'.format(self.host_name, self.name))[0]
        
    def cont(self):
        return subprocess.getstatusoutput('ssh {0} "echo cont | socat - UNIX-CONNECT:/tmp/{1}.sock"'.format(self.host_name, self.name))[0]
        
    def info(self):
        info = '''
        host: {}
        vnc: {}
        mem: {}
        smp: {}
        '''
        return info.format(self.host_name, self.opt['vnc'], self.opt['m'], self.opt['smp'])
        
        
        
        