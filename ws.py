#!-*- coding:utf-8 -*-
import time
import random
from threading import Lock
import threading
from flask_socketio import SocketIO,send, emit
from flask import Flask,current_app,render_template,make_response,request
from functools import wraps
from flask_cors import CORS
from flask_restful import Api,Resource,reqparse, abort,marshal
from taskController import TaskController
import configGlobal
from dbHandle import DbHandle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=None)
thread = None
thread_lock = Lock()
app.config.update(RESTFUL_JSON=dict(ensure_ascii=False),SECRET_KEY='secretadsfasdfa')
CORS(app, supports_credentials=True)
api = Api(app)
 
# 后台线程 产生数据，即刻推送至前端
def background_thread():
    while True:
        socketio.sleep(5)
        if not configGlobal.getDown():
            tc=TaskController()
            #print (tc.testsStatus)
            socketio.emit('updateStatus',
                            tc.testsStatus,
                            namespace='/test')
            if tc.buf and 'buf' in tc.buf and tc.buf['buf']:
                print (tc.buf)
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
class Task(Resource):
    def __init__(self):
        self.data=request.get_json()
    def post(self):
        #print(self.data)
        tc=TaskController(self.data)
        parseReslt=tc.parseTask()
        print (parseReslt)
        if not parseReslt[0]:
            return packageResponse(401,parseReslt[1],"")
        t=threading.Thread(target=tc.runTests)
        t.setDaemon(False)
        t.start()
        return packageResponse(200,"success","")
class Running(Resource):
    def get(self):
        data={}
        if not configGlobal.getDown():
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
if __name__ == '__main__':
    #app.debug=True
    socketio.run(app)
    #app.run(port=5000)
