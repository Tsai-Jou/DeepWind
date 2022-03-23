<<<<<<< HEAD
"""
[中央氣象局衛星雲圖下載]

<說明>
   1. 雲圖網址範例: "https://www.cwb.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800-2020-09-05-00-10.jpg"
   2. 雲圖共有五類(ex.TWI_IR1_CR_800)
   3. 透過編輯"雲圖類型"及"更新時間"下載指定的雲圖檔案
   4. 雲圖依類型儲存於個別資料夾: /cwb/[雲圖類型]/[檔名.jpg] 
     (ex. /cwb/TWI_IR1_CR_800/TWI_IR1_CR_800-2020-09-05-00-10.jpg)
   
<執行目標>
   1. 衛星雲圖下載至GCP_VM
   2. 將GCP_VM內圖檔上傳GoogleCloudStorage
   3. 下載過的圖檔資料匯入CloudSQL_cwb資料庫

<程式流程>
依圖檔類型執行以步驟-
步驟一：查詢資料庫中3天內最後一筆資料 (以最新網頁時間回推)
   1. 無3天內資料：建立3天的時間列，下載圖檔並匯入資料
   2. 有3天內資料：
      a. 最後一筆資料時間與網頁時間相同 → 不執行檔案下載
      b. 最後一筆資料時間與網頁時間不同 → 下載檔案至最新時間
步驟二：
   1. query各類型圖檔3天內未下載到檔案的時間
   2. query結果不為空值(3天內有時段沒有資料) → 補下載檔案
"""

import requests
import os
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import pymysql
from google.cloud import storage


# 函數: GCP_VM圖檔上傳到 goole cloud storage
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    # 進行身分驗證
    storage_client = storage.Client.from_service_account_json('/home/kdd_gcp/Desktop/chromedriver/GoogleCloudStorage/sharing-project-218310-0f8ebd583fb1.json')

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

    print("Cloud_Storage新增: {} ".format(source_file_name.split("/")[-1]))


# 函數: 產出10分鐘間隔的時間串列
def timelist(startime, endtime):
   Startdatetime = datetime.strptime(startime, "%Y-%m-%d %H:%M")
   Enddatetime = datetime.strptime(endtime, "%Y-%m-%d %H:%M")
   time_list = []      
   while Startdatetime < Enddatetime :
      Startdatetime = Startdatetime + timedelta(minutes = 10)
      time_list.append(Startdatetime.strftime("%Y-%m-%d %H:%M"))
   return time_list


# 函數: 圖檔下載到GCP_VM、上傳goole cloud storage、資料匯入cwb
def download_image(image_time, image_mode):
   datetimeOfFile = image_time.replace(" ", "-").replace(":", "-") # 檔名中的日期
   # 資料匯入的SQL語法 (記錄下載過的檔案資料)
   sql_insert_data = \
      """INSERT INTO satellite_image (update_time, satellite_mode, file_name, file_size) VALUES"""
   values = "('%s', '%s', '%s', '%d'),"
   # 圖檔網址
   img_url = "https://www.cwb.gov.tw/Data/satellite/%s/%s-%s.jpg" %(image_mode, image_mode, datetimeOfFile)
   try:
      image = requests.get(img_url) 
      img_name = img_url.split("/")[-1]  # 圖檔名稱
      # 狀態碼等於200時，下載檔案到GCP_VM
      if image.status_code == 200:                                     
         filepath = path + "/" + image_mode + "/" + img_name # 圖檔路徑
         imgfile = open(filepath,'wb')
         imgfile.write(image.content) # 圖檔儲存
         print('下載檔案到GCP_VM: %s'%(img_name))
         imgfile.close()         
         size = os.path.getsize(filepath)  # 圖檔大小
         # 將檔案從GCP_VM上傳到Google Cloud Storage         
         try:
            destination_blob_name = "cwb_image" + "/" + image_mode + "/" + img_name
            upload_blob("cwb_tpc_image", filepath, destination_blob_name)
            sql_insert_data += values %(image_time, image_mode, img_name, size)
            cur_cloud.execute(sql_insert_data[:-1])   # 新增資料
            db_cloud.commit()
            print("Cloud SQL新增資料:{}".format(img_name))
         except:
            print('Storage Error: %s'%(img_name))
      else:         
         print("%s"%(img_name), image.status_code)
   except:
      print('Error: %s'%(img_name))
      

