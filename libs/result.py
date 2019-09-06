import os
import json
import copy
from libs.dbHandle import DbHandle
import datetime

class TestResult(object):
    def __init__(self):
        self.db=DbHandle()
    def getBhFromSession(self,sessionId,status=1):
        sql="select bh from session where status=%d and sessionId=\'%s\'" %(status,sessionId)
        result=self.db.search(sql)
        bhs=[]
        for i in range(0,len(result)):
            bhs.append(result[i][0])
        return bhs
    
    def getTestSetItemsFromSession(self,sessionId):
        sql="select testSettings from session where  sessionId=\'%s\'" %(sessionId)
        result=self.db.searchOne(sql)
        return json.loads(result[0]) if result else {}
    def judgeResult(self,testItem,temperature,value):
        pass
        return True
    def getTestResult(self,sessionId,bh,testSettings):
        result=[]
        if not bh :
            return result
        if not sessionId:
            return result
        temperature=''
        testItems=[]
        for key,val in testSettings.items():
            testItems=val
            if key=='normal':
                temperature='15<temperature<35'
            elif key=='low':
                temperature='-80<temperature<0'
            elif key=='high':
                temperature='40<temperature<80'
            for item in testItems:
                if item=='lp':
                    sql='select lp, lp_wdx,data_file from lp where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result.append({'testItem': 'lp','temperature':key,'testResult':tempResult[0],'judgeResult':1 if self.judgeResult('lp',key,tempResult[0]) else 0, 'dataFile':tempResult[2]})
                        result.append({'testItem': 'lp_wdx','temperature': key,'testResult':tempResult[1],'judgeResult':1 if self.judgeResult('lp_wdx',key,tempResult[1]) else 0, 'dataFile':'-'})
                elif item=='lp_cfx':
                    sql='select lp_cfx,data_file from lp_cfx where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result.append({'testItem': 'lp_cfx','temperature':key,'testResult':tempResult[0],'judgeResult':1 if self.judgeResult('lp_cfx',key,tempResult[0]) else 0, 'dataFile':tempResult[1]})   
                elif item=='bdys':
                    sql='select bdys,bdys_xxd,data_file from bdys where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result.append({'testItem': 'bdys','temperature':key,'testResult':tempResult[0],'judgeResult':1 if self.judgeResult('bdys',key,tempResult[0]) else 0, 'dataFile':tempResult[2]})
                        result.append({'testItem': 'bdys_xxd','temperature':key,'testResult':tempResult[1],'judgeResult':1 if self.judgeResult('bdys_xxd',key,tempResult[1]) else 0, 'dataFile':'-'})              
                elif item=='bdys_cfx':
                    sql='select bdys,bdys_xxd,data_file from bdys_cfx where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        result.append({'testItem': 'bdys_cfx','temperature':key,'testResult':tempResult[0],'judgeResult':1 if self.judgeResult('bdys',key,tempResult[0]) else 0, 'dataFile':tempResult[2]})
                        result.append({'testItem': 'bdys_xxd_cfx','temperature':key,'testResult':tempResult[1],'judgeResult':1 if self.judgeResult('bdys_xxd',key,tempResult[1]) else 0, 'dataFile':'-'})    
        return result
    def updateSession(self,sessionId):
        bhs=self.getBhFromSession(sessionId,status=0)
        for bh in bhs:
            result = 1 if self.judgeAllResult(sessionId,bh) else 0
            updated="status = 1, result = %d" %result
            cond="sessionId = \'" + sessionId + "\' and bh = \'" + bh + "\'" 
            self.db.updateTable('session',updated,cond)
    def judgeAllResult(self,sessionId,bh):
        testSettings=self.getTestSetItemsFromSession(sessionId)
        for key,val in testSettings.items():
            testItems=val
            if key=='normal':
                temperature='15<temperature<35'
            elif key=='low':
                temperature='-80<temperature<0'
            elif key=='high':
                temperature='40<temperature<80'
            for item in testItems:
                if item=='lp':
                    sql='select lp, lp_wdx from lp where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        if not self.judgeResult('lp',key,tempResult[0]):
                            return False
                        if not self.judgeResult('lp_wdx',key,tempResult[1]):
                            return False
                    else:
                        return False
                elif item=='lp_cfx':
                    sql='select lp_cfx from lp_cfx where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        if not self.judgeResult('lp_cfx',key,tempResult[0]):
                            return False
                    else:
                        return False
                elif item=='bdys':
                    sql='select bdys,bdys_xxd from bdys where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        if not self.judgeResult('bdys',key,tempResult[0]):
                            return False
                        if not self.judgeResult('bdys_xxd',key,tempResult[1]):
                            return False
                    else:
                        return False 
                elif item=='bdys_cfx':
                    sql='select bdys,bdys_xxd from bdys_cfx where bh=\''+bh+'\' and session=\''+sessionId+'\' and '+temperature
                    tempResult=self.db.searchOne(sql)
                    if tempResult:
                        if not self.judgeResult('bdys',key,tempResult[0]):
                            return False
                        if not self.judgeResult('bdys_xxd',key,tempResult[1]):
                            return False
        return True        
    def getGeneralResult(self,sessionId,bh):
        bhs=[]
        if not bh:
            bhs=self.getBhFromSession(sessionId)
        else:
            bhs.append(bh)
        result=[]
        for bh in bhs:
            sql="select product,testType,testDate,result from session where status=1 and sessionId=\'" +sessionId+ "\' and bh=\'" +bh+ "\'"
            generalResult=self.db.searchOne(sql)
            temp={}
            temp['bh']=bh
            temp['product']=generalResult[0]
            temp['testType']=generalResult[1]
            temp['testDate']=generalResult[2]
            temp['result']=generalResult[3]
            temp['session']=sessionId
            result.append(temp) 
        return result
    def getSessionResult(self,sessionId,bh):
        testSettings=self.getTestSetItemsFromSession(sessionId)
        bhs=[]
        if not bh:
            bhs=self.getBhFromSession(sessionId)
        else:
            bhs.append(bh)
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
        sql='select distinct(sessionId) from session where status=1'
        if condition:
            sql+=' and '+condition
        print (sql)
        result=[]
        tempResult=self.db.search(sql)
        for item in tempResult:
            result.append(item[0])
        return result
    def getResultFromCond(self, startDate,endDate,bh,testType,product,general=False):
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
            condition+='testDate>= \''+startDate+'\' and testDate<=\''+endDate+'\''
        if bh:
            if condition:
                condition+=' and '
            condition+= 'bh = \''+bh+'\''
        if testType:
            if condition:
                condition+=' and '
            condition+= 'testType=\''+testType+'\''
        if product:
            if condition:
                condition+=' and '
            condition+= 'product=\''+product+'\''   
        print (condition)     
        sessions=self.getSessionIdsFromCond(condition)
        results=[]
        if general:
            for session in sessions:
                results+=self.getGeneralResult(session,bh)
        else:
            for session in sessions:
                results+=self.getSessionResult(session,bh)
        return results
             

        
"""
testSettings="{\"normal\": [\"lp\"]}"
sessionId="TTRGzW1eZS8reTx"
tr=TestResult()
print(tr.getSessionResult(sessionId,'16'))

bh="1"
tr=TestResult()
print(tr.getResultFromCond('','','','',''))
"""