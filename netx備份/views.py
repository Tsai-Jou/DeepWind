from django.db.models.fields import NullBooleanField
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from io import BytesIO
import os
from json import dumps
from networkx.readwrite import json_graph
import networkx as nx
import math
#import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import base64
from numpy import source

#import api.stock

#資料庫讀取
from .models import (SnaStudieskeywordsLinks,SnaStudieskeywordsNodes,
    SnaStudiespikeywordLinks,SnaEngineerkeywordsLinks,
    ProjectDiscipline,SnaDisciplinecrossLinks,
    SnaScholarrelationshipLinks)#,ResearcherInfo,
    #UniversityTeacher,ScholarInfo)

##中文設定
matplotlib.rcParams['font.family']='SimSun'

############################form1###################################

def netExquickform1(request):
    request.first = '1.歷年熱門關鍵詞網絡'
    request.second = '呈現碩博論文與科技部計畫中，熱門關鍵詞之間的關係強弱'
    return render(request,'netx/quickform1.html')

def netExquick1(request):
    #BASE_DIR = Path(__file__).resolve().parent.parent
    #STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    year = request.POST.get('yearSelect')
    keywordsAmount = request.POST.get('keywordsAmount')

    request.first = '1.歷年熱門關鍵詞網絡'
    request.second = f'呈現碩博論文與科技部計畫中，熱門關鍵詞之間的關係強弱：{year}年 / 前{keywordsAmount}名'
    
    df_nodes = SnaStudieskeywordsNodes.objects.raw(f"SELECT id, keyword, keywordsAmount AS 'value' FROM `sna_studieskeywords_nodes` WHERE year = '{year}' ORDER BY keywordsAmount DESC Limit {int(keywordsAmount)}")
    nodes_top = "','".join([ff.keyword for ff in df_nodes])
    df_links = SnaStudieskeywordsLinks.objects.raw(f"SELECT id, source, target, value FROM `sna_studieskeywords_links` WHERE year = '{year}' AND source IN ('{nodes_top}') AND target IN ('{nodes_top}')")
    
    rawData = []
    n = 0
    for row in df_nodes:
        rawData.append({'from':row.keyword, 'rank':n, 'length':keywordsAmount, 'count':row.value})
        n += 1    
    for row in df_links:
        rawData.append({'from':row.source, 'to':row.target, 'value':row.value})
        rawData.append({'from':row.target, 'to':row.source, 'value':row.value})
#    if int(keywordsAmount) <= 30:
#        font_size = 10
#        node_size = 150
#    else:
#        font_size = 8
#        node_size = 100

#    Graph = nx.Graph()
#    ##匯入節點資料
#    for row in df_nodes:
#        Graph.add_node(row.keyword, value=row.value)
#    ##匯入連線資料
#    for row in df_links:
#        Graph.add_edge(row.source, row.target, value=row.value)
#    ##layout    
#    pos = nx.circular_layout(Graph)
#    #利用邊的"value"屬性設定邊的粗細與顏色值
#    edge_colors = [int(value) for (u, v, value) in Graph.edges(Graph, 'value')]
#    edge_widths = [math.log(value*10, 7) for (u, v, value) in Graph.edges(Graph, 'value')]
#    node_colors = [value["value"] for (n, value) in Graph.nodes(data=True)]
#    #labels = {n:str(G_keywordsNetwork.node[n]["degree"]) for n,lab in pos.items()}
#    plt.figure(figsize=(10.5,6.5))
#    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["grey", "blue"]) 
##    cmap = plt.cm.tab20
#    ##底圖
#    nx.draw(Graph, pos, node_size=node_size, cmap=plt.cm.cool, node_color=node_colors, alpha=0.3, edge_color="white", width=0, with_labels=False)
#    ##節點、連線、標籤設定
#    nodes = nx.draw_networkx_nodes(Graph, pos, node_size=node_size, cmap=plt.cm.cool, node_color=node_colors, alpha=0.2)
#    edges = nx.draw_networkx_edges(Graph, pos, edge_color=edge_colors, edge_cmap=cmap, edge_vmin=0.1, width=edge_widths, alpha=0.2)
#    nx.draw_networkx_labels(Graph, pos, font_size=font_size, font_color="k", font_family="SimSun")
#    #nx.draw_networkx_labels(Graph, pos_c, labels=labels, font_size=25, font_color="r", alpha=0.7, font_family="SimSun")
#    plt.margins(x=0.1)
#    plt.colorbar(edges, shrink=0.6, location="left", label="colorbar of edges", pad=0.005)
#    plt.colorbar(nodes, shrink=0.6, location="right", label="colorbar of nodes", pad=0.005)
#    
#    buffer = BytesIO()
#    plt.savefig(buffer)
#    plot_data = buffer.getvalue()
#    
#    imb = base64.b64encode(plot_data)#對plot_data進行編碼
#    ims = imb.decode()
#    imd = "data:image/png;base64,"+ims
#    return render(request,'netx/quick.html',{"imgs":imd})
    dataJSON = dumps(rawData)
    return render(request,'netx/charts1.html',{"data":dataJSON})


############################form2###################################

def netExquickform2(request):
    request.first = '2.重點技術PI查詢'
    request.second = '呈現碩博論文與科技部計畫中，相關研究領域的PI'
    return render(request,'netx/quickform2.html')

