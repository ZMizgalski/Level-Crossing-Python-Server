import cv2 as cv
import numpy as np
import os


class VideoDetector:
    def __init__(self, frame):
        self.frame = frame

        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        # Tablice z punkatmi do zaznaczanai obszaru
        self.contours_list = []
        self.contours = []

        # Zmienne do rectContains(rec1, rect2)
        self.puzzle_rect = None
        self.puzzle_rect_name = None

        # Wielkość okna
        self.windowWidth = 416  # Szerokośc otwieranego detectora
        self.windowHeight = 416  # Szerokośc otwieranego detectora

        # Zmienne do dokładności wykrywacza
        self.confidenceThresh = 0.15  # Pewnośc wykrywania zalecane: (0.15)
        self.maxThresh = 0.2  # Granica wykrywalności zalecane: (0.20)

        # Dane dla nazw przy dekekcji obiektów
        self.fileWithClassesNames = os.path.join(self.root_dir, "coco.names")  # Plik z nazwami dla obiektów
        self.names = None  # Na początku jest None bo jeszczew nic nie wykryło

        # Otwiera plik "coco.names" i ładuje clasy
        with open(self.fileWithClassesNames, 'rt') as file:  # Otwiera plik i pobiera nazwy class
            self.names = file.read().rstrip('\n').split('\n')  # z lisy

        # Dane dla Modelu AI do wykrywania obiektów
        self.modelIAConfigFile = os.path.join(self.root_dir, 'yolov3-tiny.cfg')  # Plik configuracyjny AI
        self.modelAIWeighs = os.path.join(self.root_dir, 'yolov3-tiny.weights')  # Plik wag AI taki brain

        # Siatka modelu z plików AI
        self.net = cv.dnn.readNetFromDarknet(self.modelIAConfigFile,
                                             self.modelAIWeighs)  # ładuje mi siatke z modelu i AI
        self.net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)  # Robi backend siatki
        self.net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)  # Ustawia mózg kalkulacji

    # Wyznacza kontury obszaru w macierzu
    def extract_area(self, dot_points=None):
        if dot_points is None:
            dot_points = []

        for i in range(len(dot_points)):
            pt = dot_points[i]
            self.contours_list.append(pt)
            # print(self.contours_list)
        self.contours = [np.array(self.contours_list)]

    # Sprawdza czy macierze (Numpy array) sie pokrywają NIE UŻYWANE!!
    @staticmethod
    def rectContains(rect1, rect2):
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        return x1 > x2 and x1 > w1 < x2 + w2 and y1 > y2 and y1 + h1 < y2 + h2

    # Szuka Nazwy po indexie w pliku coco.names
    def findString(self, classId):
        if self.names:
            assert (classId < len(self.names))
            label = '%s' % (self.names[classId])
            return label

    # Metoda rysuje prostokąt z klasa (nazwą) na gorze
    def drawRect(self, frame, nameID, left, top, right, bottom):
        global detectedText
        cv.rectangle(frame, (left, top), (right, bottom), (255, 178, 50), 3)
        if self.names:
            assert (nameID < len(self.names))
            detectedText = '%s' % (self.names[nameID])
        self.puzzle_rect = left, top, right, bottom
        self.puzzle_rect_name = detectedText
        cv.putText(frame, detectedText, (left, top), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

    # Pobiera wykryte nazwy
    @staticmethod
    def getNamesFromNet(net):
        namesFormLayers = net.getLayerNames()
        return [namesFormLayers[layer - 1] for layer in net.getUnconnectedOutLayers()]

    # Przewiduje prostokaty do rysowania na podstawie net i pewności kalkulacji
    def predictRectangles(self, frame, edges):
        frameH = frame.shape[0]
        frameW = frame.shape[1]
        rectangles = []
        confidences = []
        nameIDs = []

        for edge in edges:
            for det in edge:

                scores = det[5:]

                classID = np.argmax(scores)
                confidence = scores[classID]

                if confidence > self.confidenceThresh:
                    w = int(det[2] * frameW)
                    h = int(det[3] * frameH)

                    x = int(det[0] * frameW)
                    y = int(det[1] * frameH)

                    l = int(x - w / 2)
                    t = int(y - h / 2)

                    rectangles.append([l, t, w, h])
                    confidences.append(float(confidence))
                    nameIDs.append(classID)

                    detectedRectangles = cv.dnn.NMSBoxes(rectangles, confidences, self.confidenceThresh, self.maxThresh)
                    for detect in detectedRectangles:
                        rect = rectangles[detect]
                        l = rect[0]
                        t = rect[1]
                        w = rect[2]
                        h = rect[3]
                        self.drawRect(frame, nameIDs[detect], l, t, l + w, t + h)

    # PObiera i modyfikuje klatkę za klatką
    def getFrame(self):
        # if self.frame.isOpened():
        #     isTrue, frame = self.frame.read()
        #     if isTrue:
        blob = cv.dnn.blobFromImage(self.frame, 1 / 255, (self.windowWidth, self.windowHeight), [0, 0, 0], 1,
                                    crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.getNamesFromNet(self.net))

        self.predictRectangles(self.frame, outs)
        return cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
    # else:
    #     return isTrue, None
