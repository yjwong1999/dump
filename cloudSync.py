import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from drive_utils1.sheetCreateEdit import spreadsheetCreation,spreadSheetEditor

from datetime import datetime, timedelta
import pandas as pd

class TestSingLog:
    def __init__(self):
        self.parentName ="LogFld"                                        # Parent folder name
        self.cred_drive = r'drive_utils/credentials/Aouth2.json'         # Credential.json file for aouth 2.0 
        self.cred_spread = r'drive_utils/credentials/serviceAcc.json'    # Credential.json file for service account 
        self.token = r'drive_utils/credentials/token.json'               # token.json file, keep it as it is as it will create itself if its null
        self.sheet_ID = 6868
        
        filePath = r'log' 
        self.localRoot = os.getcwd()					# Root Path
        self.filePath = os.path.join(self.localRoot,filePath)		# file path to the parent folder of the text file
    
    def postSing(self,dayLog,camNum):
        
        fdate = str(dayLog).split('-')

        sheetCreation = spreadsheetCreation(self.cred_drive,self.token,self.parentName)        # initialize credential for creating
        sheetEditor = spreadSheetEditor(self.cred_spread,camNum)				# initialize credential for editing google sheet

        cloudName = f"cam_{dayLog}_count"							# Daily log name in cloud
        monthMasterName = f"masterFile_{fdate[0]}/{fdate[1]}"					# Monthly Log name in cloud

	# create daily log in cloud if not exist, skip otherswise
        if sheetCreation.findSheet(str(cloudName)) != False : 
            print(f"{str(cloudName)} existed")
        else:
            sheetCreation.createSheet(str(cloudName))
            print(f"created blank {str(cloudName)}")

        # create monthly log in cloud if not exist, skip otherswise
        if sheetCreation.findSheet(monthMasterName) == False:
            print("masterfile does not exist, proceed with creation...")
            sheetCreation.createSheet(monthMasterName)
            print(f"Month Masterfile for the month {fdate[0]}/{fdate[1]} created")

	# create new sheet for daily and montly log for bar chart, skip if existed
        sheetEditor.dfChart(cloudName , self.sheet_ID , 1 ,"hour" ,2)
        sheetEditor.dfChart(monthMasterName , self.sheet_ID , 0 ,"day" ,1)
        
        # Import log from local, will skip if log for such date does not exist
        sheetEditor.importLog(dayLog,self.filePath)
        if not sheetEditor.emptyDate:
            sheetEditor.cloudExport(dayLog)

dayBefore = datetime.today().date() - timedelta(days=1)				# this retrive date before current date

cloudLogPath = "/home/library/Desktop/new/log/CloudSyncLog.txt"

try:
    TSL = TestSingLog()
    TSL.postSing(str(dayBefore),5)							# postSing({Log date to be import in string format}, {number of camera use})
    # "/home/library/Desktop/new/log/CloudSyncLog.txt"
    f = open(cloudLogPath, "a")
    f.write(f"[{datetime.now()}] Cloud Log Sync to drive for the date {str(dayBefore)}\n")
    f.close()
except Exception as e:
    f = open(cloudLogPath, "a")
    f.write(f"[{datetime.now()}] Cloud Log Sync error due to {e}, log for {str(dayBefore)} is not synced to drive\n")
    f.close()
except BaseException:
    f = open(cloudLogPath, "a")
    f.write(f"[{datetime.now()}] Unexpected Error occured, log for {str(dayBefore)} is not synced to drive\n")
    f.close()

# use ./cloudSyncExecute.sh to test for this code under crontab
            




            


