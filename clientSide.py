import socketserver, json, threading, socket, sys, time

# имя клиента
hostName = socket.gethostname()

# ip клиента
hostAddress = socket.gethostbyname(hostName)

# флаг для завершения всех потоков
threadFlag = True

# запрос на проверку порта 3242 (string)
mainRequest = """{
  "type": "mainRequest",
  "command": "mainCheck",
  "message": "PORT 3242 STATUS"
}"""

# запрос на проверку оставшихся портов (py obj)
simpleRequest = '''{
  "type": "request",
  "command": "check",
  "message": "PORT STATUS"
}'''

# Считывание json файла со списком серверов
serverListFileName = sys.argv[1]
with open(serverListFileName, 'r') as f_r:
    serverList = json.load(f_r)
    
# Список потоков (проверяемых серверов)
checkList = []

# Класс поток, который осуществляет проверку серверов
class myThread(threading.Thread):
    def __init__(self, host, port, portCheck):
        self.host = host
        self.port = port
        self.portCheck = portCheck
        threading.Thread.__init__(self)
    def run(self):
        global threadFlag
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if threadFlag:
            try:
                sock.connect((self.host, self.port))
            except:
                threadFlag = False
                return 0
            else:
                sock.sendall(bytes(mainRequest, encoding='utf-8'))
                rcv = sock.recv(1024).decode()
                print(rcv)
        else:
            return 0

        portList = {
            "type": "portList",
            "command": "check",
            "ports": self.portCheck
            }
        portList = json.dumps(portList)
        sock.sendall(bytes(portList, encoding="utf-8"))
        recv = sock.recv(1024).decode()
        print(recv)
        recv = sock.recv(1024).decode()
        print(recv)

        for prt, number in self.portCheck.items():
                    if number != []:
                        if prt == "TCP":
                            for n in number:
                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as prtSock:
                                    prtSock.connect((self.host, n))
                                    prtSock.sendall(bytes(simpleRequest, encoding='utf-8'))
                                    rcv = prtSock.recv(1024).decode()
                                    print(rcv)
                        elif prt == "UDP":
                            for n in number:
                                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as prtSock:
                                    prtSock.sendto(bytes(simpleRequest, encoding = "utf-8"), (self.host, n))
                                    rcv = prtSock.recv(1024).decode()
                                    print(rcv)

for srv in serverList:
    thread = myThread(srv["host"], 8888, srv["ports"])
    checkList.append(thread)
    thread.start()

time.sleep(1)
print(checkList)

for srv in checkList:
    print(srv.getName())
    print(srv.isAlive())
    if srv.isAlive():
        srv.join()
        print('STOPPED')
    else:
        print("ALREADY STOPPED")
exit(0)
