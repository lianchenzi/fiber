from wx import WXControl
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

    

