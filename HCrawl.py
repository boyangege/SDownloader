# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib
import sys
import os
import threading as td
import time

DOMAIN = "http://www.ppp179.com/"
PAGE_KEY_WORD = "丝袜"
MAX_THREAD_COUNT = 128

def getHtml(url, timeout = 10):
    global DOMAIN
    try:
        if("http" not in url):
            url = DOMAIN + url
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        req = urllib.request.Request(url, headers = headers)
        response = urllib.request.urlopen(req, timeout = timeout)
        html = response.read().decode('utf-8')
        return html
    except:
        print("Unexpected error:", sys.exc_info()[0], "Url", url)
        return ""

#返回含关键词的的索引页dict
def getIndexPageDict(html):
    global DOMAIN, PAGE_KEY_WORD
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all('a'):
        if(link.string != None and PAGE_KEY_WORD in link.string):
            tmpDict = {"keyWord": link.string, \
                       "url": link.get('href').replace(DOMAIN, "")}
            return tmpDict
    return {}

#返回内容页名称+链接dict
def getContentPageDictList(indexPageDict):
    global DOMAIN
    pageDict = []
    html = getHtml(indexPageDict["url"])
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all('a'):
        tmpDict = {"keyWord": indexPageDict["keyWord"], \
                   "name": link.string, \
                   "url": link.get('href').replace(DOMAIN, "")}
        if(tmpDict["name"] != None and len(tmpDict["name"]) > 6 and tmpDict not in pageDict):
            pageDict.append(tmpDict)
    return pageDict

#返回内容页中图片链接dict
def getImgUrlDictList(contentPageDict):
    global DOMAIN
    filePath = DOMAIN.split(".")[1] +  "\\" + contentPageDict["keyWord"] +  "\\" + contentPageDict["name"]
    if(not os.path.exists(filePath)):
        os.makedirs(filePath) 
    else:
        print("Path existed:" + filePath)
        return []
    imgDictList = []
    html = getHtml(contentPageDict["url"])
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all('img'):
        tmpDict = {"keyWord": contentPageDict["keyWord"], \
                   "name": contentPageDict["name"], \
                   "url": link.get('src')}
        if(tmpDict not in imgDictList):
            imgDictList.append(tmpDict)
    if(len(imgDictList) > 10):
        return imgDictList
    else:
        return []

#下载图片
def downloadImg(imgUrlDict):
    global DOMAIN
    if("http" not in imgUrlDict["url"]):
        imgUrlDict["url"] = DOMAIN + imgUrlDict["url"]
    filePath = DOMAIN.split(".")[1] +  "\\" + imgUrlDict["keyWord"] +  "\\" + imgUrlDict["name"]
    fileName = imgUrlDict["url"].split("/")[-1]
    fileFullPath = filePath + "\\" + fileName
    try:
        response = urllib.request.urlopen(imgUrlDict["url"], timeout = 10)
        urlImg = response.read()
        if(len(urlImg) > 10000):
            try:
                if(not os.path.exists(filePath)):
                    os.makedirs(filePath) 
                with open(fileFullPath,'wb') as f:
                    f.write(urlImg)
                print("Download Success:" + fileFullPath)
                return fileFullPath
            except:
                print("Unexpected error:" + str(sys.exc_info()[0]))
                return ""
        else:
            return ""
    except:
        print("Unexpected error:" + str(sys.exc_info()[0]))
        return ""

def getNextIndexPageDict(indexPageDict):
    global DOMAIN
    html = getHtml(indexPageDict["url"])
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all('a'):
        if(link.string != None and "下一页" in link.string):
            tmpDict = {"keyWord": indexPageDict["keyWord"], \
                       "url": link.get('href').replace(DOMAIN, "")}
            return tmpDict
    return {}

base_active_count = td.active_count()
html = getHtml(DOMAIN)
indexPageDict = getIndexPageDict(html)
while(indexPageDict != {}):
    contentPageDictList = getContentPageDictList(indexPageDict)
    for contentPageDict in contentPageDictList:
        imgUrlDict = getImgUrlDictList(contentPageDict)
        while(td.active_count() - base_active_count + len(imgUrlDict) > MAX_THREAD_COUNT):
            time.sleep(0.01)
        for imgUrl in imgUrlDict:
            t = td.Thread(target=downloadImg, args=(imgUrl,))
            t.start()
    indexPageDict = getNextIndexPageDict(indexPageDict)
    print("next page")