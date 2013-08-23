INTRODUCTION
============

vmcli aims to be an intuitive command line tool to manage guests on one or more cluster.
It's written in python 3 and it relays ssh (see also README).

PARALLEL REQUESTS
=================

To make things a quick a possible, we contact all the host at the same time instead od one after the other.
This is achieved by the use of parallel-ssh.
Notice that, instead of using several ssh rqeusts (one for retrieve guest process informations, one for retrieve hosts informations etc), we make just one that runs all the necessary remote command.
Their output is store in a file (one for each host), i.e. /tmp/vmcli/<username>/hostname.
This way, we can fast parse the local files and generate the necessary python objects.

ALWAYS UPDATED DATA
===================

vmcli never reuse informations stored on parallel-ssh file.
Each time you call it, it will know which qemu processes are running in that precise moment.

AVOID PERMISSION FILE PROBLEMS
==============================

/tmp/vmcli/<username>/hostname.
If you use vmcli as user 'ted' and then as user 'thomas', and parallel-ssh was going to write on the same folde, you were going to have permission problem.
Using a subfolder for each user, avoid that.

CLASSES
=======
vmcli.py itself simply read the command line arguments and call the related object method.
As written in the read me, you could easily reuse these classes to build a different project (for example, web based).

We have 3 classes: Cluster, Host and Guest.
When a Host object is istantiated, it will istantiate Guest objects (if they are running).
Cluster object will istantiate Host.
This way, calling
    c = Cluster(parameters)
will istantiate all objects at once.

FILES
=====

for semplicity, we created a single file for each class, plus libvmcli that contains some easy common functions.
libvmcli also import modules used by the classes in the other files.





It will take care to avoid virtual disk corruption running the same guest on more than one host.
It will also a