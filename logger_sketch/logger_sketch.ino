#include <WiFi.h>
#include <WiFiUdp.h>
#include <secrets.h>
#include <DHT.h>
#include <ESP_Google_Sheet_Client.h>

#define DHTPIN 3     // what pin we're connected to
#define DHTTYPE DHT22   // DHT22
DHT dht(DHTPIN, DHTTYPE); // Initialize DHT sensor for normal 16mhz Arduino

//set up to connect to an existing network (e.g. mobile hotspot from laptop that will run the python code)
const char* ssid = SECRET_SSID;
const char* password = SECRET_PASS;
WiFiUDP Udp;
unsigned int localUdpPort = 4210;  //  port to listen on
char incomingPacket[255];  // buffer for incoming packets

// Service Account's private key and gsheet id
const char PRIVATE_KEY[] PROGMEM = PRIVATE_KEY_GS;
const char spreadsheetId[] = SPREADSHEETID_1;

// measurement variables
float hum;  // Stores humidity value
float temp; // Stores temperature value
const unsigned long transmissionDelay = 60 * 60;  // How long between transmissions, in seconds.
const unsigned long measureDelay = 5 * 60 - 1;  // How long between measurements, in seconds.
unsigned long lastTime = 0;
unsigned long lastMeasure = 0;
int i = 0;
float temps[60];
float hums[60];
String times[60];

//time variables
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 0;
const int   daylightOffset_sec = 0;
String localTime;

// Token Callback function
void tokenStatusCallback(TokenInfo info);

unsigned long sec() {
   static unsigned long secondCounter = 0;
   static unsigned long prevSecMillis = 0;
   if (millis() - prevSecMillis >= 1000) {
       prevSecMillis += 1000;
       secondCounter ++;
   }
   return secondCounter;
}


String returnLocalTime()
{
  time_t now;
  struct tm timeinfo;
  String timing = "";
  if(!getLocalTime(&timeinfo)){
    Serial.println("Failed to obtain time");
    return "No time";
  }

  char timeStringBuff[50];
  strftime(timeStringBuff, sizeof(timeStringBuff), "%Y%m%d %H:%M:%S", &timeinfo);  // 
  timing += timeStringBuff;
  return timing;
}


void setup()
{ 
  Serial.begin(115200);
  delay(2000);

  //Initialize the DHT sensor
  dht.begin();
}

void loop(){
  if (sec() - lastMeasure > measureDelay){
    lastMeasure = sec();
    temp = dht.readTemperature();
    hum = dht.readHumidity();
    localTime = sec();

    temps[i] = temp;
    hums[i] = hum;
    times[i] = localTime;
    Serial.print(i);
    Serial.print(": ");
    Serial.println(localTime);
    i += 1;
  }

  if (sec() - lastTime > transmissionDelay){
    if(WiFi.getSleep() == true) {
      WiFi.setSleep(false);
    }
    // Connect to Wi-Fi
    WiFi.setAutoReconnect(true);
    if (WiFi.status() != WL_CONNECTED) {
      WiFi.begin(ssid, password);
    }
    Serial.print("Connecting to Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
      Serial.print(".");
      delay(1000);
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Connected to wifi");
        configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
        Serial.println();
      }
    }

    GSheet.printf("ESP Google Sheet Client v%s\n\n", ESP_GOOGLE_SHEET_CLIENT_VERSION);
    // Set the callback for Google API access token generation status (for debug only)
    GSheet.setTokenCallback(tokenStatusCallback);
    // Set the seconds to refresh the auth token before expire (60 to 3540, default is 300 seconds)
    GSheet.setPrerefreshSeconds(10 * 60);
    // Begin the access token generation for Google API authentication
    GSheet.begin(CLIENT_EMAIL, PROJECT_ID, PRIVATE_KEY);
    bool ready = GSheet.ready();

    if (ready){
      lastTime = sec();

      for (int j = -1; j < i; j++) {
        FirebaseJson response;
        if (j == i - 1) {
          times[j] += " ";
          times[j] += returnLocalTime();
        }

        FirebaseJson valueRange;
        valueRange.add("majorDimension", "COLUMNS");
        valueRange.set("values/[0]/[0]", times[j]);
        valueRange.set("values/[1]/[0]", temps[j]);
        valueRange.set("values/[2]/[0]", hums[j]);

        // For Google Sheet API ref doc, go to https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append
        // Append values to the spreadsheet
        bool success = GSheet.values.append(&response /* returned response */, spreadsheetId /* spreadsheet Id to append */, "Sheet1!A1" /* range to append */, &valueRange /* data range to append */);
        if (success){
          valueRange.clear();
        }
        else{
          Serial.println(GSheet.errorReason());
        }
      }

    WiFi.setAutoReconnect(false);
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    i = 0;
    }
  }
}

void tokenStatusCallback(TokenInfo info){
  if (info.status == token_status_error){
    GSheet.printf("Token info: type = %s, status = %s\n", GSheet.getTokenType(info).c_str(), GSheet.getTokenStatus(info).c_str());
    GSheet.printf("Token error: %s\n", GSheet.getTokenError(info).c_str());
  }
  else{
    GSheet.printf("Token info: type = %s, status = %s\n", GSheet.getTokenType(info).c_str(), GSheet.getTokenStatus(info).c_str());
  }
}

