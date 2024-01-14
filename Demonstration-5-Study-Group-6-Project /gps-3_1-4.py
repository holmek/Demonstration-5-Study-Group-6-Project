import umqtt_robust2 as mqtt
from machine import UART
from machine import Pin
from neopixel import NeoPixel
from time import sleep
import time
from gps_bare_minimum import GPS_Minimum
#########################################################################
# CONFIGURATION
gps_port = 2                               # ESP32 UART port, Educaboard ESP32 default UART port
gps_speed = 9600                           # UART speed, defauls u-blox speed
#last_value = 0.0
#########################################################################
# OBJECTS
uart = UART(gps_port, gps_speed)           # UART object creation
gps = GPS_Minimum(uart)                    # GPS object creation

n = 12                                     # number of pixerls
p = 15                                     # Pin on EPS32 used for Neopixel
np = NeoPixel(Pin(p, Pin.OUT), n)
#########################################################################
# clear
def clear():
    for i in range(n):
        np[i] = (0, 0, 0)
        np.write()

# bounce
def bounce(r, g, b, wait):
  for i in range(4 * n):
      for j in range(n):
          np[j] = (r, g, b)
      if (i // n) % 2 == 0:
          np[i % n] = (0, 0, 0)
      else:
        np[n - 1 - (i % n) ] = (0, 0, 0)
      np.write()
      time.sleep_ms(wait)

def get_adafruit_gps():
    if gps.receive_nmea_data():
        # hvis der er kommet end bruggbar værdi på alle der skal anvendes
        if gps.get_speed() != 0 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0:
            # returnerer data med adafruit gps format
            speed =str(gps.get_speed())
            lat = str(gps.get_latitude())
            lon = str(gps.get_longitude())
            return speed + "," + lat + "," + lon + "," + "0.0"
        else: # hvis ikke både hastighed, latitude og longtitude er korrekte 
            print(f"GPS data to adafruit not valid:\nspeed: {speed}\nlatitude: {lat}\nlongtitude: {lon}")
            return False
    else:
        return False

last_value = None

while True:
    try:
        # Hvis funktionen returnere en string er den True ellers returnere den False
        gps_data = get_adafruit_gps()
        gps_speed = gps.get_speed()
        #if gps_data: # hvis der er korrekt data så send til adafruit

        if gps_data: # hvis der er korrekt data så send til adafruit
            print(f'\ngps_data er: {gps_data}')
            print(f'\ngps_speed er: {gps_speed}')
            mqtt.web_print(get_adafruit_gps(), 'glra/feeds/mapfeed/csv')
            sleep(3)
            mqtt.web_print(gps_speed, 'glra/feeds/Speedfeed/csv\n')
       
        current_value = gps.get_speed()

        def check_value(current_value):
            global last_value
            if current_value == last_value:
                return True
            else:
                last_value = current_value
                print("new speed value")
                return False
        if check_value(current_value) == True:
            print("Waiting for GPS data - move GPS to a place with direct visual access to the sky and retry...")
            bounce(15, 0, 0, 40)
            clear()
        else:
            bounce(0, 15, 0, 40)
            clear()
 
            
            
            
        #For at sende beskeder til andre feeds kan det gøres sådan:
        # mqtt.web_print("Besked til anden feed", DIT_ADAFRUIT_USERNAME/feeds/DIT_ANDET_FEED_NAVN/ )
        #Indsæt eget username og feednavn til så det svarer til dit eget username og feed du har oprettet

        #For at vise lokationsdata på adafruit dashboard skal det sendes til feed med /csv til sidst
        #For at sende til GPS lokationsdata til et feed kaldet mapfeed kan det gøres således:
        #mqtt.web_print(gps_data, 'DIT_ADAFRUIT_USERNAME/feeds/mapfeed/csv')        
        sleep(4) # vent mere end 3 sekunder mellem hver besked der sendes til adafruit
        
        #mqtt.web_print("test1") # Hvis der ikke angives et 2. argument vil default feed være det fra credentials filen      
        #sleep(4)  # vent mere end 3 sekunder mellem hver besked der sendes til adafruit
        if len(mqtt.besked) != 0: # Her nulstilles indkommende beskeder
            mqtt.besked = ""            
        mqtt.sync_with_adafruitIO() # igangsæt at sende og modtage data med Adafruit IO             
        print(".", end = '') # printer et punktum til shell, uden et enter        
    # Stopper programmet når der trykkes Ctrl + c
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        mqtt.c.disconnect()
        mqtt.sys.exit()


