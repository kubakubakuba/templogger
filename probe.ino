#include <WiFi.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* ssid = "wifi_ssid";
const char* password = "wifi_password";

const char* server = "10.0.1.62";
const int serverPort = 8000;

#define ONE_WIRE_BUS 25
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

String deviceName = "";

void setup() {
	Serial.begin(115200);
	
	WiFi.begin(ssid, password);
	Serial.print("Connecting to WiFi");
	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
		Serial.print(".");
	}
	Serial.println("\nConnected to WiFi");
	Serial.print("IP Address: ");
	Serial.println(WiFi.localIP());

	sensors.begin();
	Serial.println("Dallas Temperature Sensor Initialized");
}

void getDeviceName() {
	WiFiClient client;
	Serial.println("Requesting device name from server...");
	
	if (client.connect(server, serverPort)) {
		String ipAddress = WiFi.localIP().toString();
		String request = String("GET /get_name/") + ipAddress + " HTTP/1.1\r\n" +
						 "Host: " + server + "\r\n" +
						 "Connection: close\r\n\r\n";
		
		client.print(request);
		
		unsigned long timeout = millis();
		bool foundName = false;
		
		while (client.connected() && millis() - timeout < 5000L) {
			while (client.available()) {
				String line = client.readStringUntil('\r');
				client.read();
				
				// skip HTTP headers (empty line marks end of headers)
				if (line.length() == 1 && line[0] == '\n') {
					continue;
				}
				
				if (line.startsWith("DeviceName:")) {
					deviceName = line.substring(11);
					deviceName.trim();
					Serial.print("Received device name: ");
					Serial.println(deviceName);
					foundName = true;
					break;
				}
			}
			if (foundName) break;
		}
		
		client.stop();
		
		if (!foundName) {
			Serial.println("Failed to get device name, using default");
			deviceName = "unknown";
		}
	} else {
		Serial.println("Failed to connect to server for name, using default");
		deviceName = "unknown";
	}
}

void loop() {
	getDeviceName();

	sensors.requestTemperatures();
	float temperature = sensors.getTempCByIndex(0);
	
	Serial.print("Temperature: ");
	Serial.print(temperature);
	Serial.println(" °C");

	WiFiClient client;
	Serial.println("Connecting to server...");
	if (client.connect(server, serverPort)) {
		Serial.println("Connected! Sending data...");
		
		String url = "/temp/" + deviceName + "/" + String(temperature);
		client.print(String("GET ") + url + " HTTP/1.1\r\n" +
					 "Host: " + server + "\r\n" +
					 "Connection: close\r\n\r\n");
		
		Serial.println("Data sent successfully");
		client.stop();
	} else {
		Serial.println("Connection failed");
	}

	Serial.println("Waiting 5 minutes...");
	delay(300000);
}