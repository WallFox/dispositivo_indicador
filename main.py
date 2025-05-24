from WiFi_connection_manager import WiFiManager
from Web_server import WebServer
from MQTT_manager import MQTTManager
from _thread import start_new_thread
import time

# Host = "test.mosquitto.org"
# Host = "10.253.50.210" # My broker VPN
# Host = "localhost" # My broker Local
# Host = "192.168.10.23" # My broker Local
Host = "35.198.34.125"  # Cloud broker
Port = 1883 #WebSocket port 8081
Topic_Pub = 'Fox_32_Home/Status'
Topic_Sub = 'Fox_32_Home/Sensor'

wifi = WiFiManager()
server = WebServer()

if wifi.connect():
    print('Successful connection')

    if server.has_internet():
        print('Internet connected')

        mqtt = MQTTManager(Host,Port,Topic_Pub,Topic_Sub)
        mqtt.connect()

        if not mqtt.client:
            print('Could not connect to MQTT')
        else:
            start_new_thread(server.check_internet, ())
            start_new_thread(mqtt.listen,())
            start_new_thread(mqtt.publish_button(),())

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print('Ending MQTT...')
                mqtt.disconnect()

    else:
        print('Connected to WiFi, but without internet access')
        print('Unable to connect, launching web server')
        server.launch_server()
else:
    print('Unable to connect, launching web server')
    server.launch_server()