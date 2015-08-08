#!/bin/bash

if [ -f /etc/debian_version ]
then
    debian_version=`cat /etc/debian_version | awk -F '.' '{print $1}'`
    if [ $debian_version -eq 7 ]
    then
        apt-get install python3-pip pssh socat
        pip-3.2 install docopt==0.6.2
    elif [ $debian_version -eq 8 ]
    then
        apt-get install python-pip pssh socat
        pip install docopt==0.6.2
    fi
fi