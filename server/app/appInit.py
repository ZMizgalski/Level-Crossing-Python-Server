from server.tcp.serverDataService import *
from flask import Flask, render_template, Response
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_img(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_img():
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + camerasLiveImages[0] + b'\r\n\r\n')


class appInit(object):
    def __init__(self, host_ip="0.0.0.0", host_port=0000):
        self.host_ip = host_ip
        self.host_port = host_port
        app.run(host=self.host_ip, port=self.host_port, debug=False)
