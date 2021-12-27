import socket
import cv2
import pickle
import struct
import threading
from server.tcp.serverDataService import *
from server.detector.videoDetector import VideoDetector


class SocketHandler(object):
    def __init__(self, host_ip="localhost", host_port=00000):
        self.host_ip = host_ip
        self.host_port = host_port
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host_ip, self.host_port))
        self.socket.listen(10)
        self.create_connection()

    def create_connection(self):
        print("Server is listening on -> " + self.host_ip + ":" + str(self.host_port))
        while True:
            sock, address = self.socket.accept()
            self.connections.append(ConnectedClient(sock, address, True, self.connections))
            self.connections[len(self.connections) - 1].start()
            print("New Connection -> " + str(address))


class ConnectedClient(threading.Thread):
    def __init__(self, sock, address, connection_established=True, connections=None):
        threading.Thread.__init__(self)
        if connections is None:
            connections = []
        self.data = b""
        self.connections = connections
        self.payload_size = struct.calcsize(">L")
        self.socket = sock
        self.address = address
        self.connection_established = connection_established
        self.data_received = False
        self.client_address = ""

    def disconnect(self):
        print("Client with address: " + str(self.address) + " has disconnected")
        self.data_received = False
        if str(self.address) is not None:
            cv2.destroyWindow(str(self.address))
        camerasAddressees.remove(self.client_address)
        self.connection_established = False
        self.socket.close()
        print(camerasAddressees)

    @staticmethod
    def checkIfOpenCrossing(data):
        try:
            if data == "open":
                print("open")
            elif data == "close":
                print("close")
        except socket.error:
            print("cannot make action")

    def run(self):
        while self.connection_established:
            try:
                self.socket.send('elo'.encode("UTF-8"))
                if not self.data_received:
                    data = self.socket.recv(4096)
                    self.client_address = str(data).replace("b", "").replace("'", "")
                    camerasAddressees.append(self.client_address)
                    print(camerasAddressees)
                    self.data_received = True
                while len(self.data) < self.payload_size:
                    try:
                        self.data += self.socket.recv(4096)
                        self.checkIfOpenCrossing(self.data)
                    except socket.error:
                        self.disconnect()
                        self.connections.remove(self)
                        break
                packed_size = self.data[:self.payload_size]
                self.data = self.data[self.payload_size:]
                try:
                    data_size = struct.unpack(">L", packed_size)[0]
                except struct.error:
                    break
                while len(self.data) < data_size:
                    try:
                        self.data += self.socket.recv(4096)
                    except socket.error:
                        self.disconnect()
                        self.connections.remove(self)
                        break
                frameData = self.data[:data_size]
                self.data = self.data[data_size:]
                try:
                    frame = pickle.loads(frameData, fix_imports=True, encoding="bytes")
                except pickle.PickleError:
                    self.disconnect()
                    self.connections.remove(self)
                    break
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                try:
                    camerasLiveImages.remove(frame)
                except ValueError:
                    camerasLiveImages.append(frame)
                frame2 = VideoDetector(frame).getFrame()
                cv2.imshow(str(self.address), frame2)
                cv2.waitKey(1)
            except socket.error:
                self.disconnect()
                self.connections.remove(self)
                break