#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/kdd_gcp/Desktop/chromedriver/GoogleCloudStorage/sharing-project-218310-0f8ebd583fb1.json'

# 以chrome瀏覽器抓取中央氣象局網頁資料更新時間   
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options = chrome_options)  # 開啟chrome瀏覽器
driver.get("https://www.cwb.gov.tw/V8/C/W/OBS_Sat.html")  # 載入中央氣象局網頁

soup = bs(driver.page_source, 'html.parser')  # 以bs解析html網頁
driver.quit() # 關閉瀏覽器
html_update_time = soup.find('div',{'class':"tab-content showIMG"}).find("span").text  # 取得網頁時間
print("網頁更新時間: " + html_update_time)
html_update_time = html_update_time.replace("/", "-")

# 設定時間:網頁時間3天前
three_days_before = (datetime.strptime(html_update_time, "%Y-%m-%d %H:%M") - timedelta(days = 3)).strftime("%Y-%m-%d %H:%M")

# 連線雲端資料庫
db_cloud = pymysql.connect("34.80.235.201", "root", "esfortest", "cwb")
cur_cloud = db_cloud.cursor()


# 指定工作目錄(圖檔儲存路徑)
path = r'/home/kdd_gcp/Desktop/chromedriver/cwb'
os.chdir(path)

# 利用資料夾名稱建立"圖檔類型"的串列
folders = os.listdir(path)
TWI_folders = [i for i in folders if "TWI" in i]


# 依圖類類型依序進行任務
for f in TWI_folders:   
   # 步驟一: query 3天內最後一筆資料時間
   sql_last_updatetime = \
   """SELECT MAX(update_time) FROM satellite_image WHERE update_time > '%s' AND satellite_mode = '%s'""" % (three_days_before, f)
   cur_cloud.execute(sql_last_updatetime)
   last_updatetime = cur_cloud.fetchall()
   # 無3天內資料 → 下載3天內各時段檔案
   if last_updatetime[0] == None:
      time_list = timelist(three_days_before, html_update_time)
      for t in time_list:
         download_image(t, f)
   # 有3天內的資料
   else:
      # 最後一筆資料時間與網頁時間相同 → 不執行檔案下載
      if last_updatetime[0][0] == html_update_time:
         print("%s：最新圖檔已存在"%(f))
      # 最後一筆資料時間與網頁時間不同(小於) → 下載檔案至最新時間
      else:
         time_list = timelist(last_updatetime[0][0], html_update_time)
         for t in time_list:
            download_image(t, f)
      # 步驟二: query各類型圖檔3天內未下載到檔案的時間
      sql_data = \
         """SELECT * 
               FROM (SELECT a.update_time AS update_time, b.file_name AS file_name 
                        FROM (SELECT DISTINCT update_time FROM satellite_image)a 
                        LEFT JOIN (SELECT update_time, file_name FROM satellite_image 
                                      WHERE satellite_mode = "%s")b 
                        ON a.update_time = b.update_time 
                        WHERE a.update_time > "%s")c 
               WHERE file_name IS NULL""" % (f, three_days_before)
      cur_cloud.execute(sql_data)
      result = cur_cloud.fetchall()
      # 如有3天內有時段沒有資料，則進行檔案補下載
      if result != ():
         print("補下載：%s"%(f))
         for i in result:
            download_image(i[0], f)
               
db_cloud.close()     

