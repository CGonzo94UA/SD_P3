"""
    Clara Gonzalez

    Modulo de registro de los jugadores en el nucleo. Recibe como parametros el puerto de escucha
"""
import binascii
import json
import logging
import socket
import mysql.connector
from mysql.connector import errorcode
import threading
import re
from datetime import datetime
import hashlib
import os
import ssl
from flask import Flask, jsonify, request

global IP
global PORT
global MAXCONNECTIONS
global DATABASE
global USERDB
global PWDDB
global DBIP
global DBPORT
global config

HEADER = 10
current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

logging.basicConfig(
    filename="Registry.log",
    format='%(asctime)s - %(message)s',
    filemode='w',
    level=logging.DEBUG)


class APIManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        app = Flask(__name__)


class SocketManager(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)

        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((ip, port))
            logging.debug(f'Socket binded to {ip}:{port}')
        except Exception as e:
            logging.error(f'ERROR BINDING {ip}:{port} - {e}')

    def handle_client(self, connection, address):
        res = False
        logging.debug(f"NEW CONNECTION: {address}")

        c_length = int(connection.recv(HEADER))
        credentials = connection.recv(c_length).decode()

        logging.debug(f"Received: {credentials}")
        data = credentials.split(":")
        operation = data[0]

        # Registry - Registrar
        if operation.upper() == 'R':
            alias = data[1]
            passwd = data[2]
            logging.info(f"{address[0]} - REGISTRY - PARAMETERS alias: {alias} passwd: {passwd}")
            res = sign(alias, passwd)
        # Update - Actualizar
        elif operation.upper() == 'U':
            alias = data[1]
            n_alias = data[2]
            n_passwd = data[3]
            logging.info(f"{address[0]} - UPDATE profile of player: {alias}")
            res = modify(alias, n_alias, n_passwd)
        elif operation.upper() == 'L':
            alias = data[1]
            passwd = data[2]
            logging.info(f"{address[0]} - LOGIN for update - alias: " + alias + " passwd: " + passwd)
            res = login(alias, passwd)
        if res:
            connection.send(b'ok')
        else:
            logging.error(f"{address[0]} - ERROR: IT IS NOT POSSIBLE TO REGISTER OR UPDATE: ")
            connection.send(b'no')
        connection.close()

    def run(self):
        print("AA_Registry started")
        print(f"LISTENING TO {IP}:{PORT}")
        self.server.listen()
        logging.debug("AA_Registry started")
        logging.debug(f"LISTENING TO {IP}:{PORT}")
        n_connections = threading.active_count() - 1
        logging.debug(f"CURRENT CONNECTIONS: {n_connections}")

        # Wrap the server socket in an SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(certfile="certRegistry.pem", keyfile="certRegistry.pem")
        # context.verify_mode = ssl.CERT_REQUIRED
        # context.load_verify_locations(cafile=client_certs)
        secure_server_socket = context.wrap_socket(self.server, server_side=True)

        while True:
            try:
                conn, addr = secure_server_socket.accept()
                n_connections = threading.active_count()
                if n_connections >= MAXCONNECTIONS:
                    logging.error(f"{addr} - CONNECTION - ERROR: MAX CONNECTIONS REACHED")
                    print("MAX CONNECTIONS REACHED")
                    conn.send(b"THE SERVER HAS EXCEEDED THE LIMIT OF CONNECTIONS")
                    conn.close()
                    n_connections = threading.active_count() - 1
                else:
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.start()
                    logging.debug("Connection has been established: " + addr[0] + ":" + str(addr[1]))
                    logging.debug(f"[ACTIVE CONNECTIONS] {n_connections}")
                    logging.debug(f"REMAINING CONNECTIONS: {MAXCONNECTIONS - n_connections}")

            except Exception as exc:
                logging.error(f"Error accepting connections: {exc}")


def sign(ali: str, psw: str) -> bool:
    """
    :param alias: nick del jugador
    :param passwd: contrasenya del jugador
    :return: True/False si se ha registrado con exito o no al jugador
    """

    result = False

    # Generate 32 random bytes
    salt = os.urandom(32)
    hashed_password = hashlib.pbkdf2_hmac('sha256', psw.encode(), salt, 10000)

    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "INSERT INTO Player (alias, passwd, salt) VALUES (%s,%s, %s);"
        args = (ali, binascii.hexlify(hashed_password), binascii.hexlify(salt))
        cur.execute(sentence, args)
        con.commit()
        logging.info(f"REGISTERED SUCCESSFULLY")
        result = True
    except mysql.connector.Error as err:
        result = False
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR REGISTERING: {err}")
    else:
        con.close()

    finally:
        return result


