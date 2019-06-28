# rsync-time-machine-backup
Python Script. Time Machine style backup worker with Rsync. 

# Requirements
* python version >= 3.0
* rsync version >= 3.0

# Example
## Linux local storage backup ( backing up a '/etc' directory ) for 15 days
### Command Line
```
$ python3 rsync_backup_worker.py --src=/etc --dst=/backups/my_linux_etc --keep=1000*60*60*24*15
```
### Crontab
```
#linux etc backup with every hour, keep owner run as root : keep 15 days
01 01 * * * python3 rsync_backup_worker.py --src=/etc --dst=/backups/my_linux_etc --keep=1000*60*60*24*15 
```


## Backup from remote Mac machine to Linux machine for 30 days
* You need a sharing settings with 'Remote Login' from Mac Settings.
* I suggest to use '--src-charset=utf-8-mac' option for Mac.

### Command Line
```
python3 rsync_backup_worker.py --src-charset=utf-8-mac --dst-charset=utf-8 --sshpass-password=mac_user_password --src=MY_MAC_USER_NAME@MAC_IP_ADDRESS_LIKE_192.168.0.100:~/backup/source/directory --dst=/backup/destination/directory/on/linux --keep-owner=false --keep=1000*60*60*24*30
```
### Crontab
```
01 */2 * * *  python3 rsync_backup_worker.py --src-charset=utf-8-mac --dst-charset=utf-8 --sshpass-password=mac_user_password --src=MY_MAC_USER_NAME@MAC_IP_ADDRESS_LIKE_192.168.0.100:~/backup/source/directory --dst=/backup/destination/directory/on/linux --keep-owner=false --keep=1000*60*60*24*30
```




# Backup Result
Like this.

```
drwxr-xr-x.   3 root root  4096  Jan  4 00:01 backup-20170104_000101_548783
drwxr-xr-x.   3 root root  4096  Jan  4 02:01 backup-20170104_020101_395637
drwxr-xr-x.   3 root root  4096  Jan  4 16:01 backup-20170104_160102_052244
drwxr-xr-x.   3 root root  4096  Jan  4 18:01 backup-20170104_180102_696759
lrwxrwxrwx.   1 root root    66  Jan  4 18:01 current-backup -> /backups/backup_title/backup-20170104_180102_696759
drwxr-xr-x.   2 root root 45056  Jan  4 18:02 logs
```
