"""
    Clara Gonzalez
    Modulo de principal del programa.
"""
import binascii
import hashlib
import json
import logging
import random
import re
import warnings

import aesEncryptDecrypt
import ssl
import time
import threading
import socket
import mysql.connector
from mysql.connector import errorcode
import requests
from kafka import KafkaConsumer, KafkaProducer

global engineId
global IP
global PORT
global MAXPLAYERS
global PLAYERS
global CITIES
global GAME
global MAPA
global QUEUEPLAYERS
global EMOJIS
global CHARACTERS
global DATABASE
global USERDB
global PWDDB
global DBIP
global DBPORT
global config
global API_KEY
global AESPassword

HEADER = 10
SEPARADOR = '#'
TAMANYO = 20

MINES = []
FOOD = []
NPCs = {}
QUADRANTS = {}
CITIES = {}  # diccionario con las ciudades y temperaturas
PLAYERS = {}
EMOJIS = {}
CHARACTERS = ["\U0001F435", "\U0001F436", "\U0001F43A", "\U0001F98A", "\U0001F99D", "\U0001F431", "\U0001F981",
              "\U0001F42F", "\U0001F434", "\U0001F993", "\U0001F42E", "\U0001F428", "\U0001F43C", "\U0001F438", "\U0001F437"]

logging.basicConfig(
    filename="./logs/Engine.log",
    format='%(asctime)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z',
    filemode='w',
    level=logging.DEBUG)

loggerk = logging.getLogger('kafka')
loggerk.setLevel(logging.WARN)

# suppress warning messages
warnings.filterwarnings("ignore")

class KeypressManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global GAME
        key = '-'
        while not GAME:
            print("To start a game press enter")
            key = input()
            if key == '':
                if PLAYERS:
                    GAME = True
                    return
                else:
                    print('There are not players in the game.')
                    logging.warning('There are not players in the game.')
            time.sleep(1)


