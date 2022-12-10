"""
    Clara Gonzalez
    Ivan Cano


    Clase que representa un jugador de la partida
"""
import json
import logging
import ssl
import threading
import socket
import re
import time

from kafka import KafkaConsumer, KafkaProducer

# String que guarda el alias del jugador
global ALIAS
# Variable que indica si la partida se ha finalizado para este jugador
global END
# Variable que inidica que la partida se ha iniciado
global GAME
# Variable que inidica que el player esta el cola
global QUEUE
# Lista con los movimientos validos de un jugador
MOVEMENTS = ['N', 'S', 'W', 'E', 'NW', 'NE', 'SW', 'SE']

HEADER = 10
SEPARADOR = '#'
END = False
QUEUE = False

logging.basicConfig(filename="logfilePlayer.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


class MapManager(threading.Thread):
    """""
    Clase que representa el hilo que esta constantemente escuchando a kafka para actualizar el mapa del jugador
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
            global QUEUE
            #            while True:
            for message in consumer:
                message = message.value.decode()
                # Separar partes del mensaje procedente del servidor
                msg = message.split(SEPARADOR)
                receiver = msg[1]
                if receiver == 'ALL' or receiver == ALIAS.upper():
                    mensaje = msg[2]
                    if mensaje == 'JOIN':
                        # Player deja de estar en cola y se une a partida
                        QUEUE = False

                    if not QUEUE:
                        if mensaje == 'START':
                            print("START")
                        elif mensaje == 'END':
                            # Senyal de muerte para el jugador
                            print("GAME OVER...")
                            print("Press Enter to leave the game.")
                            END = True
                            return
                        elif mensaje == 'TIMEOUT':
                            # Senyal de muerte para el jugador
                            print("TIME OUT, GAME OVER...")
                            print("Press Enter to leave the game.")
                            END = True
                            return
                        elif mensaje == 'WIN':
                            print("CHAMPION!")
                            END = True
                            print("Press Enter to leave the game.")
                            return
                        else:
                            updatemap(mensaje)
        except Exception as e:
            consumer.close()
            logging.error(f'ERROR in MapManager: {e}')
        finally:
            if 'consumer' in locals():
                consumer.close()
            logging.info("END MapManager")


class MovementManager(threading.Thread):
    """""
    Clase que representa el hilo que envia los movimientos del jugador a kafka. Actua como productor en el topin 'toserver'
    """""

    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port

    def run(self):
        try:
            logging.info("START MovementManager")
            producer = KafkaProducer(bootstrap_servers=[f'{self.ip}:{self.port}'])
            global END
            while not END:

                movement = input()
                valido = True
                global MOVEMENTS

                if movement.upper() not in MOVEMENTS:
                    if END and movement == '':
                        return
                    else:
                        print("Please, choose a correct movement.")
                        valido = False

                if valido:
                    global ALIAS
                    # Enviar a kafka un mensaje con el movimiento del jugador
                    msg = ALIAS.upper() + SEPARADOR + movement.upper()
                    # Envia a kafka topic: toserver, mensaje
                    producer.send('toserver', msg.encode())
                    # producer.flush() / producer.poll()

                # Espera un segundo antes volver a realizar el bucle y poder comprobar valor de END
                time.sleep(1)

            return

        except Exception as e:
            producer.close()
            logging.error(f'ERROR in MovementManager: {e}')
        finally:
            if 'producer' in locals():
                producer.close()
            logging.info("END MovementManager")


def updatemap(newmap):
    print(newmap)
    if newmap != 'You have joined the game. Waiting for players...' and newmap != 'JOIN':
        print("Choose your next move: N,S,W,E,NW,NE,SW,SE")


def login(ip, port) -> bool:
    print("Enter your data: ")
    global ALIAS
    alias = input("alias: ")
    ALIAS = alias.upper()
    passwd = input("passwd: ")
    credentials = f"l:{ALIAS}:{passwd}"
    ret = ""

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        # context.load_cert_chain(certfile="certRegistry.pem", keyfile="certRegistry.pem")
        # context.load_verify_locations(cafile='server.crt')
        secure_client_socket = context.wrap_socket(client_socket)

        secure_client_socket.connect((ip, port))
        ret = communication(secure_client_socket, credentials)
        if ret == 'ok':
            logging.info("SUCCESSFULLY LOGGED IN")
        elif ret == 'no':
            logging.info("ALIAS OR PASSWORD WRONG")
        elif ret == 'in':
            logging.warning("YOU ARE ALREADY LOG IN")
        elif ret == 'wait':
            # En espera para siguiente PARTIDA
            logging.info("WAITING FOR PLAYERS...")
        else:
            logging.info("Engine has to many connections")

    except Exception as e:
        logging.error(f'ERROR in login: {e}')
    finally:
        if 'secure_client_socket' in locals():
            secure_client_socket.close()

    logging.info("Close connection in LOGIN")
    return ret


def communication(client: object, message: object) -> str:
    length = str(len(message)).encode()
    length_msg = length + b" " * (HEADER - len(length))
    logging.info(f"sending: {length_msg}")
    client.send(length_msg)
    logging.info(f"sending: {message.encode()}")
    client.send(message.encode())
    respuesta = client.recv(2)
    return respuesta.decode()


def signinplayer(ip, port):
    """
        :param port: int
        :param ip: string
        :return:
    """
    global ALIAS
    alias = input("alias: ")
    ALIAS = alias.upper()
    passwd = input("password: ")
    credentials = f"r:{ALIAS}:{passwd}"
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))
        ret = communication(client, credentials)
        if ret == 'ok':
            print("REGISTERED SUCCESSFULLY")
            logging.info("REGISTERED SUCCESSFULLY")
        elif ret == 'exists':
            print("ERROR REGISTERING, player already exists")
            logging.error("ERROR REGISTERING, player already exists")
        else:
            print("ERROR REGISTERING")
            logging.error("ERROR REGISTERING")
    except Exception as e:
        logging.error(f'ERROR registering: {e}')
        print("It is not possible to sign in. Try again later.")
    finally:
        if 'client' in locals():
            client.close()

    logging.info("Close connection in SIGN IN")


def updateplayer(ip, port) -> bool:
    print("Current alias and password:")
    global ALIAS
    alias = input("alias: ")
    ALIAS = alias.upper()
    passwd = input("passwd: ")
    credentials = f"l:{ALIAS}:{passwd}:"

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))
        ret = communication(client, credentials)
        if ret == 'ok':
            print("Enter your new alias and password. Leave blank the data you do not want to modify")
            n_alias = input("new alias: ")
            n_passwd = input("new password: ")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))
            credentials = f"u:{ALIAS}:{n_alias.upper()}:{n_passwd}"
            update = communication(client, credentials)
            if update == 'ok':
                print("PROFILE UPDATED SUCCESSFULLY")
                logging.info("PROFILE UPDATED SUCCESSFULLY")
            elif update == 'no':
                print("IT IS NOT POSSIBLE TO UPDATE YOUR PROFILE")
                logging.info("IT IS NOT POSSIBLE TO UPDATE YOUR PROFILE")
        else:
            print('Alias or password wrong')
            logging.error('Alias or password wrong')
    except Exception as e:
        logging.error(f'ERROR updating: {e}')
        print('It is not possible to update your profile now. Try again later.')

    finally:
        if 'client' in locals():
            client.close()

    logging.info("Close connection in UPDATE PLAYER")


def menu():
    print("R - Sign in: Create player profile")
    print("U - Update: Update your profile")
    print("L - Login: Join a game")
    print("Q - Quit")


def checkargs(engine, registry, kafka) -> bool:
    """
    Indica si el formato de los parametros es el correcto
    """

    regex_1 = '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}$'
    regex_2 = '^\S+:[0-9]{1,5}$'
    engineaddress = engine
    registryaddress = registry
    karfkaaddress = kafka

    if not (re.match(regex_1, engineaddress) or re.match(regex_2, engineaddress)):
        print("Wrong Engine address")
        return False

    if not (re.match(regex_1, registryaddress) or re.match(regex_2, registryaddress)):
        print("Wrong Registry address")
        return False

    if not (re.match(regex_1, karfkaaddress) or re.match(regex_2, karfkaaddress)):
        print("Wrong Kafka address")
        return False

    return True


if __name__ == '__main__':

    try:
        with open("PlayerParameters.json", "r") as read_file:
            logging.info("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.info(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    if not checkargs(parameters["ENGINE"], parameters["REGISTRY"], parameters["KAFKA"]):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

    enginedir = parameters["ENGINE"].split(':')
    ip_e = enginedir[0]
    port_e = int(enginedir[1])

    registrydir = parameters["REGISTRY"].split(':')
    ip_r = registrydir[0]
    port_r = int(registrydir[1])

    kafkadir = parameters["KAFKA"].split(":")
    ip_k = kafkadir[0]
    port_k = int(kafkadir[1])

    option = ""
    while option.upper() != "Q":
        menu()
        option = input("option> ")
        if option.upper() == 'Q':
            exit()
        elif option.upper() == 'R':
            signinplayer(ip_r, port_r)
        elif option.upper() == 'U':
            updateplayer(ip_r, port_r)
        elif option.upper() == 'L':
            res = login(ip_e, port_e)
            if res == 'ok':
                print('Waiting for the server, starting the game.')
                # Se conecta a kafka como consumidor y productor, un hilo para enviar los movimientos del jugador y otro para leer las actualizaciones del mapa
                thread = [MovementManager(ip_k, port_k), MapManager(ip_k, port_k)]
                for i in thread:
                    i.start()

                for i in thread:
                    i.join()

            elif res == 'no':
                print("Alias or password wrong.")
            elif res == '':
                print("It is not possible to log in. Try again later.")
            elif res == 'in':
                print("You are already logged in.")
            else:
                print("IN QUEUE: Waiting for players...")
                QUEUE = True

                # Se conecta a kafka como consumidor y productor, un hilo para enviar los movimientos del jugador y otro para leer las actualizaciones del mapa
                thread = [MovementManager(ip_k, port_k), MapManager(ip_k, port_k)]
                for i in thread:
                    i.start()

                for i in thread:
                    i.join()

        else:
            print("Please, choose an option from the menu")
    exit()
