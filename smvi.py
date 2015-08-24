#! /usr/bin/env python

"""Data download and visualization tool for `smartmeter <https://github.com/vschw/smartmeter>

Dependencies
############

`paramiko_scp <https://github.com/jbardin/scp.py>`
"""

import paramiko
import numpy as np
import matplotlib.pyplot as plt
from pylab import ylabel
import ConfigParser
from scp import SCPClient
import argparse
import datetime
import time


def config_init():
    """Loads configuration data from config.ini
    """

    global ip, usr, key_path, data_folder, db_name

    config = ConfigParser.ConfigParser()
    config.read('config.ini')

    ip = config.get('ssh_login', 'ip')
    usr = config.get('ssh_login', 'username')
    key_path = config.get('ssh_login', 'key_path')
    data_folder = config.get('ssh_login', 'data_folder')
    db_name = config.get('db_login', 'db_name')
    print "config.ini parsed"


def ssh_init():
    """SSH to the server using paramiko.
    """

    global ssh
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=usr, key_filename=key_path)
    print 'SSH Connection established'


def ssh_close():
    ssh.close()


def csv_create(args, circuit, csvname):
    command = 'mongoexport --db '+db_name
    command += ' --csv'
    command += ' --out '+csvname
    command += ' --fields timestamp,value'
    command += ' --collection nodes'
    command += " -q \'{node:"+str(args['nodes']).replace('[','').replace(']','')+", \
               variable:\"circuit_"+str(circuit)+"\", \
               timestamp:{$gt: "+str(date_to_timestamp(args['startdate'], args['starttime']))+", \
                          $lt: "+str(date_to_timestamp(args['enddate'], args['endtime']))+"}}\';"
    #print command
    ssh.exec_command('cd '+data_folder+';'
                     +command)

    print 'csv created on remote server'


def csv_name(args, circuit):
    if circuit == 2:
        circ = 'c2'
    else:
        circ = 'c1'

    return 'node'+str(args['nodes']).replace('[','').replace(']','').replace(' ','')+'-' \
           +circ+'-'\
           +args['startdate'].replace('-','')+'-'\
           +args['enddate'].replace('-','')+'.csv'


def csv_download(csvname):
    scp = SCPClient(ssh.get_transport())
    scp.get(data_folder+'/'+csvname)
    scp.close()
    print 'csv file downloaded'


def csv_remove(csvname):
    ssh.exec_command('cd '+data_folder+';'
                     +'rm '+csvname)

    print 'csv file deleted from remote server'


def date_to_timestamp(date, clock='00:00:00'):
    s = str(date)+' '+clock
    return str(int(time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timetuple())))


def valid_date(s):
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def valid_time(x):
    try:
        datetime.datetime.strptime(x, "%H:%M:%S")
        return x
    except ValueError:
        msg = "Not a valid time: '{0}'.".format(x)
        raise argparse.ArgumentTypeError(msg)


def valid_node(n):
    try:
        nodelist = [int(x) for x in n.split(',')]
        return nodelist
    except TypeError:
        msg = "Not a valid node format"
        raise argparse.ArgumentTypeError(msg)


def valid_timezone(t):
    if int(t) > 12 or int(t) < -12:
        msg = "Not a valid valid timezone (-12<=t<=12)"
        raise argparse.ArgumentTypeError(msg)
    return t


def valid_circuit(c):
    if int(c) != 1 and int(c) != 2:
        msg = "Not a valid circuit selected (enter 1 or 2)"
        raise argparse.ArgumentTypeError(msg)
    return c


