"""
    Clara Gonzalez
    Ivan Cano
    Modulo de principal del programa.
"""
import json
import logging
import random
import re
import time
import threading
import socket
import sqlite3
import os

from kafka import KafkaConsumer, KafkaProducer

global PORT
global DATABASE
global MAXPLAYERS
global PLAYERS
global CITIES
global GAME
global MAPA
global QUEUEPLAYERS

HEADER = 10
SEPARADOR = '#'
TAMANYO = 20

MINES = []
FOOD = []
NPCs = {}
QUADRANTS = {}
CITIES = {}  # diccionario con las ciudades y temperaturas
PLAYERS = {}

logging.basicConfig(filename="logfileEngine.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')

loggerk = logging.getLogger('kafka')
loggerk.setLevel(logging.WARN)

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)


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
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        res = False
        try:
            cur.execute("SELECT alias, passwd FROM player WHERE alias = ? AND passwd = ?", (ali, psw))
            query = cur.fetchall()
            res = len(query) != 0
        except sqlite3.Error as error:
            logging.error(f'ERROR LOGIN {error}')
        finally:
            con.close()
            return res

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
        while True:
            try:
                conn, addr = self.server.accept()
                n_connections = threading.active_count()
                if n_connections >= MAX_CONNECTIONS:
                    logging.warning("MAX CONNECTIONS REACHED")
                    print("MAX CONNECTIONS REACHED")
                    conn.send(b'THE SERVER HAS EXCEEDED THE LIMIT OF CONNECTIONS')
                    conn.close()
                    n_connections = threading.active_count() - 1
                else:
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.start()
                    logging.info(f"\nConnection has been established: {addr[0]}:{str(addr[1])}")
                    logging.info(f"[ACTIVE CONNECTIONS] {n_connections}")
                    logging.info(f"REMAINING CONNECTIONS: {MAX_CONNECTIONS - n_connections}")

            except Exception as exc:
                logging.error('Error accepting connections')
                logging.error('ERROR: ', exc)


def updatemap():
    global MAPA
    global FOOD
    MAPA = [[' ' for _ in range(20)] for _ in range(20)]
    for index in FOOD:
        x = index[0]
        y = index[1]
        MAPA[x][y] = 'A'.center(3)

    global MINES
    for index in MINES:
        x = index[0]
        y = index[1]
        MAPA[x][y] = 'M'.center(3)

    global NPCs
    for index in NPCs:
        position = NPCs[index]
        x = position[0]
        y = position[1]
        # Separar alias de NPCs (ej: NPC123456_09)
        level = index.split('_')[1]
        MAPA[x][y] = str(level).center(3)

    global PLAYERS
    for index in PLAYERS:
        position = PLAYERS[index]
        x = position[0]
        y = position[1]
        # Los jugadores se identifican por los dos primeros caracteres de su alias
        MAPA[x][y] = index[0:2].center(3)


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

        #       while True:
        for message in self.consumer:
            message = message.value.decode()
            # Se procesa mensaje y se envia a todos
            self.processmsg(message)
            # Comprueba si hay un jugador solo y es el ganador
            if self.checkwin():
                return
            # Comprueba si quedan jugadores vivos
            if self.checkgame():
                return

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
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        try:
            query = cur.execute("SELECT nivel, EF, EC FROM player WHERE alias = ?", (player1,))
            res = query.fetchone()
            level1 = res[0]
            ef1 = res[1]
            ec1 = res[2]
            # Se calcula una sola vez porque estan en el mismo cuadrante
            plus = calculateecoref(PLAYERS[player1])

            if plus == 'EF':
                level1 += ef1
            elif plus == 'EC':
                level1 += ec1

            if level1 < 0:
                level1 = 0

            print(f'{player1} level: ' + str(level1))

            query = cur.execute("SELECT nivel, EF, EC FROM player WHERE alias = ?", (player2,))
            res = query.fetchone()
            level2 = res[0]
            ef2 = res[1]
            ec2 = res[2]

            if plus == 'EF':
                level2 += ef2
            elif plus == 'EC':
                level2 += ec2

            if level2 < 0:
                level2 = 0

            print(f'{player2} level: ' + str(level2))

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
            # Resetear a 0 leve, EC, EF del jugador que acaba de moriri
            resetplayer(alias)
        except sqlite3.Error as error:
            logging.error(f"ERROR in SELECT {error}")
        finally:
            con.close()

    def battlenpcs(self, player, npc):
        global PLAYERS
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        try:
            query = cur.execute("SELECT nivel, EF, EC FROM player WHERE alias = ?", (player,))
            res = query.fetchone()
            level = res[0]
            ef = res[1]
            ec = res[2]
            plus = calculateecoref(PLAYERS[player])

            if plus == 'EF':
                level += ef
            elif plus == 'EC':
                level += ec

            if level < 0:
                level = 0

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

        except sqlite3.Error as error:
            logging.error(f'ERROR in SELECT: {error}')
        finally:
            con.close()

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
            logging.info(f"Player {alias} has leveled up.")
            print(f"Player {alias} has leveled up.")

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
    kafkaproducer.send('fromserver', msg.encode())


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
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    global MAPA
    try:
        map = maptostring()
        cur.execute(
            "INSERT INTO game (map, timestamp, players, npcs, cities, quadrants, mines, food) VALUES (?, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?);",
            (map, str(PLAYERS), str(NPCs), str(CITIES), str(QUADRANTS), str(MINES), str(FOOD)))
        con.commit()
        logging.info('SAVE SUCCESSFULLY')
    except sqlite3.Error as error:
        logging.error(f'ERROR SAVING {error}')
    finally:
        con.close()


