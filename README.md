# rsync-time-machine
Python Script. Time Machine style backup worker with Rsync. 

# Requirements
* python version >= 3.0

# Example
## Linux local storage backup ( backing up a '/etc' directory ) for 15 days
 python3 rsync_backup_worker.py --src=/etc --dst=/backups/my_linux_etc --keep=1000*60*60*24*15
 
## Backup from remote Mac maching to Linux machine for 30 days
* You need a sharing settings with 'Remote Login' from Mac Settings.
 python3 rsync_backup_worker.py --src-charset=utf-8-mac --dst-charset=utf-8 --sshpass-password=mac_user_password --src=MY_MAC_USER_NAME@MAC_IP_ADDRESS_LIKE_192.168.0.100:~/backup/source/directory --dst=/backup/destination/directory/on/linux --keep-owner=true --keep=1000*60*60*24*30
