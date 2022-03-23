<<<<<<< HEAD
"""
[爬蟲排程監控]

* 每6小時監控一次
* 回溯過去24小時資料(6小時為單位)
* 編輯監控資料mail給計劃相關人員

<監控程式>
A. 台電即時發電量爬蟲(連線GCP_VM資料庫)
    1. 台電爬蟲執行次數
    2. 台電站點數
    3. 台電站點資料數是否相同

B. 中央氣象局衛星雲圖爬蟲(連線Cloud SQL資料庫)
    # 衛星雲圖檔案下載數確認
"""

import pymysql
import datetime
import smtplib
from email.mime.text import MIMEText

# 監控時間設定
lookback_time = 24  # 回溯時間
period = 6  # 時間週期

time_slicing = []
for i in range(int(lookback_time/period)+1):
    time_slicing.append((datetime.datetime.now() - datetime.timedelta(hours = 6 * i)).strftime("%Y-%m-%d %H:%M"))


# [START sql_query]

# GCP_VM資料庫連線 (TPC資料監控)
db = pymysql.connect("localhost", "root", "esfortest", "TPC")
cursor = db.cursor()

# Cloud SQL資料庫連線 (cwb資料監控)
db_cloud = pymysql.connect("34.80.235.201", "root", "esfortest", "cwb")
cur_cloud = db_cloud.cursor()


# 台電爬蟲執行次數
tpc_crawlers = []
for i in range(int(lookback_time/period)):
   sql_crawler = \
   """SELECT COUNT(DISTINCT tpc_last_update) 
      FROM tpc_realtime_info 
      WHERE LEFT(tpc_last_update, 16) >= "%s" AND LEFT(tpc_last_update, 16) < "%s" """%(time_slicing[i+1], time_slicing[i])
   cursor.execute(sql_crawler)
   result = str(cursor.fetchall()).strip("(',)")
   tpc_crawlers.append(result)
#print(crawlers)

# 台電站點數
sql_generator = \
"""SELECT LEFT(record_time, 16), COUNT(*) 
   FROM tpc_realtime_info  
   WHERE record_time IN ((SELECT MAX(record_time) FROM tpc_realtime_info), 
                         (SELECT MAX(record_time) FROM tpc_realtime_info WHERE LEFT(record_time, 16) <= "%s"),
                         (SELECT MAX(record_time) FROM tpc_realtime_info WHERE LEFT(record_time, 16) <= "%s"), 
                         (SELECT MAX(record_time) FROM tpc_realtime_info WHERE LEFT(record_time, 16) <= "%s"))    
   GROUP BY record_time 
   ORDER BY record_time DESC""" %(time_slicing[1],time_slicing[2],time_slicing[3])

cursor.execute(sql_generator)
generators = list(cursor.fetchall())
#print(generators)

# 台電站點資料數是否相同
sql_generator_datas = \
"""SELECT t2.record_date, COUNT(*) 
   FROM (SELECT * FROM 
              (SELECT LEFT(record_time, 10) AS record_date, COUNT(*) AS generator_datas 
               FROM tpc_realtime_info
               WHERE LEFT(record_time, 16) BETWEEN "%s" AND "%s"
               GROUP BY LEFT(record_time, 10), generation_method, generator_name) t1
         GROUP BY record_date, generator_datas) t2
   GROUP BY t2.record_date
   HAVING COUNT(*) >1
   ORDER BY record_date""" %(time_slicing[-1], time_slicing[0])

cursor.execute(sql_generator_datas)
generator_datas = list(cursor.fetchall())
#print(generator_datas)

# 判斷是否有不同的站點資料數
if generator_datas == []:
   string = ""
else:
   string = "\n24小時內出現站點資料數不一致的狀況!"
#print("TPC sql OK")


# 衛星雲圖檔案下載確認
cwb_crawlers = []
for i in range(int(lookback_time/period)):
   sql_images = \
   """SELECT satellite_mode, COUNT(*) FROM satellite_image 
      WHERE update_time >= "%s" AND update_time < "%s"
      GROUP BY satellite_mode"""%(time_slicing[i+1], time_slicing[i])
   cur_cloud.execute(sql_images)
   result = cur_cloud.fetchall()
   cwb_crawlers.append(result)
#print("cwb sql OK")

db.close()
db_cloud.close()
   # [END sql_query]


