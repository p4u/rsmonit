# rsmonit

Rsnapshot monitor is a simple python tool to analyze the output log of rsnapshot (the backup utility which uses rsync).

I developed it in some hours under the aim of monitorize my backups, so do not take it as a professional tool. It is just a simple script.

# Requirements

- Python2.7
- Standard python libraries
- rsnapshot

# Usage

```sh
./rsmonit.py -d
State | Start-time  | Backup-info
ok    | 5:30        | localhost
ok    | 5:34        | server1.test
ok    | 5:39        | server2.test
error | 5:55        | server3.test
Total:4  Error:1  Unknown:0  OK:3
```

# Configuration
By default you don't need to configure anything. However if your rsnapshot configuration is not the common one, you may edit these two variables.

```py
RS_LOG = ['/var/log/rsnapshot.log']
RS_CONF = ['/etc/rsnapshot.conf']
```

# Author
p4u

