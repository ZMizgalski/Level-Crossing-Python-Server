from flask import Flask, Response


class EndpointAction(object):

    def __init__(self, action):
        self.action = action
        self.response = Response(status=200, headers={})

    def __call__(self, *args):
        self.action()
        return self.response


class App(object):
    def __init__(self, host_ip="0.0.0.0", host_port=0000, app_name="DefaultName"):
        self.name = app_name
        self.app = Flask(self.name)
        self.host_ip = host_ip
        self.host_port = host_port

    def run(self):
        self.app.run(host=self.host_ip, port=self.host_port, debug=False)

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None):
        self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(handler))
