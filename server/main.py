from server.tcp.serverSocketHandler import SocketHandler
import threading


def initSocket(APP_PORT):
    SocketHandler(host_ip=HOST, host_port=HOST_PORT, app_port=APP_PORT)


if __name__ == "__main__":
    HOST = "192.168.1.212"
    HOST_PORT = 10001
    APP_PORT = 8080
    threading.Thread(target=initSocket, args=[APP_PORT]).start()
