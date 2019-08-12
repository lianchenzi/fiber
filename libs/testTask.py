from datetime import datetime
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
import numpy as np
import time
import os,json
import contextlib
import libs.configGlobal
#from  Rs232 import RS232
from queue import Queue
import threading
from threading import Thread, Event
import libs.gjb2426
from libs.dbHandle import DbHandle
import os
np.set_printoptions(suppress=True)
DATA_DIR='data'
DB_DIR=os.path.join(DATA_DIR,'result.db')
class TestExector(threading.Thread):
    def __init__(self,queue,testType,date,niDevName,rs,objectsLists,configFile,product):
        Thread.__init__(self)
        self.singal = threading.Event()
        self.queue=queue
        self.testDate=date
        self.product=product
        self.singal.set() 
        self.config=None
        self.testType=testType
        self.rs=rs
        self.rs.connect()
        self.curTaskLeftTime=0
        self.curTaskDown=False
        self.niDevName=niDevName
        self.isRepeat=False
        self.curTest={'test':None,'repeator':None}
        self.objectLists=dict()
        self.objectMap={}
        for (k,v) in objectsLists.items():
            self.objectMap[v]=int(k)
            self.objectLists[int(k)]=v
        if not os.path.exists(configFile):
            raise Exception (product + " 测试，配置文件不存在 ")
        with open(configFile,"r") as f:
            self.config=json.load(f)
    def warmUp(self,duration,temperature=25):
        print("warm up:")
        print(temperature)
        if self.rs is None:
            raise Exception('转台温箱没有初始化成功')
        #start=0
        self.rs.powerOn()
        self.rs.setTemperature(temperature)
        time.sleep(duration)   
    def getConfig(self,test,temperature):
        if self.config is None:
            raise Exception ("零偏测试配置不存在")
        if temperature<0: 
            if 'low' in self.config and test in self.config['low']:
                return self.config['low'][test]
        elif temperature>40:
            if 'high' in self.config and test in self.config['high']:
                return self.config['high'][test]            
        else:
            if 'normal' in self.config and test in self.config['normal']:
                return self.config['normal'][test]           
        return None         

    def stopDevTask(self):
        if self.rs is None:
            raise Exception('转台温箱没有初始化成功')
        self.rs.close()
    def lp(self,temperature,seconds=0):
        lpConfig=self.getConfig('lp',temperature)
        if not self.isRepeat:
            self.curTest['test']='lp'
            self.curTest['repeator']=None
        if seconds==0:
            self.setWxzt(temperature)
            seconds=int(lpConfig["duration"])
            #time.sleep(int(lpConfig["wait"]))
            libs.configGlobal.setStop(False)
        frequency=int(lpConfig["frequency"])
        samples=int(lpConfig["samples"])
        buf = np.empty((len(self.objectMap.values()), 0), dtype=np.float64)
        while seconds>0:
            if  libs.configGlobal.getDown():
                self.stopDevTask()
                return None
            self.singal.wait()
            s1=self.niRead(self.niDevName,samples,sorted(self.objectMap.values()))
            buf = np.column_stack((buf, s1))
            temp={'test':self.curTest['test'],'repeator':self.curTest['repeator'],'buf':buf}
            self.queue.put(temp)
            #time.sleep(frequency)
            seconds-=1
        if not self.isRepeat:
            self.compute('lp',buf.copy(),temperature)
        return buf.copy()

    def lpRepeat(self,temperature): 
        self.isRepeat=True   
        self.curTest['test']='lp_cfx'
        lpRepeatConfig=self.getConfig('lp_cfx',temperature)
        repeatNums=int(lpRepeatConfig["repetition"])
        seconds=int(lpRepeatConfig["duration"])
        stopSeconds=int(lpRepeatConfig["powerDown"])
        time.sleep(int(lpRepeatConfig["wait"]))
        res=[]
        for i in range(repeatNums):
            print ( 'No:'+str(i))
            self.setWxzt(temperature)
            #time.sleep(int(lpRepeatConfig["wait"]))
            self.curTest['repeator']=i
            libs.configGlobal.setStop(False)
            if self.lp(temperature,seconds) is not None:
                res.append(self.lp(temperature,seconds))
            else:
                return 
            time.sleep(stopSeconds)
        self.compute('lp_cfx',res.copy(),temperature)
        self.isRepeat=False

    def bdys(self,temperature):
        bdysConfig=self.getConfig('bdys',temperature)
        if not self.isRepeat:
            self.curTest['test']='bdys'
            self.curTest['repeator']=None
        print (bdysConfig)
        speeds=[int(x) for x in bdysConfig['speeds'].split(',')]
        #frequence=int(bdysConfig["frequence"])
        seconds=int(bdysConfig["samplesPerSpeed"])
        samples=int(bdysConfig["samples"])
        buf = np.empty((len(self.objectMap.values()), 0), dtype=np.float64)
        for speed in speeds:
            self.setWxzt(temperature,speed)
            time.sleep(10)
            temp=seconds
            while temp>0:
                if libs.configGlobal.getDown():
                    self.stopDevTask()
                    return None
                self.singal.wait()
                s1=self.niRead(self.niDevName,samples,sorted(self.objectMap.values()))
                buf = np.column_stack((buf, s1))
                #print (buf)
                #time.sleep(1)
                temp-=1
            self.stopDevTask()
            temp={'test':self.curTest['test'],'repeator':self.curTest['repeator'],'buf':\
                np.column_stack([d.mean(axis=1) for d in np.hsplit(buf, buf.shape[1] / seconds)])}
            #temp=np.column_stack([d.mean(axis=1) for d in np.hsplit(buf, buf.shape[1] / seconds)])
            self.queue.put(temp)
        buf = np.column_stack([d.mean(axis=1) for d in np.hsplit(buf, buf.shape[1] / seconds)])
        if not self.isRepeat:
            self.compute('bdys',buf.copy(),temperature)
        return buf.copy()

    def compute(self,test,data,temperature):
        if test is None or test =='':
            return False, 'test is None'
        if data is None:
            return False, "data is empty"
        
        bdysConfig=self.getConfig('bdys',temperature)
        speeds=[int(x) for x in bdysConfig['speeds'].split(',')]    
        result=None      
        if test=="lp":
            lpConfig=self.getConfig('lp',temperature)
            result=libs.gjb2426.lp(data,int(lpConfig["stableFactor"]))
        elif test=="lp_cfx":
            result=libs.gjb2426.lp_cfx(data)
        elif test=="bdys":
            result=libs.gjb2426.bdys(data,speeds)
        elif test=="bdys_cfx":
            result=libs.gjb2426.bdys_cfx(data,speeds)
        else:
            return False, "Unknown test"
        db=DbHandle()
        dataPath=os.path.join(DATA_DIR,os.path.join(self.testDate,self.product))
        t=''
        if temperature>40:
            t='high'
        elif temperature<0:
            t='low'
        else:
            t='normal'

        testPath=os.path.join(dataPath,test+'_'+t)
        if not os.path.exists(testPath):
            os.makedirs(testPath)
        if result and len(result)==len(self.objectLists):
            bhIndex=sorted(self.objectLists.keys())
            for i in range(len(bhIndex)):
                dataKey=test+'_data'
                temp=result[i]
                bh=self.objectLists[bhIndex[i]]
                resultFile=os.path.join(testPath,bh)+'.log'
                #resultFile2=os.path.join(testPath,bh)+'_result.log'
                if os.path.exists(resultFile):
                    os.remove(resultFile)              
                with open(resultFile,'a') as f:
                    f.write("\n".join(list(map(self.asNum, temp[dataKey]))))
                if test=="lp":
                    db.insert_lp(self.product,self.testDate,temperature,self.testType,bh,temp['lp'],temp['lp_wdx'],resultFile)
                    
                    with open(resultFile,'a') as f:
                        f.write('\n\n')
                        f.write(r'测试日期：' +str(self.testDate)+'\n')
                        f.write(r'零位: '+ str(temp['lp']) +'\n' )
                        f.write(r'零位稳定性: '+ str(temp['lp_wdx']) +'\n' )
                    
                elif test=="lp_cfx":
                    db.insert_lp_cfx(self.product,self.testDate,temperature,self.testType,bh,temp['lp_cfx'],resultFile)
                elif test=="bdys":
                    db.insert_bdys(self.product,self.testDate,temperature,self.testType,bh,temp['bdys'],temp['bdys_xxd'],resultFile)

                elif test=="bdys_cfx":
                    db.insert_bdys_cfx(self.product,self.testDate,temperature,self.testType,bh,temp['bdys'],temp['bdys_xxd'],resultFile)
        else:
            del db
            return False, "Test result is empty or wrong"
        del db
        return True,""
    def asNum(self,x):
        y = '{:.20f}'.format(x)
        return str(y)
    def bdysRepeat(self,temperature):
        self.isRepeat=True  
        self.curTest['test']='bdys_cfx'
        bdysRepeatConfig=self.getConfig('bdys_cfx',temperature)
        stopSeconds=int(bdysRepeatConfig["powerDown"])
        repeatNums=int(bdysRepeatConfig["repetition"])
        res=[]
        for i in range(repeatNums):
            print ("scale factor repeat testing, the "+str(i+1)+"th test, total: "+str(repeatNums))
            self.curTest['repeator']=i
            if self.bdys(temperature) is not None:
                res.append(self.bdys(temperature))
            else:
                return
            time.sleep(stopSeconds)
        self.isRepeat=False
        self.compute('bdys_cfx',res.copy(),temperature)

    def setWxzt(self,temperature,speed=None):
        if temperature>100 or temperature<-100:
            raise Exception ("无效温度配置")
        elif temperature<0 or temperature>40:
            self.rs.setTemperature(temperature)
        else:
            pass
        if speed is not None:
            self.rs.setSepeadExec(speed,1)
        self.rs.powerOn()
    def pause(self):
        print ("paused")
        self.singal.clear()
 
    def restart(self):
        print ("restart")
        self.singal.set()

    def niRead(self,dev,samples,indexs):
        #buf = np.empty((len(indexs), 0), dtype=np.float64)
        data = np.empty((len(indexs), samples), dtype=np.float64)
        try:
            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(
                    ','.join([dev + '/ai' + str(c) for c in indexs]))
                task.timing.cfg_samp_clk_timing(samples, samps_per_chan=samples)
                stream_task = AnalogMultiChannelReader(task.in_stream)
                stream_task.read_many_sample(
                    data, number_of_samples_per_channel=samples)
                s1 = data.mean(axis=1)
                return s1.copy()
        except:
            return
"""
rs=RS232()
queue=Queue()

def recv():
    while True:
        queue.get()
t=threading.Thread(target=recv)
t.setDaemon(True)
t.start()
     
today=time.strftime("%Y-%m-%d")
te=TestExector(queue,today,'dev1',rs,{'0':'t1','1':'t2'},os.path.join('config','10FA.json'))

te.lp(25)
#te.lpRepeat(25)
#te.bdys(25)
#te.bdysRepeat(25)
"""