def resetecef(player):
    ec = random.randint(-10, 10)
    ef = random.randint(-10, 10)

    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        cur.execute("UPDATE player set EF = ?, EC = ? where alias = ?", (ef, ec, player))
        con.commit()
        logging.info(f"SAVE SUCCESSFULLY")
    except sqlite3.Error as error:
        logging.error(f'ERROR RESET EC EF: {error}')
    finally:
        con.close()


def resetplayer(alias):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        cur.execute("UPDATE player set nivel = ?, EF = ?, EC = ? where alias = ?", (0, 0, 0, alias))
        con.commit()
        logging.info(f"RESET SUCCESSFULLY")
    except sqlite3.Error as error:
        logging.error(f'ERROR RESET PLAYER {error}')
    finally:
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


def updatelevel(alias, sum):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        query = cur.execute("SELECT nivel FROM player WHERE alias = ?", (alias,))
        res = query.fetchone()
        level = res[0] + sum
        cur.execute("UPDATE player SET nivel = ? WHERE alias = ?", (level, alias))
        con.commit()
    except sqlite3.Error as error:
        logging.error(f'ERROR UPDATING LEVEL: {error}')
    finally:
        con.close()


def resetlevel(alias):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    level = 1
    try:
        cur.execute("UPDATE player SET nivel = ? WHERE alias = ?", (level, alias))
        con.commit()
        logging.info("UPDATE")
    except sqlite3.Error as error:
        logging.error(f'ERROR RESETING LEVEL: {error}')
    finally:
        con.close()


def saveposition(alias, position):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        cur.execute("UPDATE player SET posicion = ? WHERE alias = ?", (str(position), alias))
        con.commit()
        logging.info("Saved position")
    except sqlite3.Error as error:
        logging.error(f'ERROR SAVING POSITION {error}')
    finally:
        con.close()


def maptosend():
    stringcities = []
    string = ''
    for index in QUADRANTS:
        nextcity = QUADRANTS[index]
        stringcities.append(nextcity + ': ' + str(CITIES[nextcity]) + 'ºC')

    string += '\n' + stringcities[0] + '\t\t\t\t\t\t\t' + stringcities[1] + '\n'
    string += maptostring()
    string += '\n' + stringcities[2] + '\t\t\t\t\t\t\t' + stringcities[3] + '\n'

    return string


