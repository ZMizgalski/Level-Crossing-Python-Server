import threading
from server.app.app import App
from server.tcp.serverDataService import *


class appInit(threading.Thread):
    def __init__(self, host_ip="0.0.0.0", host_port=0000, app_name="DefaultName"):
        threading.Thread.__init__(self)
        self.host_ip = host_ip
        self.name = app_name
        self.host_port = host_port
        threading.Thread.__init__(self)
        flaskApp = App(host_ip=self.host_ip, host_port=self.host_port)
        flaskApp.add_endpoint(endpoint="/elo", endpoint_name="elo", handler=self.get_elo)
        flaskApp.run()

    @staticmethod
    def get_elo():
        return "sasasasas"
