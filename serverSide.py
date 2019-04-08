import socketserver, json, threading, time, socket

# имя клиента
hostName = socket.gethostname()
# ip клиента
hostAddress = socket.gethostbyname(hostName)
hostAddress = "192.168.226.115"
print(hostAddress)

# Сервера проверяемых портов
serverDic = {}

# Сервер отвечающий за TCP соединение по 3242 (главный поток после MAIN)
mainServer = None

# список портов и их статусов
portStatus = {
    "TCP": {},
    "UDP": {}
}

# запрос на проверку порта 3242 (string)
mainRequest = {
  "type": "mainRequest",
  "command": "mainCheck",
  "message": "PORT 3242 STATUS",
  "client": hostAddress
}
mainRequest = json.dumps(mainRequest)

# Ответ о проверкке порта 3242
mainRespond = {
  "type": "mainRespond",
  "command": "mainCheck",
  "message": "OK",
  "server": hostAddress
}
mainRespond = json.dumps(mainRespond)

# Ответ о получении списка проверяемых портов
portListRespond = {
  "type": "portListRespond",
  "command": "mainCheck",
  "message": "OK",
  "server": hostAddress
}
portListRespond = json.dumps(portListRespond)

# Ответ о запуске проверяемых портов
activePortListRespond = {
  "type": "activePortListRespond",
  "command": "mainCheck",
  "message": "OK",
  "server": hostAddress
}
activePortListRespond = json.dumps(activePortListRespond)

# запрос на проверку порта по TCP или UDP
simpleRequest = {
  "type": "request",
  "command": "check",
  "message": "PORT STATUS",
  "client": hostAddress,
  "protocol": None,
  "port": None
}
#simpleRequest = json.dumps(simpleRequest)

# Ответ от проверяемого порта
simpleRespond = {
  "type": "simpleRespond",
  "command": "mainCheck",
  "message": "OK",
  "server": hostAddress,
  "protocol": None,
  "port": None
}
#simpleRespond = json.dumps(simpleRespond)

# Запрос отчета о выполнении полного цикла проверок на сервер
reportRequest = {
  "type": "reportRequest",
  "message": "NEED REPORT",
  "client": hostAddress
}
reportRequest = json.dumps(reportRequest)

reportRespond = {
  "type": "reportRespond",
  "message": "REPORT",
  "server": hostAddress
}
reportRespond = json.dumps(reportRespond)

# Handler для обработки соедниений на порту 3242
class MyTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # Чтобы не разрывать соединение мы будем проверять получаемые сообщение в цикле,
        # выйдем из цикла и разорвем соединение по окончанию работы с клиентом
        while True:
            try:
                msg = self.request.recv(1024)           # получили сообщение
                c_str = msg.decode()                    # декодировали сообщение из b в str
                p_f = json.loads(c_str)                 # преобразовали json строку в объект python
                print(p_f)
            except:
                break
                pass
            else:
                # Проверка типа полученного запроса
                # ЗАПРОС - ОТВЕТ о проверке порта 3242
                if p_f["type"] == "mainRequest":
                    self.request.sendall(bytes(mainRespond, encoding='utf-8'))

                elif p_f["type"] == "reportRequest":
                    self.request.sendall(bytes(reportRespond, encoding='utf-8'))

                # ЗАПРОС - ОТВЕТ о получении списка проверяемых портов
                elif p_f["type"] == "portList":
                    self.request.sendall(bytes(portListRespond, encoding='utf-8'))
                    print(p_f["ports"])

                    # Проходим по словарю портов, которые необходимо поднять для проверки
                    for prt, number in p_f["ports"].items():
                        if number != []:
                            for n in number:
                                # создаем и запускаем сервер на каждом из портов в отедьном потоке
                                portThread = launchedPort(hostAddress, n, prt)
                                portThread.start()

                    # ОТВЕТ о запуске всех портов (готов к проверке)
                    self.request.sendall(bytes(activePortListRespond, encoding='utf-8'))
                    #break

# Класс - поток проверяемого порта. Экземплярами данного класаа являются
# сервера TCP UDP поднятые на провереяемых портах
class launchedPort(threading.Thread):
    # передаем ip адресс нашего сервера (на котором заупстим сервер)
    # порт (для которого запустим сервер)
    # протокол транспортного уровня, по которому будет работать сервер (TCP или UDP)
    def __init__(self, host, port, protocol):
        self.host = hostAddress
        self.port = port
        self.protocol = protocol
        threading.Thread.__init__(self)
        self.setDaemon(True)

    # Данная ф-ция описывает действия потока при его запуске (start())
    def run(self):
        global serverDic                                                # Словарь поднятых TCP UDP серверов для проверяемых портов (чтобы потом их положить)
        if self.protocol == "TCP":
            try:
                aServer = socketserver.TCPServer((self.host, self.port), mySecondaryTCPRequestHandler)
                serverDic[self.protocol, self.port] = aServer
                print("PORT {} IS TCP UP".format(self.port))
                print(serverDic)
                aServer.serve_forever()
            except:
                print(self.port, self.protocol, "is already opened")
        elif self.protocol == "UDP":
            try:
                aServer = socketserver.UDPServer((self.host, self.port), mySecondaryUDPRequestHandler)
                serverDic[self.protocol, self.port] = aServer
                print("PORT {} IS UDP UP".format(self.port))
                print(serverDic)
                aServer.serve_forever()
            except:
                print(self.port, self.protocol, "is already opened")

class mySecondaryTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        msg = self.request.recv(1024)
        c_str = msg.decode()
        p_f = json.loads(c_str)
        print(p_f)
        mySimpleRespond = simpleRespond.copy()
        mySimpleRespond["protocol"] = "TCP"
        mySimpleRespond["port"] = "AZAZA"
        mySimpleRespond = json.dumps(mySimpleRespond)
        self.request.sendall(bytes(mySimpleRespond, encoding='utf-8'))

class mySecondaryUDPRequestHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        msg = self.request[0].decode()
        socket = self.request[1]
        msg = json.loads(msg)
        print(msg)
        mySimpleRespond = simpleRespond.copy()
        mySimpleRespond["protocol"] = "UDP"
        mySimpleRespond["port"] = "AZAZA"
        mySimpleRespond = json.dumps(mySimpleRespond)
        socket.sendto(bytes(mySimpleRespond, encoding='utf-8'), self.client_address)

def my_server1():
    global mainServer
    mainServer= socketserver.TCPServer((hostAddress, 3242), MyTCPRequestHandler)
    mainServer.serve_forever()
    print("SERVER ON 3242 IS CLOSED")

mainThread = threading.Thread(target=my_server1)
mainThread.start()
print('SERVER IS LAUNCHED')

while True:
    try:
        time.sleep(5)
        print(threading.activeCount(), "ACTIVE THREADS")
        print(serverDic)
    except KeyboardInterrupt:
        mainServer.shutdown()
        mainServer.server_close()
        break

exit(code="SERVER IS STOPPED")
    # for i in serverDic.values():
    #     i.shutdown()
    #     i.server_close()                # вызывается для очистки сервера (сокета, если конкретнее) (self.socket.close())
    #     print("DOOOWN B**CH")
    # serverDic = {}
    # print("I\'M CLEAN AND READY FOR WORK")