# [START send_mail]   
sender = "kdd.gcp@gmail.com"
passwd = "eS414o6kdd"

# 要發送的email帳號
receivers = ["N96081088@gs.ncku.edu.tw", "bulawu@gmail.com", "N96081135@gs.ncku.edu.tw", "wgteng@mail.ncku.edu.tw", "queto9612@gmail.com"]
tpc_emails = [elem.strip().split(',') for elem in receivers]
cwb_emails = [elem.strip().split(',') for elem in receivers[2:]]

# 建立寄送mail的server(SMTP)
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(sender, passwd)
   
# TPC email內文
tpc_text = ""
for i in range(1,int(lookback_time/period)+1):
   tpc_text = tpc_text + \
   """   
   --前%s小時--  %s ~ %s 
   --爬蟲次數--  應為：36次，實為：%s次
   --台電站點數--  %s站\n"""%(str(i*period), time_slicing[i], time_slicing[i-1], tpc_crawlers[i-1], generators[i-1][1])

tpc_text = tpc_text + string
#print("tpc_text OK")

# email格式
msg = MIMEText(tpc_text, "plain", "utf-8")
msg["Subject"] = "台電即時發電資料監控"
msg["To"] = ",".join(receivers)


server.sendmail(sender, tpc_emails, msg.as_string())
#print("TPC mail OK")


# Satellite email內文
cwb_text = ""
for i in range(1,int(lookback_time/period)+1):
   cwb_text = cwb_text + \
   "\n前%s小時 圖檔下載數--  %s ~ %s\n"%(str(i*period), time_slicing[i], time_slicing[i-1])
   for m in cwb_crawlers[i-1]:
      cwb_text = cwb_text + \
      "%-18s：  應為：36次，實為：%s次\n"%(m[0], m[1])

#print("cwb_text OK")

# email格式
msg = MIMEText(cwb_text, "plain", "utf-8")
msg["Subject"] = "衛星雲圖爬蟲排程監控"
msg["To"] = ",".join(receivers[2:])

server.sendmail(sender, cwb_emails, msg.as_string())

server.quit()
#print("cwb mail OK")
   # [END send_mail]
      

=======
"""
[爬蟲排程監控]

* 每6小時監控一次
* 回溯過去24小時資料(6小時為單位)
* 編輯監控資料mail給計劃相關人員

<監控程式>
A. 台電即時發電量爬蟲(連線GCP_VM資料庫)
    1. 台電爬蟲執行次數
    2. 台電站點數
    3. 台電站點資料數是否相同

B. 中央氣象局衛星雲圖爬蟲(連線Cloud SQL資料庫)
    # 衛星雲圖檔案下載數確認
"""

import pymysql
import datetime
import smtplib
from email.mime.text import MIMEText

# 監控時間設定
lookback_time = 24  # 回溯時間
period = 6  # 時間週期

time_slicing = []
for i in range(int(lookback_time/period)+1):
    time_slicing.append((datetime.datetime.now() - datetime.timedelta(hours = 6 * i)).strftime("%Y-%m-%d %H:%M"))


# [START sql_query]

# GCP_VM資料庫連線 (TPC資料監控)
db = pymysql.connect("localhost", "root", "esfortest", "TPC")
cursor = db.cursor()

# Cloud SQL資料庫連線 (cwb資料監控)
db_cloud = pymysql.connect("34.80.235.201", "root", "esfortest", "cwb")
cur_cloud = db_cloud.cursor()


# 台電爬蟲執行次數
tpc_crawlers = []
for i in range(int(lookback_time/period)):
   sql_crawler = \
   """SELECT COUNT(DISTINCT tpc_last_update) 
      FROM tpc_realtime_info 
      WHERE LEFT(tpc_last_update, 16) >= "%s" AND LEFT(tpc_last_update, 16) < "%s" """%(time_slicing[i+1], time_slicing[i])
   cursor.execute(sql_crawler)
   result = str(cursor.fetchall()).strip("(',)")
   tpc_crawlers.append(result)
#print(crawlers)

