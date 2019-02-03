import json
import os
from testTask import TestTask
from  Rs232 import RS232
import configGlobal
import time
import threading
import copy
from queue import Queue
class FiberTest(object):
    #单例模式，对象加锁
    _instance_lock = threading.Lock()

    def __init__(self):
        """
        单例模式下，所有属性只有在第一次声明对象时才给与初始化
        """
        if not hasattr(self, "queue"):
            self.queue=Queue()
        if not hasattr(self, "curTestStatus"):
            self.curTestStatus={}
        if not hasattr(self, "results"):    
            self.results={}
        if not hasattr(self, "testObjects"):     
            self.testObjects={}
        if not hasattr(self, "config"):     
            self.config={}
        if not hasattr(self, "testItems"):      
            self.testItems=[]
        if not hasattr(self, "device"):     
            self.device=None
        if not hasattr(self, "curTaskLeftTime"):       
            self.curTaskLeftTime=-1
        if not hasattr(self, "curTaskLength"):    
            self.curTaskLength=-1
        if not hasattr(self, "curTestIdx"):     
            self.curTestIdx=0
        if not hasattr(self, "totalTests"):    
            self.totalTests=0 
        if not hasattr(self, "isResume"):     
            self.isResume=False
        if not hasattr(self, "devices"):  
            self.devices={"dev1":RS232()}
    def __new__(cls, *args, **kwargs):
        """
        实现单例模式
        """
        if not hasattr(FiberTest, "_instance"):
            with FiberTest._instance_lock:
                if not hasattr(FiberTest, "_instance"):
                    FiberTest._instance = object.__new__(cls)  
        return FiberTest._instance
    def setTestParameter(self,device,testObjects,testItems):
        if not testObjects:
            raise Exception ("测试表号不存在")
        if not device:
            raise Exception ("请配置温箱转台")
        if not testItems:
            raise Exception ("请配置测试项") 
        for item in testItems:
            self.results[item]=-1     
        self.device=device
        if self.device not in self.devices:
            raise Exception ("Unknown device")
        self.testItems=testItems      
        self.totalTests=len(testItems)
        for index,item in enumerate(testObjects):
            self.testObjects[item]=index
        for test in testItems:
            configFile=test+".json"
            if not os.path.exists(configFile):
                raise Exception (test + " 测试，配置文件不存在 ")
            with open(configFile,"r") as f:
                self.config[test]=json.load(f)
    def pauseTest(self):
        configGlobal.setStop(True)
        configGlobal.setPause(True)
        while True:
            if configGlobal.getPause()==False:
                break
            time.sleep(1)
    def resumeTest(self):
        configGlobal.setStop(False)      
        configGlobal.setPause(False)  
        self.isResume=True
        self.execNext()
    def warmUp(self,task,temp):
        try:
            task.warmUp(int(temp))
        except:
            return False, 'wamUp：失败'
        return True, 'warmUp Down'
    def timing(self):
        print(self.curTaskLeftTime)
        while self.curTaskLeftTime>0:
            if configGlobal.getStop():
                break
            self.curTaskLeftTime-=1
            time.sleep(1)
        if self.curTaskLeftTime==0:
            configGlobal.setStop(True)
            time.sleep(1)
        
    def initCurrentTestStatus(self,curConfig,curTest):
        #设置测试步骤的状态 -1：未开始，0：运行失败，1：运行成功，2：运行中
        self.curTestStatus={}
        try:
            steps=curConfig["steps"]
            for step in steps:
                stepName=step['name']
                print (stepName)
                if step["warmUp"]["needed"]:
                    self.curTestStatus[curTest+'_'+stepName+'_warmup']=-1
                self.curTestStatus[curTest+'_'+stepName+'_runTest']=-1
                if "after" in step:
                    action=step["after"]["action"]
                    self.curTestStatus[curTest+'_'+stepName+'_aftertest_'+action]=-1
        except:
            raise Exception("初始化状态信息失败")          
    def __canExec(self):
        if not self.results:
            return False, 'Test results have not been inited!'
        if not self.testObjects:
            return False, 'Test objects have not been inited!'
        if not self.config:
            return False, 'Test configuration has not been inited!'
        if not self.testItems:
            return False, 'Test items have not been inited!'
        if not self.device:
            return False, 'Device has not been inited'
        return True,''
    def execNext(self):
        canExec=self.__canExec()
        if not canExec[0]:
            raise Exception(canExec[1])
        if self.curTestIdx>=self.totalTests:
            return True
        curTest=self.testItems[self.curTestIdx]
        curConfig=self.config[curTest]
        if not self.isResume or self.curTestStatus=={}:
            self.initCurrentTestStatus(curConfig,curTest)
        print (self.curTestStatus)
        steps=curConfig["steps"]
        for step in steps:        
            try:
                testDuration=int(step["testDurations"])
                stepName=step['name']
                temperature=int(step["temperature"])
                speed=int(step["speed"])
                accelate=int(step["accelation"])
                sampleNums=int(step["samples"][0]["totalSamples"])
                sampleFreq=int(step["samples"][0]["frequence"])
            except:
                raise Exception("cast test duration failure")          
            task=TestTask(self.devices[self.device],self.queue)

            if step["warmUp"]["needed"]: 
                configGlobal.setStop(False)
                warmUpStatus=self.curTestStatus[curTest+'_'+stepName+'_warmup']
                warmUpDuration=step["warmUp"]["duration"]
                self.curTaskLength=int(warmUpDuration)
                if warmUpStatus==-1 or warmUpStatus==2:               
                    self.curTaskLeftTime=int(warmUpDuration)
                    if warmUpStatus==2:
                        warmUpDuration=self.curTaskLeftTime
                    self.curTestStatus[curTest+'_'+stepName+'_warmup']=2
                    self.warmUp(task,step["warmUp"]["temperature"])
                    self.timing()
                    task.stopDevTask()
                    if configGlobal.getPause():
                        return 
                    self.curTestStatus[curTest+'_'+stepName+'_warmup']=1
            if speed and accelate:
                task.configTask(sampleNums,self.device,temperature,self.testObjects.values(),sampleFreq,speed,accelate)
            else:
                task.configTask(sampleNums,self.device,temperature,self.testObjects.values(),sampleFreq)
            configGlobal.setStop(False)
            taskStatus=self.curTestStatus[curTest+'_'+stepName+'_runTest']
            self.curTaskLength=int(testDuration)
            if taskStatus==-1 or taskStatus==2:
                if taskStatus==-1:
                    self.curTaskLeftTime=testDuration
                self.curTestStatus[curTest+'_'+stepName+'_runTest']=2
                threads=[]
                t1 = threading.Thread(target=task.runTask)
                threads.append(t1)
                t2 = threading.Thread(target=self.recvTestData,args=[sampleFreq])
                threads.append(t2)
                for t in threads:
                    t.setDaemon(True)
                    t.start()
                    time.sleep(1)
                self.timing()
                task.stopDevTask()
                if configGlobal.getPause():
                    return 
                self.curTestStatus[curTest+'_'+stepName+'_runTest']=1
            if "after" in step:
                configGlobal.setStop(False)
                action=step["after"]["action"]
                self.curTaskLength=int(step["after"]["duration"]) 
                afterStatus=self.curTestStatus[curTest+'_'+stepName+'_aftertest_'+action]
                if afterStatus==-1 or afterStatus==2:    
                    if afterStatus==-1:
                        self.curTaskLeftTime=int(step["after"]["duration"])    
                    self.curTestStatus[curTest+'_'+stepName+'_aftertest_'+action]=2
                    self.timing()
                    if configGlobal.getPause():
                        return 
                    self.curTestStatus[curTest+'_'+stepName+'_aftertest_'+action]=1     
        self.afterTestItem(curTest)
    def afterTestItem(self,curTest):
        if not self.curTestStatus:
            self.results[curTest]=0
        else:
            results=list(set(self.curTestStatus.values()))
            if len(results)>1 or results[0]!=1:
                self.results[curTest]=0
            else:
                self.results[curTest]=1
        print (self.results)
        print (self.curTestStatus)
        self.curTestStatus={}
        self.curTestIdx+=1
        self.isResume=False
        configGlobal.setPause(False)
        configGlobal.setStop(False)
        if self.curTestIdx<self.totalTests:
            self.execNext()

    def recvTestData(self,frequence):
        while True:
            if configGlobal.getStop():
                break 
            print (self.curTaskLeftTime)
            self.queue.get()
            time.sleep(frequence)     
    def getAllTestsStatus(self):
        return self.results
    def getCurTestStatus(self):
        return self.curTestStatus
    def getCurLeftTime(self):
        return self.curTaskLeftTime
    def getCurTestTime(self):
        return self.curTaskLength


 
t=FiberTest()
t.setTestParameter('dev1',['test1','test2','test3','test4','test5','test6','test7','test8'],['lp'])
threads=[]
t1=threading.Thread(target=t.execNext)
threads.append(t1)
t2 = threading.Thread(target=t.pauseTest)
threads.append(t2)

for th in threads:
    #t.setDaemon(True)
    th.start()
    time.sleep(15)
f=FiberTest()
print (f==t)
f.resumeTest()
print ("all down")


    