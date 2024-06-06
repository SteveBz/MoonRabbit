from urllib.request import urlopen
import json

class LocationProvider:
    def __init__(self):
        self.gps = urlopen('https://ipinfo.io')

    def get_location(self):
        response_bytes = self.gps.read()
        response_json = response_bytes.decode()
        d = json.loads(response_json)
        loc = d["loc"].split(',')
        latitude = float(loc[0])
        longitude = float(loc[1])
        return latitude, longitude


