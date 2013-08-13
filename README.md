vmcli
=====

Manage virtual machines on a cluster using a shared storage



Requirements
============

aptitude install socat python3 python3-setuptools parallel-ssh
easy_install3 docopt



Installation
============

git clone https://github.com/sirio81/vmcli.git



Convention
==========
 - Default configuration directory is /etc/vmcli.
 - For each cluster you wish to manage:
  * add a section editing /etc/vmcli/clusters.conf;
  * create a directory for guests configuration files: /etc/vmcli/guests/<cluster_name>/.
 - In guest's configuration file you must set the option '-name'.
 - The guest name has and the guest configuration file name must match.
 
   I.e. /etc/vmcli/guests/debian.conf
        --name debian
        
 - It has to be possible to connect to hosts by ssh without specifying user or port (see Cluster Setup).
 - 'socat'; 'parallel-ssh' and all other command used by the vmcli have to be io the PATH of your user.
 - All hosts use the same qemy/kvm command.



Cluster Setup
==============

Create a pair of ssh keys:
  ssh-keygen -t rsa 
  (you may choose a different file name like. /home/user/.ssh/id_rsa_vmcli)
  
Export the key on every host: 
  ssh-copy-id -i /home/user/.ssh/id_rsa_vmcli.pub hostname
  
Create an ssh_config file adding host configuration like this:

    Host test001
        User root
        hostname 192.168.2.41
        IdentityFile ~/.ssh/id_rsa_vmcli

    Host test002
        User root
        hostname 192.168.2.42
        IdentityFile ~/.ssh/id_rsa_vmcli
    ...
Create the default cluster configuration file (see examples).

    /etc/vmcli/etc/default.conf



Usage
=====

Show all options

    cd vmcli
    ./vmcli --help

To check if all host are reachable by ssh

    ./vmcli --cluster=test cluster show

Start a guest and show it's vnc

    ./vmcli --cluster=test guest start_and_show debian

Use non standard configuration directory

    ./vmcli.py --config=~/myconf --cluster=test cluster show
  
Sueggestions:

link the vmcli to your path, you can run the command everywere:

    ln -s /home/user/vmcli/vmcli.py /usr/local/bin
    
You may whant to create an alias for the cluster you use the most (it may be just one).

    alias vmcli='vmcli.py --cluster=production'



Examples
========

Cluster Configuration File

    [cluster]
    host_names = host01,host02,host03
    pssh_time_out = 15
    bin = qemu-system-x86_64
    vnc_over_ssh = false
    guests_shutdown_delay = 10
    migration_ports = 6000-7000


Guest Configuration File

    -name template
    -enable-kvm
    -drive file=/media/nas/template.qcow2
    -m 1024 -smp 2
    -k it -vnc :1
    -usbdevice tablet
    -boot order=c
    -monitor unix:/tmp/template.sock,server,nowait
    -daemonize
    #-net nic,macaddr=52:54:00:03:5b:29 -net tap
    #-netdev type=tap,id=lan0,script=no,vhost=on -device virtio-net-pci,netdev=lan0,mac=52:54:00:03:5b:29
    
