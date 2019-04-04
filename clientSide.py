import socketserver, json, threading, socket, sys, time

# имя клиента
hostName = socket.gethostname()

# ip клиента
hostAddress = socket.gethostbyname(hostName)

# запрос на проверку порта 3242 (string)
mainRequest = """{
  "type": "mainRequest",
  "command": "mainCheck",
  "message": "PORT 3242 STATUS"
}"""

# запрос на закрытие соединения по порту 3242 (string)
closeRequest = """{
  "type": "closeRequest",
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
    serverDic = json.load(f_r)

# Список всех организуемых потоков (столько же, сколько проверяемых серверов)
checkList = []

# Словарь проверяемых серверов (адрес хоста и статус порта 3242)
mainCheckList = []

# Класс - поток. Экземплярами данного класса являются
# клиентские сокеты, через которые проходит соединение с сервером
# каждый сокет (порт) в отдельном потоке
class myThread(threading.Thread):
    # передаем ip хоста (клиентской машины)
    # порт на котором хотим организовать сокет
    # и словарь портов, которые сервер должен будет поднять на своей стороне
    def __init__(self, host, port, portCheck):
        self.host = host
        self.port = port
        self.portCheck = portCheck
        threading.Thread.__init__(self)

    # Данная ф-ция описывает, что будет происходить при запуске потока (start())
    def run(self):
        global mainCheckList                                                # список всех серверов и статус порта 3242
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            # создаем сокет
        try:
            sock.settimeout(1)                                              # сокращаем время на установление соединения с сервером
            print("trying to connect", self.host)
            sock.connect((self.host, self.port))                            # Устанавливаем соединение с сервером на порту 3242
            print("connected", self.host)
        except:
            mainCheckList.append('KEK')                                     # Если не удалось установить соединение с сервером, то в список мы добавляем блокирующее значение, которое говорит, что можно закругляться
            print(self.host, "HERE SOME PROBLEM")
            return 0                                                        # Выходим из ф-ции тем самым прерывая поток
        else:
            sock.sendall(bytes(mainRequest, encoding='utf-8'))              # Если соединение установлено, нужно отправить запрос на подтверждение установки соединения
            rcv = sock.recv(1024).decode()                                  # Получаем ответ на запрос, что подверждает, что соединение по 3242 установлено
            mainCheckList.append([self.host, "UP"])                         # По получении ответа Добавляем в контрольный список инфу, что на этом хосте порт 3242 работает четко
            print(rcv)

        # проверяем список, всех ли мы опросили и все ли порты доступны
        # если нет, то говорим, что на каком-то порту проблемы и завершаем процесс
        while True:
            if len(mainCheckList) == len(serverDic):
                if "KEK" in mainCheckList:
                    print("SOME SERVER IS NOT UP")
                    sock.sendall(bytes(closeRequest, encoding='utf-8'))     # Т.к. соединение установлено, но мы в нем не нуждаемся, мы отправляем запрос о закрытии соединения с сервером
                    rcv = sock.recv(1024).decode()                          # Получили подврждение, что соединение сейчас закроется
                    print(rcv)
                    return                                                  # Завершаем ф-цию и поток вместе с ней
                else:
                    print("ALL SERVERS ARE UP")
                    break

        # формируем список портов, которые сервер должен будет поднять на своей стороне
        portList = {
            "type": "portList",
            "command": "check",
            "ports": self.portCheck
            }
        portList = json.dumps(portList)
        sock.sendall(bytes(portList, encoding="utf-8"))                     # отправляем список
        recv = sock.recv(1024).decode()                                     # получили подверждение, что список был получен
        print(recv)
        recv = sock.recv(1024).decode()                                     # получили подтверждение того, что все порты подняты и готовы к дальнейшему опросу
        print(recv)

        # получив подтверждение, начинаем опрашивать поочередно наши порты
        # с помощью with открываем соединение, ЗАПРОС - ОТВЕТ, закрываем соединение
        for prt, number in self.portCheck.items():
                    # [] - в случае если по данному протоколу не нужно поднимать никакого порта
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

# Создаем потоки, в вкоторых будет происходить проверка порта 3242
# и дальнейшая проверка других портов, если все сервера доступны на 3242
for srv in serverDic:
    thread = myThread(srv["host"], 8888, srv["ports"])
    checkList.append(thread)
    thread.start()
    print("THREAD GO GO GO GO")

print(checkList)            # список потоков в которыъ проверяются все сервера = колич-во серверов в json файле
print(mainCheckList)        # список всех серверов + статус порта 3242 + ключ о дальнейшей проверки

# Проверка завершения всех вызванных потоков
for srv in checkList:
    print(srv.getName())
    print(srv.isAlive())
    if srv.isAlive():
        srv.join()
        print('STOPPED')
    else:
        print("ALREADY STOPPED")

print("FIN")
