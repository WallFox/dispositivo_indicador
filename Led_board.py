from machine import Pin, Timer, reset, unique_id
import time
import ubinascii

class Board:
    def __init__(self):
        self.device_id = ubinascii.hexlify(unique_id()).decode()
        self.button = Pin(4, Pin.IN, Pin.PULL_DOWN)

    def reset(self,seg = 3):
        for _ in range(seg):
            print(f'{seg}')
            seg -= 1
            time.sleep(1)
        reset()

    def get_id(self):
        return self.device_id

class ButtonManager:
    def __init__(self, buttons_config):
        """
        For the list safe Output read
        GPIO
        buttons_config={"name": GPIO}
        ej:
        buttons_config={
        "button_1: 4",
        "button_2: 5
        }
        """
        self.buttons = {name: Pin(pin, Pin.IN, Pin.PULL_DOWN) for name, pin in buttons_config.items()}

    def get_state(self, name):
        if name in self.buttons:
            return self.buttons[name].value()
        return None

    def wait_for_press(self, name, debounce=0.1):
        if name in self.buttons:
            while not self.buttons[name].value():
                time.sleep(debounce)
            return True
        return False

class LedManager:
    def __init__(self,leds_config,period=250):
        """
        For the list safe Input read
        GPIO
        leds_config={"name": GPIO}
        ej:
        leds_config={
        "button":     25,
        "temp":       26,
        "humidity":   27,
        "esp_onboard": 2
        }
        """
        self.leds = {name: Pin(pin, Pin.OUT) for name, pin in leds_config.items()}
        self.period = period
        self.timer = Timer(0)

    def turn_on(self, name):
        if name in self.leds:
            self.leds[name].value(1)

    def turn_off(self, name):
        if name in self.leds:
            self.leds[name].value(0)

    def blink(self,timer):
        self.leds["esp_onboard"].value(not self.leds["esp_onboard"].value())

    def start_blink(self):
        self.timer.init(period=self.period, mode=Timer.PERIODIC, callback=self.blink)

    def stop_blink(self):
        self.timer.deinit()
        self.leds["esp_onboard"].value(0)