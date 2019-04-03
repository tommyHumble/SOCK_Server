import socketserver, json, threading, socket, sys, time

# имя клиента
hostName = socket.gethostname()
# ip клиента
hostAddress = socket.gethostbyname(hostName)
# флаг для завершения всех потоков
threadFlag = True
# запрос на проверку порта 3242
mainRequest = """{
  "type": "mainRequest",
  "command": "mainCheck",
  "message": "PORT 3242 STATUS"
}"""
# запрос на проверку оставшихся портов
simpleRequest = {
  "type": "request",
  "command": "check",
  "message": "PORT {} STATUS"
}
# Считывание json файла со списком серверов
serverListFileName = sys.argv[1]
with open(serverListFileName, 'r') as f_r:
    serverList = json.load(f_r)
# Список потоков (проверяемых серверов)
checkList = []

# Класс поток, который осуществляет проверку серверов
class myThread(threading.Thread):
    def __init__(self, host, port):
        self.host = host
        self.port = port
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


for srv in serverList:
    thread = myThread(srv["host"], 8888)
    checkList.append(thread)
    thread.start()

print(checkList)

# Ждем закрытия всех потоков для правильного завершения программы
for srv in checkList:
    print(srv.getName())
    print(srv.isAlive())
    if srv.isAlive():
        srv.join()
        print('STOPPED')
    else:
        print("ALREADY STOPPED")
exit(0)
