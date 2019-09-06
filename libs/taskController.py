import threading
import json
import copy
from libs.testTask import TestExector
from queue import Queue
import time
import os
import libs.configGlobal
import random
from libs.wx import WxConfig
from libs.dbHandle import DbHandle
from libs.result import TestResult
class TaskController(object):
    _instance_lock = threading.Lock()
    def __init__(self,*args):
        if args and libs.configGlobal.getDown():
            print ('inited')
            self.queue=Queue()    
            self.buf=dict()
            self.dataDir='data'
            self.taskJson=args[0]
            self.session=self._generateSessionStr()
            self.isCurrentBusy=False
            self.testsStatus=list()
            self.temperatures={}
            self.testList=dict()
            self.devConfig=dict()
            self.bdysSpeeds=[]
            self.curTemperature=None
            self.isRestart=False
            self.sessionFile=''
            #self.db=DbHandle()
            t=threading.Thread(target=self._recvTestData)
            t.setDaemon(True)
            t.start()
            self.dev=None
            self.wx=None

    def __new__(cls, *args, **kwargs):
        """
        实现单例模式
        """
        if not hasattr(TaskController, "_instance"):
            with TaskController._instance_lock:
                if not hasattr(TaskController, "_instance"):
                    TaskController._instance = object.__new__(cls)  
        return TaskController._instance
    def _generateSessionStr(self):
        db=DbHandle()
        while True:
            sessionStr=self._randomStr()
            if not db.getSessionId(sessionStr):
                del db
                return sessionStr
    def _randomStr(self):
        #randomlength=10
        str = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        #chars='abcdefghijklmnopqrstuvwxyz0123456'
        length = len(chars) - 1
        for i in range(15):
            str+=chars[random.randint(0, length)]
        return str
    def _recvTestData(self):
        while True:
            if not self.taskJson:
                break
            temp=self.queue.get()
            #print(temp['test'])
            if 'test' not in self.buf or not self.buf['test']:
                self.buf['test']=temp['test']
            if 'object' not in self.buf or not self.buf['object']:
                    self.buf['object']=self.taskJson['objects-list']
                    if temp['test']=='lp' or temp['test']=='lp_cfx':
                        self.buf['object']=['time']+self.buf['object']
                    elif temp['test']=='bdys' or temp['test']=='bdys_cfx':
                        self.buf['object']=['speed']+self.buf['object']
            if temp['test']=='lp' or temp['test']=='lp_cfx':
                if 'buf' not in self.buf or  len(temp['buf'][0])==1:
                        self.buf['buf']=[]
                else:
                    if len(self.buf['buf'])>=900:
                        self.buf['buf'].pop(0)

                testData={'time':time.strftime("%H:%M:%S")}
                for i in range(len(temp['buf'])):
                    testData[self.taskJson['objects-list'][i]]=temp['buf'][i][-1]
                self.buf['buf'].append(testData)
                #print(self.buf)
            if temp['test']=='bdys' or temp['test']=='bdys_cfx':
                if self.bdysSpeeds:
                    if 'buf' not in self.buf or len(temp['buf'][0])==1:
                        self.buf['buf']=[]
                    testData={'speed':str(self.bdysSpeeds[len(temp['buf'][0])-1])}

                    for i in range(len(temp['buf'])):
                        testData[self.taskJson['objects-list'][i]]=temp['buf'][i][-1]
                    self.buf['buf'].append(testData)
                print (self.buf)
    def testTaskInit(self):
            self.buf=dict()
            self.taskJson={}
            self.isCurrentBusy=False
            self.devConfig=dict()
            self.testsStatus=list()
            self.isRestart=False
            self.temperatures={}
            self.curTemperature=None
            self.session=self._generateSessionStr()
            self.testList=dict()
            self.bdysSpeeds=[]
            self.sessionFile=''
            libs.configGlobal.setDown(True)
    def initDevice(self):
        devFile=os.path.join("config","dev.json")
        with open (devFile,"r") as f:
            temp=json.load(f)
            #print (temp)
            self.devConfig['wx']=temp["wx"]["wxtype"]
            self.devConfig['com']=temp["wx"]["com"]
            self.devConfig['ni-dev']=temp["board"]["voltage"]
    def restartTask(self):
        self.buf=dict()
        self.testsStatus=list()
        self.isCurrentBusy=False
        self.temperatures={}
        self.curTemperature=None
        #self.devConfig=dict()
        self.testList=dict()
        self.isRestart=True
        self.bdysSpeeds=[]
        #self.sessionFile=''
        #libs.configGlobal.setDown(False)
        time.sleep(10)
        print(self.parseTask())
        self.runTests()
    def deleteInvalidRecords(self):
        db=DbHandle()
        db.deleteInvalidSession()
        del db
    def runTests(self):
        if self.taskJson is None or self.testList is None:
            self.testTaskInit()
            return False,'config is None'
        if self.temperatures is None:
            #self.isCurrentBusy=False
            self.testTaskInit()
            return False, 'Test temperature is None'
        today=time.strftime("%Y-%m-%d")
        db=DbHandle()
        for item in self.taskJson['objects-list']:
            db.insertSession(self.session,self.taskJson['product'],item,json.dumps(self.testList),self.taskJson['test-type'],today)
        del db
        
        temp=list(self.taskJson['test-tasks'].keys())
        sortedtemp=list()
        if 'basic' in temp and self.taskJson['test-tasks']['basic']['testItems']:
            sortedtemp.append('basic')
        if 'normal' in temp and self.taskJson['test-tasks']['normal']['testItems']:
            sortedtemp.append('normal')
        if 'low' in temp and self.taskJson['test-tasks']['low']['testItems']:
            sortedtemp.append('low')
        if 'high' in temp and self.taskJson['test-tasks']['high']['testItems']:
            sortedtemp.append('high')
        te=TestExector(self.queue,self.taskJson['test-type'],today,self.devConfig['ni-dev'],\
        self.wx,self.taskJson['test-objects'],self.sessionFile,self.session,self.taskJson['product'])
        for i in range(len(sortedtemp)):
            t=sortedtemp[i]
            self.testsStatus[i]['status']=2
            self.curTemperature=self.temperatures[t]
            if t=='low' or t=='high':
                self.testsStatus[i]['tests'][0]['status']=2
                te.warmUp(5,self.curTemperature)
                self.testsStatus[i]['tests'][0]['status']=1
            #for test in self.testList[t]:
            for j in range(len(self.testList[t])):
                test=self.testList[t][j]
                print ('Here comes:')
                print (t, test)
                self.buf={}
                if t=='high' or t=='low':
                    self.testsStatus[i]['tests'][j+1]['status']=2
                else:
                    self.testsStatus[i]['tests'][j]['status']=2
                if test=='lp':
                    te.lp(self.curTemperature)
                elif test=='lp_cfx':
                    te.lpRepeat(self.curTemperature)
                elif test=='bdys':
                    te.bdys(self.curTemperature)
                elif test=='bdys_cfx':
                    te.bdysRepeat(self.curTemperature)
                else:
                    time.sleep(5) 
                #fileName=test+'.txt'
                #print (self.buf)
                if libs.configGlobal.getDown():
                    return
                time.sleep(2)
                if t=='high' or t=='low':
                    self.testsStatus[i]['tests'][j+1]['status']=1
                else:
                    self.testsStatus[i]['tests'][j]['status']=1
                self.buf={}
            self.testsStatus[i]['status']=1
        print ("all Down")
        tr=TestResult()
        tr.updateSession(self.session)
        del tr
        time.sleep(5)
        self.testTaskInit()
    def combinConfig(self):
        product=self.taskJson['product']
        testType=self.taskJson['test-type']
        tempConfigPath=os.path.join('config','temp')
        configFile="config/"+product+"_"+testType+".json"
        template=''
        if not os.path.exists(configFile):
            return False,product + " 测试，配置文件不存在"
        #userConfig=self.taskJson['test-settings']
        with open(configFile,"r") as f:
            temp=json.load(f)
            template=temp['test-settings']
        if testType=='defined':
            userConfig=self.taskJson['test-settings']
        else:
            userConfig=template
        for temperature in template:
            if temperature not in userConfig:
                continue
            for test in template[temperature]:
                if test not in userConfig[temperature]:
                    continue
                for item in template[temperature][test]:
                    if item in userConfig[temperature][test]:
                            #print (temperature,test,item)
                        template[temperature][test][item]=userConfig[temperature][test][item]
                    if test=='bdys' and item=='speeds':
                        self.bdysSpeeds=[int(x) for x in template[temperature][test][item].split(',')]
        for f in os.listdir(tempConfigPath):
            os.remove(os.path.join(tempConfigPath,f))
        self.sessionFile=os.path.join(tempConfigPath,product+'_'+str(self.session)+'.json')
        with open(self.sessionFile, 'w') as f:
            json.dump(template, f)
                
    def parseTask(self):
        if self.isCurrentBusy:
            #self.testTaskInit()
            return False,'busy'
        if self.taskJson is None:
            self.testTaskInit()
            return False,'config is None'
        #printprint (self.taskJson)
        libs.configGlobal.setDown(False)
        if not self.isRestart:
            self.initDevice()
        if self.devConfig is None:
            self.testTaskInit()
            return False,'System device initial failed'        
        self.combinConfig()
        self.isCurrentBusy=True

        #if self.devConfig['wx']=="rs232":
        if not self.isRestart or not self.wx:
            self.wx=WxConfig(self.devConfig['wx'],self.devConfig['com'])
        testType=self.taskJson['test-type']
        if testType in ['jj','zj']:
            configFile="config/"+self.taskJson['product']+"_"+testType+".json"
            with open(configFile,"r") as f:
                temp=json.load(f)
                self.taskJson['test-tasks']=temp['test-tasks']

        temp=list(self.taskJson['test-tasks'].keys())
        #print (temp)
        sortedtemp=list()
        if 'basic' in temp:
            sortedtemp.append('basic')
        if 'normal' in temp:
            sortedtemp.append('normal')
        if 'low' in temp:
            sortedtemp.append('low')
        if 'high' in temp:
            sortedtemp.append('high')
        for t in sortedtemp:
            if self.taskJson['test-tasks'][t]['testItems']:
                task={'item':t,'tests':[],'status':0}
                if 'temperature' in self.taskJson['test-tasks'][t]:
                    self.temperatures[t]=int(self.taskJson['test-tasks'][t]['temperature'])
                else:
                    self.temperatures[t]=25
                self.testList[t]=copy.deepcopy(self.taskJson['test-tasks'][t]['testItems'])
                if 'lp' in self.testList[t] and 'lp_wdx' in self.testList[t]:
                    self.testList[t].remove('lp_wdx')
                if 'bdys' in self.testList[t] and 'xxd' in self.testList[t]:
                    self.testList[t].remove('xxd') 
                if t=='low' or t=='high':
                    task['tests'].append({'name':'warmUP','status':0})
                for item in self.testList[t]:
                    task['tests'].append({'name':item,'status':0})
                self.testsStatus.append(task)
        print (self.testsStatus)
        print (self.temperatures)
        print (self.testList)
        return True, 'success'
        #task=json.loads(self.taskJson)
    def __del__(self):
        if self.sessionFile and os.path.exists(self.sessionFile):
            os.remove(self.sessionFile)
"""  
config={'test-type':'jj','test-objects': {'1': 'abc', '0': '121', '5': 'ed'}, 'product': '10FA','objects-list':['abc','121','ed']}
tc=TaskController(config)
#tc.taskJson=config
tc.parseTask()
tc.runTests()
#del tc
"""

