"""
    Clara Gonzalez

    API de Engine que sera consumida por el front para mostrar el desarrollo de la partida
"""
import json
from flask import Flask, jsonify, request
import logging
import mysql.connector
from mysql.connector import errorcode
from prettytable import from_db_cursor, PrettyTable

global DATABASE
global USERDB
global PWDDB
global DBIP
global DBPORT
global config


logging.basicConfig(
    filename="Registry.log",
    format='%(asctime)s : %(message)s',
    filemode='w',
    level=logging.DEBUG)

app = Flask(__name__)


# Get the Players of the game
@app.route('/players', methods=['GET'])
def get_players():
    logging.info(f"{request.remote_addr} - GET PLAYERS")

    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT players FROM Game WHERE stamp = (SELECT max(stamp) FROM Game);"
        cur.execute(sentence)
        query = cur.fetchone()
        # Devuelve tuplas con los datos
        if not query:
            return jsonify({'msg': "There is no game in play at this time", 'result': False})
            logging.info(f"{request.remote_addr} - NO GAME IN PLAY AT THIS TIME")
        else:
            players = query[0]
            PLAYERS = eval(players)
            answer = PrettyTable()
            answer.field_names = ["Alias", "Level", "EC", "EF", "Total level", "Position"]

            if not PLAYERS:
                return jsonify({'msg': "There are no players at this time", 'result': False})
                logging.info(f"{request.remote_addr} - NO PLAYERS AT THIS TIME")
            else:
                for player in PLAYERS:
                    sentence = "SELECT nivel, niveltotal, EC, EF, posicion FROM Player WHERE alias = %s;"
                    args = (player,)
                    cur.execute(sentence, args)
                    query = cur.fetchone()
                    if query:
                        level = query[0]
                        total = query[1]
                        EC = query[2]
                        EF = query[3]
                        pos = query[4]
                        answer.add_row(player, level, EC, EF, total, pos)

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


# Get the NPCs of the game
@app.route('/npcs', methods=['GET'])
def get_npcs():
    logging.info(f"{request.remote_addr} - GET NPCs")
    res = False

    if res:
        return jsonify({'msg': "REGISTERED SUCCESSFULLY", 'result': True})
        logging.info(f"{request.remote_addr} - REGISTERED SUCCESSFULLY")
    else:
        return jsonify({'msg': "ERROR THE PLAYER ALREADY EXISTS", 'result': False})
        logging.info(f"{request.remote_addr} - ERROR REGISTERING THE PLAYER ALREADY EXISTS")


# Get the map of the game
@app.route('/map', methods=['GET'])
def get_map():
    logging.info(f"{request.remote_addr} - GET MAP")
    res = False

    if res:
        return jsonify({'msg': "REGISTERED SUCCESSFULLY", 'result': True})
        logging.info(f"{request.remote_addr} - REGISTERED SUCCESSFULLY")
    else:
        return jsonify({'msg': "ERROR THE PLAYER ALREADY EXISTS", 'result': False})
        logging.info(f"{request.remote_addr} - ERROR REGISTERING THE PLAYER ALREADY EXISTS")


# Get the NPCs of the game
@app.route('/cities', methods=['GET'])
def get_cities():
    logging.info(f"{request.remote_addr} - GET NPCs")
    res = False

    if res:
        return jsonify({'msg': "REGISTERED SUCCESSFULLY", 'result': True})
        logging.info(f"{request.remote_addr} - REGISTERED SUCCESSFULLY")
    else:
        return jsonify({'msg': "ERROR THE PLAYER ALREADY EXISTS", 'result': False})
        logging.info(f"{request.remote_addr} - ERROR REGISTERING THE PLAYER ALREADY EXISTS")


if __name__ == '__main__':

    try:
        with open("RegistryParameters.json", "r") as read_file:
            logging.debug("Converting JSON encoded data into Python dictionary")
            parameters = json.load(read_file)
            logging.debug(str(parameters))
    except Exception as e:
        logging.error(f'ERROR reading parameters: {e}')
        exit()

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
        'raise_on_warnings': True,
    }

    try:
        logging.info("Starting the Engine API...")
        app.run(debug=False, port=3000)
        logging.info("The Engine API has started.")
    except Exception as error:
        logging.error(f"Error running the Engine API: {error}")
