import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(10):
    sock.sendto(bytes('IT\'S UDP REQUEST FROM {}, I NEED A RESPOND ABOUT PORT {}'.format('192.168.226.115', 8880 + i ), encoding='utf-8'), ("192.168.226.115", 8880 + i))
    print(sock.recv(1024).decode())
