"""
    Clara Gonzalez
    Ivan Cano

    Modulo de clima. Recibe como parametros el puerto de escucha
"""
import json
import logging
import socket
import sqlite3
import threading
import re

global PORT
global DATABASE
global MAXCONNECTIONS

HEADER = 10

logging.basicConfig(filename="logfileWeather.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


def requestcity(idcity):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT name, temperature FROM city WHERE id = ?", (idcity,))
    # devuelve una tupla
    query = cur.fetchone()
    con.close()
    return query


def handle_client(connection, address):
    logging.info(f"NEW CONNECTION: {address}")

    c_length = int(connection.recv(HEADER))
    idciudad = connection.recv(c_length).decode()
    logging.info(f"Received: {idciudad}")

    data = requestcity(idciudad)

    if data is None:
        logging.error(f"ERROR: no city with the id: {idciudad}")
        answer = "Error"
        # connection.send(b'no')
    else:
        answer = data[0] + ':' + str(data[1])

    length = str(len(answer)).encode()
    length_msg = length + b" " * (HEADER - len(length))
    logging.info(f"sending: {length_msg}")
    connection.send(length_msg)
    logging.info(f"sending: {answer.encode()}")
    connection.send(answer.encode())
    connection.close()


def start(server):
    print("AA_Weather started")
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
                logging.warning("MAX CONNECTIONS REACHED")
                conn.send(b"THE SERVER HAS EXCEEDED THE LIMIT OF CONNECTIONS")
                conn.close()
                n_connections = threading.active_count() - 1
            else:
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.start()
                logging.info("\nConnection has been established: " + addr[0] + ":" + str(addr[1]))
                logging.warning(f"[ACTIVE CONNECTIONS] {n_connections}")

        except Exception as exc:
            logging.error(f"Error accepting connections: {exc}")


def checkargs(port) -> bool:
    """
    Comprueba si los parametros recibidos son correctos
    """

    puerto = port
    regex_1 = '^[0-9]{1,5}$'
    if not re.match(regex_1, puerto):
        print("Wrong format port")
        return False
    return True


if __name__ == '__main__':

    try:

        with open("WeatherParameters.json", "r") as read_file:
            logging.info("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.info(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

    address = parameters["ADDRESS"].split(':')
    IP = address[0]
    PORT = int(address[1])

    if not checkargs(str(PORT)):
        print("ERROR: Wrong args")
        logging.error("ERROR: Wrong args")
        exit()

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
