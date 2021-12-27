from server.tcp.serverSocketHandler import SocketHandler

if __name__ == "__main__":
    HOST = "192.168.1.212"
    HOST_PORT = 10001
    SocketHandler(host_ip=HOST, host_port=HOST_PORT)
