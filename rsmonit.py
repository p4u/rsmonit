#!/usr/bin/env python2.7

__author__ = "Pau Escrich"
__title__ = "Rsnapshot Monitor: rsmonit"
__version__ = "0.1"
__license__ = "gplv3"

import string
import os
import sys
import re
import time
from operator import itemgetter

##### Configuration #####
RS_LOG = ['/var/log/rsnapshot.log']
RS_CONF = ['/etc/rsnapshot.conf']


def configServers():
    # Returns the list of servers from the configuration file in dictionary format
    # SERVER1 -> DIRECTORY1 -> STATE
    # SERVER2 -> DIRECTORY2 -> STATE
    SERVERS = {}
    DIRS = []
    TIMES = {}

    for file in RS_CONF:
        try:
            fd = open(file, 'r')
        except:
            print "Cannot open %s for read!" % (file)
            sys.exit(2)

        for line in fd.readlines():

            if re.search("^backup", line):
                # fields: 1->backup 2->remote_dir 3->local_dir
                fields = []
                for f in line.strip().split("\t"):
                    if len(f) > 1:
                        fields.append(f)

                try:
                    name = fields[1].split('@')[1].split(':')[0]
                    dir = re.sub("/$", "", fields[1].split(':')[1])
                except IndexError:
                    name = "localhost"
                    dir = re.sub("/$", "", fields[1])

                # Aquesta condicio es un parche per evitar analitzar el
                # localhost (TODO)
                if not name == "localhost":
                    if not name in SERVERS.keys():
                        SERVERS[name] = {dir: 'none'}
                    else:
                        SERVERS[name][dir] = 'none'

                    TIMES[name] = {dir: 'none'}

        fd.close()
    return SERVERS, TIMES


def print_info():
    total = 0
    err = 0
    ok = 0
    unk = 0
    servers_error = []
    servers_unknown = []
    servers_info = []

    for k1 in servers.keys():
        for k2 in servers[k1].keys():
            try:
                time = int("%s%s" % (times[k1][k2][0], times[k1][k2][1]))
            except:
                time = 000

            servers_info.append(
                {'name': k1, 'dir': k2, 'state': servers[k1][k2], 'stime': time})

            if servers[k1][k2] == "error":
                err += 1
                if k1 not in servers_error:
                    servers_error.append(k1)
            elif servers[k1][k2] == "none":
                unk += 1
                if k1 not in servers_unknown:
                    servers_unknown.append(k1)
            else:
                ok += 1
            total += 1

    print "State\t| Start-time\t| Backup-info"
    print ""

    for s in sorted(servers_info, key=itemgetter('stime')):
        t = str(s['stime'])
        minute = t[len(t) - 2:len(t)]
        hour = t[0:len(t) - 2]
        print "%s\t| %s:%s\t\t| %s %s" % (s['state'], hour, minute, s['name'], s['dir'])

    if len(servers_error) > 0:
        print ""
        sys.stderr.write("\n== Servers with errors ==\n")
        for s in servers_error:
            sys.stderr.write(s + '\n')
        print ""

    if len(servers_unknown) > 0:
        sys.stderr.write("\n== Servers with unknown results ==\n")
        for s in servers_unknown:
            sys.stderr.write(s + '\n')

    return total, ok, err, unk


def print_noInfo():
    t = 0
    err = 0
    ok = 0
    unk = 0

    for k1 in servers.keys():
        for k2 in servers[k1].keys():
            if servers[k1][k2] == "error":
                err += 1
            elif servers[k1][k2] == "none":
                unk += 1
            else:
                ok += 1
            t += 1
    return t, ok, err, unk


def print_help():
    print "Use: %s [-d] [Date] " % (sys.argv[0])
    print " -d: Enable debug mode (see all information)"
    print " Date: Date you want analize (ex. 04/Dec/2008). If none, today is used."


##############
#### Main ####
##############

if len(sys.argv) == 1:
    DATE = time.strftime("%d/%b/%Y")
    DEBUG = False

elif len(sys.argv) == 2:
    if sys.argv[1] == "-d":
        DEBUG = True
        DATE = time.strftime("%d/%b/%Y")
    else:
        DATE = sys.argv[1]
        DEBUG = False

elif len(sys.argv) == 3:
    if sys.argv[1] == "-d":
        DEBUG = True
        DATE = sys.argv[2]
    elif sys.argv[2] == "-d":
        DEBUG = True
        DATE = sys.argv[1]
else:
    print_help()
    sys.exit(1)

try:
    time.strptime(DATE, "%d/%b/%Y")
except:
    print "Error: Date malformed! You should use some date like: 04/Dec/2008"
    print_help()
    sys.exit(1)

regexp_date = "^\[%s" % (DATE)
regexp_backup = "\@.*\:"
regexp_error = "ERROR:"
state = "ok"
servers, times = configServers()
backup = ""

# Once we got the server parsed from the config file
# lets read the log and check the status

for file in RS_LOG:
    try:
        fd = open(file, 'r')
    except:
        print "Cannot open %s for read!" % (file)
        sys.exit(2)

    for line in fd.readlines():
        # For each line, look if it match the date
        if re.search(regexp_date, line):
            # For each word of the line, look for server@directory from backup
            for l in line.split():
                if re.search(regexp_backup, l):
                    backup = l
                    break
            # Is there error
            if re.search(regexp_error, line):
                state = "error"

            name = ""
            dir = ""
            # Have we find it? Which is the state?
            # At this point backup is something like root@server:directory
            if len(backup) > 0:
                name = backup.split('@')[1].split(':')[0]
                dir = re.sub("/$", "", backup.split(':')[1])
                date = line.split()[0]
                start_time = date.split(":")[1:3]
                # If it exists (in the config file)
                if name in servers.keys() and dir in servers[name].keys():
                    servers[name][dir] = state
                    times[name][dir] = start_time
                # If it does not exist
                elif DEBUG:
                    print "WTF!! %s:%s found in log but not in configure" % (name, dir)
            backup = ""
            state = "ok"
    fd.close()


if DEBUG:
    total, ok, err, unk = print_info()
else:
    total, ok, err, unk = print_noInfo()

sys.stderr.write(
    "\nTotal:%s  Error:%s  Unknown:%s  OK:%s\n\n" %
    (total, err, unk, ok))

if err > 0:
    sys.exit(2)
if unk > 0:
    sys.exit(1)

sys.exit(0)