=======
"""
[中央氣象局衛星雲圖下載]

<說明>
   1. 雲圖網址範例: "https://www.cwb.gov.tw/Data/satellite/TWI_IR1_CR_800/TWI_IR1_CR_800-2020-09-05-00-10.jpg"
   2. 雲圖共有五類(ex.TWI_IR1_CR_800)
   3. 透過編輯"雲圖類型"及"更新時間"下載指定的雲圖檔案
   4. 雲圖依類型儲存於個別資料夾: /cwb/[雲圖類型]/[檔名.jpg] 
     (ex. /cwb/TWI_IR1_CR_800/TWI_IR1_CR_800-2020-09-05-00-10.jpg)
   
<執行目標>
   1. 衛星雲圖下載至GCP_VM
   2. 將GCP_VM內圖檔上傳GoogleCloudStorage
   3. 下載過的圖檔資料匯入CloudSQL_cwb資料庫

<程式流程>
依圖檔類型執行以步驟-
步驟一：查詢資料庫中3天內最後一筆資料 (以最新網頁時間回推)
   1. 無3天內資料：建立3天的時間列，下載圖檔並匯入資料
   2. 有3天內資料：
      a. 最後一筆資料時間與網頁時間相同 → 不執行檔案下載
      b. 最後一筆資料時間與網頁時間不同 → 下載檔案至最新時間
步驟二：
   1. query各類型圖檔3天內未下載到檔案的時間
   2. query結果不為空值(3天內有時段沒有資料) → 補下載檔案
"""

import requests
import os
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import pymysql
from google.cloud import storage


# 函數: GCP_VM圖檔上傳到 goole cloud storage
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    # 進行身分驗證
    storage_client = storage.Client.from_service_account_json('/home/kdd_gcp/Desktop/chromedriver/GoogleCloudStorage/sharing-project-218310-0f8ebd583fb1.json')

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

    print("Cloud_Storage新增: {} ".format(source_file_name.split("/")[-1]))


# 函數: 產出10分鐘間隔的時間串列
def timelist(startime, endtime):
   Startdatetime = datetime.strptime(startime, "%Y-%m-%d %H:%M")
   Enddatetime = datetime.strptime(endtime, "%Y-%m-%d %H:%M")
   time_list = []      
   while Startdatetime < Enddatetime :
      Startdatetime = Startdatetime + timedelta(minutes = 10)
      time_list.append(Startdatetime.strftime("%Y-%m-%d %H:%M"))
   return time_list


# 函數: 圖檔下載到GCP_VM、上傳goole cloud storage、資料匯入cwb
def download_image(image_time, image_mode):
   datetimeOfFile = image_time.replace(" ", "-").replace(":", "-") # 檔名中的日期
   # 資料匯入的SQL語法 (記錄下載過的檔案資料)
   sql_insert_data = \
      """INSERT INTO satellite_image (update_time, satellite_mode, file_name, file_size) VALUES"""
   values = "('%s', '%s', '%s', '%d'),"
   # 圖檔網址
   img_url = "https://www.cwb.gov.tw/Data/satellite/%s/%s-%s.jpg" %(image_mode, image_mode, datetimeOfFile)
   try:
      image = requests.get(img_url) 
      img_name = img_url.split("/")[-1]  # 圖檔名稱
      # 狀態碼等於200時，下載檔案到GCP_VM
      if image.status_code == 200:                                     
         filepath = path + "/" + image_mode + "/" + img_name # 圖檔路徑
         imgfile = open(filepath,'wb')
         imgfile.write(image.content) # 圖檔儲存
         print('下載檔案到GCP_VM: %s'%(img_name))
         imgfile.close()         
         size = os.path.getsize(filepath)  # 圖檔大小
         # 將檔案從GCP_VM上傳到Google Cloud Storage         
         try:
            destination_blob_name = "cwb_image" + "/" + image_mode + "/" + img_name
            upload_blob("cwb_tpc_image", filepath, destination_blob_name)
            sql_insert_data += values %(image_time, image_mode, img_name, size)
            cur_cloud.execute(sql_insert_data[:-1])   # 新增資料
            db_cloud.commit()
            print("Cloud SQL新增資料:{}".format(img_name))
         except:
            print('Storage Error: %s'%(img_name))
      else:         
         print("%s"%(img_name), image.status_code)
   except:
      print('Error: %s'%(img_name))
      

