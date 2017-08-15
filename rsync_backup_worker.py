#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import argparse
import os,stat
import shutil
from datetime import datetime, timedelta, timezone
import io
import subprocess 
import logging

parser = argparse.ArgumentParser(description='Rsync timemachine backup worker')

#-----
parser.add_argument('--keep',dest='keep', default='0', 
		help='keep backups by milliseconds: default - 0 (forever), ex)1000*60*60*24*30, ex)1000*60*60*24*7')

parser.add_argument('--src',dest='src', required=True, help='source')
parser.add_argument('--dst',dest='dst', required=True, help='destination')

parser.add_argument('--custom-rsync-args',dest='customargs', default=None, required=False, help='set this only if you want rsync arguments that you want ( other settings will be ignored )')
parser.add_argument('--src-charset',dest='srccharset', default='utf8', required=False, help='charset of OS working on source (linux=utf8, macos=utf8-mac)')
parser.add_argument('--dst-charset',dest='dstcharset', default='utf8', required=False, help='charset of OS working on destination (linux=utf8, macos=utf8-mac) ')
parser.add_argument('--bwlimit',dest='bwlimit', default=None, required=False, help='just same option using with rsync')
parser.add_argument('--keep-owner',dest='keepowner', default="true", required=False, help='keep file\'s owner')
parser.add_argument('--sshpass-password',dest='sshpassPasswd', default=None, required=False, help='password for source side. this using \'sshpass -p\' command')
parser.add_argument('--sshpass-file',dest='sshpassFile', default=None, required=False, help='password-file for source side. this using \'sshpass -f\' command')
parser.add_argument('--ssh-port',dest='sshport', default=None, required=False, help='sshport if not standard \'22\'')
parser.add_argument('--debug-donotrun-rsync',dest='doNotRunRsync', default="false", required=False, help='for debug - just print rsync command set and exit')
parser.add_argument('--keep-min-backup-count',type=int, dest='keepMin', default=-1, required=False, help='keep count of rsynced folder from expiration')


args = parser.parse_args()

#### init
CURRENT_BACKUP_DIR="current-backup"
LOG_DIR='logs'
RSYNC_LOG_PREFIX='rsync-'
LOGGER_LOG_PREFIX='debug-'
BACKUP_DIR_PREFIX='backup-'
LOG_EXT='.log'

DT_FORMAT="%Y%m%d_%H%M%S_%f"

nowDt = datetime.now()
nowStr = nowDt.strftime(DT_FORMAT)

logger = logging.getLogger()

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

logger.setLevel(logging.DEBUG)

class HelperObject:
	def __init__(self, args, timeStr):
		self.keep = None
		self.src= None
		self.dst = None
		self.args = args 
		self.timeStr = timeStr
		self.keepOwner=True

	def getSshPassCommand(self):
		result = ''
		if self.args.sshpassPasswd!=None:
			result += 'sshpass -p \''+self.args.sshpassPasswd+'\' '
		elif self.args.sshpassFile!=None:
			result += 'sshpass -f \''+self.args.sshpassFile+'\' '
		return result
	
	def getRSyncArgs(self):
		result='--recursive --links --perms --times --dirs --progress -v --delete --numeric-ids'
		if self.keepOwner==True:
			result+=' --group --owner'
			
		result+= ' --iconv='+self.args.dstcharset + ',' + self.args.srccharset

		if self.args.bwlimit!=None:
			result += ' --bwlimit='+self.args.bwlimit
		
		if self.args.sshport!=None:
			result += ' -e "ssh -p ' + self.args.sshport + '"'

		return result
	
	def setDirs(self):
		dstDir = self.getDstDir()
		logDir = self.getLogDir()
		if not os.path.exists(dstDir):
			logger.debug('mkdir : ' + dstDir)
			os.makedirs(dstDir)
		if not os.path.exists(logDir):
			logger.debug('mkdir : ' + logDir)
			os.makedirs(logDir)


		
	def getDstDir(self):
		return os.path.abspath(self.dst)
	def getLogDir(self):
		return os.path.join(self.getDstDir(),LOG_DIR)

	def getCurrentBackupDir(self):
		return os.path.join(self.getDstDir(),CURRENT_BACKUP_DIR)

	def getThisTimeBackupDir(self):
		return os.path.join(self.getDstDir(),self.getThisTimeBackupDirName())
	def getThisTimeBackupDirName(self):
		return BACKUP_DIR_PREFIX+self.timeStr


	def makeRSyncLogPath(self):
		return os.path.join(self.getLogDir(),self.makeRSyncLogFileName())
	def makeRSyncLogFileName(self):
		return RSYNC_LOG_PREFIX+self.timeStr+LOG_EXT

	def makeLoggerLogPath(self):
		return os.path.join(self.getLogDir(),self.makeLoggerLogFileName())
	def makeLoggerLogFileName(self):
		return LOGGER_LOG_PREFIX+self.timeStr+LOG_EXT


class FileRemover:
	def __init__(self):
		pass
	def rmtree(self,path):
		if os.path.exists(path):
			shutil.rmtree(path,onerror=self.onReadonly)
		
	def onReadonly(self,action,name,exc):
		logger.debug('remove readonly : ' + name)
		os.chmod(name,stat.S_IWRITE)
		os.remove(name)
		
	


argsObj = HelperObject(args,nowStr)
argsObj.src=args.src
argsObj.dst=args.dst
argsObj.args=args

argsObj.setDirs()

##### set logger

hdlr = logging.FileHandler(argsObj.makeLoggerLogPath())
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 

try:
	argsObj.keep = float(float(eval(args.keep))/1000.0)
