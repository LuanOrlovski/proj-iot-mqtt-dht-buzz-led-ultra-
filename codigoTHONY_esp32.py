
import network
from umqtt.simple import MQTTClient
from machine import Pin, PWM #import para o buzzer
import time
import json
import dht #import para o DHT

# ==== CONFIGURACOES ====
SSID = " " #  MUDAR PARA NOME DA REDE 
SENHA = " " # <-- Wi-Fi: senha 
BROKER = "broker.hivemq.com" 
PORTA = 1883
CLIENT_ID = "esp32-grupo6-zxcvbnm123" 
TOPICO_ASSINAR = "pucprGrupo06/+/Comandos" 

# led da ESP32 pino 2
led = Pin(2, Pin.OUT, value = 0) #garante que inicia off
led_estado = False

buzzer = PWM(Pin(21, Pin.OUT)) 
buzzer.duty(0) #inicia desligado 

# ==== SENSORES ====
#DHT
sensor_dht = dht.DHT11(Pin(23)) #NO FISICO TROCAR PRA DHT11 

def ler_dht(): #funcao de leitura do DHT
    while True:
        try:
            sensor_dht.measure()
            break
        except Exception as e:
            print("[MICRO] Erro ao verificar temperatura e umidade")
            time.sleep(2)
            
    return sensor_dht.temperature(), sensor_dht.humidity() 

#ultrasonico
trigger = Pin(5, Pin.OUT) # LEMBRAR PINO 5 e 18
echo = Pin(18, Pin.IN) 

#funcao de leitura do ultrasonico
def medir_distancia():
    trigger.value(0) 
    time.sleep_us(2)
    trigger.value(1) 
    time.sleep_us(10) 
    trigger.value(0) 
    
    pulse_start = time.ticks_us() 
    pulse_end = time.ticks_us() 

    while echo.value() == 0: 
        pulse_start = time.ticks_us() 

    while echo.value() == 1: 
        pulse_end = time.ticks_us() 

    pulse_duration = time.ticks_diff(pulse_end, pulse_start) 
    distancia = (pulse_duration / 2) * 0.0343 # dois trajetos logo /2 e * velocidade do som
    
    return round(distancia, 2) 

# ---- Conexao Wi-Fi ----
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao Wi-Fi...")
        wlan.connect(SSID, SENHA)
        tentativas = 0
        while not wlan.isconnected() and tentativas < 20:
            time.sleep(1)
            tentativas += 1
            print(f"Tentativa {tentativas}/20...")
    if wlan.isconnected():
        print(f"Wi-Fi conectado! IP: {wlan.ifconfig()[0]}")
        return True
    else:
        print("ERRO: Nao foi possivel conectar ao Wi-Fi")
        return False

# ---- Callback de mensagens recebidas ----
def callback_mensagem(topico, mensagem):
    global led_estado
    topico = topico.decode("utf-8")
    payload = mensagem.decode("utf-8")
    print(f"[MICRO] Recebido em '{topico}': {payload}")
    
    try:
        dados = json.loads(payload)
        comando = dados.get("comando", "")
        
        if comando == "led_on":
            led.value(1) 
            led_estado = True
            print("[MICRO] LED ligado!")
            publicar_estado_LED() 
            publicar_estado_BUZZER() 
        elif comando == "led_off": 
            led.value(0) 
            led_estado = False
            print("[MICRO] LED desligado!") 
            publicar_estado_LED() 
            publicar_estado_BUZZER() 
        elif comando == "buzzer_on":
            buzzer.freq(300) 
            buzzer.duty(300) 
            print("[MICRO] Buzzer ligado!")
            publicar_estado_LED() 
            publicar_estado_BUZZER() 
        elif comando == "buzzer_off": 
            buzzer.duty(0) 
            print("[MICRO] Buzzer desligado!")
            publicar_estado_LED() 
            publicar_estado_BUZZER() 
        elif comando == "status":
            publicar_dados_dht() 
            publicar_dados_ultra() 
        else:
            print(f"[MICRO] Comando desconhecido: {comando}")
    except Exception as e:
        print(f"[MICRO] Erro ao processar: {e}")

# ---- Funcoes de publicacao ----
def publicar_estado_LED(): 
    TOPICO_PUBLICAR = "pucprGrupo06/grupo_6_dht/dados" #led pega carona no topico do DHT
    estado_l = "ligado" if led_estado else "desligado" 
    msg = json.dumps({"led": estado_l}) 
    client.publish(TOPICO_PUBLICAR, msg, qos=1) # ADICIONADO QoS 1 AQUI
    print(f"[MICRO] Publicado: {msg}") 

def publicar_estado_BUZZER(): 
    TOPICO_PUBLICAR = "pucprGrupo06/grupo_6_ultra/dados" #buzzer pega carona no topico do ultra
    estado_b = "ligado" if buzzer.duty() > 0 else "desligado" 
    msg = json.dumps({"buzzer": estado_b}) 
    client.publish(TOPICO_PUBLICAR, msg, qos=1) #ADICIONADO QoS 1 AQUI
    print(f"[MICRO] Publicado: {msg}") 

# Leitura real em vez de random
def publicar_dados_dht(): 
    TOPICO_PUBLICAR = "pucprGrupo06/grupo_6_dht/dados" 
    temperatura, umidade = ler_dht() 
    
    dados = { 
        "temperatura": temperatura, 
        "umidade": umidade, 
        "led": "ligado" if led_estado else "desligado" #estado do led pega carona com o DHT
    } 
    msg = json.dumps(dados) 
    client.publish(TOPICO_PUBLICAR, msg, qos=1) #ADICIONADO QoS 1 AQUI
    print(f"[MICRO] Dados publicados: {msg}") 

def publicar_dados_ultra(): 
    TOPICO_PUBLICAR = "pucprGrupo06/grupo_6_ultra/dados" 
    distancia = medir_distancia() 
    
    dados = { 
        "distancia": distancia, 
        "buzzer": "ligado" if buzzer.duty() > 0 else "desligado" #estado do buzzer pega carona com o ultra
    } 
    msg = json.dumps(dados)
    client.publish(TOPICO_PUBLICAR, msg, qos=1) #ADICIONADO QoS 1 AQUI
    print(f"[MICRO] Dados publicados: {msg}")

# ---- Conexao e loop principal ----
if not conectar_wifi():
    print("Abortando: sem Wi-Fi.")
    raise SystemExit

print("[MICRO] Conectando ao broker MQTT...")
client = MQTTClient(CLIENT_ID, BROKER, port=PORTA)
client.set_callback(callback_mensagem)
client.connect()
print(f"[MICRO] Conectado a {BROKER}")
client.subscribe(TOPICO_ASSINAR, qos=1) #ADICIONADO QoS 1 AQUI NA INSCRICAO
print(f"[MICRO] Inscrito em: {TOPICO_ASSINAR}")
print("[MICRO] Aguardando comandos...\n")

# Loop principal
contador = 0
try:
    while True:
        client.check_msg()

        # A cada 30 segundos, publica dados automaticamente
        contador += 1
        if contador >= 30:
            publicar_dados_dht() 
            publicar_dados_ultra() 
            contador = 0

        time.sleep(1)

except KeyboardInterrupt:
    print("\n[MICRO] Interrompido pelo usuario.")
finally:
    client.disconnect()
    print("[MICRO] Desconectado do broker.")