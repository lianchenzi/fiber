import sqlite3
import os
class DbHandle(object):
    def __init__(self):
        dbPath=os.path.join(os.getcwd(),os.path.join('data',"result.db"))
        self.conn = sqlite3.connect(dbPath)
        self.cursor = self.conn.cursor()
    def createUserTable(self):
        sql="drop table if exists user"
        self.cursor.execute(sql)
        sql="""
            create table if not exists user(
                id integer primary key AUTOINCREMENT,
                username varchar(20),
                password varchar(20),
                auth integer
            )
        """
        self.cursor.execute(sql)
        self.conn.commit()
    def createWxTable(self):
        sql="drop table if exists wx"
        self.cursor.execute(sql)
        sql="""
            create table if not exists wx(
                id integer primary key AUTOINCREMENT,
                wx_type varchar(20)
            )
        """
        self.cursor.execute(sql)
        self.conn.commit()
    def addUser(self,username, password,auth):
        sql="""
        insert into user (username,password,auth) values (\'%s\',\'%s\',%d)
        """ %(username,password,auth)
        print (sql)
        self.cursor.execute(sql)
        self.conn.commit()
    def addWx(self,wx):
        sql="""
        insert into wx (wx_type) values (\'%s\')
        """ %(wx)
        self.cursor.execute(sql)
        self.conn.commit()
    def createTables(self):
        sql="drop table if exists lp"
        self.cursor.execute(sql)
        sql="""
            create table if not exists lp(
                id integer primary key AUTOINCREMENT,
                product varchar(20),
                test_date date,
                temperature integer,
                test_type text,
                bh varchar(20),
                lp text,
                lp_wdx text,
                data_file varchar(100)
            )
        """
        self.cursor.execute(sql)
        sql="drop table if exists lp_cfx"
        self.cursor.execute(sql)
        sql="""
            create table if not exists lp_cfx(
                id integer primary key AUTOINCREMENT,
                product varchar(20),
                test_date date,
                temperature integer,
                test_type text,
                bh varchar(20),
                lp_cfx text,
                data_file varchar(100)
            )
        """
        self.cursor.execute(sql)
        sql="drop table if exists bdys"
        self.cursor.execute(sql)
        sql="""
            create table if not exists bdys(
                id integer primary key AUTOINCREMENT,
                product varchar(20),
                test_date date,
                temperature integer,
                test_type text,
                bh varchar(20),
                bdys text,
                bdys_xxd text,
                data_file varchar(100)
            )
        """
        self.cursor.execute(sql)
        sql="drop table if exists bdys_cfx"
        self.cursor.execute(sql)
        sql="""
            create table if not exists bdys_cfx(
                id integer primary key AUTOINCREMENT,
                product varchar(20),
                test_date date,
                temperature integer,
                test_type text,
                bh varchar(20),
                bdys text,
                bdys_xxd text,
                data_file varchar(100)
            )
        """
        self.cursor.execute(sql)
        self.conn.commit()
    def insert_lp(self,product,date,temperature,test_type,bh,lp,lp_wdx,data_file,session):
        sql="""
        insert into lp (product,test_date,temperature,test_type,bh,lp,lp_wdx,data_file,session) values (\'%s\',\'%s\',%d,\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
        """ %(product,date,temperature,test_type,bh,self.asNum(lp),self.asNum(lp_wdx),data_file,session)
        print (sql)
        self.cursor.execute(sql)
        self.conn.commit()
    def insert_lp_cfx(self,product,date,temperature,test_type,bh,lp_cfx,data_file,session):
        sql="""
        insert into lp_cfx (product,test_date,temperature,test_type,bh,lp_cfx,data_file,session) values (\'%s\',\'%s\',%d,\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
        """ %(product,date,temperature,test_type,bh,self.asNum(lp_cfx),data_file,session)
        print (sql)
        self.cursor.execute(sql)
        self.conn.commit()
    def insert_bdys(self,product,date,temperature,test_type,bh,bdys,bdys_xxd,data_file,session):
        sql="""
        insert into bdys (product,test_date,temperature,test_type,bh,bdys,bdys_xxd,data_file,session) values (\'%s\',\'%s\',%d,\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
        """ %(product,date,temperature,test_type,bh,self.asNum(bdys),self.asNum(bdys_xxd),data_file,session)
        print (sql)
        self.cursor.execute(sql)  
        self.conn.commit()
    def insert_bdys_cfx(self,product,date,temperature,test_type,bh,bdys,bdys_xxd,data_file,session):
        sql="""
        insert into bdys_cfx (product,test_date,temperature,test_type,bh,bdys,bdys_xxd,data_file,session) values (\'%s\',\'%s\',%d,\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
        """ %(product,date,temperature,test_type,bh,self.asNum(bdys),self.asNum(bdys_xxd),data_file,session)
        print (sql)
        self.cursor.execute(sql)  
        self.conn.commit()
    def insertSession(self,sessionId,product,bh,testSettings,testType,testDate):
        initStatus=0
        sql="""
        insert into session (sessionId,status,product,bh,testSettings,testType,testDate) values (\'%s\',%d,\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
        """%(sessionId,initStatus,product,bh,testSettings,testType,testDate)
        self.cursor.execute(sql)  
        self.conn.commit()
    def updateSession(self,sessionId):
        sql="""
        update session set status=1 where sessionId=\'%s\'
        """%(sessionId)
        self.cursor.execute(sql)  
        self.conn.commit()
    def updateTable(self, table, updateValue, cond):
        sql="update " +table+ " set " +updateValue
        if cond:
            sql+=" where " + cond
        print (sql)
        self.cursor.execute(sql)  
        self.conn.commit()       

    def getSessionId(self,sessionId):
        sql="""
        select * from session where sessionId=\'%s\'
        """%(sessionId)
        return self.search(sql)
    def deleteInvalidDataFile(self,table,sessions):
        sql="select data_file from "+table+" where session in ("+sessions+")"
        result=self.search(sql)
        if result:
            for item in result:
                if os.path.exists(item[0]) and os.path.isfile(item[0]):
                    os.remove(item[0])
    def deleteInvalidSession(self):
        sql="""
        select sessionId from session where status=0
        """
        result=self.search(sql)
        print (result)
        if result:
            invalSessionsStr='\''+result[0][0]+'\''
            for i in range(1,len(result)):
                invalSessionsStr+=',\''+result[i][0]+'\''
            self.deleteInvalidDataFile('lp',invalSessionsStr)
            sql="delete from lp where session in ("+invalSessionsStr+")"
            self.cursor.execute(sql) 
            self.deleteInvalidDataFile('lp_cfx',invalSessionsStr)
            sql="delete from lp_cfx where session in ("+invalSessionsStr+")"
            self.cursor.execute(sql) 
            self.deleteInvalidDataFile('bdys',invalSessionsStr)
            sql="delete from bdys where session in ("+invalSessionsStr+")"
            self.cursor.execute(sql) 
            self.deleteInvalidDataFile('bdys_cfx',invalSessionsStr)
            sql="delete from bdys_cfx where session in ("+invalSessionsStr+")"
            self.cursor.execute(sql) 
            sql="delete from session where sessionId in ("+invalSessionsStr+")"
            self.cursor.execute(sql) 
            self.conn.commit()
    def search(self,sql):
        self.cursor.execute(sql)
        values=self.cursor.fetchall()
        return values
    def searchOne(self,sql):
        print (sql)
        self.cursor.execute(sql)
        values=self.search(sql)
        if values:
            return values[0]
        else:
            return None
    def verifyUser(self,username,password):
        sql= "select * from user where username =\'"+username+"\' and password=\'"+password+"\'"
        result=self.search(sql)
        if result:
            return True, list(result[0])
        return False,[] 
    def getWx(self):
        sql="select wx_type from wx"
        result=self.search(sql)
        return list(result[0])

    def asNum(self,x):
        y = '{:.20f}'.format(x)
        return str(y)

    def __del__(self):
        self.cursor.close()
        self.conn.close()
"""
db=DbHandle()
db.createTables()
del db


db=DbHandle()
db.deleteInvalidSession()

#print(db.getWx())
#db.addUser('admin','admin',1)
#db.createWxTable()
#db.addWx('Rs232')
#print (db.verifyUser('admin','admin'))
"""