except Exception as e:
	logger.exception(e)
	logger.exception("error with --keep : " + args.keep)
	exit()

logger.debug("Check KeepOwner : " + args.keepowner)
if args.keepowner.upper() == "FALSE":
	argsObj.keepOwner=False
else:
	argsObj.keepOwner=True 


if argsObj.dst.strip().find('~')==0:
	logger.error('do not use \'~\' on the dst path')
	exit()

logger.debug("============= Set current time : "+ nowStr)
logger.debug("============= Keep backup expires : %f " % argsObj.keep)

logger.debug(os.getcwd())
logger.debug((argsObj.src))
logger.debug(os.path.abspath(argsObj.dst))


#### check same backup process working 
processCount=0
checkSameProcess =  subprocess.Popen("ps -aux", shell=True, stdout=subprocess.PIPE).stdout.readlines()
for line in checkSameProcess:
	lineStr = line.decode("utf-8")
	if lineStr.find(__file__)>=0 and lineStr.find('--dst='+args.dst+' ')>=0:
		logger.debug("checking process : "+lineStr)
		processCount+=1

#cancel backing up when the same backup process already working
if processCount>1:
	logger.debug('error : same process already working')
	exit()
	

#### set default dirs
if os.path.isdir(argsObj.getDstDir())==False:
	logger.error('destination path is not a directory : ' + argsObj.getDstDir())
	exit()
if os.path.isdir(argsObj.getLogDir())==False:
	logger.error('log path is not a directory : ' + argsObj.getLogDir())
	exit()

#### check os working on source and destination




#### START PROCESS
rsyncCommand = argsObj.getSshPassCommand() + 'rsync ' + argsObj.getRSyncArgs()
rsyncCommand += ' --link-dest=..'+os.path.sep+CURRENT_BACKUP_DIR 
rsyncCommand += ' --log-file="' + argsObj.makeRSyncLogPath() + '"'
rsyncCommand += ' "'+ argsObj.src + '" "' + argsObj.getThisTimeBackupDir()+'"'
logger.debug(rsyncCommand)

if argsObj.args.doNotRunRsync=="true":
	exit()


rsyncProc = subprocess.Popen(rsyncCommand,shell=True,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
for line in io.TextIOWrapper(rsyncProc.stdout, encoding="utf-8"):  # or another encoding
	print(line.rstrip())
	

if os.path.exists(argsObj.getThisTimeBackupDir())==False:
	logger.debug('Rsync backup failed. try next time.')
	exit()

#Unlink current-backup directory
logger.debug('remove '+CURRENT_BACKUP_DIR+' dir : '+argsObj.getCurrentBackupDir())
try:
	os.unlink(argsObj.getCurrentBackupDir())
except Exception as e:
	logger.exception(e)

if os.path.exists(argsObj.getCurrentBackupDir())==False:
	logger.debug('removed')
else:
	logger.debug('still exists!')


#Replace current-backup directory for new rsync destination folder
if os.path.exists(argsObj.getThisTimeBackupDir()):
	logger.debug('create new '+CURRENT_BACKUP_DIR+' dir from : '+argsObj.getThisTimeBackupDir())
	os.symlink(argsObj.getThisTimeBackupDir(),argsObj.getCurrentBackupDir())

if os.path.exists(argsObj.getCurrentBackupDir())==False:
	logger.debug('does not exists!')
else:
	logger.debug('created!')


#### REMOVE OLD BACKUPS
fileRemover = FileRemover()

backupDt=None


keepMinCount = argsObj.args.keepMin
logger.debug('Keep backups from expiration : '+str(keepMinCount))

logger.debug('REMOVE EXPIRED BACKUPS')

itemList = os.listdir(argsObj.getDstDir())

#for itemListCount - current-backup, logs, thisTimeBackup
itemCount = len(itemList)-3


thisTimeBackupDirName = argsObj.getThisTimeBackupDirName()
thisTimeRSyncLogName = argsObj.makeRSyncLogFileName()
thisTimeLoggerLogName = argsObj.makeLoggerLogFileName()


for item in itemList:
	logger.debug("======================")

	if item==CURRENT_BACKUP_DIR or item==LOG_DIR or item==thisTimeBackupDirName:
		logger.debug("pass "+item)
		continue

	logger.debug(item)
	if item.find("backup-")==0:
		itemDtStr = item.replace("backup-",'')
		logger.debug("this is backup folder : " + itemDtStr)
		try:
			backupDt = datetime.strptime(itemDtStr,DT_FORMAT)
		except Exception as e:
			logger.exception(e)
			continue

		dtDelta = nowDt-backupDt
		logger.debug("Datetime Delta : "+ str(dtDelta.total_seconds()))
		if dtDelta.total_seconds() > argsObj.keep:
			logger.debug("itemCount : " + str(itemCount))

			if keepMinCount != -1 and itemCount <= keepMinCount:
				logger.debug("keep backup folder from expiration by keepMinBackupCount")
				break

			itemCount = itemCount - 1
			logger.debug("remove this backup")
			fileRemover.rmtree(os.path.join(argsObj.getDstDir(),item))
		
			rsyncLogItem = RSYNC_LOG_PREFIX+itemDtStr+LOG_EXT
			loggerLogItem = LOGGER_LOG_PREFIX+itemDtStr+LOG_EXT
			logger.debug('REMOVE EXPIRED LOGS : ' + rsyncLogItem + ', ' + loggerLogItem)
			os.remove(os.path.join(argsObj.getLogDir(),rsyncLogItem))
			os.remove(os.path.join(argsObj.getLogDir(),loggerLogItem))
		
		else:
			logger.debug("keep this backup")
		