# 台電站點數
sql_generator = \
"""SELECT LEFT(record_time, 16), COUNT(*) 
   FROM tpc_realtime_info  
   WHERE record_time IN ((SELECT MAX(record_time) FROM tpc_realtime_info), 
                         (SELECT MAX(record_time) FROM tpc_realtime_info WHERE LEFT(record_time, 16) <= "%s"),
                         (SELECT MAX(record_time) FROM tpc_realtime_info WHERE LEFT(record_time, 16) <= "%s"), 
                         (SELECT MAX(record_time) FROM tpc_realtime_info WHERE LEFT(record_time, 16) <= "%s"))    
   GROUP BY record_time 
   ORDER BY record_time DESC""" %(time_slicing[1],time_slicing[2],time_slicing[3])

cursor.execute(sql_generator)
generators = list(cursor.fetchall())
#print(generators)

# 台電站點資料數是否相同
sql_generator_datas = \
"""SELECT t2.record_date, COUNT(*) 
   FROM (SELECT * FROM 
              (SELECT LEFT(record_time, 10) AS record_date, COUNT(*) AS generator_datas 
               FROM tpc_realtime_info
               WHERE LEFT(record_time, 16) BETWEEN "%s" AND "%s"
               GROUP BY LEFT(record_time, 10), generation_method, generator_name) t1
         GROUP BY record_date, generator_datas) t2
   GROUP BY t2.record_date
   HAVING COUNT(*) >1
   ORDER BY record_date""" %(time_slicing[-1], time_slicing[0])

cursor.execute(sql_generator_datas)
generator_datas = list(cursor.fetchall())
#print(generator_datas)

# 判斷是否有不同的站點資料數
if generator_datas == []:
   string = ""
else:
   string = "\n24小時內出現站點資料數不一致的狀況!"
#print("TPC sql OK")


# 衛星雲圖檔案下載確認
cwb_crawlers = []
for i in range(int(lookback_time/period)):
   sql_images = \
   """SELECT satellite_mode, COUNT(*) FROM satellite_image 
      WHERE update_time >= "%s" AND update_time < "%s"
      GROUP BY satellite_mode"""%(time_slicing[i+1], time_slicing[i])
   cur_cloud.execute(sql_images)
   result = cur_cloud.fetchall()
   cwb_crawlers.append(result)
#print("cwb sql OK")

db.close()
db_cloud.close()
   # [END sql_query]


# [START send_mail]   
sender = "kdd.gcp@gmail.com"
passwd = "eS414o6kdd"

# 要發送的email帳號
receivers = ["N96081088@gs.ncku.edu.tw", "bulawu@gmail.com", "N96081135@gs.ncku.edu.tw", "wgteng@mail.ncku.edu.tw", "queto9612@gmail.com"]
tpc_emails = [elem.strip().split(',') for elem in receivers]
cwb_emails = [elem.strip().split(',') for elem in receivers[2:]]

# 建立寄送mail的server(SMTP)
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(sender, passwd)
   
# TPC email內文
tpc_text = ""
for i in range(1,int(lookback_time/period)+1):
   tpc_text = tpc_text + \
   """   
   --前%s小時--  %s ~ %s 
   --爬蟲次數--  應為：36次，實為：%s次
   --台電站點數--  %s站\n"""%(str(i*period), time_slicing[i], time_slicing[i-1], tpc_crawlers[i-1], generators[i-1][1])

tpc_text = tpc_text + string
#print("tpc_text OK")

# email格式
msg = MIMEText(tpc_text, "plain", "utf-8")
msg["Subject"] = "台電即時發電資料監控"
msg["To"] = ",".join(receivers)


server.sendmail(sender, tpc_emails, msg.as_string())
#print("TPC mail OK")


# Satellite email內文
cwb_text = ""
for i in range(1,int(lookback_time/period)+1):
   cwb_text = cwb_text + \
   "\n前%s小時 圖檔下載數--  %s ~ %s\n"%(str(i*period), time_slicing[i], time_slicing[i-1])
   for m in cwb_crawlers[i-1]:
      cwb_text = cwb_text + \
      "%-18s：  應為：36次，實為：%s次\n"%(m[0], m[1])

#print("cwb_text OK")

# email格式
msg = MIMEText(cwb_text, "plain", "utf-8")
msg["Subject"] = "衛星雲圖爬蟲排程監控"
msg["To"] = ",".join(receivers[2:])

server.sendmail(sender, cwb_emails, msg.as_string())

server.quit()
#print("cwb mail OK")
   # [END send_mail]
      

>>>>>>> bb47a6288e540a7100130d401d717a317a2abc2f
