from umqtt.simple import MQTTClient
from Led_board import LedManager, Board, ButtonManager
from Oled_manager import OledManager
from Web_server import WebServer
import time
import ujson


class MQTTManager:
    def __init__(self, host, port, topic_pub, topic_sub, debug=False):
        self.board = Board()
        self.display = OledManager()
        self.server = WebServer()
        self.leds = LedManager({
            "button_led": 19,  # white
            "temp_led": 18,  # grey
            "hum_led": 17  # blue
        })
        self.buttons = ButtonManager({
            "button_push": 23  #orange
        })
        self.client_id = self.board.get_id()
        self.host = host
        self.port = port
        self.topic_pub = topic_pub.encode()
        self.topic_sub = topic_sub.encode()
        self.debug = debug
        self.client = None

    def connect(self):
        self.client = MQTTClient(self.client_id, self.host, self.port,keepalive=60)
        self.client.set_callback(self.on_message)
        for _ in range(3):
            try:
                self.client.connect()
                self.client.subscribe(self.topic_sub)
                if self.debug:
                    print(f'Connect to broker MQTT: {self.host}')
                return
            except Exception as e:
                print(f'Trying reconnected: {e}')
                time.sleep(2)
        print('Critical Error, Rebooting...')
        self.board.reset()
        return False

    def on_message(self, topic, msg):
        try:
            data = ujson.loads(msg.decode())
            print(f'Received message from {self.topic_sub.decode()}: {data}')

            if data.get('id') in ['Sensor_ESP', 'Telegram', 'Node']:
                self.display.update_display(data['dato_temp'], data['dato_hum'], data['dato_button'])
                if 'dato_button' in data and data['dato_button'] in [0, 1]:
                    self.leds.turn_on('button_led') if data['dato_button'] else self.leds.turn_off('button_led')
                else:
                    print("Error: 'dato_button' must be 0 or 1.")

                self.leds.turn_on('temp_led') if data.get('dato_temp', 0) >= 27 else self.leds.turn_off('temp_led')
                self.leds.turn_on('hum_led') if data.get('dato_hum', 0) >= 80 else self.leds.turn_off('hum_led')
            else:
                print('Ignored message: Invalid ID')
        except Exception as e:
            print(f'Error processing MQTT message: {e}')

    def publish(self, msg):
        if self.client:
            self.client.publish(self.topic_pub, msg.encode())
            if self.debug:
                print(f'Published: {msg} in {self.topic_pub.decode()}')

    @staticmethod
    def is_mqtt_connected(client):
        try:
            client.ping()
            return True
        except:
            return False

    @staticmethod
    def reconnect_mqtt(client):
        try:
            client.disconnect()
        except:
            pass
        time.sleep(2)
        try:
            client.connect()
            print("Reconnected to the MQTT broker")
        except Exception as e:
            print("Error reconnecting MQTT:", e)

    def publish_button(self):
        before_stage = self.buttons.get_state('button_push')

        while True:
            actual_state = self.buttons.get_state('button_push')
            msg = ujson.dumps({
                'id': 'Status_ESP',
                'dato_button': actual_state
            })
            if not self.is_mqtt_connected(self.client):
                print('Broker disconnected. Trying to reconnect...')
                self.reconnect_mqtt(self.client)
            if actual_state != before_stage:
                try:
                    self.client.publish(self.topic_pub, msg.encode())
                    print(f'Message sent from {self.topic_pub.decode()}: {msg}')
                    before_stage = actual_state
                except Exception as e:
                    print('Error posting button change:', e)

    def listen(self):
        while True:
            try:
                self.client.check_msg()
                time.sleep(0.5)
            except Exception as e:
                print(f'Error MQTT: {e}')
                self.board.reset()
                break

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            if self.debug:
                print('Disconnected from MQTT')