def figure(args, csvname1, csvname2):
    if int(args['circuit']) == 0 or int(args['circuit']) == 1:
        data1 = np.genfromtxt(csvname1, delimiter=',', skip_header=1,
                               skip_footer=0, names=['time', 'power'])
        time1 =[datetime.datetime.fromtimestamp(ts) for ts in data1['time']]

    if int(args['circuit']) == 0 or int(args['circuit']) == 2:
        data2 = np.genfromtxt(csvname2, delimiter=',', skip_header=1,
                               skip_footer=0, names=['time', 'power'])
        time2 =[datetime.datetime.fromtimestamp(ts) for ts in data2['time']]

    if int(args['circuit']) == 0:
        if len(data1['power']) + 1 == len(data2['power']):
            power1 = data1['power']
            power2 = data2['power'][:-1]
            time = time2[:-1]
            timest = data1['time']
        elif len(data1['power']) == len(data2['power']) + 1:
            power1 = data1['power'][:-1]
            power2 = data2['power']
            time = time1[:-1]
            timest = data2['time']
        elif len(data1['power']) + 2 == len(data2['power']):
            power1 = data1['power']
            power2 = data2['power'][:-2]
            time = time2[:-2]
            timest = data1['time']
        elif len(data1['power']) == len(data2['power']) + 2:
            power1 = data1['power'][:-2]
            power2 = data2['power']
            time = time1[:-2]
            timest = data2['time']
        else:
            power1 = data1['power']
            power2 = data2['power']
            time = time1
            timest = data1['time']
    elif int(args['circuit']) == 1:
            power1 = data1['power']
            power2 = [0] * len(data1['power'])
            time = time1
            timest = data1['time']
    elif int(args['circuit']) == 2:
            power1 = [0] * len(data2['power'])
            power2 = data2['power']
            time = time2
            timest = data2['time']

    kwh = [0]
    kwh[0] = 0

    for i, ts in enumerate(time[:-1]):
        if i == 0:
            kwh.append(0)
        else:
            kwh.append(kwh[i] + ((power1[i] + power2[i]) / 1000 * (timest[i] - timest[i-1]) / 3600))

    fig1 = plt.figure()
    plt.xlabel('Time [%H:%M:%S]')
    plt.ylabel('Power [W]')

    ax1=plt.subplot(111)
    ax1.plot(time, power1, label='circuit 1')
    ax1.plot(time, power2, label='circuit 2')
    ax1.plot(time, power2 + power1, label='total power')
    plt.legend(loc='upper left')

    if args['energy'] == 'true':
        ax2 = fig1.add_subplot(111, sharex=ax1, frameon=False)
        ax2.yaxis.tick_right()
        ax2.yaxis.set_label_position("right")
        ylabel("Energy [kWh]")
        ax2.plot(time, kwh, 'black',label='total energy')
        plt.legend(loc='upper right')

    plt.show()


def parse_args():
    parser = argparse.ArgumentParser(description='Data download and visualization tool for smartmeter')

    parser.add_argument('-n','--nodes', help='single node as int, aggregate of multiple nodes as comma-separated list '
                                             '(e.g.: 1,2,3,4)', required=True, type=valid_node)
    parser.add_argument('-t','--timezone', help='timezone as int from -12 to 12 in relation to UTC time (e.g.: -8), '
                                                'default = UTC', required=False, type=valid_timezone, default=0)
    parser.add_argument('-s', "--startdate", help="start date - format YYYY-MM-DD ", required=False, type=valid_date,
                        default=datetime.date.fromordinal(datetime.date.today().toordinal()-2).strftime('%Y-%m-%d'))
    parser.add_argument('-e', "--enddate", help="end date - format YYYY-MM-DD ", required=False, type=valid_date,
                        default =datetime.date.fromordinal(datetime.date.today().toordinal()-1).strftime('%Y-%m-%d'))
    parser.add_argument('-x', "--starttime", help="start time - format HH:MM:SS", required=False, type=valid_time,
                        default='00:00:00')
    parser.add_argument('-y', "--endtime", help="end time - format HH:MM:SS", required=False, type=valid_time,
                        default='00:00:00')
    parser.add_argument('-c','--circuit', help='single circuit as int, default = aggregate of both circuits',
                        required=False, type=valid_circuit, default=0)
    parser.add_argument('-a','--energy', help='display energy aggregate in figure (true or false)',
                        required=False, default='true')
    args = vars(parser.parse_args())
    return args


if __name__ == "__main__":
    args = parse_args()
    print args

    config_init()
    ssh_init()

    if int(args['circuit']) == 0:
        csv_create(args, 1, csv_name(args, 1))
        csv_create(args, 2, csv_name(args, 2))
    elif int(args['circuit']) == 1:
        csv_create(args, 1, csv_name(args, 1))
    elif int(args['circuit']) == 2:
        csv_create(args, 1, csv_name(args, 2))

    time.sleep(3)

    if int(args['circuit']) == 0:
        csv_download(csv_name(args, 1))
        csv_download(csv_name(args, 2))
    elif int(args['circuit']) == 1:
        csv_download(csv_name(args, 1))
    elif int(args['circuit']) == 2:
        csv_download(csv_name(args, 2))

    if int(args['circuit']) == 0:
        csv_remove(csv_name(args, 1))
        csv_remove(csv_name(args, 2))
    elif int(args['circuit']) == 1:
        csv_remove(csv_name(args, 1))
    elif int(args['circuit']) == 2:
        csv_remove(csv_name(args, 2))

    ssh_close()

    figure(args, csv_name(args, 1),csv_name(args, 2))
