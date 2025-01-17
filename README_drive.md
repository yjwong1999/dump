To access local log file
> path: /home/library/Desktop/new/log

> local log file available in text file (.txt) format only

**Addon for floor 6 IT room pc (Mr Teo) [not available for library currently]
> path: /home/{PC Name}/Desktop/new/log

> Removed online logging, only local log available

> Video file logging is available

> Video Log file name: {video file name}_Count.txt

> Video log file only have one line, "accumulated count for {video file name} is {cumulated count}, and Cumulative count in video log file rewrites every frame

> If pipeline reruns for the same video file with same name, existing video log file for such video will be rewritten, this issue will not happen if the same video is renamed as new name before running as that given name.***

--------------------------------------------------------------------------------------

[ONLINE ACCESS] [Log file available in google drive as google sheet only]
email: <your email>
password: <your password>

Code for creating new google sheet logfile on drive and update it is in drive_utils1 and cloudSync.py

--------------------------------------------------------------------------------------

To access Online log file:
(individual day file)
> My Drive -> LogFld -> cam_{log data for that date}_count 
[eg: cam_2024-05-16_count, means log data for 2024-05-16]

> First sheet shows the count details.

> col 1 is log count of that date, with last column at 12 am midnight mark (shows next day date)

> col 2 shows the time (hour hand) at which accumulated count is logged.
[eg: 	1 pm with 100 at camera 000 means before 1 pm there are already 100 people passing ]
[	camera 000 geofencing								   ]

> col 3 onwards shows each camera count at different time, which last column being the final cumulative count for the day.

> Second sheet shows the bar graph of the day, x-axis shows the time (hour hand) when each count logged and y axis shows the count [graph downloadable as pdf/png/svg]

--------------------------------------------------------------------------------------

(individual month file)
> My Drive -> LogFld -> masterFile_{log data for the year}/{log data for the month}
[eg: masterFile_2024/05, means monthly log data for 2024/05]

> First sheet shows the count details.

> col 1 is the total cumulative count of that date at 12 am midnight

> col 2 onwards shows each camera cumulative count at each date

> Second sheet shows the bar graph of the month, x-axis shows the date logged and y axis shows the cumulative count for the date [graph downloadable as pdf/png/svg]

---------------------------------------------------------------------------------------

**Important note
> As per 17/05/2024, the script is ran manually (Yijie will update it to call it autonomously)

> Script is independent from the main pipeline code, can be executed from other code.

> There is a bug for the script, where if such log file logged count at 7am for the day and logged the last cumulative count at 7 am next day (due to multithread lagging), main code will return error. (Yijie will also update this later)
[explanation refer to no.5]

> The final log time should be at 12 am midnight, else last row for corresponding camera will be 0.

> Final local log time recorded pass 12 am [hour hand] midnight (e.g. 4 AM or 7 AM on May 17th) will be presented on cloud as if they were recorded on previous day. (e.g. logged at 4 AM or 7 AM on May 16th) [this bug is due to local log file format error (also multithreading lag)]

> The cloudSync is fully dependent on the log file format, so file name should remain as camera_00{index}_{date}_count.txt, and format inside should be date, time, count format

> Count presented as 0 for the whole column can be due to missing log file for such camera for the day, mostly due to camera went offline or pipeline stopped for that day.

> Count presented as 0 in between rows or after certain row with count value can be due to pipeline stop during that time.

> Script will automatically update the given date logged, just need to input the number of camera and the logged date to be sync

> Script exports txt file as dataframe format, therefore it can also be modified to export in excel format (without graph)

Token Section:
> token can expire under few criteria
- user revoked app access
- refresh token not been used or accessed for 6 months
- user changed password
- max number of granted(live) refresh token exceeded (accessing this account oauth credential in other pc will grant new token in that pc)
- the account disable that app's scopes (drive, sheets)

> Google service account may fix this issue, which may also allow autonomous gmail sending, however this may need g-suite(google workspace admin account) which is not free, and require some training before able to navigate the admin console
	> Fyi pricing for business starter is 15 rm per monthly bill, 36 rm for standard and so on. (more info for pricing under: https://workspace.google.com/pricing?hl=en_my)

> another way which can use to notify user if token expire is to enable 2 factor authentication, however that will need a device or phone number to verify the account before enabling the "less secure app" for the code to send email through smtp server.

> preferrable do a checkup on token validity every month


