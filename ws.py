#!-*- coding:utf-8 -*-
import time
import random
from threading import Lock
import threading
from flask_socketio import SocketIO,send, emit
from flask import Flask,current_app,render_template,make_response,request,send_from_directory
from functools import wraps
from flask_cors import CORS
from flask_restful import Api,Resource,reqparse, abort,marshal
from libs.taskController import TaskController
import libs.configGlobal
from libs.dbHandle import DbHandle
from libs.product import Product
from libs.result import TestResult
import os
from datetime import datetime, date, timedelta
import json
#import eventlet
#eventlet.monkey_patch()
async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
#socketio = SocketIO(app)
thread = None
thread_lock = Lock()
app.config.update(RESTFUL_JSON=dict(ensure_ascii=False),SECRET_KEY='secretadsfasdfa')
CORS(app, supports_credentials=True)
api = Api(app)
 
# 后台线程 产生数据，即刻推送至前端
def background_thread():
    while True:
        socketio.sleep(5)
        if not libs.configGlobal.getDown():
            tc=TaskController()
            #print (tc.testsStatus)
            socketio.emit('updateStatus',
                            tc.testsStatus,
                            namespace='/test')
            if tc.buf and 'buf' in tc.buf and tc.buf['buf']:
                #print (tc.buf)
                socketio.emit('server_response',
                              tc.buf,
                              namespace='/test')

            info={'running': 'Busy','test': '','temperature': str(tc.curTemperature),'current': ''}
            for item in tc.testsStatus:
                if item['status']==2:
                    info['test']=item['item']
                    break
            socketio.emit('updateInfo',
                            info,
                            namespace='/test')   
        else:
            socketio.emit('initialPage',
                            namespace='/test')   

            

 
class Login(Resource):
    def __init__(self):
        self.parser=reqparse.RequestParser()
        self.parser.add_argument('username',type=str,required=True,help='Username is required!')
        self.parser.add_argument('password',type=str,required=True,help='Password is required!')
        
        
    def post(self):
        args = self.parser.parse_args()
        username=args['username']
        password=args['password']
        if not username:
            return packageResponse(401,"username can not be none","")
        if not password:
            return packageResponse(401,"password can not be none","")
        db=DbHandle()
        result=db.verifyUser(username,password)
        if result[0]:            
            data={}
            data["username"]=result[1][1]
            data["userId"]=result[1][0]
            data["auth"]=result[1][3]
            data["token"]='92371670136'
            return packageResponse(200,"success",data)
        else:
            return packageResponse(403,"invalid user",'')
class Device(Resource):
    def __init__(self):
        self.data=request.get_json()
    def get(self):
        db=DbHandle()
        wx=db.getWx()
        data={}
        data['wxList']=wx
        devConfigFile=os.path.join('config','dev.json')
        with open(devConfigFile,"r") as f:
            temp=json.load(f)
            data['wx']=temp['wx']
            data['board']=temp['board']
        return packageResponse(200,'success',data)

    def post(self):
        devConfigFile=os.path.join('config','dev.json')
        temp=None
        with open(devConfigFile,"r") as f:
            temp=json.load(f)
        for m in self.data:
            for n in self.data[m]:
                if m in temp and n in temp[m]:
                    temp[m][n]=self.data[m][n]
        print (temp)
        with open(devConfigFile,"w") as f:
            json.dump(temp,f)
        return packageResponse(200,"success","")

class Task(Resource):
    def __init__(self):
        self.data=request.get_json()
        self.parser=reqparse.RequestParser()
        self.parser.add_argument('action', type=str)

    def get(self):
        args = self.parser.parse_args()
        print (args)
        if 'action' in args and not libs.configGlobal.getDown():
            tc=TaskController()
            if args['action']=='stop':
                tc.deleteInvalidRecords()
                libs.configGlobal.setDown(True)
            elif args['action']=='restart':
                tc.deleteInvalidRecords()
                libs.configGlobal.setDown(True)
                t=threading.Thread(target=tc.restartTask)
                t.setDaemon(False)
                t.start()
        return packageResponse(200,"success",{'testSession':tc.session})
    def post(self):
        print(self.data)
        tc=TaskController(self.data)
        parseReslt=tc.parseTask()
        tc.deleteInvalidRecords()
        print (parseReslt)
        if not parseReslt[0]:
            return packageResponse(401,parseReslt[1],"")
        t=threading.Thread(target=tc.runTests)
        t.setDaemon(False)
        t.start()
        return packageResponse(200,"success",{'testSession':tc.session})

