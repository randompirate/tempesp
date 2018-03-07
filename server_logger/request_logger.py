#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
# from urlparse import urlparse
import urllib.parse as urlparse
import subprocess
import re
import urllib.request
import json
import os
import datetime
import private_ip #Gitignored

IOT_LOGFILE   = r'/home/pi/server_requests.log'
SERVER_IP     = private_ip.ip   # Raspberry pi (string)
SERVER_PORT   = private_ip.port # IOT listening port (int)
KNOWN_DEVICES = ['laptop_test', 'ESP_018D15']



def write_iot_log(path, query_dict):
  # utc_to_ams = lambda utc_dt : utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Europe/Amsterdam"))
  timestmp = datetime.datetime.now()
  # timestmp_ams = utc_to_ams(timestmp)
  payload = json.dumps(query_dict)
  with open(IOT_LOGFILE, 'a') as f:
    f.write('{};{}\n'.format(timestmp, payload))
  return 'payload received:' + str(payload)




class HTTPServer_RequestHandler(BaseHTTPRequestHandler):
  #
  # GET
  #
  def do_GET(self):
    print('Path:', self.path)
    print(self.headers, flush = True)

    # Parse the query string into a dict
    query_dict = self.parse_query_dict()
    device_id = query_dict.get('device_id', None)

    # Authorisation test device id:
    if device_id not in KNOWN_DEVICES:
      self.send_response(404)
      self.end_headers()
      self.wfile.write(bytes('Access denied', 'utf-8'))
      return  #End response

    # proces iot_log
    if '/iot_log/' in self.path:
      log_result = write_iot_log(self.path, query_dict)
      self.send_response(200)
      self.end_headers()
      self.wfile.write(bytes(log_result, 'utf-8'))
      return #End response

    return

  #
  # helper functions
  #
  def parse_query_dict(self):
    qdict = urlparse.parse_qs(urlparse.urlparse(self.path).query)
    return {k:(v[0] if len(v) ==1 else v) for k,v in qdict.items()} # only parse first element


###############
# Main access #
###############

if __name__ == "__main__":

  # Server settings
  server_address = (SERVER_IP, SERVER_PORT)
  print('Server listening on {}:{}'.format(SERVER_IP, SERVER_PORT))
  httpd = HTTPServer(server_address, HTTPServer_RequestHandler)
  httpd.serve_forever()
