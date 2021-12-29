import socket

import cv2
import pickle
import struct
import threading
from time import sleep
from server.tcp.serverDataService import *
from server.app.appInit import appInit
from server.detector.videoDetector import VideoDetector
import uuid
import numpy as np
import os
from datetime import datetime
import pathlib


def initApp(HOST, APP_PORT):
    appInit(host_ip=HOST, host_port=APP_PORT)


# github method
def simplest_cb2(img, percent=1):
    out_channels = []
    cumstops = (
        img.shape[0] * img.shape[1] * percent / 200.0,
        img.shape[0] * img.shape[1] * (1 - percent / 200.0)
    )
    for channel in cv2.split(img):
        cumhist = np.cumsum(cv2.calcHist([channel], [0], None, [256], (0, 256)))
        low_cut, high_cut = np.searchsorted(cumhist, cumstops)
        lut = np.concatenate((
            np.zeros(low_cut),
            np.around(np.linspace(0, 255, high_cut - low_cut + 1)),
            255 * np.ones(255 - high_cut)
        ))
        out_channels.append(cv2.LUT(channel, lut.astype('uint8')))
    return cv2.merge(out_channels)


class SocketHandler(object):
    def __init__(self, host_ip="localhost", host_port=00000, app_port=0000):
        self.host_ip = host_ip
        self.app_port = app_port
        self.host_port = host_port
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host_ip, self.host_port))
        self.socket.listen(10)
        self.create_connection()

    def create_connection(self):
        print("Server is listening on -> " + self.host_ip + ":" + str(self.host_port))
        threading.Thread(target=initApp, args=[self.host_ip, self.app_port]).start()
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
        self.uuid = str(uuid.uuid4())
        self.connections = connections
        self.payload_size = struct.calcsize(">L")
        self.socket = sock
        self.address = address
        self.connection_established = connection_established
        self.data_received = False
        self.client_address = ""
        self.crossing_action = False
        self.img_array = []
        self.root_dir = os.path.dirname(os.path.abspath('logs')) + '\\logs\\'
        self.img_frame_counter = 0

    def disconnect(self):
        print("Client with address: " + str(self.address) + " has disconnected")
        self.data_received = False
        if str(self.address) is not None:
            cv2.destroyWindow(str(self.address))
        camerasAddressees.pop(self.client_address)
        self.connection_established = False
        self.socket.close()
        print(camerasAddressees)

    def open(self, sock, uuid):
        sock.send('open'.encode("UTF-8"))
        crossingsToOpen.pop(uuid)

    def close(self, sock, uuid):
        sock.send('close'.encode("UTF-8"))
        crossingsToOpen.pop(uuid)

    def checkIfOpenCrossing(self, socket, data, uuid):
        print(data)
        if data == "open":
            self.open(socket, uuid)
        elif data == "close":
            self.close(socket, uuid)
        else:
            try:
                crossingsToOpen.pop(uuid)
            except KeyError:
                pass

    def run(self):
        while self.connection_established:
            # reducing fps but increasing performance
            sleep(0.02)
            try:
                try:
                    if not self.crossing_action:
                        crossingStatus = crossingsToOpen[self.uuid]
                        self.checkIfOpenCrossing(self.socket, crossingStatus, self.uuid)
                        self.crossing_action = True
                except KeyError:
                    pass

                if not self.data_received:
                    data = self.socket.recv(4096)
                    self.client_address = str(data).replace("b", "").replace("'", "")
                    camerasAddressees[self.client_address] = self.uuid
                    print(camerasAddressees)
                    self.data_received = True
                while len(self.data) < self.payload_size:
                    try:
                        self.data += self.socket.recv(4096)
                        if str(self.data) == "b''":
                            self.disconnect()
                            self.connections.remove(self)
                            break
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
                self.crossing_action = False
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                colored_frame2 = simplest_cb2(frame, 1)
                frame2 = VideoDetector(colored_frame2).getFrame()
                w, h = 240 + 500, 320 + 400
                x, y = 10, 0
                crop_img = frame2[y:y + h, x:x + w]
                resized_frame = cv2.resize(crop_img, (240 + 550, 320 + 450), interpolation=cv2.INTER_AREA)
                try:
                    camerasLiveImages.pop(self.uuid)
                    camerasLiveImages[self.uuid] = resized_frame
                except KeyError:
                    camerasLiveImages[self.uuid] = resized_frame
                self.createVideo(resized_frame)
                cv2.imshow(str(self.address), resized_frame)
                cv2.waitKey(1)

            except socket.error:
                self.disconnect()
                self.connections.remove(self)
                break

    def createVideo(self, frame):
        self.img_array.append(frame)
        self.img_frame_counter += 1
        if self.img_frame_counter % 700 == 0:
            now = datetime.now()
            date_dir = now.strftime("%Y\\%m\\%d")
            filename = now.strftime("%H_%M_%S")
            file = self.root_dir + date_dir + "\\" + filename + ".avi"
            path = self.root_dir + date_dir
            pathlib.Path(path).mkdir(parents=True, exist_ok=True)
            height, width, layers = frame.shape
            out = cv2.VideoWriter(file, cv2.VideoWriter_fourcc(*'DIVX'), 15, (width, height))
            for i in range(len(self.img_array)):
                out.write(self.img_array[i])
            out.release()
            self.img_array.clear()
