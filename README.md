vmcli
=====

Manage virtual machines on a cluster using a shared storage



Description
===========

This project is meant to be used to quickly manage virtual machines by command line.

Two or more hosts using a shared storage can be managed by your laptop, as long you have root access to them by ssh.

The storage may be a nfs folder, a sheepdog cluster or whatever.

You can then easily start a guest, show it's vnc, migrate it to another host, shut id down and more.

Before starting a guest, several controls are performed in order to:

  - check if the host has enough resources (ram and cpu) to start the guest;
  - check if the guest is already running on another host, to avoid virtual disk corruption;
  - check if a mac address or a virtual disk is already used by another running guest (due to user configuration error).
  
You don't necessarily need to choose a host for starting guest, it will be automatically chosen (load balance).

Guest's configuration files do not have their own syntax, simply write down qemu options (one per line).

Virtual disk file are not managed by the vmcli, so you have to create / delete them by you own.

@Developers:

'vmcli' is in fact an application of the libraries it's shipped with.
You may want to create you own project using the classes Guest, Host, Cluster



Requirements
============

**Cluster hosts:**

qemu-kvm; ssh daemon + public key (to allow working station login)

**Working Station:**

ssh client + private key + ssh_config

    aptitude install socat python3 python3-setuptools parallel-ssh
    easy_install3 docopt



Installation
============

git clone https://github.com/sirio81/vmcli.git



Convention
==========
To reduce at the minimum the necessary configuration, you are bound to some convention:

 - Default configuration directory is /etc/vmcli.
 - There's a single configuration file for all clusters named 'clusters.conf'. It has to be present in the root of the configuration folder.
 - For each cluster you wish to manage:
  * add a section by editing /etc/vmcli/clusters.conf;
  * create a directory for guests configuration files named 'guests' and a sub folder for each cluster using the same cluster name:
    /etc/vmcli/guests/production
 - In guest's configuration file you must set the option '-name'.
 - The guest name has and the guest configuration file name must match. I.e.
 
    /etc/vmcli/guests/production/debian.conf
    
        --name debian

 - It has to be possible to connect to hosts by ssh without specifying user or port (see Cluster Setup).
 - 'socat'; 'parallel-ssh' and all other command used by the vmcli have to be in your user PATH.
 - All hosts use the same qemy/kvm command.



Cluster Setup
==============

ssh is at the base of the project.
To simplify code and configuration we assume it's possible to connect to a cluster host by 'ssh hostname'.

Create a pair of ssh keys:

  ssh-keygen -t rsa 
  (you may choose a different file name like /home/user/.ssh/id_rsa_vmcli)
  
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
    
Make sure you can login by ssh on all host without being asked for password or fingerprint before continuing.

Create the a cluster configuration file (see examples).

    /etc/vmcli/etc/production.conf



Usage
=====

Show all options

    cd vmcli
    ./vmcli.py --help

To check if all host are reachable by ssh

    ./vmcli.py --cluster=test cluster show

Start a guest and show it's vnc

    ./vmcli.py --cluster=test guest start_and_show debian

Use non standard configuration directory

    ./vmcli.py --config=~/myconf --cluster=test cluster show
  
Suggestions:

link the vmcli to your path, you can run the command every were:

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
    