class ProductConfig(Resource):
    def __init__(self):
        self.data=request.get_json()
        self.parser=reqparse.RequestParser()
        self.parser.add_argument('productName', type=str)
        self.parser.add_argument('productType', type=str)
        #self.parser=reqparse.RequestParser()
        self.prodObj=Product()

    def get(self):
        args = self.parser.parse_args()
        productName=''
        productType=''
        print(args)
        if 'productName' in args:
            productName=args['productName']
        if 'productType' in args:
            productType=args['productType']
        result=self.prodObj.getProductConfig(productName,productType)
        if result[0]:
            return packageResponse(200,"success",result[1])
        else:
            return packageResponse(400,result[1],'')
        
        
    def post(self):
        result=self.prodObj.addNewProduct(self.data)
        if result[0]:
            return packageResponse(200,"success","")
        else:
            return packageResponse(400,result[1],"")

    def put(self):
        result=self.prodObj.updateProduct(self.data['product'],self.data['testType'],self.data['config'])
        if result[0]:
            return packageResponse(200,"success","")
        else:
            return packageResponse(400,result[1],"")
class TestObject(Resource):
    def __init__(self):
        self.parser=reqparse.RequestParser()
        self.parser.add_argument('session', type=str)
        self.resObj=TestResult()
    def get(self):
        args = self.parser.parse_args()
        data=self.resObj.getBhFromSession(args['session'])
        return packageResponse(200,"success",data)
class Result(Resource):
    def __init__(self):
        self.parser=reqparse.RequestParser()
        self.parser.add_argument('session', type=str)
        self.parser.add_argument('startDate', type=str)
        self.parser.add_argument('endDate', type=str)
        self.parser.add_argument('bh', type=str)
        self.parser.add_argument('product', type=str)
        self.parser.add_argument('testType', type=str)
        #self.parser=reqparse.RequestParser()
        self.resObj=TestResult()
    def get(self):
        args = self.parser.parse_args()
        if args['session']:
            result=self.resObj.getSessionResult(args['session'],args['bh'])
            return packageResponse(200, "success", result)
        else:
            endDate=datetime.now().strftime('%Y-%m-%d')
            #startDate=(date.today() + timedelta(days = -30)).strftime("%Y-%m-%d")
            startDate=endDate
            bh=''
            product=''
            testType=''
            print (args)
            if args['startDate'] and args['endDate']:
                startDate=args['startDate']
                endDate=args['endDate']
            if args['bh'] != 'all':
                bh=args['bh']
            if args['product'] != 'all':
                product=args['product']
            if args['testType'] != 'all':
                testType=args['testType']
            print (startDate,endDate,bh,product,testType)
            result=self.resObj.getResultFromCond(startDate,endDate,bh,testType,product,general=True)
            print (result)
            return packageResponse(200, "success", result)
            
            



class Running(Resource):
    def get(self):
        data={}
        if not libs.configGlobal.getDown():
            tc=TaskController()
            data['buf']=tc.buf
            data['info']={'running': 'Busy','test': '','temperature': str(tc.curTemperature),'current': ''}
            for item in tc.testsStatus:
                if item['status']==2:
                    data['info']['test']=item['item']
                    break
            data['status']=tc.testsStatus
        return packageResponse(200,"success",data)

        
 
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/download', methods=['GET'])
def download():
    fileEntry=request.args.get('fileEntry')
    directory="\\".join(fileEntry.split('\\')[0:-1])
    filename=fileEntry.split('\\')[-1]
    print (directory)
    response = make_response(send_from_directory(directory, filename, as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename.encode().decode('utf-8'))
    return response

@socketio.on('connect', namespace='/test')
def test_connect():
    #print ("connected")
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)

@socketio.on('message')
def handle_message(message):
    print ('message')
    socketio.send(message)
    # emit('my response')


def packageResponse(code,msg, data): 
    response={}
    response["code"]=code
    response["message"]=msg
    response["data"]=data
    return response         
api.add_resource(Login,'/login',endpoint='Login')
api.add_resource(Task,'/task',endpoint='Task')
api.add_resource(Running,'/running',endpoint='Running')
api.add_resource(Device,'/device',endpoint='Device')
api.add_resource(ProductConfig,'/product',endpoint='Product')
api.add_resource(Result,'/result',endpoint='Result')
api.add_resource(TestObject,'/bhs',endpoint='TestObject')
if __name__ == '__main__':
    app.debug=True
    socketio.run(app)
    #app.run(port=5000)
