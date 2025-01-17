from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

import os.path
import calendar
from datetime import datetime, timedelta,time

import gspread
from gspread_dataframe import get_as_dataframe,set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Create parents, spreadsheet, and find if sheet existed(even from trash)
class spreadsheetCreation:

    # Initialize drive credentail token for drive if token not existed, service used and parent name
    # Only use Aouth credential for this, service account credential should not be used
    def __init__(self, cred_aouth,token,parent_name):
        SCOPES = ["https://www.googleapis.com/auth/drive"]

        creds = None
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
        if os.path.exists(token):
            creds = Credentials.from_authorized_user_file(token, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cred_aouth, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token, "w") as token:
                token.write(creds.to_json())
        
        self.service = build("drive", "v3", credentials=creds)
        self.parent_name = parent_name

    #create parent folder
    def createParents(self):
        file_metadata = {
            "name" : self.parent_name,
            "mimeType": "application/vnd.google-apps.folder"
        }

        file = self.service.files().create(
            body=file_metadata,
            fields = "id"
            ).execute()
        
        folder_id = file.get('id') 

        return folder_id    

    # find if certain spreadsheet exist inside drive
    def findSheet(self,sheet_name):
        response = self.service.files().list(
            q="name = '"+ sheet_name +"' and mimeType='application/vnd.google-apps.spreadsheet'",
            spaces = 'drive'
        ).execute()
        
        if not response['files']:
            return False
        else:
            return True
        
#######################################################################################################################################################################
    '''
    def listSheet(self,sortname):

        response = self.service.files().list(
            q="fullText contains '"+ sortname +"' and mimeType='application/vnd.google-apps.spreadsheet'",
            spaces = 'drive'
        ).execute()
        
        driveFile = pd.DataFrame(columns=['id','name'])
        
        files = response.get('files',[])
        for file in files:
            appendFile = pd.DataFrame([file['id'],file['name']]).transpose()
            appendFile.columns = ['id','name']
            driveFile = pd.concat([driveFile,appendFile],ignore_index=True)
            
        return driveFile    # return the dataframe for the results found in the drive for filename containing the string in "sortname"
                            # returned dataframe contains both id and name of the file in drive, id can be used for locating the file in drive later
    '''  
#####################################################################################################################################################################
        
    # create spreadsheet in drive, auto create parent if does not exist
    # Edit permission is also being shared with service account for it to be able edit later
    def createSheet(self,sheet_name):

        response = self.service.files().list(
            q="name = '"+ self.parent_name +"' and mimeType='application/vnd.google-apps.folder'",
            spaces = 'drive'
        ).execute()

        if not response['files']:
            folder_id = self.createParents()
        else:
            folder_id = response['files'][0]['id']

        body = {
            "name": sheet_name,
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "parents": [folder_id]
        }
        
        spreadsheet = self.service.files().create(body=body,
                                    fields="id", 
                                    supportsAllDrives=True).execute()
        
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': "ms-ang@libcounttest.iam.gserviceaccount.com"
        }

        req = self.service.permissions().create(
            fileId=spreadsheet['id'],
            body=permission,
            fields='id'
        ).execute()

# -Edit spreadsheet
# -mainly import data from txt file to spreadsheet, 
# -create chart sheet(only once for every spredsheet)
# -Append last row data(accumulated count each day) to the master sheet(for counting entire week, month, or year of your choice)
 