def maptostring():
    string = ''
    string += ('\n'.join([' '.join(['{:3}'.format(item) for item in row])
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


def requestcities(ip, port):
    global CITIES
    numbers = []  # lista de numeros para comprobar que no se repiten
    counter = 0
    while counter < 4:
        n = random.randint(1, 20)
        if n not in numbers:
            numbers.append(n)
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((ip, port))
                msg = f"{n}"
                ret = communication(client, msg)
                if ret == 'Error':
                    logging.error("It is not possible to get the city")
                else:
                    datos = ret.split(':')
                    ciudad = datos[0]
                    temperatura = datos[1]
                    CITIES[ciudad] = temperatura
                    counter += 1

            except Exception as e:
                logging.error('ERROR requesting the city')
            finally:
                if 'client' in locals():
                    client.close()
    logging.info(CITIES)


def checkpreviousgame():
    # Hay partida previa si alguno de los niveles no esta a 0 y si hay mapa guardado
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    res = False
    global PLAYERS
    global NPCs
    global QUADRANTS
    global CITIES
    global MINES
    global FOOD
    try:
        cur.execute(
            "SELECT players, npcs, cities, quadrants, mines, food FROM game WHERE id == (SELECT max(id) FROM game)")
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

    except sqlite3.Error as error:
        logging.error(f'ERROR CHECKING PREVIOUS GAME {error}')
    finally:
        con.close()
        return res


def resetmaptable():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        cur.execute("DELETE FROM game")
        con.commit()
        logging.warning(f"DELETED ROWS FROM MAP TABLE")
    except sqlite3.Error as error:
        logging.error(f'ERROR DELETING MAP ROWS {error}')
    finally:
        con.close()


def checkhighestlevel():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    winners = []
    try:
        cur.execute("SELECT alias FROM player WHERE nivel == (SELECT max(nivel) FROM player)")
        query = cur.fetchall()

        for element in query:
            alias = element[0]
            winners.append(alias)

    except sqlite3.Error as error:
        logging.error(f'ERROR CHECKING LEVELS {error}')
    finally:
        con.close()
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
    producer.send('toserver', sendmsg.encode())
    resetmaptable()


def checkargs(engine, numplayers, weather, kafka) -> bool:
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
    weatheraddress = weather
    karfkaaddress = kafka

    if not (re.match(regex_1, engineaddress) or re.match(regex_2, engineaddress)):
        print("Wrong Engine address")
        logging.error("Wrong Engine address")
        return False

    if not (re.match(regex_1, weatheraddress) or re.match(regex_2, weatheraddress)):
        print("Wrong Weather address")
        logging.error("Wrong Engine address")
        return False

    if not (re.match(regex_1, karfkaaddress) or re.match(regex_2, karfkaaddress)):
        print("Wrong Kafka address")
        logging.error("Wrong Engine address")
        return False

    return True


if __name__ == '__main__':

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

    if not checkargs(parameters["ADDRESS"], str(parameters["MAXPLAYERS"]), parameters["WEATHER"], parameters["KAFKA"]):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

    address = parameters["ADDRESS"].split(':')
    IP = address[0]
    PORT = int(address[1])

    MAXPLAYERS = parameters["MAXPLAYERS"]
    DATABASE = parameters["DATABASE"]

    logging.info('MAX PLAYERS: ' + str(MAXPLAYERS))

    weatherdir = parameters["WEATHER"].split(':')
    ip_w = weatherdir[0]
    port_w = int(weatherdir[1])

    kafkadir = parameters["KAFKA"].split(":")
    ip_k = kafkadir[0]
    port_k = int(kafkadir[1])

    MAX_MINES = parameters["MAX_MINES"]
    MAX_FOOD = parameters["MAX_FOOD"]
    TIMELIMITTOSTART = parameters["TIMELIMITTOSTART"]
    TIMELIMITTOFINISH = parameters["TIMELIMITTOFINISH"]

    MAX_CONNECTIONS = parameters["MAX_CONNECTIONS"]

    try:
        consumer = KafkaConsumer('toserver',
                                 bootstrap_servers=[f'{ip_k}:{port_k}'],
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 group_id=f'engine'
                                 )

        producer = KafkaProducer(bootstrap_servers=[f'{ip_k}:{port_k}'])

    except Exception as e:
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
    # Inicia bucle inifinito, para estar siempre ejecutandose. Forma de parar servidor, ctlr+c en consola
    while True:

        if not previousgame:
            MAPA = [[' ' for _ in range(20)] for _ in range(20)]
            PLAYERS = {}  # dictionary con los jugadores
            CITIES = {}
            requestcities(ip_w, port_w)
            assigncitytoquadrant()

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
                    sendmessage(producer, alias.upper(), 'JOIN')
                    sendmessage(producer, alias.upper(), 'You have joined the game. Waiting for players...')

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
