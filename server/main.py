from server.tcp.serverSocketHandler import SocketHandler
from server.app.appInit import appInit

if __name__ == "__main__":
    HOST = "192.168.1.212"
    HOST_PORT = 10001
    APP_PORT = 8080
    SocketHandler(host_ip=HOST, host_port=HOST_PORT).start()
    appInit(host_ip=HOST, host_port=APP_PORT).start()


