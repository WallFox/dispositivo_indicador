from sh1106 import SH1106_I2C
from machine import I2C, Pin
import framebuf
import icons

class OledManager:
    def __init__(self,width=128, height=64, scl=22, sda=21):
        self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda))
        self.display = SH1106_I2C(width,height,self.i2c)
        self.display.fill(0)
        self.display.flip(True)
        self.display.show()
        self.fb_temp= framebuf.FrameBuffer(icons.icons['icon_temp'], 8, 8, framebuf.MONO_HLSB)
        self.fb_hum = framebuf.FrameBuffer(icons.icons['icon_hum'], 8, 8, framebuf.MONO_HLSB)
        self.fb_fox = framebuf.FrameBuffer(icons.icons['icon_fox'], 32, 32, framebuf.MONO_HLSB)

    def welcome(self):
        self.display.fill(0)
        self.title()
        self.display.blit(self.fb_fox, 48, 16)
        self.display.text('Loading Wait',3,54)
        self.display.show()

    def title(self):
        self.display.rect(0, 0, 128, 64, 1)
        self.display.text('Fox Home ESP', 16, 3,1)

    def update_display(self,temp,hum,button_state):
        self.display.fill(0)
        self.title()
        self.display.text(f'Temp:{temp:.1f}C',3,14,1)
        #self.display.blit(self.fb_temp,100,24)
        self.draw_bar(3,24,temp,30)
        self.display.text(f'Hum:{hum:.1f}%', 3, 34, 1)
        #self.display.blit(self.fb_hum, 100, 34)
        self.draw_bar(3,44,hum,100)
        self.display.text(f'Button:{'On' if button_state else 'Off'}', 3, 54, 1)
        self.display.blit(self.fb_fox,94,30)
        #self.display.blit(100, 54, icons.icons['icon_button_on'] if button_state else icons.icons['icon_button_off'])
        self.display.show()

    def server_ip(self):
        self.display.fill(0)
        self.title()
        self.display.text(f'Into:',2,14,1)
        self.display.text(f'192.168.4.1',2,24,1)
        self.display.blit(self.fb_fox, 15, 31)
        self.display.blit(self.fb_fox, 47, 31)
        self.display.blit(self.fb_fox, 79, 31)
        self.display.show()

    def not_internet(self):
        self.display.fill(0)
        self.title()
        self.display.text("Not Internet", 3, 30,1)
        self.display.blit(self.fb_fox, 94, 30)
        self.display.show()

    def reconnect_wifi(self):
        self.display.fill(0)
        self.title()
        self.display.text('Reconnecting',3,14,1)
        self.display.text('Wifi...', 3, 24, 1)
        self.display.show()

    def draw_bar(self,x,y,value,max_value,width=75,height=8):
        bar_length = int((value/max_value)*width)
        self.display.rect(x,y,width,height,1)
        self.display.fill_rect(x+1,y+1,bar_length,height-2,1)