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