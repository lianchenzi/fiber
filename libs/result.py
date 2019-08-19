import os
import json
import copy
from dbHandle import DbHandle
import datetime

class TestResult(object):
    def __init__(self):
        self.db=DbHandle()
    def getBhFromSession(self,sessionId):
        sql="select testObjects from session where status=1 and sessionId=\'"+sessionId+"\'"
        result=self.db.searchOne(sql)
        return result[0].split(',,,') if result else []
    
    def getTestSetItemsFromSession(self,sessionId):
        sql="select testSettings from session where status=1 and sessionId=\'"+sessionId+"\'"
        result=self.db.searchOne(sql)
        return json.loads(result[0]) if result else {}
 
    def getTestResult(self,sessionId,bh,testSettings):
        result={}
        if not bh :
            return result
        if not sessionId:
            return result
        temperature=''
        testItems=[]
        sql='select '
        for key,val in testSettings.items():
            result[key]={}
            testItems=val
            if key=='normal':
                temperature='15<temperature<35'
            elif key=='low':
                temperature='-50<temperature<0'
            elif key=='high':
                temperature='40<temperature<60'
            for item in testItems:
                result[key][item]={}
                if item=='lp':
                    sql+='lp, lp_wdx from lp where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result[key][item]['lp']=tempResult[0]
                        result[key][item]['lp_wdx']=tempResult[1]
                elif item=='lp_cfx':
                    sql+='lp_cfx from lp_cfx where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result[key][item]['lp_cfx']=tempResult[0]         
                elif item=='bdys':
                    sql+='bdys,bdys_xxd from bdys where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result[key][item]['bdys']=tempResult[0]
                        result[key][item]['bdys_xxd']=tempResult[1]                      
                elif item=='bdys_cfx':
                    sql+='bdys,bdys_xxd from bdys_cfx where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result[key][item]['bdys']=tempResult[0]  
                        result[key][item]['bdys_xxd']=tempResult[1]
        return result
    def getSessionResult(self,sessionId):
        testSettings=self.getTestSetItemsFromSession(sessionId)
        bhs=self.getBhFromSession(sessionId)
        sql="select product,testType,testDate from session where status=1 and sessionId=\'"+sessionId+"\'" 
        generalResult=self.db.searchOne(sql)
        result=[]
        for bh in bhs:
            temp={}
            temp['bh']=bh
            temp['product']=generalResult[0]
            temp['testType']=generalResult[1]
            temp['testDate']=generalResult[2]
            temp['result']=self.getTestResult(sessionId,bh,testSettings)
            result.append(temp)
        return result
    def getSessionIdsFromCond(self,condition):
        sql='select sessionId from session where status=1'
        if condition:
            sql+=' and '+condition
        result=[]
        print (sql)
        tempResult=self.db.search(sql)
        for item in tempResult:
            result.append(item[0])
        return result
    def getResultFromCond(self, startDate,endDate,bh,testType,product):
        condition=''
        if startDate and endDate:
            try:
                sDate=datetime.datetime.strptime(startDate,"%Y-%m-%d")
                eDate=datetime.datetime.strptime(startDate,"%Y-%m-%d")
                delta = eDate-sDate
                if int(delta.days)<0:
                    raise Exception("end date is earlier than start date")
            except Exception as e:
                print (e)
            if condition:
                condition+=' and '
            condition+=' \''+startDate+'\'<=testDate<=\''+endDate+'\''
        if bh:
            if condition:
                condition+=' and '
            condition+= 'bh=\''+bh+'\''
        if testType:
            if condition:
                condition+=' and '
            condition+= 'testType=\''+testType+'\''
        if product:
            if condition:
                condition+=' and '
            condition+= 'product=\''+product+'\''        
        sessions=self.getSessionIdsFromCond(condition)
        results=[]
        for session in sessions:
            results+=self.getSessionResult(session)
        return results
             

        

testSettings="""{"normal": ["lp"]}"""
sessionId="TTRGzW1eZS8reTx"
bh="1"
tr=TestResult()
print(tr.getResultFromCond('2019-08-17','2019-08-17','','defined','10FA'))
