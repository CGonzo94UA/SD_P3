"""
    Clara Gonzalez Sanchez

    Clase que representa un jugador de la partida
"""
import json
import logging
import random
import threading
import re
import time

from kafka import KafkaConsumer, KafkaProducer

import aesEncryptDecrypt

logging.basicConfig(
    filename="./logs/NPC.log",
    format='%(asctime)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z',
    filemode='w',
    level=logging.DEBUG)

# String con la contrasenya para encriptar con AES
global AESPassword
# String que guarda el alias del jugador
global ALIAS
# Variable que indica si la partida se ha finalizado para este jugador
global END
# Lista con los movimientos validos de un jugador
MOVEMENTS = ['N', 'S', 'W', 'E', 'NW', 'NE', 'SW', 'SE']

HEADER = 10
SEPARADOR = '#'
END = False


class MapManager(threading.Thread):
    """""
    Clase que representa el hilo que esta constantemente escuchando a kafka para actualizar el mapa del npc
    """""

    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port

    def run(self):
        try:
            logging.info('START MapManager')
            global ALIAS
            consumer = KafkaConsumer('fromserver',
                                     bootstrap_servers=[f'{self.ip}:{self.port}'],
                                     auto_offset_reset='earliest',
                                     enable_auto_commit=True,
                                     group_id=f'{ALIAS}'
                                     )
            global END
            for message in consumer:
                message = message.value.decode()
                msg = eval(message)
                msg = aesEncryptDecrypt.decrypt(msg, AESPassword)
                msg = msg.decode()
                # Separar partes del mensaje procedente del servidor
                msg = msg.split(SEPARADOR)
                receiver = msg[1]
                if receiver == 'ALL' or receiver == 'NPC' or receiver == ALIAS.upper():
                    mensaje = msg[2]
                    if mensaje == 'START':
                        print("START")
                    elif mensaje == 'END':
                        # Senyal de muerte
                        print("END GAME")
                        END = True
                        return
                    elif mensaje == 'TIMEOUT':
                        # Senyal de muerte
                        print("TIME OUT, END GAME")
                        END = True
                        return
                    elif mensaje == 'WIN':
                        print("CHAMPION! END GAME")
                        END = True
                        return
                    else:
                        print(mensaje)
        except Exception as e:
            consumer.close()
            logging.error(f"ERROR in MapManager: {e}")
        finally:
            if 'consumer' in locals():
                consumer.close()
            logging.info("END MapManager")


class MovementManager(threading.Thread):
    """""
    Clase que representa el hilo que envia los movimientos del npc a kafka. Actua como productor en el topin 'toserver'
    """""

    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port

    def run(self):
        try:
            logging.info("START MovementManager")
            producer = KafkaProducer(bootstrap_servers=[f'{self.ip}:{self.port}'])
            global ALIAS
            msg = ALIAS.upper() + SEPARADOR + 'has entered'
            message = aesEncryptDecrypt.encrypt(msg, AESPassword)
            producer.send('toserver', str(message).encode())
            producer.flush()
            global END
            while not END:
                rand = random.randint(0, 7)
                movement = MOVEMENTS[rand]

                # Enviar a kafka un mensaje con el movimiento
                msg = ALIAS.upper() + SEPARADOR + movement
                print(msg)
                # Envia a kafka topic: toserver, mensaje
                message = aesEncryptDecrypt.encrypt(msg, AESPassword)
                producer.send('toserver', str(message).encode())
                producer.flush()

                # Espera un segundo antes volver a realizar el bucle y generar nuevo movimiento
                time.sleep(5)

            return

        except Exception as e:
            producer.close()
            logging.error(f"ERROR in MovementManager: {e}")
        finally:
            if 'producer' in locals():
                producer.close()
            logging.info("END MovementManager")


def updatemap(newmap):
    print(newmap)


def checkargs(kafka) -> bool:
    """
    Indica si el formato de los parametros es el correcto
    """

    regex_1 = '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}$'
    regex_2 = '^\S+:[0-9]{1,5}$'
    karfkaaddress = kafka

    if not (re.match(regex_1, karfkaaddress) or re.match(regex_2, karfkaaddress)):
        print("Wrong Kafka address")
        return False

    return True


if __name__ == '__main__':

    try:
        with open("NPCParameters.json", "r") as read_file:
            logging.info("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.info(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    if not checkargs(parameters["KAFKA"]):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

    kafkadir = parameters["KAFKA"].split(":")
    ip_k = kafkadir[0]
    port_k = int(kafkadir[1])

    global AESPassword
    AESPassword = parameters["AESPWD"]

    global ALIAS
    level = random.randint(1, 15)
    identification = random.randint(100000, 999999)
    ALIAS = 'NPC' + str(identification) + '_' + str(level)

    # Se conecta a kafka como consumidor y productor, un hilo para enviar los movimientos del jugador y otro para leer las actualizaciones del mapa
    thread = [MovementManager(ip_k, port_k), MapManager(ip_k, port_k)]
    for i in thread:
        i.start()

    for i in thread:
        i.join()
    exit()
