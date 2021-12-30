import json

from server.tcp.serverDataService import *
from flask import Flask, render_template, Response, request, send_file, jsonify
from flask_cors import CORS, cross_origin
import cv2
from uuid import UUID
import io
from datetime import datetime, date
import defaultdict
from os.path import exists
import os

app = Flask(__name__)
CORS(app)
root_dir = os.path.dirname(os.path.abspath('logs')) + "\\logs"


@app.route('/')
@cross_origin()
def index():
    return render_template('index.html')


@app.route('/updateArea', methods=["PUT"])
@cross_origin()
def update_area():
    return Response("ass", status=200)


@app.route('/deleteArea', methods=["DELETE"])
@cross_origin()
def delete_area():
    return Response("ass", status=200)


@app.route('/setArea', methods=["POST"])
@cross_origin()
def set_area():
    return Response("ass", status=200)


@app.route('/getAllAreasById/<id>', methods=["GET"])
@cross_origin()
def get_all_areas_by_id(id):
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    uuid = request.view_args['id']

    return Response(uuid, status=200)


@app.route('/downloadFileByDate/<id>/<input_date>', methods=["GET"])
@cross_origin()
def download_file_by_date(id, input_date):
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    uuid = request.view_args['id']
    input_date = request.view_args['input_date']

    try:
        year, month, day_with_hours, minutes, seconds = input_date.split('-')
        day, hours = day_with_hours.split('_')
    except ValueError:
        return Response("Invali Date yyyy-MM-dd_HH-mm-ss", status=400)
    try:
        formatted_date = datetime(int(year), int(month), int(day), int(hours), int(minutes), int(seconds))
    except ValueError:
        return Response("Invali Date yyyy-MM-dd_HH-mm-ss", status=400)
    try:
        date_time = datetime.strftime(formatted_date, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return Response("Invali Date yyyy-MM-dd_HH-mm-ss", status=400)

    return Response(uuid + "  " + date_time, status=200)


@app.route('/getFilesByDay/<id>/<day>', methods=["GET"])
@cross_origin()
def get_files_by_day(id, day):
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    uuid = request.view_args['id']
    day = request.view_args['day']

    camera_name = ""
    for name, stored_uuid in camerasAddressees.items():
        if stored_uuid == uuid:
            camera_name = name

    if camera_name == "":
        return Response("uuid not exists", status=400)

    try:
        year, month, day = day.split('-')
    except ValueError:
        return Response("Invali Date yyyy-MM-dd", status=400)
    try:
        formatted_date = datetime(int(year), int(month), int(day))
    except ValueError:
        return Response("Invali Date yyyy-MM-dd", status=400)
    try:
        date_time = datetime.strftime(formatted_date, "%Y-%m-%d")
    except ValueError:
        return Response("Invali Date yyyy-MM-dd", status=400)
    path = root_dir + "\\" + year + "\\" + month + "\\" + day + "\\" + camera_name
    print(path)
    try:
        files = next(os.walk(path))[2]
    except StopIteration:
        return Response("Files found", status=400)
    date_array = []
    for file in files:
        date_dict = {"id": id, "time": year + "-" + month + "-" + day + "_" + file.replace(".avi", "")}
        date_array.append(date_dict)
    return Response(json.dumps(date_array), status=200, mimetype="application/json")


@app.route('/getFileByDate/<id>/<input_date>', methods=["GET"])
@cross_origin()
def get_file_by_date(id, input_date):
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    uuid = request.view_args['id']
    input_date = request.view_args['input_date']
    camera_name = ""
    for name, stored_uuid in camerasAddressees.items():
        if stored_uuid == uuid:
            camera_name = name

    if camera_name == "":
        return Response("uuid not exists", status=400)

    try:
        year, month, day_with_hours, minutes, seconds = input_date.split('-')
        day, hours = day_with_hours.split('_')
    except ValueError:
        return Response("Invali Date yyyy-MM-dd_HH-mm-ss", status=400)
    try:
        formatted_date = datetime(int(year), int(month), int(day), int(hours), int(minutes), int(seconds))
    except ValueError:
        return Response("Invali Date yyyy-MM-dd_HH-mm-ss", status=400)
    try:
        date_time = datetime.strftime(formatted_date, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return Response("Invali Date yyyy-MM-dd_HH-mm-ss", status=400)

    path = root_dir + "\\" + year + "\\" + month + "\\" + day + "\\" + camera_name + "\\" + hours + "-" + minutes + "-" + seconds + ".avi"
    print(path)
    file_exists = exists(path)
    if not file_exists:
        return Response("File not exists", status=400)
    return send_file(attachment_filename=str(date_time) + ".avi", path_or_file=path, as_attachment=True, mimetype="video/mp4")


@app.route('/stream-cover/<id>')
@cross_origin()
def get_Camera_Cover(id):
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    uuid = request.view_args['id']
    try:
        data = camerasLiveImages[uuid]
    except KeyError:
        return Response("UUID not found", status=400)
    return send_file(
        io.BytesIO(generate_img(uuid)),
        mimetype='image/jpeg')


@app.route('/checkIfCameraIsOnline/<id>', methods=["GET"])
@cross_origin()
def check_if_cameras_is_online(id):
    uuid = request.view_args['id']
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    if id in camerasAddressees.values():
        return jsonify(response="ok")
    else:
        return Response("UUID not found", status=400)


@app.route('/getAllCameras', methods=['GET'])
@cross_origin()
def get_all_cameras():
    cameras = []
    if len(camerasAddressees) == 0:
        return Response(json.dumps([]), status=200, mimetype="application/json")
    for id in camerasAddressees.values():
        cameraResponse = {"id": id, "data": "Default Data"}
        cameras.append(cameraResponse)
    return Response(json.dumps(cameras), status=200, mimetype="application/json")


@app.route('/server-stream/<id>', methods=['GET'])
@cross_origin()
def video_feed(id):
    uuid = request.view_args['id']
    try:
        valid_uuid = UUID(id)
    except ValueError:
        return Response("Not valid uuid", status=400)
    try:
        data = camerasLiveImages[uuid]
    except KeyError:
        return Response("UUID not found", status=400)

    return Response(gen(uuid), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route('/crossingAction', methods=['POST'])
@cross_origin()
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