def netExquick2(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    keyword = request.POST.get('keywordFindPI')
    yearFrom = request.POST.get('yearFrom')
    yearTo = request.POST.get('yearTo')

    request.first = '2.重點技術PI查詢'
    request.second = f'呈現碩博論文與科技部計畫中，相關研究領域的PI：{keyword} / {yearFrom}~{yearTo}年'
    
    # 從資料庫篩選資料匯入
    piTop = 10  #取得PI人數
    pikeywordTop = 5  #PI的關鍵詞個數
    ##篩選連線資料
    keyword_pi = SnaStudiespikeywordLinks.objects.raw(f"SELECT id, source, target, SUM(value) AS value FROM `sna_studiesPIkeyword_links` WHERE (year BETWEEN '{yearFrom}' AND '{yearTo}') AND (target = '{keyword}') GROUP BY source, target ORDER BY value DESC LIMIT {piTop}")
    if keyword_pi:
        piList = sorted([ff.source for ff in keyword_pi], reverse = True)
        sqlStr = ""
        for pi in piList:
            sqlStr += f"(SELECT id, source, target, SUM(value) AS value FROM `sna_studiesPIkeyword_links` WHERE (year BETWEEN '{yearFrom}' AND '{yearTo}') AND (source = '{pi}') AND (target <> '{keyword}') GROUP BY target ORDER BY value DESC LIMIT {pikeywordTop})"
            sqlStr += " UNION "
        sqlStr = sqlStr[0:-7]
        pi_keyword = SnaStudiespikeywordLinks.objects.raw(sqlStr)

        maxValue1 = max([ff.value for ff in keyword_pi])
        maxValue2 = max([ff.value for ff in pi_keyword])
        if maxValue1 > maxValue2:
            maxValue = maxValue1
        else:
            maxValue = maxValue2
     
        if maxValue > 15:
            width = round(maxValue/15, 2)
        else:
            width = 1
            
        rawData = [{'name':keyword, 'value':40, 'neighbors':0, 'children':[]}]
        n = 0
        for row in (keyword_pi):
            rawData[0]["children"].append({'name':row.source, 'value':int(row.value), 'linkWidth':int(row.value)/width, 'children':[]})        
            pi = row.source
            for row in (pi_keyword):
                if row.source == pi:
                    rawData[0]["children"][n]["children"].append({'name':row.target, 'value':int(row.value), 'linkWidth':int(row.value)/width})
            n += 1
        rawData[0]["neighbors"] = len(rawData[0]["children"])
        try:
            dataJSON = dumps(rawData)
            return render(request,'netx/charts2.html',{"data":dataJSON})
        except:
            plt.figure(figsize=(10,7))
            plt.title("查無資料...", loc="left", fontdict={'fontsize': 22})
            plt.axis("off")
        
            buffer = BytesIO()
            plt.savefig(buffer)
            plot_data = buffer.getvalue()
            
            imb = base64.b64encode(plot_data)#對plot_data進行編碼
            ims = imb.decode()
            imd = "data:image/png;base64,"+ims
            return render(request,'netx/quick.html',{"imgs":imd})
            

#        derivekeyword = list(set([ff.target for ff in keyword_pi]+[ff.target for ff in pi_keyword]))
#        derivekeyword.remove(keyword)
#        # 網絡圖：學門與關鍵字間的關係
#        Graph = nx.Graph()
#        ##匯入連線資料
#        for row in (keyword_pi):
#            Graph.add_edge(row.source, row.target, value=row.value)
#        for row in (pi_keyword):
#            Graph.add_edge(row.source, row.target, value=row.value)
        ##layout 
#        pos = nx.spring_layout(Graph, k=0.15, seed=33)
#        #利用邊的"value"屬性設定邊的粗細與顏色值
#        edge_colors = [float(value) for (u, v, value) in Graph.edges(Graph, 'value')]
#        edge_widths = [(float(value)/2.2) for (u, v, value) in Graph.edges(Graph, 'value')]
#        ##設定學門(中心)、關鍵字(外圈)節點標籤
#        labelkeyword = {n:n for n,lab in pos.items() if n == keyword}
#        labelderivekeyword= {n:n for n,lab in pos.items() if n in derivekeyword}
#        labelPI= {n:n for n,lab in pos.items() if n in piList}
#        plt.figure(figsize=(11,6.5))
#        ##底圖
#        nx.draw(Graph, pos, node_size = 0, node_color="blue", alpha=1, width=0, font_size=18, with_labels=False, font_color="w", font_family="SimSun")
#        ##節點、連線、標籤設定
#        edges = nx.draw_networkx_edges(Graph, pos, edge_color=edge_colors, edge_cmap=plt.cm.cool, edge_vmin=0.1, width=edge_widths, alpha=0.5)
#        nx.draw_networkx_labels(Graph, pos, labels=labelkeyword, font_size=15, font_color="k", font_family="SimSun")
#        nx.draw_networkx_labels(Graph, pos, labels=labelPI, font_size=12, font_color="k", font_family="SimSun")
#        nx.draw_networkx_labels(Graph, pos, labels=labelderivekeyword, font_size=9, font_color="k", font_family="SimSun")
#        plt.margins(x=0.1)
#        plt.colorbar(edges, shrink=0.6, label="colorbar of edges", pad=0.005)
    else:
        plt.figure(figsize=(10,7))
        plt.title("查無資料...", loc="left", fontdict={'fontsize': 22})
        plt.axis("off")
    
        buffer = BytesIO()
        plt.savefig(buffer)
        plot_data = buffer.getvalue()
        
        imb = base64.b64encode(plot_data)#對plot_data進行編碼
        ims = imb.decode()
        imd = "data:image/png;base64,"+ims
        return render(request,'netx/quick.html',{"imgs":imd})

############################form3###################################

def netExquickform3(request):
    request.first = '3.研究技術(關鍵詞)網絡'
    request.second = '呈現碩博論文與科技部計畫中，與研究技術較相關的關鍵詞及之間的關係'
    return render(request,'netx/quickform3.html')

def netExquick3(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    keyword = request.POST.get('keywordNetwork')

    request.first = '3.研究技術(關鍵詞)網絡'
    request.second = f'呈現碩博論文與科技部計畫中，與研究技術較相關的關鍵詞及之間的關係：{keyword}'
    
    top = 30
    for_nodes = SnaStudieskeywordsLinks.objects.raw(f"SELECT id, source, target, SUM(value) AS 'value' FROM `sna_studieskeywords_links` WHERE source='{keyword}' OR target='{keyword}' GROUP BY source, target ORDER BY value DESC LIMIT {top}")
    if for_nodes:
        source=[]
        target=[]
        for ff in for_nodes:
            source.append(ff.source)
            target.append(ff.target)
        nodes = source #list(for_nodes.source)
        nodes.extend(target)#(list(for_nodes.target))
        nodes = "','".join(list(set(nodes)))
        df_links = SnaStudieskeywordsLinks.objects.raw(f"SELECT id, source, target, SUM(value) AS 'value' FROM `sna_studieskeywords_links` WHERE source IN ('{nodes}') AND target IN ('{nodes}') GROUP BY source, target")
        maxValue = int(max([ff.value for ff in df_links]))
        rawData = [{'name':keyword, 'value':maxValue, 'neighbors':0, 'linkWidths':{}, 'children':[]}]
        n = 0
        for node in nodes.split("','"):
            if node != keyword:
                rawData[0]["linkWidths"][node] = 2.5
                rawData[0]["children"].append({'name':node, 'value':0, 'neighbors':0, 'link':[], 'linkWidths':{}})
                for row in df_links:
                    if row.source == node or row.target == node:
                        if row.source == node:
                            node1 = row.target
                        elif row.target == node:
                            node1 = row.source
                        if node1 == keyword:
                            rawData[0]["children"][n]["value"] = int(row.value)
                        else:
                            rawData[0]["children"][n]["link"].append(node1)
                            rawData[0]["children"][n]["linkWidths"][node1] = 0.8
                rawData[0]["children"][n]["neighbors"] = len(rawData[0]["children"][n]["link"])+1
                n += 1
        rawData[0]["neighbors"] = len(rawData[0]["linkWidths"])
        dataJSON = dumps(rawData)
        return render(request,'netx/charts3.html',{"data":dataJSON})

#        Graph = nx.Graph()
#        ##匯入連線資料
#        for row in df_links:#df_links.values:
#            Graph.add_edge(row.source, row.target, value=row.value)
#    
#        ## 繪製"太陽能"為中心的關鍵字網絡圖，layout指定
#        pos = nx.spring_layout(Graph, seed=47)
#        ##利用邊的"value"屬性設定邊的粗細與顏色值
#        edge_colors = [int(value) for (u, v, value) in Graph.edges(Graph, 'value')]
#        edge_widths = [math.log(int(value), 10.5)+0.5 for (u, v, value) in Graph.edges(Graph, 'value')]
#        labelCenter = {n:n for n in Graph if n==keyword}
#        labelNeighbors = {n:n for n in Graph if n!=keyword}
#        plt.figure(figsize=(10,7))
#    #    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["blue", "orange", "green", "purple", "red"]) 
#        cmap = plt.cm.tab20c
#        ##底圖
#        nx.draw(Graph, pos, node_size = 0, edge_color="white", width=0, with_labels=False)
#        ##節點、邊、標籤設定
#        nx.draw_networkx_nodes(Graph, pos, node_size=80, node_color='white', alpha=0) 
#        edges = nx.draw_networkx_edges(Graph, pos, edge_color=edge_colors, edge_cmap=cmap, edge_vmin=0.1, width=edge_widths, alpha=0.4)
#        nx.draw_networkx_labels(Graph, pos, labels=labelNeighbors, font_size=13, font_color="k", font_family="SimSun")
#        nx.draw_networkx_labels(Graph, pos, labels=labelCenter, font_size=25, font_color="r", font_family="SimSun")
#        plt.margins(x=0.1)
#        plt.colorbar(edges, shrink=0.6, label="colorbar of edges", pad=0.005)
    else:
        plt.figure(figsize=(10,7))
        plt.title("查無資料...", loc="left", fontdict={'fontsize': 22})
        plt.axis("off")
    
        buffer = BytesIO()
        plt.savefig(buffer)
        plot_data = buffer.getvalue()
        
        imb = base64.b64encode(plot_data)#對plot_data進行編碼
        ims = imb.decode()
        imd = "data:image/png;base64,"+ims
        return render(request,'netx/quick.html',{"imgs":imd})

############################form4###################################

def netExquickform4(request):
    request.first = '4.學門研究技術網絡'
    request.second = '呈現科技部計畫中，所屬學門計畫的熱門關鍵詞及之間的關係'
    return render(request,'netx/quickform4.html')

def netExquick4(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    discipline1 = request.POST.get('discipline1')
    discipline2 = request.POST.get('discipline2')

    request.first = '4.學門研究技術網絡'
#    request.second = f'呈現科技部計畫中，所屬學門計畫的熱門關鍵詞及之間的關係：{discipline1} {"& "+discipline2}'

    keywordsAmount = 20
    if (discipline1 and discipline2) and (discipline1 != discipline2):
        request.second = f'呈現科技部計畫中，所屬學門計畫的熱門關鍵詞及之間的關係：{discipline1} {"& "+discipline2}'
        discipline = [discipline1.split("-")[-1]]
        discipline.append(discipline2.split("-")[-1])
        ##篩選多學門連線資料
        sqlStr = ""
        for dcp in discipline:
            sqlStr += f"(SELECT id, source, target, SUM(value) AS value FROM `sna_engineerkeywords_links` WHERE source = '{dcp}' GROUP BY target ORDER BY value DESC LIMIT {keywordsAmount})"
            sqlStr += " UNION "
        sqlStr = sqlStr[0:-7]
        df_links = SnaEngineerkeywordsLinks.objects.raw(sqlStr)   
        ##layout
        target=[]
        keywordShare = []
        for ff in df_links:
            if ff.target in target:
                keywordShare.append(ff.target)
            else:
                target.append(ff.target)                
#        keywordunShare = list(set(target).difference(set(keywordShare)))
#        shell = [keywordShare, discipline, keywordunShare]  #設定各圈節點資料    
#        fig = (9,6.5)
        maxValue = int(max([ff.value for ff in df_links]))
        if maxValue > 15:
            width = maxValue/15
        else:
            width = 1
        
        rawData = []
        keywordIndex = {}
        n = 0
        for dcp in discipline:
            rawData.append({'name':dcp, 'value':40, 'neighbors':0, 'width':width, 'linkWidths':{}, 'children':[]})
            m = 0
            for row in df_links:
                if row.source == dcp:
                    rawData[n]['linkWidths'][row.target] = int(row.value)/width
                    if row.target in keywordShare and n==0:
                        rawData[n]['children'].append({'name':row.target, 'value':int(row.value), 'link':[discipline[1]], 'linkWidths':{}})
                        keywordIndex[row.target] = m
                        m += 1
                    elif row.target in keywordShare and n==1:
#                        continue
                        rawData[0]['children'][keywordIndex[row.target]]["linkWidths"][discipline[1]] = int(row.value)/width
                    else:
                        rawData[n]['children'].append({'name':row.target, 'value':int(row.value)})
                        m += 1
            n += 1
        rawData[0]["neighbors"] = len(rawData[0]["linkWidths"])
        rawData[1]["neighbors"] = len(rawData[1]["linkWidths"])
        dataJSON = dumps(rawData)
        return render(request,'netx/charts4_2.html',{"data":dataJSON})
    else:
        if discipline1:
            request.second = f'呈現科技部計畫中，所屬學門計畫的熱門關鍵詞及之間的關係：{discipline1}'
            discipline = [discipline1.split("-")[-1]]  #指定繪製學門
        elif discipline2:
            request.second = f'呈現科技部計畫中，所屬學門計畫的熱門關鍵詞及之間的關係：{discipline2}'
            discipline = [discipline2.split("-")[-1]]  #指定繪製學門
        ##篩選連線資料
        sqlStr = f"SELECT id, source, target, SUM(value) AS value FROM `sna_engineerkeywords_links` WHERE source = '{discipline[0]}' GROUP BY target ORDER BY value DESC LIMIT {keywordsAmount}"
        df_links = SnaEngineerkeywordsLinks.objects.raw(sqlStr)
        ##layout    
        shell = [discipline, [ff.target for ff in df_links]]  #設定各圈節點資料
        fig = (8,6.5)
        
        maxValue = int(max([ff.value for ff in df_links]))
        if maxValue > 15:
            width = round(maxValue/15, 2)
        else:
            width = 1
        
        rawData = [{'name':discipline[0], 'value':40, 'neighbors':0, 'linkWidths':{}, 'children':[]}]
        for row in df_links:
            rawData[0]['linkWidths'][row.target] = int(row.value)/width
            rawData[0]['children'].append({'name':row.target, 'value':int(row.value)})
        
        rawData[0]["neighbors"] = len(rawData[0]["linkWidths"])
        dataJSON = dumps(rawData)
        return render(request,'netx/charts4_1.html',{"data":dataJSON})

#    Graph = nx.Graph()  
#    ##匯入連線資料
#    for row in df_links:
#        Graph.add_edge(row.source, row.target, value=row.value)
#    pos_s = nx.shell_layout(Graph, shell, scale=10)
#    #利用邊的"value"屬性設定邊的粗細與顏色值
#    edge_colors = [float(value) for (u, v, value) in Graph.edges(Graph, 'value')]
#    edge_widths = [(float(value)/15)+0.3 for (u, v, value) in Graph.edges(Graph, 'value')]
#    ##設定學門(中心)、關鍵字(外圈)節點標籤
#    labelKeywords = {n:n for n,lab in pos_s.items() if n not in discipline}
#    labelCenter = {n:n for n,lab in pos_s.items() if n in discipline}
#    ##中文設定
#    matplotlib.rcParams['font.family']='SimSun'
#    plt.figure(figsize=fig)
#    ##底圖
#    nx.draw(Graph, pos_s, node_size = 0, node_color="blue", alpha=1, width=0, font_size=12, with_labels=False)
#    ##節點、連線、標籤設定
#    edges = nx.draw_networkx_edges(Graph, pos_s, edge_color=edge_colors, edge_cmap=plt.cm.cool, edge_vmin=0.1, width=edge_widths, alpha=0.5)
#    nx.draw_networkx_labels(Graph, pos_s, labels=labelCenter, font_size=15, font_color="k", font_family="SimSun")
#    nx.draw_networkx_labels(Graph, pos_s, labels=labelKeywords, font_size=10, font_color="k", font_family="SimSun")
#    plt.colorbar(edges, shrink=0.5, label="colorbar of edges", pad=0.003)
#    plt.margins(x=0.1)
#    
#    buffer = BytesIO()
#    plt.savefig(buffer)
#    plot_data = buffer.getvalue()
#    
#    imb = base64.b64encode(plot_data)#對plot_data進行編碼
#    ims = imb.decode()
#    imd = "data:image/png;base64,"+ims
#    return render(request,'netx/quick.html',{"imgs":imd})

############################form5###################################

def netExquickform5(request):
    request.first = '5.學門之間的合作網絡'
    request.second = '呈現科技部計畫中，學門之間的合作關係強弱'
    return render(request,'netx/quickform5.html')

def netExquick5(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    linkType = request.POST.get('disciplineRadio')
    if linkType == "pi-self":
        crossValue = int(request.POST.get('crossValueSelf'))
        typeName = "PI自我跨學門"
    else:
        crossValue = int(request.POST.get('crossValueOthers'))
        typeName = "不同PI間的跨學門合作"

    request.first = '5.學門之間的合作網絡'
    request.second = f'呈現科技部計畫中，學門之間的合作關係強弱：{typeName} / 至少合作過{crossValue}次'

    # 從資料庫篩選資料匯入
    if linkType == "pi-self":        
        ##PI自我跨學門
        typeSelect = "= 'pi-self'"
#        weight = "weight"
        value = "value"
    else:
        #PI共同指導&口試委員合作
        typeSelect = "<> 'pi-self' GROUP BY source, target"
#        weight = "SUM(weight) AS 'weight'"    
        value = "SUM(value) AS 'value'"
    
    sqlStr = \
    f"""SELECT t1.id AS 'id', CONCAT(t1.source, '-', t2.name) AS 'source', CONCAT(t1.target, '-', t3.name) AS target, {value}
        FROM sna_disciplinecross_links AS t1
        INNER JOIN project_discipline AS t2 ON t1.source = t2.code 
        INNER JOIN project_discipline AS t3 ON t1.target = t3.code 
        WHERE t1.value >= {crossValue} AND t1.type {typeSelect}"""
    
    df_links = SnaDisciplinecrossLinks.objects.raw(sqlStr)
    df_nodes = ProjectDiscipline.objects.raw("SELECT id, CONCAT(code, '-', name) AS 'name' FROM project_discipline WHERE code <> 'E08' ORDER BY name")

    dcp_links = {}
    for row in df_nodes:
        dcp_links[row.name] = {"neighbors":0, "count":0}
    rawData = []
    temp = []
    for row in df_links:
        dcp_links[row.source]["neighbors"] = dcp_links[row.source]["neighbors"] + 1
        dcp_links[row.source]["count"] = dcp_links[row.source]["count"] + int(row.value)
        dcp_links[row.target]["neighbors"] = dcp_links[row.target]["neighbors"] + 1
        dcp_links[row.target]["count"] = dcp_links[row.target]["count"] + int(row.value)
        temp.append({'from':row.source, 'to':row.target, 'value':int(row.value)})
        temp.append({'from':row.target, 'to':row.source, 'value':int(row.value)})
    node_values = sorted([value["count"] for key, value in dcp_links.items()], reverse = True)
    for node, value in sorted(list(dcp_links.items())): 
        valueIndex = node_values.index(value["count"])
        rawData.append({'from':node, 'type':typeName, 'rank':valueIndex, 'neighbors':value["neighbors"], 'count':value["count"]})
    rawData.extend(temp)
    
    dataJSON = dumps(rawData)
    return render(request,'netx/charts5.html',{"data":dataJSON})

#    def edgeParameter(value):
#        if max([ff.value for ff in df_links]) < 100:
#            width = math.log(value*100, 10)
#        else:
#            width = math.log(value, 12)
#        return width
#    
#    # 建立跨學門(ET)合作網絡
#    Graph = nx.Graph()
#    Graph.add_nodes_from([ff.name for ff in df_nodes])
#    for row in  df_links:   
#        Graph.add_edge(row.source, row.target, weight = row.value)
#    edges_weight_index = nx.get_edge_attributes(Graph, 'weight')
#    colors = [int(v) for k, v in edges_weight_index.items()]
#    widths = [edgeParameter(v) for k, v in edges_weight_index.items()]
#    pos = nx.circular_layout(Graph)
#    labels = {n:n for n,lab in pos.items()}
#    plt.figure(figsize=(8.1,6.3))
#    nx.draw(Graph, pos, node_size = 300, node_color='grey', width=0, alpha=0.3, with_labels=False)
#    edges = nx.draw_networkx_edges(Graph, pos, edge_color=colors, edge_cmap=plt.cm.coolwarm, edge_vmin=0.1, width=widths, alpha=0.5)
#    nx.draw_networkx_labels(Graph, pos, labels=labels, font_size=9.5, font_color="k",font_weight='heavy', font_family="SimSun", horizontalalignment="center")
#    plt.margins(x=0.09)
#    plt.colorbar(edges, shrink=0.5, label="colorbar of edges", pad=0.005)
#    
#    buffer = BytesIO()
#    plt.savefig(buffer)
#    plot_data = buffer.getvalue()
#    
#    imb = base64.b64encode(plot_data)#對plot_data進行編碼
#    ims = imb.decode()
#    imd = "data:image/png;base64,"+ims
#    return render(request,'netx/quick.html',{"imgs":imd})

############################form6###################################

def netExquickform6(request):
    request.first = '6.PI關係網絡'
    request.second = '呈現碩博論文中，PI之間的合作關係強弱'
    return render(request,'netx/quickform6.html')

def netExquick6(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    piName = request.POST.get('piName')
    relationship = request.POST.get('relationship')
    yearFrom = request.POST.get('yearFrom')
    yearTo = request.POST.get('yearTo')

    request.first = '6.PI關係網絡'
    request.second = f'呈現碩博論文中，PI之間的合作關係強弱：{piName} / {relationship} / {yearFrom}~{yearTo}年'

    if relationship == "碩博士論文-共同指導關係":
        typeSelect = "AND type = 'Advisor'"
    elif relationship == "碩博士論文-口試委員關係":
        typeSelect = "AND type = 'OralTestCommittee'"        
    elif relationship == "共同指導及口試委員關係":
        typeSelect = ""  
    # 從資料庫篩選資料匯入
    def dataSelect(yearFrom, yearTo, piName, typeSelect):
        ##篩選連線資料
        ##編輯sql
        sqlStr =\
        f"""SELECT id, source, target FROM `sna_scholarrelationship_links` 
        WHERE (year BETWEEN '{yearFrom}' AND '{yearTo}') 
            AND (source = '{piName}' OR target = '{piName}') {typeSelect}
        ORDER BY value DESC Limit 30"""
        ##query資料
        for_nodes = SnaScholarrelationshipLinks.objects.raw(sqlStr)
        if for_nodes:
            nodes = []
            for ff in for_nodes:
                nodes.extend([ff.source, ff.target])
            piList = list(set(nodes))
            nodes = "','".join(piList)
            sqlStr =\
            f"""SELECT id, source, target, SUM(value) AS 'value' 
            FROM `sna_scholarrelationship_links` 
            WHERE (year BETWEEN '{yearFrom}' AND '{yearTo}') 
                AND (source IN ('{nodes}') AND target IN ('{nodes}')) {typeSelect}
            GROUP BY source, target"""
            df_links = SnaScholarrelationshipLinks.objects.raw(sqlStr)
        else:
            df_links = "查無資料..."
            piList = ""
        return piList, df_links
    piList, df_links = dataSelect(yearFrom, yearTo, piName, typeSelect)
    # 網絡圖
    if type(df_links) is not str:
        maxValue = int(max([ff.value for ff in df_links]))
        rawData = [{'name':piName, 'value':maxValue, 'neighbors':len(piList)-1, 'linkWidths':{}, 'children':[]}]
        n = 0
        for node in piList:
            if node != piName:
                rawData[0]["linkWidths"][node] = 2.5
                rawData[0]["children"].append({'name':node, 'value':0, 'neighbors':0, 'link':[], 'linkWidths':{}})
                for row in df_links:
                    if row.source == node or row.target == node:
                        if row.source == node:
                            node1 = row.target
                        elif row.target == node:
                            node1 = row.source
                        if node1 == piName:
                            rawData[0]["children"][n]["value"] = int(row.value)
                        else:
                            rawData[0]["children"][n]["link"].append(node1)
                            rawData[0]["children"][n]["linkWidths"][node1] = 0.8
                rawData[0]["children"][n]["neighbors"] = len(rawData[0]["children"][n]["link"])+1
                n += 1
        dataJSON = dumps(rawData)
        return render(request,'netx/charts6.html',{"data":dataJSON})

#        Graph = nx.Graph()
#        ##匯入連線資料
#        for row in df_links:
#            Graph.add_edge(row.source, row.target, value=row.value)
#        ##layout 
#        pos = nx.spring_layout(Graph, seed=33)
#        #利用邊的"value"屬性設定邊的粗細與顏色值
#        min_value = min([ff.value for ff in df_links])
#        if min_value < 5:
#            n = 5/min_value
#        else:
#            n = 1
#        edge_colors = [int(value) for (u, v, value) in Graph.edges(Graph, 'value')]
#        edge_widths = [math.log(int(value)*n, 7) for (u, v, value) in Graph.edges(Graph, 'value')]
#        ##設定學門(中心)、關鍵字(外圈)節點標籤
#        labelpi= {n:n for n,lab in pos.items() if n == piName}
#        labelothers= {n:n for n,lab in pos.items() if n != piName}
#        plt.figure(figsize=(10,6.5))
#        cmap = plt.cm.tab20c
#        ##底圖
#        nx.draw(Graph, pos, node_size = 0, node_color="blue", edge_color="g", alpha=0.5, width=0.2, font_size=18, with_labels=False, font_color="w", font_family="SimSun")
#        ##節點、連線、標籤設定
#        edges = nx.draw_networkx_edges(Graph, pos, edge_color=edge_colors, edge_cmap=cmap, edge_vmin=0.1, width=edge_widths, alpha=0.3)
#        nx.draw_networkx_labels(Graph, pos, labels=labelpi, font_size=20, font_color="k", font_family="SimSun")
#        nx.draw_networkx_labels(Graph, pos, labels=labelothers, font_size=14, font_color="k", font_family="SimSun")
#        plt.margins(x=0.05)
#        plt.colorbar(edges, shrink=0.6, label="colorbar of edges", pad=0.005)
    else:
        plt.figure(figsize=(10,7))
        plt.title("查無資料...", loc="left", fontdict={'fontsize': 22})
        plt.axis("off")
    
        buffer = BytesIO()
        plt.savefig(buffer)
        plot_data = buffer.getvalue()
        
        imb = base64.b64encode(plot_data)#對plot_data進行編碼
        ims = imb.decode()
        imd = "data:image/png;base64,"+ims
        return render(request,'netx/quick.html',{"imgs":imd})

############################form7###################################

def netExquickform7(request):
    request.first = '7.PI的關鍵詞文字雲'
    request.second = '呈現PI在碩博論文與科技部計畫中，經常使用的關鍵詞'
    return render(request,'netx/quickform7.html')

def netExquick7(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    piName = request.POST.get('piName')
    yearFrom = request.POST.get('yearFrom')
    yearTo = request.POST.get('yearTo')

    request.first = '7.PI的關鍵詞文字雲'
    request.second = f'呈現PI在碩博論文與科技部計畫中，經常使用的關鍵詞：{piName} / {yearFrom}~{yearTo}年'
    
    # 從資料庫篩選資料匯入
    def dataSelect(yearFrom, yearTo, piName):
        ##篩選連線資料
        keywords = SnaStudiespikeywordLinks.objects.raw(f"SELECT id, target, SUM(value) AS value FROM `sna_studiesPIkeyword_links` WHERE (year BETWEEN '{yearFrom}' AND '{yearTo}') AND (source = '{piName}') GROUP BY source, target ORDER BY value DESC Limit 30")
        return keywords

    keywords = dataSelect(yearFrom, yearTo, piName)                   
        
    if len(keywords) >=1:
        rawData = []
        for row in keywords:
            rawData.append({"tag":row.target, "weight":int(row.value)})
        print(rawData)
        dataJSON = dumps(rawData)
        return render(request,'netx/charts7.html',{"data":dataJSON})
        
#        words = []
#        for row in keywords:
#            words.extend([row.target]*int(row.value))
#        words = " ".join(words)        
#
#        from wordcloud import WordCloud        
#        # 文字雲
#        ##中文設定
#        font = "C:\Windows\Fonts\SimSun.ttc"
#        plt.figure(figsize=(9,6))
##        plt.title(f"{piName}的關鍵詞文字雲({yearFrom}~{yearTo})", loc="left", fontdict={'fontsize': 22})
#        wordcloud = WordCloud(random_state=16, background_color="white", colormap='copper', margin=5, font_path=font, max_font_size=60, scale=3)
#        wordcloud.generate(words)
#        #wordcloud.recolor(color_func=img_colors)
#        plt.imshow(wordcloud, interpolation='bilinear')
#        plt.axis("off")
    else:
        plt.figure(figsize=(10,7))
        plt.title("查無資料...", loc="left", fontdict={'fontsize': 22})
        plt.axis("off")
    
        buffer = BytesIO()
        plt.savefig(buffer)
        plot_data = buffer.getvalue()
        
        imb = base64.b64encode(plot_data)#對plot_data進行編碼
        ims = imb.decode()
        imd = "data:image/png;base64,"+ims
        return render(request,'netx/quick.html',{"imgs":imd})

############################form8###################################

def netExquickform8(request):
    request.first = '教師比對'
    request.second = '請確認researcher_info哪筆為university_teacher裡的老師'
    
    # SELECT * FROM researcher_info WHERE Sid IS NULL AND identity < 3 
    # AND name IN (SELECT teacherName FROM university_teacher) ORDER BY Rid
    teacherName = UniversityTeacher.objects.all().values('teachername')
    #rInforaw = ResearcherInfo.objects.filter(sid__isnull=True, identity__lt=3, name__in=teacherName).order_by('rid')#.query.__str__()
    rInforaw = ResearcherInfo.objects.filter(sid__isnull=True, identity=3, name__in=teacherName).order_by('rid')#.query.__str__()
    rInfo = rInforaw.first()
    rInfocon = rInforaw.count() # 計數 rInforaw
    #pp = list(rInfo)

    # SELECT * FROM university_teacher WHERE teacherName = '朱聖緣'
    if rInforaw:
        uInfo = UniversityTeacher.objects.filter(teachername__contains=rInfo.name)#.query.__str__()
        #pp = list(uInfo)
    else:
        uInfo = None
    
    return render(request,'netx/quickform8.html',{"rInfo":rInfo,"uInfo":uInfo,"rInfocon":rInfocon})

def netExquick8(request):
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = os.path.join(BASE_DIR, "static\data")
    
    #Checkvalue = request.POST.getlist('fChecked[]') # 不勾 => []，勾1 => ['1']，勾1、3 => ['1'，'1']
    uid = request.POST.get('fChecked')
    rid = request.POST.get('rid')
    
    if uid != '0':
        # 讀取出 university_teacher、researcher_info
        uInfo = UniversityTeacher.objects.get(uid=uid)
        rInfo = ResearcherInfo.objects.get(rid=rid)
        #pp = list(rInfo)

        # 寫入 scholar_info
        scInfo = ScholarInfo(name=uInfo.teachername, institution=uInfo.universityname, 
            department=uInfo.departmentname, 
            position=rInfo.position, email=rInfo.email, telephone=rInfo.telephone, 
            birthdate=rInfo.birthdate, national_id=rInfo.national_id, gender=rInfo.gender
        )
        scInfo.save()
        #pp = scInfo.sid # 因為AutoField可取出新 Sid

        # 更新 researcher_info Sid
        ResearcherInfo.objects.filter(rid=rid).update(sid=scInfo.sid)
    else:
        ResearcherInfo.objects.filter(rid=rid).update(sid=0) #找不到寫入0

    return HttpResponseRedirect('/netx/quickform8/')

############################form9###################################

def netExquickform9(request):
    request.first = '傳參數測試'
    request.second = ''
    #vv = api.stock.get_stock(2021,10,'2330')

    #for item in data:  #取出每一天編號為stockno的股票資料
    #    if Collection.find({    #找尋該交易資料是否不存在
    #            "date": item[0],
    #            "stockno": stockno
    #        } ).count() == 0:
    #        element={'date':item[0], 'stockno':stockno, 'shares':item[1], 'amount':item[2], 'open':item[3], 'close':item[4], 
    #             'high':item[5], 'low':item[6], 'diff':item[7], 'turnover':item[8]};  #製作MongoDB的插入元素
    #        print(element)
    #        collection.insert_one(element)  #插入元素到MongoDB
    
    return render(request,'netx/quickform9.html')

@csrf_exempt
def ajax_form9(request):
    data = ""
    # 接參數
    if request.is_ajax() and request.method == "POST":
        data = request.POST.get('v1')
    
    #資料庫讀出的資料(此地為直接帶入) 開盤 收盤 最低 最高
    rawData = [['2021/12/31', '3570.47', '3539.18', '-33.69', '-0.94%', '3538.35', '3580.6', '176963664', '25403106', '-'], 
    ['2021/12/30', '3566.73', '3572.88', '9.14', '0.26%', '3538.11', '3573.68', '187889600', '26778766', '-'], 
    ['2021/12/29', '3528.4', '3563.74', '29.96', '0.85%', '3515.52', '3564.17', '182551920', '25093890', '-'], 
    ['2021/12/28', '3635.77', '3533.78', '-94.13', '-2.59%', '3533.78', '3641.59', '269983264', '36904280', '-'], 
    ['2021/12/25', '3614.05', '3627.91', '15.43', '0.43%', '3601.74', '3635.26', '198451120', '27466004', '-'], 
    ['2021/12/24', '3631.31', '3612.49', '-23.6', '-0.65%', '3572.28', '3640.22', '227785216', '31542126', '-'], 
    ['2021/12/23', '3653.28', '3636.09', '-15.68', '-0.43%', '3633.03', '3684.57', '298201792', '41990292', '-'], 
    ['2021/12/22', '3645.99', '3651.77', '9.3', '0.26%', '3616.87', '3652.63', '261178752', '36084604', '-'], 
    ['2021/12/21', '3568.58', '3642.47', '63.51', '1.77%', '3565.75', '3651.06', '299849280', '39831696', '-'], 
    ['2021/12/18', '3574.94', '3578.96', '-1.03', '-0.03%', '3568.16', '3614.7', '273707904', '36538580', '-'], 
    ['2021/12/17', '3533.63', '3580', '63.81', '1.81%', '3533.63', '3583.41', '283856480', '38143960', '-'], 
    ['2021/12/16', '3522.09', '3516.19', '5.83', '0.17%', '3506.29', '3538.69', '193482304', '26528864', '-'], 
    ['2021/12/15', '3518.13', '3510.35', '-10.31', '-0.29%', '3496.85', '3529.96', '200471344', '27627494', '-'], 
    ['2021/12/14', '3403.51', '3520.67', '86.09', '2.51%', '3399.28', '3521.78', '215374624', '27921354', '-'], 
    ['2021/12/11', '3441.6', '3434.58', '-20.91', '-0.61%', '3410.92', '3455.55', '182908880', '24507642', '-'], 
    ['2021/12/10', '3469.81', '3455.5', '-16.94', '-0.49%', '3446.27', '3503.65', '200427520', '27949970', '-'], 
    ['2021/12/9', '3462.58', '3472.44', '2.37', '0.07%', '3454.88', '3495.7', '195698848', '26785488', '-'], 
    ['2021/12/8', '3518.65', '3470.07', '-66.86', '-1.89%', '3466.79', '3518.65', '224367312', '29782174', '-'], 
    ['2021/12/7', '3529.81', '3536.93', '11.94', '0.34%', '3506.62', '3543.95', '208302576', '28056158', '-'], 
    ['2021/12/4', '3558.15', '3524.99', '-59.83', '-1.67%', '3510.41', '3568.97', '251736416', '31976682', '-'], 
    ['2021/12/3', '3525.73', '3584.82', '47.92', '1.35%', '3517.23', '3591.73', '281111232', '33885908', '-'], 
    ['2021/12/2', '3450.28', '3536.91', '80.6', '2.33%', '3427.66', '3538.85', '301491488', '36918304', '-'], 
    ['2021/12/1', '3442.44', '3456.31', '10.9', '0.32%', '3417.54', '3483.41', '252390752', '33025674', '-'], 
    ]

    #user_list = models.Userinfo.objects.all()
    #ret = serializers.serialize('json', user_list)
    datas = {'t1': data, 'data': rawData}
    return JsonResponse(datas, safe=False)

def netExquick9(request):
    # 接參數
    data = request.POST.get('v1')
    
    #資料庫讀出的資料(此地為直接帶入)
    
    year = "2011"
    keywordsAmount = "30"
    
    df_nodes = SnaStudieskeywordsNodes.objects.raw(f"SELECT id, keyword, keywordsAmount AS 'value' FROM `sna_studieskeywords_nodes` WHERE year = '{year}' ORDER BY keywordsAmount DESC Limit {int(keywordsAmount)}")
    nodes_top = "','".join([ff.keyword for ff in df_nodes])
    df_links = SnaStudieskeywordsLinks.objects.raw(f"SELECT id, source, target, value FROM `sna_studieskeywords_links` WHERE year = '{year}' AND source IN ('{nodes_top}') AND target IN ('{nodes_top}')")
    
    rawData = []
    n = 0
    for row in df_nodes:
        rawData.append({'from':row.keyword, 'rank':n, 'count':row.value})
        n += 1    
    for row in df_links:
        rawData.append({'from':row.source, 'to':row.target, 'value':row.value})
        rawData.append({'from':row.target, 'to':row.source, 'value':row.value})
#    print("/n資料:",rawData[0],"\n")
#    rawData = [
#            {'from':'深度學習', 'rank':0, 'count':759},
#            {'from':'機器學習', 'rank':1, 'count':370},
#            {'from':'物聯網', 'rank':2, 'count':300},
#            {'from':'卷積神經網路', 'rank':3, 'count':289},
#            {'from':'類神經網路', 'rank':4, 'count':167},
#            {'from':'有限元素分析', 'rank':5, 'count':106},
#            {'from':'區塊鏈', 'rank':6, 'count':105},
#            {'from':'影像處理', 'rank':7, 'count':102},
#            {'from':'基因演算法', 'rank':8, 'count':98},
#            {'from':'石墨烯', 'rank':9, 'count':95},
#            {'from':'人工智慧', 'rank':10, 'count':92},
#            {'from':'層級分析法', 'rank':11, 'count':88},
#            {'from':'虛擬實境', 'rank':12, 'count':85},
#            {'from':'有限元素法', 'rank':13, 'count':81},
#            {'from':'二氧化鈦', 'rank':14, 'count':77},
#            {'from':'氧化鋅', 'rank':15, 'count':76},
#            {'from':'軟體定義網路', 'rank':16, 'count':74},
#            {'from':'服務品質', 'rank':17, 'count':72},
#            {'from':'資料探勘', 'rank':18, 'count':72},
#            {'from':'氮化鎵', 'rank':19, 'count':69},
#            {'from':'工業4.0', 'rank':20, 'count':68},
#            {'from':'擴增實境', 'rank':21, 'count':66},
#            {'from':'毫米波', 'rank':22, 'count':65},
#            {'from':'最佳化', 'rank':23, 'count':65},
#            {'from':'影像辨識', 'rank':24, 'count':61},
#            {'from':'神經網路', 'rank':25, 'count':60},
#            {'from':'強化學習', 'rank':26, 'count':60},
#            {'from':'田口方法', 'rank':27, 'count':59},
#            {'from':'生成對抗網路', 'rank':28, 'count':59},
#            {'from':'機械性質', 'rank':29, 'count':58},
#            {'from':'鋰離子電池', 'rank':30, 'count':58},
#            {'from':'支持向量機', 'rank':31, 'count':57},
#            {'from':'計算流體力學', 'rank':32, 'count':56},
#            {'from':'自然語言處理', 'rank':33, 'count':56},
#            {'from':'3D列印', 'rank':34, 'count':55},
#            {'from':'發光二極體', 'rank':35, 'count':54},
#            {'from':'感測器', 'rank':36, 'count':53},
#            {'from':'決策樹', 'rank':37, 'count':52},
#            {'from':'機械手臂', 'rank':38, 'count':52},
#            {'from':'無人機', 'rank':39, 'count':49},
#            {'from':'太陽能電池', 'rank':40, 'count':47},
#            {'from':'奈米碳管', 'rank':41, 'count':45},
#            {'from':'學習成效', 'rank':42, 'count':45},
#            {'from':'可靠度', 'rank':43, 'count':45},
#            {'from':'大數據', 'rank':44, 'count':45},
#            {'from':'靜電紡絲', 'rank':45, 'count':44},
#            {'from':'氧化石墨烯', 'rank':46, 'count':44},
#            {'from':'嵌入式系統', 'rank':47, 'count':44},
#            {'from':'物件偵測', 'rank':48, 'count':42},
#            {'from':'薄膜', 'rank':49, 'count':42},
#            {'from':'卷積神經網路', 'to':'深度學習', 'value':127},
#            {'from':'深度學習', 'to':'卷積神經網路', 'value':127},
#            {'from':'機器學習', 'to':'深度學習', 'value':65},
#            {'from':'深度學習', 'to':'機器學習', 'value':65},
#            {'from':'深度學習', 'to':'類神經網路', 'value':33},
#            {'from':'類神經網路', 'to':'深度學習', 'value':33},
#            {'from':'人工智慧', 'to':'深度學習', 'value':30},
#            {'from':'深度學習', 'to':'人工智慧', 'value':30},
#            {'from':'深度學習', 'to':'生成對抗網路', 'value':25},
#            {'from':'生成對抗網路', 'to':'深度學習', 'value':25},
#            {'from':'影像處理', 'to':'深度學習', 'value':24},
#            {'from':'深度學習', 'to':'影像處理', 'value':24},
#            {'from':'影像辨識', 'to':'深度學習', 'value':23},
#            {'from':'深度學習', 'to':'影像辨識', 'value':23},
#            {'from':'深度學習', 'to':'神經網路', 'value':22},
#            {'from':'神經網路', 'to':'深度學習', 'value':22},
#            {'from':'卷積神經網路', 'to':'機器學習', 'value':21},
#            {'from':'機器學習', 'to':'卷積神經網路', 'value':21},
#            {'from':'人工智慧', 'to':'機器學習', 'value':20},
#            {'from':'機器學習', 'to':'人工智慧', 'value':20},
#            {'from':'深度學習', 'to':'物件偵測', 'value':18},
#            {'from':'物件偵測', 'to':'深度學習', 'value':18},
#            {'from':'機器學習', 'to':'物聯網', 'value':17},
#            {'from':'物聯網', 'to':'機器學習', 'value':17},
#            {'from':'決策樹', 'to':'資料探勘', 'value':16},
#            {'from':'資料探勘', 'to':'決策樹', 'value':16},
#            {'from':'工業4.0', 'to':'物聯網', 'value':15},
#            {'from':'物聯網', 'to':'工業4.0', 'value':15},
#            {'from':'深度學習', 'to':'自然語言處理', 'value':15},
#            {'from':'自然語言處理', 'to':'深度學習', 'value':15},
#            {'from':'機器學習', 'to':'決策樹', 'value':11},
#            {'from':'決策樹', 'to':'機器學習', 'value':11},
#            {'from':'機器學習', 'to':'類神經網路', 'value':11},
#            {'from':'類神經網路', 'to':'機器學習', 'value':11},
#            {'from':'卷積神經網路', 'to':'影像辨識', 'value':11},
#            {'from':'影像辨識', 'to':'卷積神經網路', 'value':11},
#            {'from':'深度學習', 'to':'物聯網', 'value':11},
#            {'from':'物聯網', 'to':'深度學習', 'value':11},
#            {'from':'機器學習', 'to':'自然語言處理', 'value':11},
#            {'from':'自然語言處理', 'to':'機器學習', 'value':11},
#            {'from':'卷積神經網路', 'to':'影像處理', 'value':11},
#            {'from':'影像處理', 'to':'卷積神經網路', 'value':11},
#            {'from':'強化學習', 'to':'深度學習', 'value':11},
#            {'from':'深度學習', 'to':'強化學習', 'value':11},
#            {'from':'影像處理', 'to':'機器學習', 'value':10},
#            {'from':'機器學習', 'to':'影像處理', 'value':10},
#            {'from':'人工智慧', 'to':'卷積神經網路', 'value':9},
#            {'from':'卷積神經網路', 'to':'人工智慧', 'value':9},
#            {'from':'人工智慧', 'to':'類神經網路', 'value':9},
#            {'from':'類神經網路', 'to':'人工智慧', 'value':9},
#            {'from':'嵌入式系統', 'to':'物聯網', 'value':9},
#            {'from':'物聯網', 'to':'嵌入式系統', 'value':9},
#            {'from':'支持向量機', 'to':'機器學習', 'value':9},
#            {'from':'機器學習', 'to':'支持向量機', 'value':9},
#            {'from':'基因演算法', 'to':'類神經網路', 'value':8},
#            {'from':'類神經網路', 'to':'基因演算法', 'value':8},
#            {'from':'人工智慧', 'to':'物聯網', 'value':8},
#            {'from':'物聯網', 'to':'人工智慧', 'value':8},
#            {'from':'機器學習', 'to':'資料探勘', 'value':8},
#            {'from':'資料探勘', 'to':'機器學習', 'value':8},
#            {'from':'機器學習', 'to':'神經網路', 'value':8},
#            {'from':'神經網路', 'to':'機器學習', 'value':8},
#            {'from':'感測器', 'to':'物聯網', 'value':7},
#            {'from':'物聯網', 'to':'感測器', 'value':7},
#            {'from':'卷積神經網路', 'to':'生成對抗網路', 'value':7},
#            {'from':'生成對抗網路', 'to':'卷積神經網路', 'value':7},
#            {'from':'機械手臂', 'to':'深度學習', 'value':7},
#            {'from':'深度學習', 'to':'機械手臂', 'value':7},
#            {'from':'卷積神經網路', 'to':'支持向量機', 'value':6},
#            {'from':'支持向量機', 'to':'卷積神經網路', 'value':6},
#            {'from':'奈米碳管', 'to':'石墨烯', 'value':6},
#            {'from':'石墨烯', 'to':'奈米碳管', 'value':6},
#            {'from':'卷積神經網路', 'to':'類神經網路', 'value':6},
#            {'from':'類神經網路', 'to':'卷積神經網路', 'value':6},
#            {'from':'強化學習', 'to':'機器學習', 'value':6},
#            {'from':'機器學習', 'to':'強化學習', 'value':6},
#            {'from':'區塊鏈', 'to':'物聯網', 'value':6},
#            {'from':'物聯網', 'to':'區塊鏈', 'value':6},
#            {'from':'物聯網', 'to':'軟體定義網路', 'value':6},
#            {'from':'軟體定義網路', 'to':'物聯網', 'value':6},
#            {'from':'卷積神經網路', 'to':'物件偵測', 'value':6},
#            {'from':'物件偵測', 'to':'卷積神經網路', 'value':6},
#            {'from':'影像辨識', 'to':'機器學習', 'value':6},
#            {'from':'機器學習', 'to':'影像辨識', 'value':6},
#            {'from':'卷積神經網路', 'to':'自然語言處理', 'value':6},
#            {'from':'自然語言處理', 'to':'卷積神經網路', 'value':6},
#            {'from':'大數據', 'to':'物聯網', 'value':6},
#            {'from':'物聯網', 'to':'大數據', 'value':6},
#            {'from':'二氧化鈦', 'to':'氧化鋅', 'value':5},
#            {'from':'氧化鋅', 'to':'二氧化鈦', 'value':5},
#            {'from':'機器學習', 'to':'軟體定義網路', 'value':5},
#            {'from':'軟體定義網路', 'to':'機器學習', 'value':5},
#            {'from':'生成對抗網路', 'to':'類神經網路', 'value':5},
#            {'from':'類神經網路', 'to':'生成對抗網路', 'value':5},
#            {'from':'氮化鎵', 'to':'發光二極體', 'value':5},
#            {'from':'發光二極體', 'to':'氮化鎵', 'value':5},
#            {'from':'工業4.0', 'to':'機器學習', 'value':5},
#            {'from':'機器學習', 'to':'工業4.0', 'value':5},
#            {'from':'田口方法', 'to':'類神經網路', 'value':5},
#            {'from':'類神經網路', 'to':'田口方法', 'value':5},
#            {'from':'影像處理', 'to':'機械手臂', 'value':5},
#            {'from':'機械手臂', 'to':'影像處理', 'value':5},
#            {'from':'擴增實境', 'to':'虛擬實境', 'value':5},
#            {'from':'虛擬實境', 'to':'擴增實境', 'value':5},
#            {'from':'支持向量機', 'to':'決策樹', 'value':4},
#            {'from':'決策樹', 'to':'支持向量機', 'value':4},
#            {'from':'嵌入式系統', 'to':'深度學習', 'value':4},
#            {'from':'深度學習', 'to':'嵌入式系統', 'value':4},
#            {'from':'工業4.0', 'to':'擴增實境', 'value':4},
#            {'from':'擴增實境', 'to':'工業4.0', 'value':4},
#            {'from':'大數據', 'to':'機器學習', 'value':4},
#            {'from':'機器學習', 'to':'大數據', 'value':4},
#            {'from':'基因演算法', 'to':'最佳化', 'value':4},
#            {'from':'最佳化', 'to':'基因演算法', 'value':4},
#            {'from':'人工智慧', 'to':'影像辨識', 'value':4},
#            {'from':'影像辨識', 'to':'人工智慧', 'value':4},
#            {'from':'有限元素法', 'to':'田口方法', 'value':4},
#            {'from':'田口方法', 'to':'有限元素法', 'value':4},
#            {'from':'嵌入式系統', 'to':'影像辨識', 'value':4},
#            {'from':'影像辨識', 'to':'嵌入式系統', 'value':4},
#            {'from':'石墨烯', 'to':'鋰離子電池', 'value':4},
#            {'from':'鋰離子電池', 'to':'石墨烯', 'value':4},
#            {'from':'大數據', 'to':'深度學習', 'value':4},
#            {'from':'深度學習', 'to':'大數據', 'value':4},
#            {'from':'卷積神經網路', 'to':'神經網路', 'value':4},
#            {'from':'神經網路', 'to':'卷積神經網路', 'value':4},
#            {'from':'基因演算法', 'to':'田口方法', 'value':4},
#            {'from':'田口方法', 'to':'基因演算法', 'value':4},
#            {'from':'毫米波', 'to':'深度學習', 'value':4},
#            {'from':'深度學習', 'to':'毫米波', 'value':4},
#            {'from':'卷積神經網路', 'to':'工業4.0', 'value':3},
#            {'from':'工業4.0', 'to':'卷積神經網路', 'value':3},
#            {'from':'二氧化鈦', 'to':'薄膜', 'value':3},
#            {'from':'薄膜', 'to':'二氧化鈦', 'value':3},
#            {'from':'有限元素分析', 'to':'田口方法', 'value':3},
#            {'from':'田口方法', 'to':'有限元素分析', 'value':3},
#            {'from':'太陽能電池', 'to':'氧化鋅', 'value':3},
#            {'from':'氧化鋅', 'to':'太陽能電池', 'value':3},
#            {'from':'深度學習', 'to':'無人機', 'value':3},
#            {'from':'無人機', 'to':'深度學習', 'value':3},
#            {'from':'基因演算法', 'to':'機器學習', 'value':3},
#            {'from':'機器學習', 'to':'基因演算法', 'value':3},
#            {'from':'奈米碳管', 'to':'感測器', 'value':3},
#            {'from':'感測器', 'to':'奈米碳管', 'value':3},
#            {'from':'影像處理', 'to':'類神經網路', 'value':3},
#            {'from':'類神經網路', 'to':'影像處理', 'value':3},
#            {'from':'深度學習', 'to':'資料探勘', 'value':3},
#            {'from':'資料探勘', 'to':'深度學習', 'value':3},
#            {'from':'人工智慧', 'to':'神經網路', 'value':3},
#            {'from':'神經網路', 'to':'人工智慧', 'value':3},
#            {'from':'擴增實境', 'to':'深度學習', 'value':3},
#            {'from':'深度學習', 'to':'擴增實境', 'value':3},
#            {'from':'學習成效', 'to':'擴增實境', 'value':3},
#            {'from':'擴增實境', 'to':'學習成效', 'value':3},
#            {'from':'決策樹', 'to':'類神經網路', 'value':3},
#            {'from':'類神經網路', 'to':'決策樹', 'value':3},
#            {'from':'工業4.0', 'to':'深度學習', 'value':3},
#            {'from':'深度學習', 'to':'工業4.0', 'value':3},
#            {'from':'資料探勘', 'to':'類神經網路', 'value':3},
#            {'from':'類神經網路', 'to':'資料探勘', 'value':3},
#            {'from':'3D列印', 'to':'有限元素分析', 'value':3},
#            {'from':'有限元素分析', 'to':'3D列印', 'value':3},
#            {'from':'支持向量機', 'to':'深度學習', 'value':3},
#            {'from':'深度學習', 'to':'支持向量機', 'value':3},
#            {'from':'人工智慧', 'to':'虛擬實境', 'value':3},
#            {'from':'虛擬實境', 'to':'人工智慧', 'value':3},
#            {'from':'深度學習', 'to':'虛擬實境', 'value':3},
#            {'from':'虛擬實境', 'to':'深度學習', 'value':3},
#            {'from':'二氧化鈦', 'to':'石墨烯', 'value':3},
#            {'from':'石墨烯', 'to':'二氧化鈦', 'value':3},
#            {'from':'擴增實境', 'to':'物聯網', 'value':3},
#            {'from':'物聯網', 'to':'擴增實境', 'value':3},
#            {'from':'大數據', 'to':'工業4.0', 'value':3},
#            {'from':'工業4.0', 'to':'大數據', 'value':3},
#            {'from':'卷積神經網路', 'to':'物聯網', 'value':3},
#            {'from':'物聯網', 'to':'卷積神經網路', 'value':3},
#            {'from':'二氧化鈦', 'to':'靜電紡絲', 'value':3},
#            {'from':'靜電紡絲', 'to':'二氧化鈦', 'value':3},
#            {'from':'影像處理', 'to':'物件偵測', 'value':2},
#            {'from':'物件偵測', 'to':'影像處理', 'value':2},
#            {'from':'強化學習', 'to':'自然語言處理', 'value':2},
#            {'from':'自然語言處理', 'to':'強化學習', 'value':2},
#            {'from':'最佳化', 'to':'物聯網', 'value':2},
#            {'from':'物聯網', 'to':'最佳化', 'value':2},
#            {'from':'可靠度', 'to':'氮化鎵', 'value':2},
#            {'from':'氮化鎵', 'to':'可靠度', 'value':2},
#            {'from':'最佳化', 'to':'軟體定義網路', 'value':2},
#            {'from':'軟體定義網路', 'to':'最佳化', 'value':2},
#            {'from':'氧化石墨烯', 'to':'靜電紡絲', 'value':2},
#            {'from':'靜電紡絲', 'to':'氧化石墨烯', 'value':2},
#            {'from':'卷積神經網路', 'to':'機械手臂', 'value':2},
#            {'from':'機械手臂', 'to':'卷積神經網路', 'value':2},
#            {'from':'人工智慧', 'to':'大數據', 'value':2},
#            {'from':'大數據', 'to':'人工智慧', 'value':2},
#            {'from':'最佳化', 'to':'機械手臂', 'value':2},
#            {'from':'機械手臂', 'to':'最佳化', 'value':2},
#            {'from':'影像辨識', 'to':'無人機', 'value':2},
#            {'from':'無人機', 'to':'影像辨識', 'value':2},
#            {'from':'機械性質', 'to':'氧化石墨烯', 'value':2},
#            {'from':'氧化石墨烯', 'to':'機械性質', 'value':2},
#            {'from':'機器學習', 'to':'物件偵測', 'value':2},
#            {'from':'物件偵測', 'to':'機器學習', 'value':2},
#            {'from':'影像辨識', 'to':'神經網路', 'value':2},
#            {'from':'神經網路', 'to':'影像辨識', 'value':2},
#            {'from':'深度學習', 'to':'軟體定義網路', 'value':2},
#            {'from':'軟體定義網路', 'to':'深度學習', 'value':2},
#            {'from':'機械手臂', 'to':'物聯網', 'value':2},
#            {'from':'物聯網', 'to':'機械手臂', 'value':2},
#            {'from':'區塊鏈', 'to':'層級分析法', 'value':2},
#            {'from':'層級分析法', 'to':'區塊鏈', 'value':2},
#            {'from':'人工智慧', 'to':'工業4.0', 'value':2},
#            {'from':'工業4.0', 'to':'人工智慧', 'value':2},
#            {'from':'支持向量機', 'to':'類神經網路', 'value':2},
#            {'from':'類神經網路', 'to':'支持向量機', 'value':2},
#            {'from':'奈米碳管', 'to':'氧化石墨烯', 'value':2},
#            {'from':'氧化石墨烯', 'to':'奈米碳管', 'value':2},
#            {'from':'影像辨識', 'to':'機械手臂', 'value':2},
#            {'from':'機械手臂', 'to':'影像辨識', 'value':2},
#            {'from':'決策樹', 'to':'深度學習', 'value':2},
#            {'from':'深度學習', 'to':'決策樹', 'value':2},
#            {'from':'氮化鎵', 'to':'薄膜', 'value':2},
#            {'from':'薄膜', 'to':'氮化鎵', 'value':2},
#            {'from':'服務品質', 'to':'深度學習', 'value':2},
#            {'from':'深度學習', 'to':'服務品質', 'value':2},
#            {'from':'基因演算法', 'to':'支持向量機', 'value':2},
#            {'from':'支持向量機', 'to':'基因演算法', 'value':2},
#            {'from':'最佳化', 'to':'有限元素分析', 'value':2},
#            {'from':'有限元素分析', 'to':'最佳化', 'value':2},
#            {'from':'氧化鋅', 'to':'石墨烯', 'value':2},
#            {'from':'石墨烯', 'to':'氧化鋅', 'value':2},
#            {'from':'有限元素法', 'to':'石墨烯', 'value':2},
#            {'from':'石墨烯', 'to':'有限元素法', 'value':2},
#            {'from':'無人機', 'to':'物聯網', 'value':2},
#            {'from':'物聯網', 'to':'無人機', 'value':2},
#            {'from':'工業4.0', 'to':'感測器', 'value':2},
#            {'from':'感測器', 'to':'工業4.0', 'value':2},
#            {'from':'卷積神經網路', 'to':'資料探勘', 'value':2},
#            {'from':'資料探勘', 'to':'卷積神經網路', 'value':2},
#            {'from':'服務品質', 'to':'軟體定義網路', 'value':2},
#            {'from':'軟體定義網路', 'to':'服務品質', 'value':2},
#            {'from':'可靠度', 'to':'軟體定義網路', 'value':2},
#            {'from':'軟體定義網路', 'to':'可靠度', 'value':2},
#            {'from':'毫米波', 'to':'神經網路', 'value':2},
#            {'from':'神經網路', 'to':'毫米波', 'value':2},
#            {'from':'奈米碳管', 'to':'鋰離子電池', 'value':2},
#            {'from':'鋰離子電池', 'to':'奈米碳管', 'value':2},
#            {'from':'大數據', 'to':'決策樹', 'value':2},
#            {'from':'決策樹', 'to':'大數據', 'value':2},
#            {'from':'強化學習', 'to':'神經網路', 'value':2},
#            {'from':'神經網路', 'to':'強化學習', 'value':2},
#            {'from':'薄膜', 'to':'靜電紡絲', 'value':2},
#            {'from':'靜電紡絲', 'to':'薄膜', 'value':2},
#            {'from':'影像辨識', 'to':'物件偵測', 'value':2},
#            {'from':'物件偵測', 'to':'影像辨識', 'value':2},
#            {'from':'支持向量機', 'to':'資料探勘', 'value':2},
#            {'from':'資料探勘', 'to':'支持向量機', 'value':2},
#            {'from':'人工智慧', 'to':'自然語言處理', 'value':2},
#            {'from':'自然語言處理', 'to':'人工智慧', 'value':2},
#            {'from':'基因演算法', 'to':'軟體定義網路', 'value':2},
#            {'from':'軟體定義網路', 'to':'基因演算法', 'value':2},
#            {'from':'氧化鋅', 'to':'靜電紡絲', 'value':2},
#            {'from':'靜電紡絲', 'to':'氧化鋅', 'value':2},
#            {'from':'基因演算法', 'to':'神經網路', 'value':2},
#            {'from':'神經網路', 'to':'基因演算法', 'value':2},
#            {'from':'嵌入式系統', 'to':'物件偵測', 'value':1},
#            {'from':'物件偵測', 'to':'嵌入式系統', 'value':1},
#            {'from':'感測器', 'to':'有限元素分析', 'value':1},
#            {'from':'有限元素分析', 'to':'感測器', 'value':1},
#            {'from':'區塊鏈', 'to':'決策樹', 'value':1},
#            {'from':'決策樹', 'to':'區塊鏈', 'value':1},
#            {'from':'二氧化鈦', 'to':'奈米碳管', 'value':1},
#            {'from':'奈米碳管', 'to':'二氧化鈦', 'value':1},
#            {'from':'人工智慧', 'to':'田口方法', 'value':1},
#            {'from':'田口方法', 'to':'人工智慧', 'value':1},
#            {'from':'區塊鏈', 'to':'強化學習', 'value':1},
#            {'from':'強化學習', 'to':'區塊鏈', 'value':1},
#            {'from':'擴增實境', 'to':'物件偵測', 'value':1},
#            {'from':'物件偵測', 'to':'擴增實境', 'value':1},
#            {'from':'感測器', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'感測器', 'value':1},
#            {'from':'可靠度', 'to':'發光二極體', 'value':1},
#            {'from':'發光二極體', 'to':'可靠度', 'value':1},
#            {'from':'田口方法', 'to':'薄膜', 'value':1},
#            {'from':'薄膜', 'to':'田口方法', 'value':1},
#            {'from':'基因演算法', 'to':'服務品質', 'value':1},
#            {'from':'服務品質', 'to':'基因演算法', 'value':1},
#            {'from':'影像處理', 'to':'無人機', 'value':1},
#            {'from':'無人機', 'to':'影像處理', 'value':1},
#            {'from':'無人機', 'to':'鋰離子電池', 'value':1},
#            {'from':'鋰離子電池', 'to':'無人機', 'value':1},
#            {'from':'機器學習', 'to':'鋰離子電池', 'value':1},
#            {'from':'鋰離子電池', 'to':'機器學習', 'value':1},
#            {'from':'影像辨識', 'to':'虛擬實境', 'value':1},
#            {'from':'虛擬實境', 'to':'影像辨識', 'value':1},
#            {'from':'工業4.0', 'to':'影像處理', 'value':1},
#            {'from':'影像處理', 'to':'工業4.0', 'value':1},
#            {'from':'氧化鋅', 'to':'鋰離子電池', 'value':1},
#            {'from':'鋰離子電池', 'to':'氧化鋅', 'value':1},
#            {'from':'基因演算法', 'to':'資料探勘', 'value':1},
#            {'from':'資料探勘', 'to':'基因演算法', 'value':1},
#            {'from':'強化學習', 'to':'無人機', 'value':1},
#            {'from':'無人機', 'to':'強化學習', 'value':1},
#            {'from':'支持向量機', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'支持向量機', 'value':1},
#            {'from':'機械手臂', 'to':'田口方法', 'value':1},
#            {'from':'田口方法', 'to':'機械手臂', 'value':1},
#            {'from':'影像處理', 'to':'生成對抗網路', 'value':1},
#            {'from':'生成對抗網路', 'to':'影像處理', 'value':1},
#            {'from':'卷積神經網路', 'to':'軟體定義網路', 'value':1},
#            {'from':'軟體定義網路', 'to':'卷積神經網路', 'value':1},
#            {'from':'氧化鋅', 'to':'發光二極體', 'value':1},
#            {'from':'發光二極體', 'to':'氧化鋅', 'value':1},
#            {'from':'大數據', 'to':'資料探勘', 'value':1},
#            {'from':'資料探勘', 'to':'大數據', 'value':1},
#            {'from':'卷積神經網路', 'to':'田口方法', 'value':1},
#            {'from':'田口方法', 'to':'卷積神經網路', 'value':1},
#            {'from':'卷積神經網路', 'to':'決策樹', 'value':1},
#            {'from':'決策樹', 'to':'卷積神經網路', 'value':1},
#            {'from':'有限元素法', 'to':'機器學習', 'value':1},
#            {'from':'機器學習', 'to':'有限元素法', 'value':1},
#            {'from':'物聯網', 'to':'發光二極體', 'value':1},
#            {'from':'發光二極體', 'to':'物聯網', 'value':1},
#            {'from':'最佳化', 'to':'深度學習', 'value':1},
#            {'from':'深度學習', 'to':'最佳化', 'value':1},
#            {'from':'田口方法', 'to':'計算流體力學', 'value':1},
#            {'from':'計算流體力學', 'to':'田口方法', 'value':1},
#            {'from':'人工智慧', 'to':'物件偵測', 'value':1},
#            {'from':'物件偵測', 'to':'人工智慧', 'value':1},
#            {'from':'二氧化鈦', 'to':'田口方法', 'value':1},
#            {'from':'田口方法', 'to':'二氧化鈦', 'value':1},
#            {'from':'影像處理', 'to':'影像辨識', 'value':1},
#            {'from':'影像辨識', 'to':'影像處理', 'value':1},
#            {'from':'3D列印', 'to':'影像辨識', 'value':1},
#            {'from':'影像辨識', 'to':'3D列印', 'value':1},
#            {'from':'工業4.0', 'to':'生成對抗網路', 'value':1},
#            {'from':'生成對抗網路', 'to':'工業4.0', 'value':1},
#            {'from':'區塊鏈', 'to':'基因演算法', 'value':1},
#            {'from':'基因演算法', 'to':'區塊鏈', 'value':1},
#            {'from':'可靠度', 'to':'鋰離子電池', 'value':1},
#            {'from':'鋰離子電池', 'to':'可靠度', 'value':1},
#            {'from':'基因演算法', 'to':'物聯網', 'value':1},
#            {'from':'物聯網', 'to':'基因演算法', 'value':1},
#            {'from':'人工智慧', 'to':'基因演算法', 'value':1},
#            {'from':'基因演算法', 'to':'人工智慧', 'value':1},
#            {'from':'層級分析法', 'to':'服務品質', 'value':1},
#            {'from':'服務品質', 'to':'層級分析法', 'value':1},
#            {'from':'人工智慧', 'to':'支持向量機', 'value':1},
#            {'from':'支持向量機', 'to':'人工智慧', 'value':1},
#            {'from':'嵌入式系統', 'to':'無人機', 'value':1},
#            {'from':'無人機', 'to':'嵌入式系統', 'value':1},
#            {'from':'3D列印', 'to':'學習成效', 'value':1},
#            {'from':'學習成效', 'to':'3D列印', 'value':1},
#            {'from':'卷積神經網路', 'to':'無人機', 'value':1},
#            {'from':'無人機', 'to':'卷積神經網路', 'value':1},
#            {'from':'機械性質', 'to':'薄膜', 'value':1},
#            {'from':'薄膜', 'to':'機械性質', 'value':1},
#            {'from':'氧化石墨烯', 'to':'石墨烯', 'value':1},
#            {'from':'石墨烯', 'to':'氧化石墨烯', 'value':1},
#            {'from':'可靠度', 'to':'機器學習', 'value':1},
#            {'from':'機器學習', 'to':'可靠度', 'value':1},
#            {'from':'基因演算法', 'to':'深度學習', 'value':1},
#            {'from':'深度學習', 'to':'基因演算法', 'value':1},
#            {'from':'物聯網', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'物聯網', 'value':1},
#            {'from':'服務品質', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'服務品質', 'value':1},
#            {'from':'毫米波', 'to':'軟體定義網路', 'value':1},
#            {'from':'軟體定義網路', 'to':'毫米波', 'value':1},
#            {'from':'物件偵測', 'to':'生成對抗網路', 'value':1},
#            {'from':'生成對抗網路', 'to':'物件偵測', 'value':1},
#            {'from':'生成對抗網路', 'to':'自然語言處理', 'value':1},
#            {'from':'自然語言處理', 'to':'生成對抗網路', 'value':1},
#            {'from':'影像辨識', 'to':'擴增實境', 'value':1},
#            {'from':'擴增實境', 'to':'影像辨識', 'value':1},
#            {'from':'基因演算法', 'to':'大數據', 'value':1},
#            {'from':'大數據', 'to':'基因演算法', 'value':1},
#            {'from':'機器學習', 'to':'無人機', 'value':1},
#            {'from':'無人機', 'to':'機器學習', 'value':1},
#            {'from':'強化學習', 'to':'影像處理', 'value':1},
#            {'from':'影像處理', 'to':'強化學習', 'value':1},
#            {'from':'發光二極體', 'to':'薄膜', 'value':1},
#            {'from':'薄膜', 'to':'發光二極體', 'value':1},
#            {'from':'基因演算法', 'to':'太陽能電池', 'value':1},
#            {'from':'太陽能電池', 'to':'基因演算法', 'value':1},
#            {'from':'機械手臂', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'機械手臂', 'value':1},
#            {'from':'二氧化鈦', 'to':'鋰離子電池', 'value':1},
#            {'from':'鋰離子電池', 'to':'二氧化鈦', 'value':1},
#            {'from':'影像處理', 'to':'有限元素分析', 'value':1},
#            {'from':'有限元素分析', 'to':'影像處理', 'value':1},
#            {'from':'大數據', 'to':'服務品質', 'value':1},
#            {'from':'服務品質', 'to':'大數據', 'value':1},
#            {'from':'毫米波', 'to':'物聯網', 'value':1},
#            {'from':'物聯網', 'to':'毫米波', 'value':1},
#            {'from':'太陽能電池', 'to':'發光二極體', 'value':1},
#            {'from':'發光二極體', 'to':'太陽能電池', 'value':1},
#            {'from':'太陽能電池', 'to':'薄膜', 'value':1},
#            {'from':'薄膜', 'to':'太陽能電池', 'value':1},
#            {'from':'感測器', 'to':'機器學習', 'value':1},
#            {'from':'機器學習', 'to':'感測器', 'value':1},
#            {'from':'基因演算法', 'to':'工業4.0', 'value':1},
#            {'from':'工業4.0', 'to':'基因演算法', 'value':1},
#            {'from':'大數據', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'大數據', 'value':1},
#            {'from':'學習成效', 'to':'虛擬實境', 'value':1},
#            {'from':'虛擬實境', 'to':'學習成效', 'value':1},
#            {'from':'毫米波', 'to':'無人機', 'value':1},
#            {'from':'無人機', 'to':'毫米波', 'value':1},
#            {'from':'可靠度', 'to':'支持向量機', 'value':1},
#            {'from':'支持向量機', 'to':'可靠度', 'value':1},
#            {'from':'嵌入式系統', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'嵌入式系統', 'value':1},
#            {'from':'人工智慧', 'to':'影像處理', 'value':1},
#            {'from':'影像處理', 'to':'人工智慧', 'value':1},
#            {'from':'人工智慧', 'to':'機械手臂', 'value':1},
#            {'from':'機械手臂', 'to':'人工智慧', 'value':1},
#            {'from':'無人機', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'無人機', 'value':1},
#            {'from':'軟體定義網路', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'軟體定義網路', 'value':1},
#            {'from':'奈米碳管', 'to':'薄膜', 'value':1},
#            {'from':'薄膜', 'to':'奈米碳管', 'value':1},
#            {'from':'學習成效', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'學習成效', 'value':1},
#            {'from':'人工智慧', 'to':'決策樹', 'value':1},
#            {'from':'決策樹', 'to':'人工智慧', 'value':1},
#            {'from':'有限元素法', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'有限元素法', 'value':1},
#            {'from':'太陽能電池', 'to':'物聯網', 'value':1},
#            {'from':'物聯網', 'to':'太陽能電池', 'value':1},
#            {'from':'氮化鎵', 'to':'石墨烯', 'value':1},
#            {'from':'石墨烯', 'to':'氮化鎵', 'value':1},
#            {'from':'3D列印', 'to':'二氧化鈦', 'value':1},
#            {'from':'二氧化鈦', 'to':'3D列印', 'value':1},
#            {'from':'基因演算法', 'to':'決策樹', 'value':1},
#            {'from':'決策樹', 'to':'基因演算法', 'value':1},
#            {'from':'強化學習', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'強化學習', 'value':1},
#            {'from':'可靠度', 'to':'影像處理', 'value':1},
#            {'from':'影像處理', 'to':'可靠度', 'value':1},
#            {'from':'最佳化', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'最佳化', 'value':1},
#            {'from':'二氧化鈦', 'to':'氧化石墨烯', 'value':1},
#            {'from':'氧化石墨烯', 'to':'二氧化鈦', 'value':1},
#            {'from':'區塊鏈', 'to':'深度學習', 'value':1},
#            {'from':'深度學習', 'to':'區塊鏈', 'value':1},
#            {'from':'擴增實境', 'to':'生成對抗網路', 'value':1},
#            {'from':'生成對抗網路', 'to':'擴增實境', 'value':1},
#            {'from':'物聯網', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'物聯網', 'value':1},
#            {'from':'石墨烯', 'to':'靜電紡絲', 'value':1},
#            {'from':'靜電紡絲', 'to':'石墨烯', 'value':1},
#            {'from':'人工智慧', 'to':'強化學習', 'value':1},
#            {'from':'強化學習', 'to':'人工智慧', 'value':1},
#            {'from':'支持向量機', 'to':'物件偵測', 'value':1},
#            {'from':'物件偵測', 'to':'支持向量機', 'value':1},
#            {'from':'基因演算法', 'to':'有限元素分析', 'value':1},
#            {'from':'有限元素分析', 'to':'基因演算法', 'value':1},
#            {'from':'人工智慧', 'to':'有限元素分析', 'value':1},
#            {'from':'有限元素分析', 'to':'人工智慧', 'value':1},
#            {'from':'物聯網', 'to':'虛擬實境', 'value':1},
#            {'from':'虛擬實境', 'to':'物聯網', 'value':1},
#            {'from':'最佳化', 'to':'服務品質', 'value':1},
#            {'from':'服務品質', 'to':'最佳化', 'value':1},
#            {'from':'可靠度', 'to':'石墨烯', 'value':1},
#            {'from':'石墨烯', 'to':'可靠度', 'value':1},
#            {'from':'發光二極體', 'to':'石墨烯', 'value':1},
#            {'from':'石墨烯', 'to':'發光二極體', 'value':1},
#            {'from':'薄膜', 'to':'計算流體力學', 'value':1},
#            {'from':'計算流體力學', 'to':'薄膜', 'value':1},
#            {'from':'神經網路', 'to':'自然語言處理', 'value':1},
#            {'from':'自然語言處理', 'to':'神經網路', 'value':1},
#            {'from':'物件偵測', 'to':'類神經網路', 'value':1},
#            {'from':'類神經網路', 'to':'物件偵測', 'value':1},
#            {'from':'氧化石墨烯', 'to':'氧化鋅', 'value':1},
#            {'from':'氧化鋅', 'to':'氧化石墨烯', 'value':1},
#            {'from':'生成對抗網路', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'生成對抗網路', 'value':1},
#            {'from':'人工智慧', 'to':'資料探勘', 'value':1},
#            {'from':'資料探勘', 'to':'人工智慧', 'value':1},
#            {'from':'決策樹', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'決策樹', 'value':1},
#            {'from':'可靠度', 'to':'基因演算法', 'value':1},
#            {'from':'基因演算法', 'to':'可靠度', 'value':1},
#            {'from':'深度學習', 'to':'田口方法', 'value':1},
#            {'from':'田口方法', 'to':'深度學習', 'value':1},
#            {'from':'嵌入式系統', 'to':'機械手臂', 'value':1},
#            {'from':'機械手臂', 'to':'嵌入式系統', 'value':1},
#            {'from':'層級分析法', 'to':'田口方法', 'value':1},
#            {'from':'田口方法', 'to':'層級分析法', 'value':1},
#            {'from':'自然語言處理', 'to':'資料探勘', 'value':1},
#            {'from':'資料探勘', 'to':'自然語言處理', 'value':1},
#            {'from':'物聯網', 'to':'資料探勘', 'value':1},
#            {'from':'資料探勘', 'to':'物聯網', 'value':1},
#            {'from':'人工智慧', 'to':'軟體定義網路', 'value':1},
#            {'from':'軟體定義網路', 'to':'人工智慧', 'value':1},
#            {'from':'工業4.0', 'to':'最佳化', 'value':1},
#            {'from':'最佳化', 'to':'工業4.0', 'value':1},
#            {'from':'可靠度', 'to':'有限元素法', 'value':1},
#            {'from':'有限元素法', 'to':'可靠度', 'value':1},
#            {'from':'感測器', 'to':'靜電紡絲', 'value':1},
#            {'from':'靜電紡絲', 'to':'感測器', 'value':1},
#            {'from':'毫米波', 'to':'生成對抗網路', 'value':1},
#            {'from':'生成對抗網路', 'to':'毫米波', 'value':1},
#            {'from':'機械手臂', 'to':'神經網路', 'value':1},
#            {'from':'神經網路', 'to':'機械手臂', 'value':1},
#            {'from':'強化學習', 'to':'生成對抗網路', 'value':1},
#            {'from':'生成對抗網路', 'to':'強化學習', 'value':1},
#            {'from':'機器學習', 'to':'虛擬實境', 'value':1},
#            {'from':'虛擬實境', 'to':'機器學習', 'value':1},
#            {'from':'感測器', 'to':'氧化石墨烯', 'value':1},
#            {'from':'氧化石墨烯', 'to':'感測器', 'value':1},
#            {'from':'強化學習', 'to':'機械手臂', 'value':1},
#            {'from':'機械手臂', 'to':'強化學習', 'value':1}
#        ]

    dataJSON = dumps(rawData)
    return render(request,'netx/charts.html',{"data":dataJSON})

