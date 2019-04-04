import socketserver, json, threading, time, socket

# имя клиента
hostName = socket.gethostname()
# ip клиента
hostAddress = socket.gethostbyname(hostName)

mainRespond = """{
  "type": "mainRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

portListRespond = """{
  "type": "portListRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

activePortListRespond = """{
  "type": "activePortListRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

activePortRespond = """{
  "type": "activePortRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

class MyTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            msg = self.request.recv(1024)
            c_str = msg.decode()
            p_f = json.loads(c_str)
            print(p_f)
            if p_f["type"] == "mainRequest":
                self.request.sendall(bytes(mainRespond, encoding='utf-8'))
            elif p_f["type"] == "portList":
                self.request.sendall(bytes(portListRespond, encoding='utf-8'))
                print(p_f["ports"])
                for prt, number in p_f["ports"].items():
                    if number != []:
                        for n in number:
                            portThread = launchedPort(hostAddress, n, prt)
                            portThread.start()
                self.request.sendall(bytes(activePortListRespond, encoding='utf-8'))
                break

class launchedPort(threading.Thread):
    def __init__(self, host, port, protocol):
        self.host = hostAddress
        self.port = port
        self.protocol = protocol
        threading.Thread.__init__(self)
        self.setDaemon(False)
    def run(self):
        if self.protocol == "TCP":
            aServer = socketserver.TCPServer((self.host, self.port), mySecondaryTCPRequestHandler)
            print("PORT {} IS TCP UP".format(self.port))
            aServer.serve_forever()
        elif self.protocol == "UDP":
            aServer = socketserver.UDPServer((self.host, self.port), mySecondaryUDPRequestHandler)
            print("PORT {} IS UDP UP".format(self.port))
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
    time.sleep(30)
    print(threading.activeCount(), "ACTIVE THREADS")
