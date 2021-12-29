from server.tcp.serverDataService import *
from flask import Flask, render_template, Response, request, make_response
import cv2
from uuid import UUID

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/getAllCameras', methods=['GET'])
def get_all_cameras():
    return Response(camerasAddressees.values(), status=200)


@app.route('/video_feed/<id>', methods=['GET'])
def video_feed(id):
    uuid = request.view_args['id']
    try:
        data = camerasLiveImages[uuid]
    except KeyError:
        return Response("UUID not found", status=400)
    return Response(gen(uuid), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/crossingAction', methods=['POST'])
def crossing_action():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json = request.json
        try:
            id = json["id"]
            try:
                valid_uuid = UUID(id)
            except ValueError:
                return Response("Not valid uuid", status=400)
            action = json["action"]
            crossingsToOpen[str(valid_uuid)] = action
            return Response(id + " -> " + action, status=200)
        except KeyError:
            return Response("Content-Type not supported!", status=400)
    else:
        return Response("Content-Type not supported!", status=400)


def gen(uuid):
    while True:
        try:
            frame = generate_img(uuid)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except TypeError:
            pass


def generate_img(uuid):
    try:
        ret, buffer = cv2.imencode('.jpg', camerasLiveImages[uuid])
    except KeyError:
        return
    return buffer.tobytes()


class appInit(object):
    def __init__(self, host_ip="0.0.0.0", host_port=0000):
        self.host_ip = host_ip
        self.host_port = host_port
        app.run(host=self.host_ip, port=self.host_port, debug=False)
