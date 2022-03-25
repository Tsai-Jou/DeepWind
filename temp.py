# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 16:18:14 2021

@author: user
"""

import os
import pandas as pd

toolspath = r"C:\成大專案\學研專家網絡\程式檔\模組與資料表"    
os.chdir(toolspath)
import toolmodules as tools
datsbase = "sna_network"
con_en = tools.dbConnectEngine(datsbase)
conn = tools.dbConnect(datsbase)
cur = conn.cursor()

import scholarTables as s_table
s_table.scholarInfoTable(datsbase)

columnsDB = ["advisor_ch", "ID", "thesisYear", "schoolName", "departmentName"]
sqlstr_tpi =\
    f"""
    SELECT {",".join(columnsDB)}
    FROM `thesis_processed`
    ORDER BY ID
    """
thesis_DB = pd.read_sql(sqlstr_tpi, con_en)
con_en.close()

sID_new = 1
thesisData = []
sUnit_sID = {}
for row in thesis_DB.values:
    data = list(row[1:3])
    if row[3] != "null":
        schoolName = row[3].strip()
        if row[4] == "null":
            data.append(schoolName)
        else:
            data.append(schoolName + row[4].strip())
    else:
        data.append("null")
    scholars = list(set(row[0].split("、")))
    for scholar in scholars:
        try:
            sID = sUnit_sID[(scholar, data[-1])]
        except:
            sID = sID_new
            sUnit_sID[(scholar, data[-1])] = sID_new
            sID_new += 1
        scholar_data = [sID, scholar] + data 
        thesisData.append(scholar_data)

columns = ["s_ID", "name", "ID", "year", "institution"]
thesisDataDF = pd.DataFrame(thesisData, columns = columns)        
thesisPI = list(set(thesisDataDF.name))

#duplicate = thesisData_DF[thesisData_DF.duplicated(["ID", "advisor_ch"], keep=False)].sort_index(by = ['advisor_ch', "thesisYear"])



df_one = pd.DataFrame()   
df_schoolName = pd.DataFrame()   
df_departmentName = pd.DataFrame()   
df_educationType = pd.DataFrame()   
df_recognize = pd.DataFrame()   
df_unrecognize = pd.DataFrame()   
pi_recognize = []
pi_unrecognize = []

for pi in thesisPI:
    temp = thesisData_DF[thesisData_DF["advisor_ch"]==pi]
    eType_len = len(set(temp.educationType))
    if len(temp) == 1:  #只有一筆資料
        df_one = pd.concat([df_one, temp], ignore_index=True)
        df_recognize = pd.concat([df_recognize, temp], ignore_index=True)
        pi_recognize.append(pi)
    elif eType_len == 1:  #學類都相同
        df_educationType = pd.concat([df_educationType, temp], ignore_index=True)
        df_recognize = pd.concat([df_recognize, temp], ignore_index=True)
        pi_recognize.append(pi)
    elif (len(set(temp.schoolName)) == 1) and (eType_len == 1):  #機構都相同
        df_schoolName = pd.concat([df_schoolName, temp], ignore_index=True)
        df_recognize = pd.concat([df_recognize, temp], ignore_index=True)
        pi_recognize.append(pi)
    elif (len(set(temp.departmentName)) == 1) and (eType_len == 1):  #部門都相同
        df_departmentName = pd.concat([df_departmentName, temp], ignore_index=True)
        df_recognize = pd.concat([df_recognize, temp], ignore_index=True)
        pi_recognize.append(pi)
    else:
        df_unrecognize = pd.concat([df_unrecognize, temp], ignore_index=True)
        pi_unrecognize.append(pi)

pi_recognize.sort()  
piID_recognize = pd.DataFrame([i+1 for i in range(len(pi_recognize))], columns=["pi_ID"])
piID_recognize["name"] = pi_recognize
df_recognize.columns = columns
df_recognize = df_recognize.sort_index(by = ["advisor_ch", "thesisYear"], ascending=False)
df_recognize_piID = pd.merge(piID_recognize, df_recognize, on="name", how = "inner")
df_recognize_piID.to_csv("../研究與PI資料/碩博士論文PI資料_recognize.csv", encoding = "utf8", index = False)

df_unrecognize.columns = columns
df_unrecognize = df_unrecognize.sort_index(by = ["name", "thesisYear"], ascending=False)
piID = len(pi_recognize) + 1
df_unrecognize_piID = pd.DataFrame()
for name in pi_unrecognize:
#    name = "陳建文"    
    tempData = df_unrecognize[df_unrecognize["name"]==name]
    educationTypes = list(set(tempData.educationType))
    
    eType_keywords = {}
    for eType in educationTypes:
        tempDF = tempData[(tempData["educationType"]==eType) & (~tempData["keywordsplit_ch"].isin(["null","no",""]))]
        keywords = "、".join(list(tempDF.keywordsplit_ch))
        eType_keywords[eType] = keywords.split("、")
    
    pi_eType = []
    eType_recognize = {}
    for eType in educationTypes:
        keywords = eType_keywords[eType].copy()
        if eType_recognize == {}:
            eType_recognize = {piID:[[eType], keywords]}
            pi_eType.append([piID, name, eType])
            piID += 1
        else:
            for ID, data in eType_recognize.items():
                same_keywords = list(set(keywords) & set(data[1]))
                if same_keywords != []:
                    key = ID
                    data[0].append(eType)
                    data[1].extend(keywords)
                    value = data
                    break
                else:
                    key = piID
                    value = [[eType], keywords]
                    piID += 1
            eType_recognize[key] = value
            pi_eType.append([key, name, eType])
            
    df_pi_eType = pd.DataFrame(pi_eType, columns=["pi_ID", "name", "educationType"])
    tempData_piID = pd.merge(df_pi_eType, tempData, on=["name", "educationType"], how = "inner")
    df_unrecognize_piID = pd.concat([df_unrecognize_piID, tempData_piID], ignore_index=True)

df_unrecognize_piID.to_csv("../研究與PI資料/碩博士論文PI資料_unrecognize.csv", encoding = "utf8", index = False)
    
# piID, piName
thesis_pi = df_recognize_piID[["pi_ID", "name"]].drop_duplicates(subset=["pi_ID", "name"], keep="first")
# thesisID, piID
thesis_piID = df_recognize_piID[["pi_ID", "thesis_ID"]]
# piInfo 
columns_Info = ["pi_ID", "thesisYear", "schoolName", "departmentName", "educationType"]
thesis_piInfoL = df_recognize_piID[columns_Info].drop_duplicates(subset=["pi_ID", "schoolName", "educationType"], keep="first")
thesis_piInfoF = df_recognize_piID[columns_Info].drop_duplicates(subset=["pi_ID", "schoolName", "educationType"], keep="last")
thesis_piInfoA = pd.merge(thesis_piInfoF, thesis_piInfoL, on=["pi_ID", "schoolName", "educationType"], how = "inner", suffixes=('_start', '_end'))
thesis_piInfo = thesis_piInfoA.drop(columns=["departmentName_start"])
thesis_piInfo = thesis_piInfo[["pi_ID", "thesisYear_start", "thesisYear_end", "schoolName", "departmentName_end", "educationType"]]
thesis_piInfo = thesis_piInfo.rename(columns={"thesisYear_start":"year_start", "thesisYear_end":"year_end", "departmentName_end":"department"})
# piID, keyword
thesis_piKeyword = []  
for ID in thesis_pi.pi_ID:
    tempDF = df_recognize_piID[df_recognize_piID["pi_ID"]==ID]["keywordsplit_ch"]    
    pikeywords = []
    for keywords in tempDF.values:
        if keywords not in ["null","no","","0","N/A"]:
            pikeywords.extend(keywords.split("、"))
    pikeywords_str = "、".join(list(set(pikeywords)))
    if pikeywords_str == "":
        pikeywords_str = None
    thesis_piKeyword.append([ID, pikeywords_str])

thesis_piKeyword = pd.DataFrame(thesis_piKeyword, columns=["pi_ID", "keywords"])

# 有指導論文的科技部計畫PI姓名
piName = pd.read_sql("SELECT principal_investigator FROM crawler_log WHERE thesesAmount <> 0", con_en)


splitStr = [name[-2:] for name in thesis_DB.schoolName]
splitStr = list(set(splitStr))
for name in thesis_DB.schoolName:
    if name[-2:] == "學校":
        print(name)



tPI = pd.read_sql("SELECT ID, professorName_ch FROM `thesis_processed`", con_en)
test = tPI.iloc[:100,:]
tPIs = tools.scholarNameClean(tPI.professorName_ch)
tPI["name"] = tPIs

piNames = []
for row in tPI[["ID", "name"]].values:
    if "、" in row[1]:
        PIs = list(set(row[1].split("、")))
        temp = []
        for pi in PIs:
            data = [row[0], pi]
            temp.append(data)
        piNames.extend(temp)
    else:
        piNames.append(list(row))

df_piNames = pd.DataFrame(piNames, columns = ["ID", "name"])        

piOnce = df_piNames.copy()
piOnce["count"] = ""
piOnce = piOnce.groupby(["name"], as_index=False).count()
piOnce = piOnce[piOnce["count"]==1]
piOnce = pd.merge(piOnce["name"], df_piNames, on="name", how = "left")


test1 = df_piNames.iloc[:100,:]
df_ = piOnce.loc[piOnce["name"].str.contains('．')]
df = piOnce[piOnce["ID"]==159892]

conn = tools.dbConnect(datsbase)
cur = conn.cursor()

sqlstr = "UPDATE `thesis_processed` SET advisor_ch=%s WHERE ID=%s"
for data in tPI.values:
#    print(sqlstr %(data[-1], data[0]))    
    cur.execute(f"UPDATE `thesis_processed` SET advisor_ch='{data[-1]}' WHERE ID={data[0]}")
    conn.commit()

result = cur.fetchall()

