"""
[台電即時發電資料爬蟲]

<說明>
1. 抓取台電網頁公告的即時發電量，存入資料庫(GCP_VM/cloud SQL)
2. 網頁預計每10分鐘更新
3. 存取網頁HTML

<執行步驟>
1. 以網頁更新時間與資料庫最後時間比對網頁資料是否更新 (*網頁資料讀取錯誤時儲存HTML文字檔)
    a. 時間相同 → 結束程式
    b. 時間不同 → 程式繼續
    c. 讀不到網頁時間 → 程式繼續 (改以時段發電量總和來比對網頁資料是否更新)
2. 解析網頁資料，整理出每個站點的發電資料 (*網頁資料讀取錯誤時儲存HTML文字檔)    
3. 編輯匯入資料庫的sql指令&各站點發電量加總
4. 比對網頁發電量總和與資料庫最後時段發電量總和是否相同 
    a. 總和相同 → 程式結束
    b. 總和不同 → 網頁更新資料匯入資料庫 
"""

from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pymysql
import datetime
from selenium.webdriver.chrome.options import Options
import sys

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options = chrome_options)
driver.get("https://www.taipower.com.tw/d006/loadGraph/loadGraph/genshx_.html")

# 以bs解析html網頁
soup = bs(driver.page_source, 'html.parser')
# close the driver
driver.quit()

# 讀取現在時間        
current_time = str(datetime.datetime.now())
current_time = current_time[0:19]

path_txt = "/home/kdd_gcp/Desktop/chromedriver/tpcHTML/台電HTML_%s.txt"%(current_time.replace(' ','-').replace(':','-'))
path_error = "/home/kdd_gcp/Desktop/chromedriver/tpcHTML/台電HTML_Error.txt"

# 讀取網頁最後更新時間:用於判斷資料是否更新
try:
    web_update_time = soup.find('a', id='datetime')
    web_update_time = web_update_time.text
except Exception as e:
    # 網頁資料讀取錯誤時儲存HTML文字檔 & 記錄錯訊息
    print(e)
    with open(path_txt, 'w', encoding='utf8') as file:
        file.write(soup.prettify())
    with open(path_error, 'a', encoding='utf8') as file:
        file.write(current_time + " Error: %s\n" %(e))
    web_update_time = "nan"
    # 如讀不到網頁時間，改以發電量總和來比對
    power_generation = 0


# 資料庫連線:
# GCP_VM: 第39行資料庫連接: 測試主機運行請鍵入test，gcp主機請鍵入gcpvm
from dbaddtionaltools import dbaccount as dpa
temp = dpa.account_reporter('gcpvm')
db = pymysql.connect(temp[0], temp[1], temp[2], temp[3])
cursor = db.cursor()
# cloud SQL
db_cloud = pymysql.connect("34.80.235.201", "root", "esfortest", "TPC")
cur_cloud = db_cloud.cursor()

# sql: 如果資料表不存在，新增資料表
#sql_create_table = \
#"""CREATE TABLE IF NOT EXISTS `tpc_realtime_info` (
#   id int(20) NOT NULL AUTO_INCREMENT,
#   record_time varchar(30) CHARACTER SET utf8 NOT NULL,
#   tpc_last_update varchar(20) CHARACTER SET utf8 NOT NULL,
#   generation_method varchar(20) CHARACTER SET utf8 NOT NULL,
#   generator_name varchar(20) CHARACTER SET utf8 NOT NULL,
#   capacity varchar(20) CHARACTER SET utf8 NOT NULL,
#   power_generation varchar(20) CHARACTER SET utf8 NOT NULL,
#   percentage varchar(20) CHARACTER SET utf8 NOT NULL,
#   remark varchar(20) CHARACTER SET utf8 NOT NULL,
#   remark_in_name varchar(10) CHARACTER SET utf8 NOT NULL,
#   PRIMARY KEY (id)
#) ; """
#cursor.execute(sql_create_table)  # 新增資料表
#cur_cloud.execute(sql_create_table)  # 新增資料表


# query 資料庫中的最後時段與最後時段的發電量總和
sql_select =\
    """SELECT tpc_last_update, ROUND(SUM(power_generation)) FROM tpc_realtime_info 
        WHERE tpc_last_update=(SELECT MAX(tpc_last_update) FROM tpc_realtime_info) 
        GROUP BY tpc_last_update""" 
cursor.execute(sql_select)
result_select = cursor.fetchall()
db_update_time = result_select[0][0]  # 資料庫中的最後時段

# 資料庫中的最後時段與網頁最後更新時間相同 → 程式結束
if web_update_time == db_update_time:
    print('File already exists', current_time)
    db.close()
    db_cloud.close()
    sys.exit()

# 編輯各站點發電資料
dataInput = []
try:
    soup_table = soup.find('table', class_="display row-border compact stripe dataTable no-footer")
    columns = soup_table.find("thead").find_all('th')
    for tr in soup_table.find("tbody").find_all('tr'):
        if tr.find("a"):
            generation_method = tr.text  # 抓取發電方式
        elif "小計" in tr.text:
            continue  # 跳過小計
        elif len(tr.find_all("td"))<len(columns):
            continue  # 跳過備註(分類)列
        else:
            generation_data = [td.text for td in tr.find_all("td")]  # 發電機data
            if "(註" in generation_data[0]:
                remark_num = generation_data[0].split("(")[-1][:-1]  # 取得註解
                generation_data[0] = generation_data[0].split("(")[0]       # 取得站名
            else:
                remark_num = ""   # 站名無註解填入空值
            dataInput.append([generation_method,generation_data[0],generation_data[1],
                              generation_data[2],generation_data[3],generation_data[4],remark_num])
except Exception as e:
    # 網頁資料讀取錯誤時儲存HTML文字檔 & 記錄錯訊息
    print(e)
    with open(path_txt, 'w', encoding='utf8') as file:
        file.write(soup.prettify())
    with open(path_error, 'a', encoding='utf8') as file:
        file.write(current_time + " Error: %s\n" %(e))
    print("發電資料無法讀取")


# sql: 發電資料資料新增指令
sql_insert_data = \
      """INSERT INTO tpc_realtime_info (record_time, tpc_last_update, generation_method, generator_name, 
         capacity, power_generation, percentage, remark, remark_in_name) VALUES"""
values = "('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'),"
for data in dataInput:
    # 編輯sql   
    sql_insert_data += values % (
    current_time, web_update_time, data[0], data[1], 
    data[2], data[3], data[4], data[5], data[6]) 
    # 發電量累加
    try:
        power_generation += float(generation_data[2])
    except:
        pass


# 網頁發電量總和與資料庫最後時段發電量總和相等 → 程式結束
try:
    if round(power_generation)==result_select[0][1]:
        print('File already exists', current_time)
        db.close()
        db_cloud.close()
        sys.exit()
except:
    pass


# 網頁資料有更新 → 匯入資料庫
sql_insert_data = sql_insert_data[:-1]  # 去除字串尾端的 ","
# GCP_VM 資料庫
try:
    cursor.execute(sql_insert_data)   # 新增資料
    db.commit()
    print("Data are successfully inserted GCP_VM", current_time)
except Exception as e:
    db.rollback()
    print("GCP_VM Exception Occured : ", e)
# cloud SQL 資料庫
try:
    cur_cloud.execute(sql_insert_data)   # 新增資料
    db_cloud.commit()
    print("Data are successfully inserted GCP_CloudSQL", current_time)
except Exception as e:
    db_cloud.rollback()
    print("GCP_CloudSQL Exception Occured : ", e)

                
db.close()
db_cloud.close()
#