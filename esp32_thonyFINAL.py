import dht
from machine import Pin
import time

sensor_dht = dht.DHT11(Pin(23))

while True:
        try:
            sensor_dht.measure()
            break
        except Exception as e:
            print("[MICRO] Erro ao verificar temperatura e umidade")
            time.sleep(2)
print(sensor_dht.temperature())