def login(ali, psw) -> bool:
    result = False

    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT passwd, salt FROM Player WHERE alias = %s;"
        args = (ali,)
        cur.execute(sentence, args)
        query = cur.fetchone()
        if query:
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
        else:
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


def modify(alias, n_alias, n_passwd) -> bool:
    result = False

    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        if n_alias != '':
            sentence = "UPDATE Player set alias = %s where alias = %s;"
            args = (n_alias, alias)
            cur.execute(sentence, args)
            alias = n_alias
            logging.debug("Alias updated")
        if n_passwd != '':
            # Generate 32 random bytes
            salt = os.urandom(32)
            hashed_password = hashlib.pbkdf2_hmac('sha256', n_passwd.encode(), salt, 10000)

            sentence = "UPDATE Player set passwd = %s, salt = %s where alias = %s;"
            args = (binascii.hexlify(hashed_password), binascii.hexlify(salt), alias)
            cur.execute(sentence, args)
            logging.debug("Password updated")

        con.commit()
        result = True
        logging.debug(f"UPDATED SUCCESSFULLY")

    except mysql.connector.Error as err:
        result = False
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR UPDATING: {err}")
    else:
        con.close()

    finally:
        return result


@app.route('/update', methods=['POST'])
def api_update():
    alias = request.form['alias']
    pwd = request.form['pwd']
    n_alias = request.json['n_alias']
    n_passwd = request.form['n_pwd']
    # Check if user and passwords are correct
    if check_alias(alias) and check_alias(n_alias):
        result = login(alias, pwd)
        if result:
            res = modify(alias, n_alias, n_passwd)

            if res:
                return jsonify({'mensaje': "UPDATED SUCCESSFULLY", 'result': True})
            else:
                return jsonify({'mensaje': "ERROR UPDATING", 'result': False})
        else:
            return jsonify({'mensaje': "ERROR UPDATING", 'result': False})

    else:
        return jsonify({'mensaje': "Wrong parameters", 'result': False})



@app.route('/register', methods=['POST'])
def api_register():
    # print(request.json)
    ali = request.json['alias']
    pwd = request.json['pwd']
    if check_alias(ali):
        res = sign(ali, pwd)

        if res:
            return jsonify({'mensaje': "REGISTERED SUCCESSFULLY", 'result': True})
        else:
            return jsonify({'mensaje': "ERROR REGISTERING", 'result': False})
    else:
        return jsonify({'mensaje': "Wrong parameters", 'result': False})


# Checks if the name is correct (text without blank spaces, between 1 and 30 characters).
def check_alias(name: str) -> bool:
    name = name.strip()
    return len(name) > 0 and len(name) <= 30


def checkargs(address, numconnections, bdadress) -> bool:
    """
        Comprueba si los parametros recibidos son correctos
    """

    connections = numconnections
    regex = '^[0-9]'
    if not re.match(regex, connections):
        print("Wrong format max connections")
        logging.error("Wrong format max connections")
        return False

    regex_1 = '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}$'
    regex_2 = '^\S+:[0-9]{1,5}$'
    registry = address
    db = bdadress

    if not (re.match(regex_1, registry) or re.match(regex_2, registry)):
        print("Wrong Engine address")
        logging.error("Wrong Engine address")
        return False

    if not (re.match(regex_1, db) or re.match(regex_2, db)):
        print("Wrong MySQL address")
        logging.error("Wrong MySQL address")
        return False

    return True


if __name__ == '__main__':

    try:

        with open("RegistryParameters.json", "r") as read_file:
            logging.debug("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.debug(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    if not checkargs(parameters["ADDRESS"], str(parameters["MAXCONNECTIONS"]), parameters["MYSQL"]):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

    address = parameters["ADDRESS"].split(':')
    IP = address[0]
    PORT = int(address[1])

    MAXCONNECTIONS = parameters["MAXCONNECTIONS"]
    DATABASE = parameters["DATABASE"]
    USERDB = parameters["USER"]
    PWDDB = parameters["PWD"]
    dbserver = parameters["MYSQL"].split(':')
    DBIP = dbserver[0]
    DBPORT = int(dbserver[1])

    config = {
        'user': USERDB,
        'password': PWDDB,
        'host': DBIP,
        'database': DATABASE,
        'raise_on_warnings': True
    }

    # Hilos que ejecuta Registry: hilos para sockets, hilo para api
    socket = SocketManager(IP, PORT)
    api = APIManager()

    socket.start()
    api.start()
