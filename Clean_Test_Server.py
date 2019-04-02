import socketserver, json, threading, socket

# имя сервера
hostName = socket.gethostname()
# ip сервера
hostAddress = socket.gethostbyname(hostName)

# хэндлер для TCP соединений
class MyTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        #print(threading.activeCount()) # количество активных потоков
        #print(threading.current_thread()) # полное название текущего потока
        #print(threading.current_thread().isDaemon()) #
        f_msg = ""
        while True:
            msg = self.request.recv(1024)
            f_msg += msg.decode()
            if len(msg) < 1024:
                print(f_msg)
                break
        self.request.sendall(bytes('Yo! It\'s respond message from {}. Port {} is up TCP!', encoding="utf-8"))

# хэндлер для UDP соединений
class MyUDPRequestHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        msg = self.request[0].decode()
        socket = self.request[1]
        print(msg)
        socket.sendto(bytes('Yo! It\'s respond message from {}. Port {} is up UDP!', encoding="utf-8"), self.client_address)

# обхект поток (поднятие сервера TCP или UDP)
class threadingServerUp(threading.Thread):
    def __init__(self, host, port, protocol):
        self.host = host
        self.port = port
        self.protocol = protocol
        threading.Thread.__init__(self)
    def run(self):
        print('start server', self.host, self.port)
        if self.protocol== "TCP":
            myServer = socketserver.TCPServer((self.host, self.port), MyTCPRequestHandler)
            myServer.serve_forever()
        elif self.protocol == "UDP":
            myServer = socketserver.UDPServer((self.host, self.port), MyUDPRequestHandler)
            myServer.serve_forever()

print('asd')
for i in range(10):
    thread = threadingServerUp("192.168.226.115", 8880 + i, "UDP")
    thread.start()


for j in range(10):
    thread = threadingServerUp("192.168.226.115", 8880 + j, "TCP")
    thread.start()

