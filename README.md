# rsync-time-machine
Python Script. Time Machine style backup worker with Rsync. 

# Requirements
* python version >= 3.0

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

## Backup from remote Mac maching to Linux machine for 30 days
* You need a sharing settings with 'Remote Login' from Mac Settings.
* I suggest to use '--src-charset=utf-8-mac' option for Mac.

### Command Line
```
python3 rsync_backup_worker.py --src-charset=utf-8-mac --dst-charset=utf-8 --sshpass-password=mac_user_password --src=MY_MAC_USER_NAME@MAC_IP_ADDRESS_LIKE_192.168.0.100:~/backup/source/directory --dst=/backup/destination/directory/on/linux --keep-owner=false --keep=1000*60*60*24*30
```
### Crontab
```
#backup mac data every 2hours on 1minues. backup-count is 100, do not keep owner
01 */2 * * *  python3 rsync_backup_worker.py --src-charset=utf-8-mac --dst-charset=utf-8 --sshpass-password=mac_user_password --src=MY_MAC_USER_NAME@MAC_IP_ADDRESS_LIKE_192.168.0.100:~/backup/source/directory --dst=/backup/destination/directory/on/linux --keep-owner=false --keep=1000*60*60*24*30
```
