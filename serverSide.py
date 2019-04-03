import socketserver, json, threading

mainRespond = """{
  "type": "mainRespond",
  "command": "mainCheck",
  "message": "OK"
}"""

class MyTCPRequestHandler(socketserver.StreamRequestHandler):
    #timeout = 3 # Время до отключения от клиента
    def handle(self):
        msg = self.request.recv(1024)
        c_str = msg.decode()
        p_f = json.loads(c_str)
        if p_f["type"] == "mainRequest":
            self.request.sendall(bytes(mainRespond, encoding='utf-8'))
        elif p_f["type"] == "portActivation":
            self.request.sendall(b'portActivation request recieved')

def my_server1():
    aServer = socketserver.TCPServer(("192.168.226.115", 8888), MyTCPRequestHandler)
    aServer.serve_forever()

def my_server2():
    aServer = socketserver.TCPServer(("localhost", 8888), MyTCPRequestHandler)
    aServer.serve_forever()

t1 = threading.Thread(target=my_server1)
t1.start()

t2 = threading.Thread(target=my_server2)
t2.start()

