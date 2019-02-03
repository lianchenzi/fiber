"""
import mmap
import contextlib
import time
import threading
import configGlobal
class Mmaptest(object):
    def client(self):
        while True:
            with contextlib.closing(mmap.mmap(-1, 1024, tagname='test', access=mmap.ACCESS_READ)) as m:
                s = m.read(1024).translate(None, b'\x00').decode()  
                if configGlobal.getStop():
                    break
                if s.find('eof')>=0:
                    break
                print ("rcv:"+s)
            time.sleep(1)
class Server(object):
    def server (self):
        with contextlib.closing(mmap.mmap(-1, 1024, tagname='test', access=mmap.ACCESS_WRITE)) as m:
            for i in range(1, 1001):
                if configGlobal.getStop():
                    break
                m.seek(0)
                m.write(bytes("msg " + str(i),encoding='utf-8'))
                m.flush()
                time.sleep(1)
            m.seek(0)
            m.write("eof")
            m.flush()
            time.sleep(1)

mm=Mmaptest()
sv=Server()
threads = []
t1 = threading.Thread(target=sv.server)

threads.append(t1)
t2 = threading.Thread(target=mm.client)
threads.append(t2)
for t in threads:
    #t.setDaemon(True)
    t.start()
time.sleep(5)
"""