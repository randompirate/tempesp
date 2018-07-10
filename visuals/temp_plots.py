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
from scipy.interpolate import interp1d

temp_logfile = r"P:\Dropbox\rpi_connector\server_requests.log"
weather_logfile = r"P:\Dropbox\rpi_connector\weather.log"
csv_out = r"P:\Dropbox\RaspberryPi\temp_humid.csv"


min_date = datetime.strptime('2017-11-20 0:0:0', '%Y-%m-%d %H:%M:%S')

utc_to_local = lambda utc_dt: utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None) # Fix the time zone
parse_datetime = lambda s : utc_to_local(datetime.strptime(s.split('.')[0], '%Y-%m-%d %H:%M:%S'))
kelvin2c = lambda k : float(k) - 273.15


cur_date = utc_to_local(datetime.now())

def import_temp_log():
  time_array, temp_array, humi_array = [], [], []
  with open(temp_logfile, 'r') as fh:
    csvh = csv.reader(fh, delimiter = ';')
    next(csvh) #Skip head row
    for line in csvh:
      # print(line)
      payload = json.loads(line[1])
      #TODO: Filter out appropriate lines from payload
      temp, humid = float(payload['temperature']), float(payload['humidity'])
      if not np.isnan(temp):
        time_array.append(parse_datetime(line[0]))
        temp_array.append(temp)
        humi_array.append(humid)
  return np.array(time_array), np.array(temp_array), np.array(humi_array)

def import_weather_log():
  time_array, temp_array = [], []
  with open(weather_logfile, 'r') as fh:
    csvh = csv.reader(fh, delimiter = ';')
    next(csvh) #Skip head row
    for line in csvh:
      if not line[1] or 'error' in line[1] : continue
      payload = json.loads(line[1])

      time_array.append(parse_datetime(line[0]))
      temp_array.append(kelvin2c(payload['main']['temp']))

  return np.array(time_array), np.array(temp_array)


def uniform_resampling(t_seconds, y, t0, sample_period):
  splerp = interp1d(t_seconds, y, kind = 'cubic')
  return splerp(np.arange(t_seconds[0], t_seconds[-1], sample_period))

def export_csv(time_array, temp_array, humi_array, delta_temp):

  with open(csv_out, 'w') as f:
    f.write('timestamp;temperature;humidity;delta_temp\n')
    for tim, tem, hum, dte in zip(time_array, temp_array, humi_array, delta_temp):
      f.write('{};{};{};{}\n'.format(tim, tem, hum, dte))

def moving_avg(x_array,y_array, window = timedelta(hours = 12)):
  y_avg_array = []
  for x,y in zip(x_array, y_array):
    y_windowed = y_array[ ((x-window) < x_array) * (x_array < (x+window)) ]
    y_avg = np.mean(y_windowed)
    y_avg_array.append(y_avg)
  return np.array(y_avg_array)


def math_ops(time_array_epoch, temp_array, humi_array):
  ret_dict = {}
  # Derivative (C/minute)
  ret_dict['derivative_temp'] = 3600*np.gradient(temp_array, time_array_epoch) #degs/hour
  # Fourier (Only on the last p=2^k samples)
  k = int(np.log(len(time_array_epoch))/np.log(2))
  t_window = time_array_epoch[-2**k:]-time_array_epoch[-2**k]
  t_hat = nfft.nfft(temp_array[-2**k:], t_window)
  #freqHz = (0:1:length(X_mag)-1)*Fs/N; Fs=sampling rate, N = sample size
  # freq = np.arange(2**k)*(time_array_epoch[-1] - time_array_epoch[-2**k])/(60*60*24)
  ret_dict['fourier'] = t_hat.real
  return ret_dict


# Set variables
time_array, temp_array, humi_array = import_temp_log()
weather_time_array, weather_temp_array = import_weather_log()

time_array_epoch = np.array([(s-utc_to_local(datetime(1970,1,1))).total_seconds() for s in time_array]) # time array in seconds
time_array_clock = np.array([t.replace(day=1, month = 1) for t in time_array])

math_series = math_ops(time_array_epoch, temp_array, humi_array)
delta_temp = math_series['derivative_temp']
freq = math_series['fourier']


#
# Bokeh Plots
#

# import matplotlib.pyplot as plt

# plt.plot(weather_time_array)
# plt.show()

# exit()

if __name__ == '__main__':

  import bokeh.io
  import bokeh.plotting
  import bokeh.models
  import bokeh


  bokeh.io.output_file('./plots.html')

  data_model =  bokeh.models.ColumnDataSource(data={
      'date' : time_array,
      'date_string' : [s.strftime('%a %d-%m %H:%M') for s in time_array],
      'temp' : temp_array,
      'temp_avg': moving_avg(time_array, temp_array, timedelta(hours=12)),
  })

  weather_data_model = bokeh.models.ColumnDataSource(data={
      'weather_date' : weather_time_array,
      'weather_temp' : weather_temp_array,
      # 'temp_avg': moving_avg(time_array, temp_array, timedelta(hours=12)),
  })

  # Temp plot
  p = bokeh.plotting.figure(plot_width=1400, plot_height=400,
            title="Temperature",
            tools = ['box_zoom', 'reset'],
            x_axis_type = 'datetime',
            toolbar_location = 'above')

  # Temp plot
  p.line(x='date', y='temp',
            line_width=1,# legend = 'T',
            source = data_model)
  p.line(x='date', y='temp_avg',
            line_width=2,# legend = 'T (24hr avg)',
            source = data_model)
  p.line(x='weather_date', y='weather_temp',
            line_width=1,# legend = 'T outside',
            source = weather_data_model, color = 'firebrick')

  # Hide on legend click
  p.legend.click_policy="hide"

  p.add_tools(bokeh.models.HoverTool(
    tooltips=[
      ("time", "@date_string"),
      ("temp", "@temp{0.0}"),
      ("avg temp", "@temp_avg{0.0}"),
      # ("out temp", "@weather_temp{0.0}"),
    ]
  ))

  bokeh.io.show(p) # show the results

  # plt.plot(np.gradient(time_array_epoch))
  # plt.show()