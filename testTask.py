from datetime import datetime
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
import numpy as np
import time
import contextlib
import configGlobal
from  Rs232 import RS232
from queue import Queue
from threading import Thread, Event
class TestTask(Thread):
    def __init__(self,devObj,queue):
        Thread.__init__(self)
        self.queue = queue
        self.rs=devObj
        self.rs.connect()
        self.taskDuration=None
        self.taskLeftTime=None
        self.sampleNums=None
        self.devName=None
        self.temperature=None
        self.accelator=None
        self.objectsLists=None
        self.sepeed=None
        self.frequence=None
    def configTask(self,sampleNums,devName,temperature,objectsLists,frequence,speed=None,accelator=None):
        #self.taskDuration=taskDuration
        #self.taskLeftTime=taskDuration
        self.sampleNums=sampleNums
        self.devName=devName
        self.temperature=temperature
        self.accelator=accelator
        self.objectsLists=objectsLists
        self.speed=speed
        self.frequence=frequence    
    def _checkPameter(self):
        #if self.taskDuration is None:
        #    return (False,'测试时间为空')
        if self.sampleNums is None:
            return (False, '采样点值为空')
        if self.devName is None:
            return (False, '转台温箱设备名称为空')
        if self.temperature is None:
            return (False, '设置的温度值为空')
        if self.frequence is None:
            return (False, '采样频率为空')
        if self.objectsLists is None:
            return (False,'测试对象列表为空') 
        return (True,'') 
    def warmUp(self,temperature=25):
        if self.rs is None:
            raise Exception('转台温箱没有初始化成功')
        #start=0
        self.rs.powerOn()
        self.rs.setTemperature(temperature)   
        """  
        while start<dur:
            if configGlobal.getStop():
                break 
            print (start)
            time.sleep(1)     
            start+=1
        self.stopwarmUp()
        """
    def stopDevTask(self):
        if self.rs is None:
            raise Exception('转台温箱没有初始化成功')
        self.rs.close()
    """
    def pauseTask(self):
        self.taskLeftTime=self.taskDuration
        self.taskDuration=0
        self.rs.stop()
    def resumeTask(self):
        check=self._checkPameter()
        if not check[0]:
            raise Exception(check[1]+'，请先进行配置')
        self.taskDuration=self.taskLeftTime
        self.runTask()
    """
    def runTask(self):
        check=self._checkPameter()
        if not check[0]:
            raise Exception(check[1]+'，请先进行配置')
        if self.temperature>100 or self.temperature<-100:
            self.rs.setTemperature(25)
        else:
            self.rs.setTemperature(self.temperature)
        if self.speed is not None and self.accelator is not None :
            self.rs.setSepeadExec(self.speed,self.accelator)
        self.rs.powerOn()
        while True:
            if configGlobal.getStop():
                break 
            self.queue.put(self.niRead(self.devName,self.sampleNums,self.objectsLists))
            time.sleep(self.frequence-1) 
    def niRead(self,dev,samples,indexs):
        buf = np.empty((len(indexs), 0), dtype=np.float64)
        data = np.empty((len(indexs), samples), dtype=np.float64)
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                ','.join([dev + '/ai' + str(c) for c in indexs]))
            task.timing.cfg_samp_clk_timing(samples, samps_per_chan=samples)
            stream_task = AnalogMultiChannelReader(task.in_stream)
            stream_task.read_many_sample(
                data, number_of_samples_per_channel=samples)
            s1 = data.mean(axis=1)
            buf = np.column_stack((buf, s1))
        return buf.copy()
#t=TestTask(RS232())
#t.runTask()
#niRead('dev1',3600,[0,1,2,3,4,5,6,7])
