#!/bin/bash

`grep 'debian 7' /etc/debian_version > /dev/null`
[ $? -eq 0 ] && debian_version=7
`grep 'debian 8' /etc/debian_version > /dev/null`
[ $? -eq 0 ] && debian_version=8

if [ $debian_version -eq 7 ]
then
    apt-get install python3-pip pssh socat
    pip-3.2 install docopt==0.6.2
elif [ $debian_version -eq 8 ]
then
    apt-get install python-pip pssh socat
    pip install docopt==0.6.2
fi