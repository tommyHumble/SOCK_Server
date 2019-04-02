import socket, json

HOST = "192.168.226.115"
PORT = 8880

for i in range(10):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        sock.connect((HOST, PORT))
        sock.send(bytes('Yo! It\'s TCP request message from {}. We need answer about port {}!'.format(HOST, PORT + i), encoding='utf-8'))
        received = sock.recv(1024).decode()
        print("{}".format(received))