#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/kdd_gcp/Desktop/chromedriver/GoogleCloudStorage/sharing-project-218310-0f8ebd583fb1.json'

# 以chrome瀏覽器抓取中央氣象局網頁資料更新時間   
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options = chrome_options)  # 開啟chrome瀏覽器
driver.get("https://www.cwb.gov.tw/V8/C/W/OBS_Sat.html")  # 載入中央氣象局網頁

soup = bs(driver.page_source, 'html.parser')  # 以bs解析html網頁
driver.quit() # 關閉瀏覽器
html_update_time = soup.find('div',{'class':"tab-content showIMG"}).find("span").text  # 取得網頁時間
print("網頁更新時間: " + html_update_time)
html_update_time = html_update_time.replace("/", "-")

# 設定時間:網頁時間3天前
three_days_before = (datetime.strptime(html_update_time, "%Y-%m-%d %H:%M") - timedelta(days = 3)).strftime("%Y-%m-%d %H:%M")

# 連線雲端資料庫
db_cloud = pymysql.connect("34.80.235.201", "root", "esfortest", "cwb")
cur_cloud = db_cloud.cursor()


# 指定工作目錄(圖檔儲存路徑)
path = r'/home/kdd_gcp/Desktop/chromedriver/cwb'
os.chdir(path)

# 利用資料夾名稱建立"圖檔類型"的串列
folders = os.listdir(path)
TWI_folders = [i for i in folders if "TWI" in i]


# 依圖類類型依序進行任務
for f in TWI_folders:   
   # 步驟一: query 3天內最後一筆資料時間
   sql_last_updatetime = \
   """SELECT MAX(update_time) FROM satellite_image WHERE update_time > '%s' AND satellite_mode = '%s'""" % (three_days_before, f)
   cur_cloud.execute(sql_last_updatetime)
   last_updatetime = cur_cloud.fetchall()
   # 無3天內資料 → 下載3天內各時段檔案
   if last_updatetime[0] == None:
      time_list = timelist(three_days_before, html_update_time)
      for t in time_list:
         download_image(t, f)
   # 有3天內的資料
   else:
      # 最後一筆資料時間與網頁時間相同 → 不執行檔案下載
      if last_updatetime[0][0] == html_update_time:
         print("%s：最新圖檔已存在"%(f))
      # 最後一筆資料時間與網頁時間不同(小於) → 下載檔案至最新時間
      else:
         time_list = timelist(last_updatetime[0][0], html_update_time)
         for t in time_list:
            download_image(t, f)
      # 步驟二: query各類型圖檔3天內未下載到檔案的時間
      sql_data = \
         """SELECT * 
               FROM (SELECT a.update_time AS update_time, b.file_name AS file_name 
                        FROM (SELECT DISTINCT update_time FROM satellite_image)a 
                        LEFT JOIN (SELECT update_time, file_name FROM satellite_image 
                                      WHERE satellite_mode = "%s")b 
                        ON a.update_time = b.update_time 
                        WHERE a.update_time > "%s")c 
               WHERE file_name IS NULL""" % (f, three_days_before)
      cur_cloud.execute(sql_data)
      result = cur_cloud.fetchall()
      # 如有3天內有時段沒有資料，則進行檔案補下載
      if result != ():
         print("補下載：%s"%(f))
         for i in result:
            download_image(i[0], f)
               
db_cloud.close()     

>>>>>>> bb47a6288e540a7100130d401d717a317a2abc2f
