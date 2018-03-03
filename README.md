# tempesp
Temperature logger for ESP8266 (Wemos), server side code and on-demand visualisation and analytics.


## Client side:
A temperature & humidity sensor (DHT22) on a wifi-enabled micorocontroller (Wemos D1 Mini). Every 20 minutes, the ESP wakes from deepsleep to record the temperature and humidity and pass this to the server.


## Server side:
A raspberry pi with a simple http server (Python) to record incoming payloads from one or more clients. Offers whitelisting to accept payloads from known clients only.


## Visuals and analytics:
(TODO)
A numpy and motplotlib based dashboarding script to provide a quick overview of received values. Also formats the payloads into an sql database or a csv file.