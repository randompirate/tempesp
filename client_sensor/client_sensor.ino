

/*Make sure the Wemos is not in deep sleep
 * Hold the reset button prior to uploading
 * See here: https://www.reddit.com/r/esp8266/comments/7398fn/resetting_wemos_d1_mini/
 */


#include <ESP8266WiFi.h>
#include <DHT.h>


// Pins
#define DHTPIN D3


// Wifi network
const char* ssid     = "<ssid>";      // SSID
const char* password = "<pass>";      // Password

// Host server
const char* host = "<ip>"; // Raspberry pi on network
const int   port = 000000; // Webserver

// Client info and payload content
const char* device_id = "ESP_018D15";
const char* firmware_version = "1.2";
const char* message_type = "temp_and_humidity";
const char* extra_flags = "";

// Frequency
const int   sleeptime_millis = 5*1000;     // Time between request attempts
const int   deepsleep_seconds = 20*60;     // deep sleep

// DHT temp sensor
DHT dht(DHTPIN, DHT22);

// measured vals
float val_humidity;
float val_temperature;


/*
 * Setup things
 */
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.print("version");
  Serial.print(firmware_version);
  Serial.println();

  //Set pin modes and turn on onboard led
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  
  //Connect the Wifi
  connect_ssid();

  // Open a client
  WiFiClient client;
  //Attempt to connect
  if (!client.connect(host, port)) {
    Serial.println("connection to host failed");
    //Try again in 5 minutes
    ESP.deepSleep(5 * 60 * 1000000);
   }

  //Get temp and humid
  val_humidity = dht.readHumidity();
  val_temperature = dht.readTemperature();

  //Test for failed reading. Deep sleep for one minute if so
  if (isnan(val_humidity) || isnan(val_temperature)){
    ESP.deepSleep(1 * 60 * 1000000);
  }


  //craft the payload in the url
  String url = "/iot_log/?";
  url += "device_id=";  url += device_id;
  url += "&device_ip=";  url += WiFi.localIP().toString();
  url += "&message_type="; url += message_type;
  url += "&humidity=";  url += val_humidity;
  url += "&temperature=";  url += val_temperature;
  url += "&deepsleep_seconds=";  url += deepsleep_seconds;
  url += "&firmware_version="; url+= firmware_version;
  url += extra_flags;


  // send the request to the server (and serial)
  Serial.println(url);
  client.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + host + "\r\n" + 
               "Connection: close\r\n\r\n");
  

  // Timeout for response
  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 5000) {
      Serial.println(">>> Client Timeout !");
      client.stop();
      //Try again in 5 minutes
      ESP.deepSleep(5 * 60 * 1000000);
    }
  }

  // Report response to Serial
  while(client.available()){
    String line = client.readStringUntil('\r');
    Serial.print(line);
  }
  Serial.println("");
  
  // Stop the client
  client.stop();
  //Turn off the led
  digitalWrite(LED_BUILTIN, HIGH);

  //Deep sleep
  Serial.println("Deep sleep");
  ESP.deepSleep(deepsleep_seconds * 1000000); // Connect D0 and RST to wake up after sleep time
}


/*
 * Main loop
 * Unused 
 */
void loop() {
}



/*
 * Wifi functions
 */
void connect_ssid(){
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

}


