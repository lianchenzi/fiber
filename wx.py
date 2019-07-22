import serial
class Com(object):
    '''
    classdocs
    '''
    def __init__(self, comPort='COM1',baudrate=9600):
        '''
        Constructor
        '''
        self.ser = serial.Serial(str(comPort),baudrate)
    def connect(self):
        if not self.ser.is_open:
            self.ser.open()
        return self.ser.is_open
    def close(self):
        if self.ser.is_open:
            self.ser.close()
        return self.ser.closed
    def getPortStr(self):
        if self.ser.is_open:
            return self.ser.portstr
        raise Exception("Serise is not open!")
    def sendMsg(self,msg):
        if not self.ser.is_open:
            self.connect()
        if not msg:
            return False
        listMsg=[]
        try:
            listMsg=list(msg)        
        except:
            print ("Format input msg error")
            return False
        self.ser.write((','.join(listMsg)).encode())
        return True
class WXControl(object):
    def __init__(self, comPort,baudrate,cmdsLength=10):
        self.com=Com(comPort,baudrate)
        self.com.connect

        self.cmdsLength=cmdsLength
        
    def calcLastValue(self,curMsg):
        """
        计算第10位值
        """
        return self.complement(0-sum(eval(t) for t in curMsg),8)
    def completeAndRunCmd(self,cmd):

        
        msg=['0x0']*(self.cmdsLength-len(cmd))
        msg=cmd+msg
        msg+=self.calcLastValue(msg)
        return self._execute(msg)       
    def execDefaultCommand(self,cmd,params=None):
        command=[cmd]
        if params:
            if not isinstance(params,list):
                raise Exception('Parameters for command must be a list')
            for param in params:
                if not isinstance(param,list) or len(param)!=2:
                    raise Exception('Illegal parameter, a parameter should be like this: \'(1,8)\'')
                command+=self.complement(param[0],param[1])
        if len(command)>self.cmdsLength:
            raise Exception('Parameters are too long')
        return self.completeAndRunCmd(command)
       
    def _execute(self,msg):
        return self.com.sendMsg(msg)
    def complement(self,value, bits):
        """
        命令参数先转换为二进制，再以8bit为单位转换为16进制
        @inputs value 参数值
                bits 位数（取值8,16,24,32,40,48,56,64）
        """
        if bits not in (8,16,24,32,40,48,56,64):
            raise Exception('Illegal bits value')
        binValue=bin(value & int("1"*bits, 2))[2:]
        binValue=("{0:0>%s}" % (bits)).format(binValue)
        index=0
        hexList=[]
        while index<bits//8:
            curHex=binValue[index*8:index*8+8]
            hexList.append(str(hex(int(curHex, 2))))
            index=index+1
        return hexList

class WxConfig(object):
    def __init__(self,wx,com='COM1'):
        self.controller=WXControl(com,9600,10)
        if wx=='rs232':
            self.commands=['0x55','0x66','0x77','0x05','0x01','0x02','0x03','0x04','0x06','0x07','0x27']
        else:
            self.commands=['0x55','0x66','0x77','0x05','0x01','0x02','0x03','0x04','0x06','0x07','0x27']
        """
        温箱控制命令11个组成为一个list，
        第0位：建立通讯
        第1位：退出远控
        第2位：选择负载
        第3位：上电
        第4位：闭合
        第5位：释放
        第6位：停止
        第7位：归零
        第8位：速度运动方式
        第9位：位置运动方式
        第10位：温度设置
        """
    def connect(self):
        return self.controller.execDefaultCommand(self.commands[0])
    def exitControl(self):
        return self.controller.execDefaultCommand(self.commands[1])
    def sefWordLoad(self,load):
        if load not in (1,2,3,4):
            raise Exception('Load must be in 1,2,3,4')
        return self.controller.execDefaultCommand(self.commands[2],[[load,8]])
    def powerOn(self):
        return self.controller.execDefaultCommand(self.commands[3])
    def close(self):
        return self.controller.execDefaultCommand(self.commands[4])
    def release(self):
        return self.controller.execDefaultCommand(self.commands[5])
    def stop(self):
        return self.controller.execDefaultCommand(self.commands[6])    
    def clear(self):
        return self.controller.execDefaultCommand(self.commands[7])
    def setSepeadExec(self,speed,accelertion):
        if speed<-1000000 or speed>1000000:
            raise Exception('Invalid spead value')
        if accelertion<1 or accelertion>8000:
            raise Exception('Invalid acceleration value')
        return self.controller.execDefaultCommand(self.commands[7],[[speed,24],[accelertion,24]])
    def setPositionExec(self,pos,speed,accelertion):
        if pos<-3600000 or pos>3600000:
            raise Exception('Invalid position value')
        if speed<-1000000 or speed>1000000:
            raise Exception('Invalid spead value')
        if accelertion<1 or accelertion>8000:
            raise Exception('Invalid acceleration value')
        return self.controller.execDefaultCommand(self.commands[8],[[pos,24],[speed,24],[accelertion,16]])  
    def setTemperature(self,temp):
        if temp<-100 or temp>100:
            raise Exception('Invalid temperature value')
        return self.controller.execDefaultCommand(self.commands[9],[[temp,8]])  