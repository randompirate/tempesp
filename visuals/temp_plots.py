import numpy as np
import matplotlib.pyplot as plt
import math
import random as rng
from datetime import datetime, timezone, timedelta
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import csv
import json
import nfft


logfile = r"P:\Dropbox\rpi_connector\server_requests.log"
csv_out = r"P:\Dropbox\RaspberryPi\temp_humid.csv"


min_date = datetime.strptime('2017-11-20 0:0:0', '%Y-%m-%d %H:%M:%S')



utc_to_local = lambda utc_dt: utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None) # Fix the time zone
parse_datetime = lambda s : utc_to_local(datetime.strptime(s.split('.')[0], '%Y-%m-%d %H:%M:%S'))

cur_date = utc_to_local(datetime.now())

def filter_regularise(array_in, window = 4):
  array_out = array_in[:]
  for i,val in enumerate(array_in):
    if i<window:
      continue
    array_out[i] = np.median(array_in[i-window:i+window])
  return array_out

def import_log():
  time_array, temp_array, humi_array = [], [], []
  with open(logfile, 'r') as fh:
    csvh = csv.reader(fh, delimiter = ';')
    next(csvh) #Skip head row
    for line in csvh:
      payload = json.loads(line[1])
      #TODO: Filter out appropriate lines from payload
      temp, humid = float(payload['temperature']), float(payload['humidity'])
      if not np.isnan(temp):
        time_array.append(parse_datetime(line[0]))
        temp_array.append(temp)
        humi_array.append(humid)
  return np.array(time_array), np.array(temp_array), np.array(humi_array)

def export_csv(time_array, temp_array, humi_array, delta_temp):

  with open(csv_out, 'w') as f:
    f.write('timestamp;temperature;humidity;delta_temp\n')
    for tim, tem, hum, dte in zip(time_array, temp_array, humi_array, delta_temp):
      f.write('{};{};{};{}\n'.format(tim, tem, hum, dte))

def smoothen(np_arr, k=5):
  return np.convolve(np_arr, np.ones(k)/k, 'valid')

def math_ops(time_array_epoch, temp_array, humi_array):
  ret_dict = {}
  # Derivative (C/minute)
  ret_dict['derivative_temp'] = 3600*np.gradient(temp_array, time_array_epoch) #degs/hour
  # Fourier (Only on the last p=2^k samples)
  k = int(np.log(len(time_array_epoch))/np.log(2))
  t_hat = nfft.nfft(temp_array[-2**k:], time_array_epoch[-2**k:])
  #freqHz = (0:1:length(X_mag)-1)*Fs/N; Fs=sampling rate, N = sample size
  freq = np.arange(2**k)*(time_array_epoch[-1] - time_array_epoch[-2**k])/(60*60*24)
  mag = np.log(np.abs(t_hat))/np.log(10)
  ret_dict['fourier'] = freq[mag<1e11], mag[mag<1e11]
  return ret_dict


#
# Main
#

time_array, temp_array, humi_array = import_log()

time_array_epoch = np.array([(s-utc_to_local(datetime(1970,1,1))).total_seconds() for s in time_array]) # time array in seconds
time_array_clock = np.array([t.replace(day=1, month = 1) for t in time_array])

math_series = math_ops(time_array_epoch, temp_array, humi_array)
delta_temp = math_series['derivative_temp']
freq = math_series['fourier']

# export_csv(time_array, temp_array, humi_array, delta_temp)


#
# Bokeh Plots
#

from bokeh.io import output_file, show
from bokeh.plotting import figure
import bokeh

output_file('./plots.html')

#Hover tool
hover = bokeh.models.HoverTool(tooltips=[
    ("temp", "$y"),
    ("time", "$x"),
])

# create a new plot (with a title) using figure
p = figure(plot_width=1400, plot_height=400, title="Temperature", tools = [hover, 'box_zoom', 'reset'])

# Temp plot
tp = p.line(time_array, temp_array, line_width=1)
p.line(time_array[36:-36], smoothen(temp_array, 73), line_width=2, line_color='red')

show(p) # show the results