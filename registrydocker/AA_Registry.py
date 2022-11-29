"""
    Clara Gonzalez
    Ivan Cano

    Modulo de registro de los jugadores en el nucleo. Recibe como parametros el puerto de escucha
"""
import json
import logging
import os
import socket
import sqlite3
import threading
import re

global IP
global PORT
global DATABASE
global MAXCONNECTIONS

HEADER = 10

logging.basicConfig(filename="logfileRegistry.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


def sign(ali: str, psw: str) -> bool:
    """
    :param alias: nick del jugador
    :param passwd: contrasenya del jugador
    :return: True/False si se ha registrado con exito o no al jugador
    """

    result = True
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()

    try:
        cur.execute("INSERT INTO player (alias, passwd) VALUES (?,?);", (ali, psw))
        con.commit()
        logging.info(f"REGISTERED SUCCESSFULLY")
    except sqlite3.Error as error:
        logging.error(f"ERROR REGISTERING: {error}")
        result = False
    finally:
        con.close()
        return result


def login(ali, psw) -> bool:
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT alias, passwd FROM player WHERE alias = ? AND passwd = ?", (ali, psw))
    query = cur.fetchall()
    res = len(query) != 0
    con.close()
    return res


def modify(alias, n_alias, n_passwd) -> bool:
    final = True
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()

    try:
        if n_alias != '':
            cur.execute("UPDATE player set alias = ? where alias = ?", (n_alias, alias))
            alias = n_alias
            logging.info("Alias updated")
        if n_passwd != '':
            cur.execute("UPDATE player set passwd = ? where alias = ?", (n_passwd, alias))
            logging.info("Password updated")

        con.commit()
        logging.info(f"UPDATED SUCCESSFULLY")
    except sqlite3.Error as error:
        logging.error(f"ERROR UPDATING: {error}")
        final = False
    finally:
        con.close()
        return final


def handle_client(connection, address):
    res = False
    logging.info(f"NEW CONNECTION: {address}")

    c_length = int(connection.recv(HEADER))
    credentials = connection.recv(c_length).decode()

    logging.info(f"Received: {credentials}")
    data = credentials.split(":")
    operation = data[0]

    # Registry - Registrar
    if operation.upper() == 'R':
        alias = data[1]
        passwd = data[2]
        logging.info(f"REGISTRY alias: {alias} passwd: {passwd}")
        res = sign(alias, passwd)
    # Update - Actualizar
    if operation.upper() == 'U':
        alias = data[1]
        n_alias = data[2]
        n_passwd = data[3]
        logging.info(f"UPDATE profile {alias}")
        res = modify(alias, n_alias, n_passwd)
    if operation.upper() == 'L':
        alias = data[1]
        passwd = data[2]
        logging.info(f"LOGIN alias:" + alias + " passwd: " + passwd)
        res = login(alias, passwd)

    if res:
        connection.send(b'ok')
    else:
        logging.error(f"IT IS NOT POSSIBLE TO REGISTER OR UPDATE: ")
        connection.send(b'no')
    connection.close()


def start(server):
    print("AA_Registry started")
    print(f"LISTENING TO {IP}:{PORT}")
    server.listen()
    logging.info(f"LISTENING TO {IP}:{PORT}")
    n_connections = threading.active_count() - 1
    logging.info(f"CURRENT CONNECTIONS: {n_connections}")
    while True:
        try:
            conn, addr = server.accept()
            n_connections = threading.active_count()
            if n_connections >= MAXCONNECTIONS:
                logging.error("MAX CONNECTIONS REACHED")
                print("MAX CONNECTIONS REACHED")
                conn.send(b"THE SERVER HAS EXCEEDED THE LIMIT OF CONNECTIONS")
                conn.close()
                n_connections = threading.active_count() - 1
            else:
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.start()
                logging.info("\nConnection has been established: " + addr[0] + ":" + str(addr[1]))
                logging.info(f"[ACTIVE CONNECTIONS] {n_connections}")
                logging.info("REMAINING CONNECTIONS: ", MAXCONNECTIONS - n_connections)

        except Exception as exc:
            logging.error(f"Error accepting connections: {exc}")


def checkargs(address, numconnections) -> bool:
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

    if not (re.match(regex_1, registry) or re.match(regex_2, registry)):
        print("Wrong Engine address")
        logging.error("Wrong Engine address")
        return False
    return True


if __name__ == '__main__':

    try:

        with open("RegistryParameters.json", "r") as read_file:
            logging.info("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.info(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    if not checkargs(parameters["ADDRESS"], str(parameters["MAXCONNECTIONS"])):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

    address = parameters["ADDRESS"].split(':')
    IP = address[0]
    PORT = int(address[1])

    DATABASE = parameters["DATABASE"]
    MAXCONNECTIONS = parameters["MAXCONNECTIONS"]

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((IP, PORT))
    logging.info('Socket binded to ' + IP + ":" + str(PORT))
    try:
        start(serversocket)
    except Exception as e:
        logging.error(f"ERROR: {e}")
    finally:
        serversocket.close()