class spreadSheetEditor:
    # Authorize spreadsheet credential for editing spreadsheet files using service account
    # initialize sheet name to be edited, file path to be imported
    def __init__(self,cred_service,camNum:int =3):

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(cred_service, scope)
        self.client = gspread.authorize(self.creds)
        
        self.camName = []           # for identify camera name
        self.df = []                # for storing individual df in terms of list, each list have a dictionary with date and df corresponding to the date

        self.column = ['Date','Time']   # template for generating column , eg ['Date','Time','camera001','camera002',...,'camera00x']
        self.camNum = camNum            # number of camera used
        self.emptyDate = False          # use for verifying if log for the day is empty

        for num in range(camNum):
            localLogName = f'camera00{num}'
            self.camName.append(localLogName)

            self.column.append(localLogName)

        self.masterdf = pd.DataFrame(columns=self.column)       # for storing masterfile for the month, consist of individual df 
    
    # create blank template for individual day log
    def dfTemplate(self,dayLog):
        df = pd.DataFrame(columns=self.column)

        start_time = datetime.strptime('01:00:00','%H:%M:%S').time()
        start_date = datetime.strptime(dayLog,"%Y-%m-%d")

        emptydata = []
        for num in range(self.camNum):
            emptydata.append(0)

        for t in range(24):
            tTime = start_time.strftime("%H:%M:%S")
            tTime = tTime
            rows = [start_date,start_time.hour] + emptydata
            df.loc[t] = rows
            start_time = (datetime.combine(datetime.min, start_time) + timedelta(hours=1)).time()

            if(start_time.hour ==0):
                start_date += timedelta(days=1)

        return df
    
    # create blank template for individual monthly log
    def mastertemplate(self,dayLog,master_sheet):
        
        masterCol = self.column
        masterCol.pop(1)
        fdate = str(dayLog).split('-')

        emptydata = []
        for num in range(self.camNum):
            emptydata.append(0)

        try:
            spreadsheet = self.client.open(master_sheet)
            worksheet = spreadsheet.sheet1

            if worksheet.get_all_values() == [[]]:

                df = pd.DataFrame(columns = masterCol )  # create df for the empty template

                for i in range(calendar.monthrange(int(fdate[0]),int(fdate[1]))[1]):
                    dateWrite = '%02d' % (i+1)                          # int printed in terms of two digit, eg: 02,05
                    curDate = f'{fdate[0]}-{fdate[1]}-{dateWrite}'      # the date for each row

                    DataRow = [curDate] + emptydata                     # initialize empty data
                    appendFile = pd.DataFrame(DataRow).transpose()  # make the format for each data row
                    appendFile.columns = masterCol
                    
                    df = pd.concat([df,appendFile],ignore_index=True)   # append to df aka empty template
                
                # update empty template to google sheet
                worksheet.clear()
                set_with_dataframe(worksheet, df, include_index=False, include_column_header=True)

                print(f"template created for masetrfile_{fdate[0]}")
            else:
                cloudVal = worksheet.get_all_values()
                df = pd.DataFrame(cloudVal[1:],columns=cloudVal[0])
            
            return df
        
        except gspread.SpreadsheetNotFound:
            print(f"The spreadsheet '{master_sheet}' does not exist.")

        except Exception as e:
            print(f"An error occurred: {e}")  

    # import local logfile as df, then store inside self.df and self.masterdf respectively
    def importLog(self,dayLog,rootpath):
        self.emptyDate = False
        emptyCount = 0

        fdate = str(dayLog).split('-')
        curDatedf = self.dfTemplate(dayLog)

        for camName in self.camName:
            
            fileName = f"{camName}_{dayLog}_count.txt"
            filePath = os.path.join(rootpath,fileName)

            if os.path.isfile(filePath):

                    df = pd.read_csv(filePath,delimiter='\s',header=None,engine='python')

                    df.columns = ['Date','Time','Count']
                    
                    df_time = pd.to_datetime(df['Time'].to_list(),format='%H:%M:%S.%f')
                    df_time = df_time.hour
                    df['Time'] = df_time
                    
                    df['Count'] = df['Count'].astype(int)
                    df['Date'] = pd.to_datetime(df['Date'],format='%Y-%m-%d')
                    
                    
                    # Set 'Time' column as index for both DataFrames
                    df.set_index('Time', inplace=True)
                    curDatedf.set_index('Time', inplace=True)
                    
                    print(df)
                    print(curDatedf)
                    
                    # Replace count values in df2['Count1'] with count values from df1['Count1'] for corresponding times
                    curDatedf[f'{camName}'].update(df['Count'])

                    curDatedf.reset_index(inplace=True)

            else:
                print(f"log for {camName} does not exist")
                emptyCount = emptyCount + 1
                continue

        self.emptyDate = True if (emptyCount>=3) else False

        tTime = curDatedf.pop('Time')
        tTime = tTime.apply(lambda x:'{:02d}:00:00'.format(x))
        curDatedf.insert(1,'Time',tTime)
        curDatedf
        
        if not self.emptyDate:
            self.df.append({'date': f'{dayLog}','dataframe': curDatedf})        ## here, in the form of dictionary
            
            # extract row to masterdf
            finalRow = curDatedf.tail(1).reset_index(drop=True)
            finalRow.at[0,'Date'] -= timedelta(days=1)
            #here
            masterdf = pd.concat([self.masterdf,finalRow],ignore_index=True)
            masterdf['Date'] = pd.to_datetime(masterdf['Date'])
            masterfileDF = self.mastertemplate(dayLog,f"masterFile_{fdate[0]}/{fdate[1]}")
            
            masterdf.set_index('Date', inplace=True)
            masterfileDF.set_index('Date', inplace=True)
            masterfileDF.update(masterdf)
            masterfileDF.reset_index(inplace=True)

            self.masterdf = masterfileDF                                       ## here
        else:
            print(f"Log for date for {dayLog} does not exist")

    # export self.df and self.masterdf to google sheet
    def cloudExport(self,dayLog):
        fdate = str(dayLog).split('-')

        ws_name = f"cam_{dayLog}_count"
        masterFile = f"masterFile_{fdate[0]}/{fdate[1]}"

        df_to_cloud = self.df[0]['dataframe']

        worksheet =self.client.open(ws_name).sheet1
        worksheet.clear()
        set_with_dataframe(worksheet, df_to_cloud, include_index=False, include_column_header=True)
        
        worksheet =self.client.open(masterFile).sheet1
        worksheet.clear()
        set_with_dataframe(worksheet, self.masterdf, include_index=False, include_column_header=True)

    # generate chart for "sheet_name", will check if have chart before generating
    def dfChart(self , sheet_name , fixed_Chart_ID , label_Cell ,x_axis_title ,count_Cell):
        try:
            service_S = build("sheets","v4", credentials=self.creds)
            service_D = build("drive","v3",credentials=self.creds)

            # Check if the spreadsheet existed or not
            q_info = "name ='" + sheet_name + "'and mimeType = 'application/vnd.google-apps.spreadsheet'"
        
            txt_response = service_D.files().list(q= q_info,
                                                spaces = 'drive'
                                                ).execute()

            if txt_response['files']:

                spreadsheet = self.client.open(sheet_name)
                spreadsheet_ID = spreadsheet.id
                sheet_ID = spreadsheet.sheet1.id

                try:
                    # for checking if chart existed, if so skip this
                    target_sheet = spreadsheet.get_worksheet_by_id(fixed_Chart_ID)
                    print(f"The sheet with ID '{fixed_Chart_ID}' exists, proceed to skip this function")

                except gspread.WorksheetNotFound:
                    # if not exist, proceed with creating chart
                    print(f"Sheet with ID '{fixed_Chart_ID}' not found in the spreadsheet,proceed with chart bar creation")

                    # request body (template)
                    request_body = {
                                'requests': [
                                    {
                                    'addChart': 
                                    {
                                        'chart': 
                                        {
                                        'spec': 
                                        {
                                            'title': f"Accumulate head count as per {x_axis_title}",
                                            'basicChart': 
                                            {
                                            'chartType': "COLUMN",
                                            'legendPosition': "BOTTOM_LEGEND",
                                            'axis': 
                                            [
                                                #X-axis
                                                {
                                                'position': "BOTTOM_AXIS",
                                                'title': x_axis_title
                                                },
                                                #Y-axis
                                                {
                                                'position': "LEFT_AXIS",
                                                'title': "Count"
                                                }
                                            ],

                                            # Chart Label
                                            'domains': 
                                            [
                                                {
                                                    'domain':
                                                    {
                                                        'sourceRange':
                                                        {
                                                            'sources':
                                                            [
                                                                {
                                                                    'sheetId': sheet_ID,
                                                                    'startRowIndex': 0,
                                                                    'endRowIndex': 1000,
                                                                    'startColumnIndex': label_Cell,
                                                                    'endColumnIndex': label_Cell+1
                                                                }
                                                            ]
                                                        }
                                                    }
                                                }
                                            ],

                                            # Chart Data
                                            'series': 
                                            [
                                                {
                                                'series': 
                                                {
                                                    'sourceRange': 
                                                    {
                                                    'sources': 
                                                    [
                                                        {
                                                        'sheetId': sheet_ID,
                                                        'startRowIndex': 0,
                                                        'endRowIndex': 1000,
                                                        'startColumnIndex': count_Cell,
                                                        'endColumnIndex': count_Cell+1
                                                        }
                                                    ]
                                                    }
                                                },
                                                'targetAxis': "LEFT_AXIS"
                                                }
                                            ],
                                            'headerCount': 1
                                            }
                                        },
                                        'position': {
                                            "sheetId": fixed_Chart_ID
                                        }
                                        }
                                    }
                                    }
                                ]
                                }



                    # series (to store the data for each camera), "None" need to be replaced
                    series_template =   {
                                            'series': 
                                            {
                                                'sourceRange': 
                                                {
                                                'sources': 
                                                [
                                                    {
                                                    'sheetId': sheet_ID,
                                                    'startRowIndex': 0,
                                                    'endRowIndex': 1000,
                                                    'startColumnIndex': None,
                                                    'endColumnIndex': None
                                                    }
                                                ]
                                                }
                                            },
                                            'targetAxis': "LEFT_AXIS"
                                        }
                    
                    all_series = []
                    for idx in range(self.camNum):          
                        import copy
                        # make a copy, so that we dont mix with the template
                        series = copy.deepcopy(series_template)
                        # edit eht start column index and end column index
                        series['series']['sourceRange']['sources'][0]['startColumnIndex'] = count_Cell + idx
                        series['series']['sourceRange']['sources'][0]['endColumnIndex'] = count_Cell + idx + 1
                        # add to all_series
                        all_series.append(series)
                    
                    # replace with all_series
                    request_body['requests'][0]['addChart']['chart']['spec']['basicChart']['series'] = all_series
                    response = service_S.spreadsheets().batchUpdate(
                        spreadsheetId = spreadsheet_ID,
                        body = request_body
                    ).execute()
                    print("chart created")
            else:
                print("cannot find file")
                
        except HttpError as e:
            print("Error: " + str(e))
        

        
        

        
        