class LoginManager(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((ip, port))
        except Exception as e:
            logging.error(f'ERROR BINDING {ip}:{port}', e)

    def login(self, ali, psw) -> bool:
        result = False

        try:
            con = mysql.connector.connect(**config)
            cur = con.cursor()
            sentence = "SELECT passwd, salt FROM Player WHERE alias = %s;"
            args = (ali,)
            cur.execute(sentence, args)
            query = cur.fetchone()
            hashed_password_hex = query[0]
            salt = binascii.unhexlify(query[1])

            # Hash the salted password with SHA-256
            hashed_entered_password = hashlib.pbkdf2_hmac('sha256', psw.encode(), salt, 10000)
            hashed_password = binascii.unhexlify(hashed_password_hex)

            if hashed_entered_password == hashed_password:
                logging.debug('Password is correct')
                result = True
            else:
                logging.debug('Password is incorrect')
                result = False

        except mysql.connector.Error as err:
            result = False
            con.close()
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logging.error("Database does not exist")
            else:
                logging.error(f"ERROR LOGINING: {err}")
        else:
            con.close()

        finally:
            return result

    def handle_client(self, connection, address):
        logging.info(f"NEW CONNECTION: {address}")

        c_length = int(connection.recv(HEADER))
        credentials = connection.recv(c_length).decode()

        logging.info(f"Received: {credentials}")
        data = credentials.split(":")
        # operation = data[0]

        alias = data[1]
        passwd = data[2]
        logging.info(f"LOGIN alias: {alias} passwd: {passwd}")
        res = self.login(alias, passwd)
        global QUEUEPLAYERS
        if res:
            # Login correcto, comprobar que ese jugador no esta ya a la cola o en partida
            if alias not in QUEUEPLAYERS and alias not in PLAYERS:
                QUEUEPLAYERS.append(alias)
                logging.info('Jugador anyadido a la cola.')

                # Se comprueba si hay sitio en la partida o si la partida esta en juego
                if len(QUEUEPLAYERS) > MAXPLAYERS or GAME:
                    # No hay sitio en la partida o partida en juego -> Mensaje indicando que tiene que esperar
                    connection.send(b'wait')
                    logging.info('Player waiting for a game.')
                else:
                    connection.send(b'ok')
                    logging.info('Player joined a game.')
            else:
                logging.warning(f"THE PLAYER IS ALREADY IN")
                connection.send(b'in')
        else:
            logging.error(f"IT IS NOT POSSIBLE TO LOG IN")
            connection.send(b'no')
        connection.close()

    def run(self):
        logging.info('START LoginManager')
        self.server.listen()
        logging.info(f"LISTENING TO {IP}:{PORT}")
        n_connections = threading.active_count() - 1
        logging.info(f"CURRENT CONNECTIONS: {n_connections}")

        # Wrap the server socket in an SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(certfile="./ssl/cert.pem", keyfile="./ssl/key.pem")
        secure_server_socket = context.wrap_socket(self.server, server_side=True)

        while True:
            try:
                conn, addr = secure_server_socket.accept()
                # conn, addr = self.server.accept()
                n_connections = threading.active_count() - 2

                if n_connections >= MAX_CONNECTIONS:
                    logging.warning("MAX CONNECTIONS REACHED")
                    print("MAX CONNECTIONS REACHED")
                    conn.send(b'THE SERVER HAS EXCEEDED THE LIMIT OF CONNECTIONS')
                    conn.close()
                else:
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.start()
                    logging.info(f"\nConnection has been established: {addr[0]}:{str(addr[1])}")
                    logging.info(f"[ACTIVE CONNECTIONS] {n_connections}")
                    logging.info(f"REMAINING CONNECTIONS: {MAX_CONNECTIONS - n_connections}")

            except Exception as exc:
                logging.error(f"Error accepting connections: {exc}")


def updatemap():
    global MAPA
    global FOOD
    MAPA = [['\U0001F539' for _ in range(20)] for _ in range(20)]
    for index in FOOD:
        x = index[0]
        y = index[1]
        MAPA[x][y] = '\U0001F353'

    global MINES
    for index in MINES:
        x = index[0]
        y = index[1]
        MAPA[x][y] = '\U0001F4A3'

    global NPCs
    for index in NPCs:
        position = NPCs[index]
        x = position[0]
        y = position[1]
        # Separar alias de NPCs (ej: NPC123456_09)
        level = index.split('_')[1]
        MAPA[x][y] = str(level)

    global PLAYERS
    for index in PLAYERS:
        position = PLAYERS[index]
        x = position[0]
        y = position[1]
        # Los jugadores se identifican por el emoji que se les asigna en la partida
        emoji = EMOJIS[index]
        MAPA[x][y] = emoji


class ReadMovements(threading.Thread):
    """""
    Clase que lee los movimientos que envian los jugadores a kafka, actualiza el mapa y lo guarda en la base de datos, envia mapa a todos los jugadores
    """""

    def __init__(self, kafkaproducer, kafkaconsumer):
        threading.Thread.__init__(self)
        self.producer = kafkaproducer
        self.consumer = kafkaconsumer

    def run(self):
        logging.info('START ReadMovements')

        for message in self.consumer:
            message = message.value.decode()
            msg = eval(message)
            msg = aesEncryptDecrypt.decrypt(msg, AESPassword)
            if msg is not None:
                msg = msg.decode()
                # Se procesa mensaje y se envia a todos
                self.processmsg(msg)
                # Comprueba si hay un jugador solo y es el ganador
                if self.checkwin():
                    return
                # Comprueba si quedan jugadores vivos
                if self.checkgame():
                    return
            else:
                print("It is not possible to decrypt the message.")
                logging.info("It is not possible to decrypt the message.")

    def checkgame(self):
        global GAME
        global PLAYERS
        res = False
        if GAME and not PLAYERS:
            # Si no hay, envia el end a los NPCs
            for index in NPCs:
                sendmessage(self.producer, index, 'END')
            GAME = False
            res = True

        return res

    def checkwin(self):
        res = False
        global GAME
        global PLAYERS
        if not NPCs and len(PLAYERS) == 1:
            GAME = False
            res = True
            for key in PLAYERS:
                alias = key
            sendmessage(self.producer, alias.upper(), 'WIN')
        return res

    def checkwinorend(self):
        global GAME
        global PLAYERS
        res = False
        if GAME and not PLAYERS:
            res = True

        if not NPCs and len(PLAYERS) == 1:
            res = True

        return res

    def battleplayers(self, player1, player2):
        global PLAYERS
        level1 = gettotalevel(player1)
        level2 = gettotalevel(player2)

        # Si son iguales no ocurre nada
        if level1 == level2:
            return
        elif level1 > level2:
            # player2 muere
            alias = player2
        else:
            # player1 muere
            alias = player1

        PLAYERS.pop(alias)
        logging.info(f"Player {alias} has died.")
        sendmessage(self.producer, alias.upper(), 'END')
        # Resetear a 0 leve, EC, EF del jugador que acaba de morir
        resetplayer(alias)

    def battlenpcs(self, player, npc):
        global PLAYERS
        level = gettotalevel(player)

        # Obtiene nivel de NPC
        levelnpc = int(npc.split('_')[1])
        # Si son iguales no ocurre nada
        if level == levelnpc:
            return
        elif level > levelnpc:
            # npc muere
            alias = npc
            NPCs.pop(alias)
            logging.info(f"NPC {alias} has died.")
            print(f"NPC {alias} has died.")
        else:
            # player muere
            alias = player
            PLAYERS.pop(alias)
            resetplayer(alias)
            logging.info(f"Player {alias} has died.")
            print(f"Player {alias} has died.")

        sendmessage(self.producer, alias.upper(), 'END')

    def checkplayercollision(self, alias, pos):
        oponent = 'no'
        for index in PLAYERS:
            # Hay jugador en la posicion y no es el que se acaba de mover
            if PLAYERS[index] == pos and index != alias:
                oponent = index
                break
        return oponent

    def checknpccollision(self, alias, pos):
        oponent = 'no'
        for index in NPCs:
            # Hay npc en la posicion
            if NPCs[index] == pos and index != alias:
                oponent = index
                break
        return oponent

    def checkcollisions(self, alias, pos):
        global PLAYERS
        global NPCs
        global MINES
        global FOOD
        # Hay otro jugador en la nueva posicion
        playeroponent = self.checkplayercollision(alias, pos)
        npcoponent = self.checknpccollision(alias, pos)
        if playeroponent != 'no':
            # Lucha a ver quien sobrevive
            self.battleplayers(alias, playeroponent)

        elif npcoponent != 'no':
            # Lucha a ver quien sobrevive
            self.battlenpcs(alias, npcoponent)

        elif pos in MINES:
            # Jugador pisa mina -> muere
            MINES.remove(pos)
            PLAYERS.pop(alias)
            logging.info(f"Player {alias} has died.")
            print(f"Player {alias} has died.")
            sendmessage(self.producer, alias.upper(), 'END')
            resetplayer(alias)

        elif pos in FOOD:
            # Jugador pisa alimento -> sube de nivel
            FOOD.remove(pos)
            updatelevel(alias, 1)

    def checkNPCjoin(self, alias, msg):
        regex = 'NPC[0-9]{6}_[0-9]'

        if re.match(regex, alias) and msg == 'has entered':
            logging.info('NPC joining the game')
            return True
        return False

    def processmsg(self, message):
        # Separar partes del mensaje forma: ALIAS + SEPARADOR + x:y
        print(message)
        msg = message.split(SEPARADOR)
        alias = msg[0]
        move = msg[1]

        if alias == 'SERVER':
            return
        else:
            res = self.checkNPCjoin(alias, move)

            if res:
                if alias not in NPCs:
                    level = int(alias.split('_')[1])  # N = nivel del NPC
                    newposition = freeposition(level % 4)
                    NPCs[alias] = newposition

                    # Actualiza el mapa con los cambios que se han producido
                    updatemap()
                    # Guarda mapa en base de datos
                    savemap()
                    # Envia mapa a todos los jugadores
                    map = maptosend()
                    sendmessage(self.producer, 'ALL', map)
                    logging.info("Map sent to Kafka.")

            else:
                # Recibe el movimiento en forma de N,S,W,E,NW,NE,SW,SE
                if alias in PLAYERS:
                    if GAME:
                        position = PLAYERS[alias]
                        newposition = self.calculatenewposition(position, move)
                        # Actualiza la posicion del jugador que ha enviado el mensaje
                        # No hace falta borrar posicion previa porque dictionary no admite repetidos, solo actualiza
                        PLAYERS[alias] = newposition

                        saveposition(alias, newposition)
                        updatelevel(alias, 0)
                        # Comprueba si hay colisiones con mina, alimento, NPC u otros jugadores
                        self.checkcollisions(alias, newposition)

                        # Comprueba si hay un jugadores vivos y si es el final de partida
                        if self.checkwinorend():
                            return

                        # Actualiza el mapa con los cambios que se han producido
                        updatemap()
                        # Guarda mapa en base de datos
                        savemap()
                        # Envia mapa a todos los jugadores
                        map = maptosend()
                        sendmessage(self.producer, 'ALL', map)
                        logging.info("Map sent to Kafka.")

                    else:
                        sendmessage(self.producer, alias.upper(),
                                    'The game has not started yet. Waiting for players...')
                        logging.info("The game has not started yet. Waiting for players...")

                elif alias in NPCs:
                    if GAME:
                        position = NPCs[alias]
                        newposition = self.calculatenewposition(position, move)
                        # Actualiza la posicion del npc que ha enviado el mensaje
                        NPCs[alias] = newposition

                        # Comprueba si hay colisiones con jugadores
                        playeroponent = self.checkplayercollision(alias, newposition)
                        if playeroponent != 'no':
                            # Lucha a ver quien sobrevive
                            self.battlenpcs(playeroponent, alias)

                        # Comprueba si hay un jugadores vivos y si es el final de partida
                        if self.checkwinorend():
                            return

                        # Actualiza el mapa con los cambios que se han producido
                        updatemap()
                        # Guarda mapa en base de datos
                        savemap()
                        # Envia mapa a todos los jugadores
                        map = maptosend()
                        sendmessage(self.producer, 'ALL', map)
                        logging.info("Map sent to Kafka.")

    def calculatenewposition(self, position, movement):
        x = position[0]
        y = position[1]

        if movement == 'N':
            x -= 1
        elif movement == 'S':
            x += 1
        elif movement == 'W':
            y -= 1
        elif movement == 'E':
            y += 1
        elif movement == 'NW':
            x -= 1
            y -= 1
        elif movement == 'NE':
            x -= 1
            y += 1
        elif movement == 'SW':
            x += 1
            y -= 1
        elif movement == 'SE':
            x += 1
            y += 1

        position[0] = self.checkposition(x)
        position[1] = self.checkposition(y)

        return position

    def checkposition(self, coordenate):
        return coordenate % 20


def sendmessage(kafkaproducer, receiver, message):
    msg = 'SERVER' + SEPARADOR + receiver + SEPARADOR + message
    message = aesEncryptDecrypt.encrypt(msg, AESPassword)
    kafkaproducer.send('fromserver', str(message).encode())
    # kafkaproducer.flush()


def randomposition():
    x = random.randint(0, 19)
    y = random.randint(0, 19)
    position = [x, y]

    return position


def randompositioninquadrant(quadrant):
    position = randomposition()
    nquad = calculatequadrant(position)

    while nquad != quadrant:
        position = randomposition()
        nquad = calculatequadrant(position)

    return position


def checkifplayerinposition(position):
    for index in PLAYERS:
        if PLAYERS[index] == position:
            return True
    return False


def checkifnpcinposition(position):
    for index in NPCs:
        if NPCs[index] == position:
            return True
    return False


def freeposition(quadrant):
    position = randompositioninquadrant(quadrant)
    while (position in MINES) or (position in FOOD) or checkifplayerinposition(position) or checkifnpcinposition(
            position):
        position = randompositioninquadrant(quadrant)

    return position


def generatefood():
    for index in range(MAX_FOOD):
        pos = freeposition((index % 4) + 1)
        FOOD.append(pos)


def generatemines():
    for index in range(MAX_MINES):
        pos = freeposition((index % 4) + 1)
        MINES.append(pos)


def savemap():
    global MAPA
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "UPDATE Game set map = %s, stamp = NOW(), players = %s, npcs = %s, mines = %s, food = %s, characters = %s WHERE id = %s;"
        args = (str(MAPA), str(PLAYERS), str(NPCs), str(MINES), str(FOOD), str(EMOJIS), engineId)
        cur.execute(sentence, args)
        con.commit()
        logging.info('SAVE SUCCESSFULLY')
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR SAVING MAP: {err}")
    else:
        con.close()


def initializeGameTable():
    global MAPA
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "INSERT INTO Game (id, stamp, cities, quadrants) VALUES (%s, NOW(), %s, %s);"
        args = (engineId, str(CITIES), str(QUADRANTS))
        cur.execute(sentence, args)
        con.commit()
        logging.info('SAVE SUCCESSFULLY')
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR INITIALIZING GAME TABLE: {err}")
    else:
        con.close()


def resetecef(player):
    ec = random.randint(-10, 10)
    ef = random.randint(-10, 10)

    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "UPDATE Player set EF = %s, EC = %s where alias = %s;"
        args = (ef, ec, player)
        cur.execute(sentence, args)
        con.commit()
        logging.info(f"SAVE SUCCESSFULLY")
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR RESETING EC EF: {err}")
    else:
        con.close()


def resetplayer(alias):
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "UPDATE Player set nivel = %s, niveltotal = %s, EF = %s, EC = %s WHERE alias = %s;"
        args = (0, 0, 0, 0, alias)
        cur.execute(sentence, args)
        con.commit()
        logging.info(f"RESET SUCCESSFULLY")
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR RESETING Player: {err}")
    else:
        con.close()


def assigncitytoquadrant():
    global QUADRANTS
    QUADRANTS = {}
    counter = 1
    for index in CITIES:
        QUADRANTS[counter] = index
        counter += 1


def calculateecoref(position):
    quadrant = calculatequadrant(position)
    city = QUADRANTS[quadrant]
    res = ''
    temperature = int(CITIES[city])
    if temperature <= 10:
        res = 'EF'
    elif temperature >= 25:
        res = 'EC'

    return res


def calculatequadrant(position):
    x = position[0]
    y = position[1]

    if x < 10 and y < 10:
        quadrant = 1
    elif x < 10 and y > 9:
        quadrant = 2
    elif x > 9 and y < 10:
        quadrant = 3
    elif x > 9 and y > 9:
        quadrant = 4

    return quadrant


def gettotalevel(player):
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT niveltotal FROM Player WHERE alias = %s;"
        args = (player,)
        cur.execute(sentence, args)
        res = cur.fetchone()
        level = res[0]
        logging.debug(f'{player} level: ' + str(level))
        return level

    except mysql.connector.Error as err:
        level = 0
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR IN SELECT: {err}")
        return level
    else:
        con.close()


def updatelevel(alias, sum):
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT nivel, EF, EC FROM Player WHERE alias = %s;"
        args = (alias,)
        cur.execute(sentence, args)
        res = cur.fetchone()
        level = res[0] + sum
        ef = res[1]
        ec = res[2]
        plus = calculateecoref(PLAYERS[alias])

        totallevel = level
        if plus == 'EF':
            totallevel += ef
        elif plus == 'EC':
            totallevel += ec

        if totallevel < 0:
            totallevel = 0

        if sum > 0:
            logging.info(f"Player {alias} has leveled up to level {level}.")
            print(f"Player {alias} has leveled up to level {level}")

        sentence = "UPDATE Player SET nivel = %s, niveltotal = %s WHERE alias = %s;"
        args = (level, totallevel, alias)
        cur.execute(sentence, args)
        con.commit()
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
    else:
        con.close()


def resetlevel(alias):
    level = 1
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "UPDATE Player SET nivel = %s, niveltotal = %s WHERE alias = %s;"
        args = (level, 0, alias)
        cur.execute(sentence, args)
        con.commit()
        logging.info("UPDATE")
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
    else:
        con.close()


def saveposition(alias, position):
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "UPDATE Player SET posicion = %s WHERE alias = %s;"
        args = (str(position), alias)
        cur.execute(sentence, args)
        con.commit()
        logging.info("Saved position")
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
    else:
        con.close()


def maptosend():
    global MAPA
    stringcities = []
    string = ''
    for index in QUADRANTS:
        nextcity = QUADRANTS[index]
        stringcities.append(nextcity + ': ' + str(CITIES[nextcity]) + 'ºC')

    string += stringcities[0] + '\t\t\t\t' + stringcities[1] + '\n'
    string += maptostring()
    string += '\n' + stringcities[2] + '\t\t\t\t' + stringcities[3]
    return string


def maptostring():

    string = ''
    string += ('\n'.join([' '.join(['{:1}'.format(item) for item in row])
                          for row in MAPA]))
    return string


def communication(client, message) -> str:
    length = str(len(message)).encode()
    length_msg = length + b" " * (HEADER - len(length))
    logging.info(f"sending: {length_msg}")
    client.send(length_msg)
    logging.info(f"sending: {message.encode()}")
    client.send(message.encode())

    c_length = int(client.recv(HEADER))
    respuesta = client.recv(c_length).decode()
    return respuesta


def requestcities():
    # leer lista de ciudades
    global CITIES
    try:
        with open("Cities.txt", "r") as read_file:
            logging.debug("Converting txt encoded data into Python list")
            listcities = read_file.read().splitlines()
            logging.debug(str(listcities))
    except Exception as e:
        logging.error(f'ERROR reading list: {e}')
        exit()

    while len(CITIES) < 4:
        n = random.randint(0, 19)
        askCity = listcities[n]
        url = f"https://api.openweathermap.org/data/2.5/weather?q={askCity}&appid={API_KEY}"
        response = requests.get(url)
        data = json.loads(response.text)
        temp = data["main"]["temp"] - 273.15
        CITIES[askCity] = round(temp)

    logging.info(CITIES)


def checkemoji(emoji):
    for index in EMOJIS:
        if EMOJIS[index] == emoji:
            return True
    return False


def assignemoji(player):
    global EMOJIS
    n = random.randint(0, len(CHARACTERS)-1)
    emoji = CHARACTERS[n]

    while checkemoji(emoji):
        n = random.randint(0, len(CHARACTERS))
        emoji = CHARACTERS[n]

    EMOJIS[player] = emoji
    return emoji


def checkpreviousgame():
    # Hay partida previa si hay mapa guardado
    res = False
    global PLAYERS
    global NPCs
    global QUADRANTS
    global CITIES
    global MINES
    global FOOD
    global EMOJIS
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT players, npcs, cities, quadrants, mines, food, characters FROM Game WHERE id = %s AND stamp = (SELECT max(stamp) FROM Game);"
        args = (engineId,)
        cur.execute(sentence, args)
        query = cur.fetchone()
        # Devuelve tuplas con los datos
        if not query:
            logging.info("There is not previous game.")
            res = False
        else:
            players = query[0]
            PLAYERS = eval(players)
            res = True

            if not PLAYERS:
                res = False

            if res:
                npcs = query[1]
                NPCs = eval(npcs)
                cities = query[2]
                CITIES = eval(cities)
                quadrants = query[3]
                QUADRANTS = eval(quadrants)
                mines = query[4]
                MINES = eval(mines)
                food = query[5]
                FOOD = eval(food)
                emojis = query[6]
                EMOJIS = eval(emojis)

    except mysql.connector.Error as err:
        res = False
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
    else:
        con.close()

    finally:
        return res


def resetmaptable():
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "TRUNCATE TABLE Game"
        cur.execute(sentence)
        con.commit()
        logging.warning(f"DELETED ROWS FROM MAP TABLE")
    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
    else:
        con.close()


def checkhighestlevel():
    winners = []
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT alias FROM player WHERE nivel == (SELECT max(nivel) FROM player);"
        cur.execute(sentence)
        query = cur.fetchall()

        for element in query:
            alias = element[0]
            winners.append(alias)

    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
    else:
        con.close()
    finally:
        return winners


def timeouttostart():
    global PLAYERS
    # Si hay players es que puede empezar partida
    if PLAYERS:
        print("Time to start the game...")
        global GAME
        GAME = True


def timeouttofinish():
    msg = 'TIMEOUT'
    winners = checkhighestlevel()

    for element in winners:
        sendmessage(producer, element, 'WIN')

    for element in PLAYERS:
        if element not in winners:
            sendmessage(producer, element, msg)

    PLAYERS.clear()
    sendmsg = 'SERVER' + SEPARADOR + msg
    message = aesEncryptDecrypt.encrypt(sendmsg, AESPassword)
    producer.send('toserver', str(message).encode())
    # producer.flush()
    resetmaptable()


def readpassword():
    global AESPassword
    try:
        with open("AESPassword.json", "r") as read_file:
            logging.info("Converting JSON encoded data into Python dictionary")
            pwd = json.load(read_file)
            logging.info(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    AESPassword = pwd["AESPWD"]


def checkargs(engine, numplayers, mysql, kafka) -> bool:
    """
    Comprueba si los parametros recibidos son correctos
    """

    players = numplayers
    regex = '^[0-9]'
    if not re.match(regex, players):
        print("Wrong format numplayers")
        return False

    regex_1 = '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}$'
    regex_2 = '^\S+:[0-9]{1,5}$'
    engineaddress = engine
    dbaddress = mysql
    karfkaaddress = kafka

    if not (re.match(regex_1, engineaddress) or re.match(regex_2, engineaddress)):
        print("Wrong Engine address")
        logging.error("Wrong Engine address")
        return False

    if not (re.match(regex_1, dbaddress) or re.match(regex_2, dbaddress)):
        print("Wrong MySQL address")
        logging.error("Wrong MySQL address")
        return False

    if not (re.match(regex_1, karfkaaddress) or re.match(regex_2, karfkaaddress)):
        print("Wrong Kafka address")
        logging.error("Wrong Kafka address")
        return False

    return True


if __name__ == '__main__':
    global engineId
    global IP
    global PORT
    global MAXPLAYERS
    global DATABASE
    global MAPA
    global QUEUEPLAYERS
    QUEUEPLAYERS = []
    global MAX_FOOD
    global MAX_MINES
    global MAX_CONNECTIONS
    global TIMELIMITTOSTART
    global TIMELIMITTOFINISH
    global GAME
    GAME = False

    try:

        with open("EngineParameters.json", "r") as read_file:
            logging.info("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.info(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    if not checkargs(parameters["ADDRESS"], str(parameters["MAXPLAYERS"]), parameters["MYSQL"], parameters["KAFKA"]):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

    engineId = parameters["ADDRESS"]
    address = engineId.split(':')
    IP = address[0]
    PORT = int(address[1])

    MAXPLAYERS = parameters["MAXPLAYERS"]

    logging.info('MAX PLAYERS: ' + str(MAXPLAYERS))

    kafkadir = parameters["KAFKA"].split(":")
    ip_k = kafkadir[0]
    port_k = int(kafkadir[1])

    MAX_MINES = parameters["MAX_MINES"]
    MAX_FOOD = parameters["MAX_FOOD"]
    TIMELIMITTOSTART = parameters["TIMELIMITTOSTART"]
    TIMELIMITTOFINISH = parameters["TIMELIMITTOFINISH"]

    MAX_CONNECTIONS = parameters["MAX_CONNECTIONS"]
    DATABASE = parameters["DATABASE"]
    USERDB = parameters["USER"]
    PWDDB = parameters["PWD"]
    dbserver = parameters["MYSQL"].split(':')
    DBIP = dbserver[0]
    DBPORT = int(dbserver[1])

    API_KEY = parameters["APIKEY"]

    config = {
        'user': USERDB,
        'password': PWDDB,
        'host': DBIP,
        'database': DATABASE,
        'raise_on_warnings': True
    }

    try:
        consumer = KafkaConsumer('toserver',
                                 bootstrap_servers=[f'{ip_k}:{port_k}'],
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 group_id=f'engine'
                                 )

        producer = KafkaProducer(bootstrap_servers=[f'{ip_k}:{port_k}'])

    except Exception as e:
        if 'consumer' in locals():
            consumer.close()
        logging.error(f'ERROR in kafka: {e}')

    # Lista con los hilos que ejecuta el engine: hilos para los login de los jugadores, hilo para leer movimientos
    login = LoginManager(IP, PORT)
    read = ReadMovements(producer, consumer)

    login.start()

    # Comprueba si habia partida a medias
    previousgame = checkpreviousgame()

    read.start()
    GAME = False

    readpassword()

    # Inicia bucle inifinito, para estar siempre ejecutandose. Forma de parar servidor, ctlr+c en consola
    while True:

        if not previousgame:
            MAPA = [['\U0001F539' for _ in range(20)] for _ in range(20)]
            PLAYERS = {}  # dictionary con los jugadores
            CITIES = {}
            requestcities()
            assigncitytoquadrant()
            initializeGameTable()

            # Lee los emojis para los players
            # readCharacters()

            # Genera los alimentos y las minas del mapa
            generatefood()
            generatemines()
            updatemap()

            # Inicio de partida por pulsacion de tecla, tiempo o que se llene el maximo de Jugadores
            timertostart = threading.Timer(TIMELIMITTOSTART, timeouttostart)
            timertostart.start()
            keypress = KeypressManager()
            keypress.start()
            # Comprobar cola de jugadores para meter esos a partida
            # Si la partida no esta en juego y hay espacio para mas jugadores
            while len(PLAYERS) < MAXPLAYERS and not GAME:
                if not QUEUEPLAYERS:
                    # La cola esta vacia
                    logging.info("Waiting for players...")
                    time.sleep(1)
                else:
                    # Jugadores en cola
                    n = random.randint(0, 3)
                    pos = freeposition((n % 4) + 1)
                    # Se elimina de la cola el primero y se anyade al diccionario de jugadores con la posicion asignada
                    alias = QUEUEPLAYERS.pop(0)
                    PLAYERS[alias] = pos
                    saveposition(alias, pos)
                    updatelevel(alias, 0)
                    sendmessage(producer, alias.upper(), 'JOIN')
                    sendmessage(producer, alias.upper(), 'You have joined the game. Waiting for players...')
                    emoji = assignemoji(alias)
                    msg = "Your player will be: " + emoji
                    sendmessage(producer, alias.upper(), msg)

            GAME = True
            # Si llega aqui parar el timer y el keypress
            timertostart.cancel()
            # keypress.stop()

            # Reset del nivel de todos los jugadores, calculo de su EC y EF para la partida
            for index in PLAYERS:
                resetlevel(index)
                resetecef(index)

            # resetmaptable()

        GAME = True
        updatemap()
        # Jugadores para partida preparados --> enviar mensaje a todos indicando inicio partida
        sendmessage(producer, 'ALL', 'START')
        print("START GAME")
        # Final de partida por tiempo
        timertofinish = threading.Timer(TIMELIMITTOFINISH, timeouttofinish)
        timertofinish.start()

        actualmap = maptosend()
        savemap()
        print(actualmap)
        sendmessage(producer, 'ALL', actualmap)

        # Espera a que acabe partida
        read.join()
        timertofinish.cancel()
        print("END GAME")
        NPCs = {}
        PLAYERS = {}
        CITIES = {}
        # Pone game a false para indicar que no hay partida en curso
        GAME = False
        previousgame = False
        resetmaptable()
        read = ReadMovements(producer, consumer)
        read.start()
