import socketserver, json, threading, time, socket

# имя клиента
hostName = socket.gethostname()
# ip клиента
hostAddress = socket.gethostbyname(hostName)

# Сервера проверяемых портов
serverDic = {}

# Ответ о проверкке порта 3242
mainRespond = """{
  "type": "mainRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

# Подтврждение закрытия порта 3242
closeRespond = """{
  "type": "closeRespond",
  "command": "mainCheck",
  "message": "CLOSED"
}"""

# Ответ о получении списка проверяемых портов
portListRespond = """{
  "type": "portListRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

# Ответ о запуске проверяемых портов
activePortListRespond = """{
  "type": "activePortListRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

# Ответ от проверяемого порта
activePortRespond = """{
  "type": "activePortRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

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
                pass
            else:
                # Проверка типа полученного запроса
                # ЗАПРОС - ОТВЕТ о проверке порта 3242
                if p_f["type"] == "mainRequest":
                    self.request.sendall(bytes(mainRespond, encoding='utf-8'))

                elif p_f["type"] == "closeRequest":
                    self.request.sendall(bytes(closeRespond, encoding='utf-8'))
                    break

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
                    break

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
        self.setDaemon(False)

    # Данная ф-ция описывает действия потока при его запуске (start())
    def run(self):
        global serverDic                                                # Словарь поднятых TCP UDP серверов для проверяемых портов (чтобы потом их положить)
        if self.protocol == "TCP":
            aServer = socketserver.TCPServer((self.host, self.port), mySecondaryTCPRequestHandler)
            serverDic[self.protocol, self.port] = aServer
            print("PORT {} IS TCP UP".format(self.port))
            print(serverDic)
            aServer.serve_forever()
        elif self.protocol == "UDP":
            aServer = socketserver.UDPServer((self.host, self.port), mySecondaryUDPRequestHandler)
            serverDic[self.protocol, self.port] = aServer
            print("PORT {} IS UDP UP".format(self.port))
            print(serverDic)
            aServer.serve_forever()

class mySecondaryTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        msg = self.request.recv(1024)
        c_str = msg.decode()
        p_f = json.loads(c_str)
        print(p_f, "TCP")
        self.request.sendall(bytes(activePortRespond, encoding='utf-8'))

class mySecondaryUDPRequestHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        msg = self.request[0].decode()
        socket = self.request[1]
        msg = json.loads(msg)
        print(msg, "UDP")
        socket.sendto(bytes(activePortRespond, encoding='utf-8'), self.client_address)

def my_server1():
    aServer = socketserver.TCPServer((hostAddress, 8888), MyTCPRequestHandler)
    aServer.serve_forever()

t1 = threading.Thread(target=my_server1)
t1.start()
print('SERVER IS LAUNCHED')

while True:
    time.sleep(5)
    print(threading.activeCount(), "ACTIVE THREADS")
    print(serverDic)
    for i in serverDic.values():
        i.shutdown()
        i.server_close()                # вызывается для очистки сервера (сокета, если конкретнее) (self.socket.close())
        print("DOOOWN B**CH")
    serverDic = {}
    print("I\'M CLEAN AND READY FOR WORK")
