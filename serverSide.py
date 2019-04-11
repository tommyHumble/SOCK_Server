
import socketserver
import json
import threading
import time
import socket
import logging
import sys

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# ip клиента/сервера
hostAddress = get_ip()

# Настройка логгера
logger = logging.getLogger("Server_Side")
logger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler("server_logs.log")
fileFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s")
fileHandler.setFormatter(fileFormatter)
logger.addHandler(fileHandler)

# Список экземпляров потоков серверов запущенных на портах {(8080, "UDP"): Thread Obj, ...}
portThreadDic = {}

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

# список портов передаваемых от клиента для запуска на стороне сервера
portList = {
  "type": "portList",
  "command": "check",
  "ports": None,
  "client": hostAddress,
}

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
  "server": hostAddress,
  "ports": {
    "protocol": {
      "UDP": {},
      "TCP": {}
    }
  }
}
# reportRespond = json.dumps(reportRespond)

# Handler для обработки соедниений на порту 3242
class MyTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # Чтобы не разрывать соединение мы будем проверять получаемые сообщение в цикле,
        # выйдем из цикла и разорвем соединение по окончанию работы с клиентом
        logger.debug("TCP connection on 3242 with {} was established".format(self.client_address[0]))
        while True:
            try:
                rcv = self.request.recv(1024)           # получили сообщение
                if not rcv:
                    logger.debug("TCP connection on port 3242 with {} was completed".format(self.client_address[0]))
                    break
            except:
                logger.warning("TCP on port 3242 connection with {} was broken while recieving a message".format(self.client_address[0]))
                break
            logger.debug("message from {} was recieved".format(self.client_address[0]))

            try:
                msg = rcv.decode()                    # декодировали сообщение из b в str
                logger.debug("message from {} was decoded successfuly".format(self.client_address[0]))
                pyMsg = json.loads(msg)                 # преобразовали json строку в объект python

                if pyMsg["type"] == "mainRequest":
                    logger.debug("{} message was recieved form {}".format(pyMsg["type"], self.client_address[0]))
                    self.request.sendall(bytes(mainRespond, encoding='utf-8'))
                    logger.debug("mainRespond was sent to {}".format(self.client_address[0]))

                elif pyMsg["type"] == "reportRequest":
                    logger.debug("{} message was recieved from {}".format(pyMsg["type"], self.client_address[0]))
                    myReportRespond = json.dumps(reportRespond)
                    self.request.sendall(bytes(myReportRespond, encoding='utf-8'))
                    logger.debug("reportRespond was sent to {}".format(self.client_address[0]))

                elif pyMsg["type"] == "portList":
                    logger.debug("{} message was recieved from {}".format(pyMsg["type"], self.client_address[0]))
                    self.request.sendall(bytes(portListRespond, encoding='utf-8'))
                    logger.debug("portListRespond was sent to {}".format(self.client_address[0]))

                    # Проходим по словарю портов, которые необходимо поднять для проверки
                    for prt, number in pyMsg["ports"].items():
                        for n in number:
                            # создаем и запускаем сервер на каждом из портов в отедьном потоке, если такого сервера еще нет
                            if (n, prt) in portThreadDic.keys():
                                logger.debug("{} server on {} is already launched".format(prt, n))
                            else:
                                portThread = launchedPort(hostAddress, n, prt)
                                portThreadDic[n, prt] = portThread
                                portThread.start()
                                logger.debug("{} on port {} serve_forever is launched".format(prt, n))

                    # ОТВЕТ о запуске всех портов (готов к проверке)
                    self.request.sendall(bytes(activePortListRespond, encoding='utf-8')) # нужна ли проверка ?
                    #break

            except UnicodeDecodeError:
                logger.warning("message from {} wasn't decoded".format(self.client_address[0]))
                break
            except json.decoder.JSONDecodeError:
                logger.warning("message form {} wasn't decoded from json format".format(self.client_address[0]))
                break
            except InterruptedError:
                logger.warning("failed to send respond to {} on {}".format(self.client_address[0], pyMsg["type"]))
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
        self.setDaemon(True)
        try:
            if self.protocol == "TCP":
                self.server = socketserver.TCPServer((self.host, self.port), mySecondaryTCPRequestHandler)
                logger.debug("{}_TCP_{} SocketServer was created".format(self.host, self.port))
            elif self.protocol == "UDP":
                self.server = socketserver.UDPServer((self.host, self.port), mySecondaryUDPRequestHandler)
                logger.debug("{}_UDP_{} SocketServer was created".format(self.host, self.port))
        except:
            logger.debug("{}_{}_{} SocketServer wasn\'t created".format(self.host, self.protocol, self.port))

    # Данная ф-ция описывает действия потока при его запуске (start())
    def run(self):
        try:
            reportRespond["ports"]["protocol"][self.protocol][self.port] = "UP"
            self.server.serve_forever()
        except:
            logger.error("{} on port {} serve_forever error ".format(self.protocol, self.port))

    def stop_server(self):
        try:
            self.server.shutdown()
            self.server.server_close()
            logger.debug("{} server on {} port was closed".format(self.protocol, self.port))
        except:
            logger.warning("{} server on {} port couldn\'t be closed correctly".format(self.protocol, self.port))



class mySecondaryTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            rcv = self.request.recv(1024)
            print(self.server)
            logger.debug("simpleRequest from {} was recieved".format(self.client_address[0]))
            msg = rcv.decode()
            logger.debug("simpleRequest from {} was decoded".format(self.client_address[0]))
            pyMsg = json.loads(msg)
            logger.debug("simpleRequest from {} was decoded in json format".format(self.client_address[0]))
            mySimpleRespond = simpleRespond.copy()
            mySimpleRespond["protocol"] = pyMsg["protocol"]
            mySimpleRespond["port"] = pyMsg["port"]
            mySimpleRespond = json.dumps(mySimpleRespond)
            self.request.sendall(bytes(mySimpleRespond, encoding='utf-8'))
            logger.debug("simpleRespond was sent to {}".format(self.client_address[0]))
        except UnicodeDecodeError:
            logger.warning("simpleRequest from {} wasn't decoded".format(self.client_address[0]))
        except json.decoder.JSONDecodeError:
            logger.warning("simpleRequest form {} wasn't decoded from json format".format(self.client_address[0]))
        except InterruptedError:
            logger.warning("failed to send\/recieve message to\/from {} on TCP {}".format(self.client_address[0], pyMsg["port"]))

class mySecondaryUDPRequestHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        try:
            rcv = self.request[0]
            logger.debug("simpleRequest from {} was recieved".format(self.client_address[0]))
            msg = rcv.decode()
            logger.debug("simpleRequest from {} was decoded".format(self.client_address[0]))
            socket = self.request[1]
            pyMsg = json.loads(msg)
            mySimpleRespond = simpleRespond.copy()
            mySimpleRespond["protocol"] = pyMsg["protocol"]
            mySimpleRespond["port"] = pyMsg["port"]
            mySimpleRespond = json.dumps(mySimpleRespond)
            socket.sendto(bytes(mySimpleRespond, encoding='utf-8'), self.client_address)
            logger.debug("simpleRespond was sent to {}".format(self.client_address[0]))
        except UnicodeDecodeError:
            logger.warning("simpleRequest from {} wasn't decoded".format(self.client_address[0]))
        except json.decoder.JSONDecodeError:
            logger.warning("simpleRequest form {} wasn't decoded from json format".format(self.client_address[0]))
        except InterruptedError:
            logger.warning("failed to send\/recieve message to\/from {} on UDP {}".format(self.client_address[0], pyMsg["port"]))

# в виде класса
class main_thread(threading.Thread):
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        threading.Thread.__init__(self)
        try:
            self.server = socketserver.TCPServer((self.addr, port), MyTCPRequestHandler)
            logger.debug("{}_{}_{} SocketServer was created".format(self.addr, "TCP", self.port))
        except:
            logger.debug("{}_{}_{} SocketServer wasn\'t created".format(self.addr, "TCP", self.port))
    def run(self):
        try:
            self.server.serve_forever()
        except:
            logger.error("SocketServer on port {} serve_forever error ".format(self.port))
    def stop_server(self):
        try:
            self.server.shutdown()
            self.server.server_close()
            logger.debug("SocketServer on {} port was closed".format(self.port))
        except:
            logger.warning("SocketServer on {} port couldn\'t be closed correctly".format(self.port))

mainThread = main_thread(hostAddress, 3242)
mainThread.start()
logger.debug("SocketServer on port {} serve_forever is launched".format(3242))

while True:
    try:
        print(threading.activeCount(), "ACTIVE THREADS")
        print(portThreadDic)
        time.sleep(60)
        #print(serverDic)
    except KeyboardInterrupt:
        mainThread.stop_server()
        break

    # for i in serverDic.values():
    #     i.shutdown()
    #     i.server_close()                # вызывается для очистки сервера (сокета, если конкретнее) (self.socket.close())
    #     print("DOOOWN B**CH")
    # serverDic = {}
    # print("I\'M CLEAN AND READY FOR WORK")
