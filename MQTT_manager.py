from umqtt.simple import MQTTClient
from Led_board import LedManager, Board, ButtonManager
from Oled_manager import OledManager
import time
import ujson
import config
from Crypto import Crypto


class MQTTManager:
    def __init__(self, host, topic_pub, topic_sub, debug=False):
        self.board = Board()
        self.display = OledManager()
        self.crypto = Crypto(config.passphrase)
        self.leds = LedManager({
            "button_led": 19,  # white
            "temp_led": 18,  # grey
            "hum_led": 17  # blue
        })
        self.buttons = ButtonManager({
            "button_push": 23  # orange
        })
        self.maxtemp = config.warning_temp
        self.maxhum = config.warning_hum
        self.client_id = self.board.get_id()
        self.host = host
        self.port = 1883  # WebSocket port 8081
        self.topic_pub = topic_pub.encode()
        self.topic_sub = topic_sub.encode()
        self.debug = debug
        self.client = None
        self.connected = False

    def connect(self):
        self.client = MQTTClient(self.client_id, self.host, self.port, keepalive=30)
        self.client.set_callback(self.on_message)
        for attempt in range(3):
            try:
                self.client.connect()
                self.client.subscribe(self.topic_sub)
                self.connected = True
                if self.debug:
                    print(f'Connect to broker MQTT: {self.host}')
                    print(f'Subscribed to: {self.topic_sub.decode()}')
                return True
            except Exception as e:
                print(f'Attempt {attempt + 1} failed: {e}')
                time.sleep(2)
        print('Critical Error, Rebooting...')
        self.board.reset()
        return False

    def on_message(self, topic, msg):
        try:

            if config.Crypto:
                texto = self.crypto.decrypt(msg)
                if self.debug:
                    print(f'Decrypted raw message: {texto}')
            else:
                texto = msg.decode()

            data = ujson.loads(texto)
            print(f'Received message from {topic.decode()}: {data}')

            msg_id = data.get('id')
            if msg_id in ['Sensor_ESP', 'Telegram', 'Node']:
                temp = data.get('dato_temp')
                hum = data.get('dato_hum')
                btn = data.get('dato_button')

                # Verificar datos requeridos antes de usarlos
                if temp is not None and hum is not None and btn is not None:
                    # Actualiza display
                    self.display.update_display(temp, hum, btn)

                    if btn == 1:
                        self.leds.turn_on('button_led')
                        print("LED encendido")
                    elif btn == 0:
                        self.leds.turn_off('button_led')
                        print("LED apagado")
                    else:
                        print("Error: 'dato_button' must be 0 or 1")

                    if temp >= self.maxtemp:
                        self.leds.turn_on('temp_led')
                    else:
                        self.leds.turn_off('temp_led')

                    if hum >= self.maxhum:
                        self.leds.turn_on('hum_led')
                    else:
                        self.leds.turn_off('hum_led')
                else:
                    print("Error: Missing one of 'dato_temp', 'dato_hum', or 'dato_button'")
            else:
                print(f'Ignored message: Invalid ID - {msg_id}')

        except Exception as e:
            print(f'Error processing MQTT message: {e}')

    def publish(self, msg):
        if self.client and self.connected:
            try:
                if config.Crypto:
                    self.client.publish(self.topic_pub, msg)
                else:
                    self.client.publish(self.topic_pub, msg.encode())
                if self.debug:
                    print(f'Published: {msg} in {self.topic_pub.decode()}')
                return True
            except Exception as e:
                print(f'Error publishing: {e}')
                self.connected = False
                return False
        return False

    def is_mqtt_connected(self):
        if not self.connected:
            return False
        try:
            self.client.ping()
            return True
        except Exception as e:
            print(f'Ping failed: {e}')
            self.connected = False
            return False

    def reconnect_mqtt(self):
        print("Attempting MQTT reconnection...")
        try:
            if self.client:
                self.client.disconnect()
        except:
            pass

        self.connected = False
        time.sleep(2)

        try:
            self.client.connect()
            self.client.subscribe(self.topic_sub)  # Re-suscribirse es crítico
            self.connected = True
            print("Reconnected to the MQTT broker")
            print(f"Re-subscribed to: {self.topic_sub.decode()}")
            return True
        except Exception as e:
            print("Error reconnecting MQTT:", e)
            return False

    def publish_data(self):
        before_stage = self.buttons.get_state('button_push')

        while True:
            try:
                actual_state = self.buttons.get_state('button_push')

                msg = ujson.dumps({
                    'id': 'Status_ESP',
                    'dato_button': actual_state
                })

                msg_cifrado = self.crypto.encrypt(msg)

                # Verificar conexión antes de publicar
                if not self.is_mqtt_connected():
                    print('Broker disconnected. Trying to reconnect...')
                    if not self.reconnect_mqtt():
                        time.sleep(5)
                        continue

                # Publicar cambio de botón inmediatamente
                if actual_state != before_stage:
                    if config.Crypto:
                        if self.publish(msg_cifrado):
                            print(f'Button change sent: {actual_state}')
                            before_stage = actual_state
                        else:
                            print('Failed to send button change')
                    else:
                        if self.publish(msg):
                            print(f'Button change sent: {actual_state}')
                            before_stage = actual_state
                        else:
                            print('Failed to send button change')

            except Exception as e:
                print(f'Error in publish_data: {e}')

            time.sleep(0.1)

    def listen(self):
        while True:
            try:
                if self.connected and self.client:
                    self.client.check_msg()
                else:
                    print("MQTT not connected, attempting reconnection...")
                    if not self.reconnect_mqtt():
                        time.sleep(5)
                        continue

                time.sleep(0.1)

            except OSError as e:
                print(f'Network error in listen: {e}')
                self.connected = False
                time.sleep(2)
            except Exception as e:
                print(f'Error in listen: {e}')
                time.sleep(1)

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
                self.connected = False
                if self.debug:
                    print('Disconnected from MQTT')
            except:
                pass