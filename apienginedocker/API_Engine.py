"""
    Clara Gonzalez

    API de Engine que sera consumida por el front para mostrar el desarrollo de la partida
"""
import json
from flask import Flask, jsonify, request
import logging
import mysql.connector
from mysql.connector import errorcode
from flask_cors import CORS, cross_origin

global DATABASE
global USERDB
global PWDDB
global DBIP
global DBPORT
global config

logging.basicConfig(
    filename="./logs/API_Engine.log",
    format='%(asctime)s : %(message)s',
    filemode='w',
    level=logging.DEBUG)

app = Flask(__name__)
CORS(app)


# Get the map of the game
@app.route('/game', methods=['GET'])
def get_map():
    logging.info(f"{request.remote_addr} - GET MAP")
    try:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        sentence = "SELECT map, cities, npcs, players, characters FROM Game WHERE stamp = (SELECT max(stamp) FROM Game);"
        cur.execute(sentence)
        query = cur.fetchone()
        # Devuelve tuplas con los datos
        if not query:
            logging.info("There is no game at the moment")
            return jsonify({'msg': "There is no game at the moment", 'result': False})
        else:
            map = eval(query[0])
            cities = eval(query[1])
            npcs = eval(query[2])
            players = eval(query[3])
            characters = eval(query[4])

            data = {"result": True,
                    "map": map,
                    "cities": cities,
                    "npcs": npcs,
                    "players": players
                    }

            if players:
                for player in players:
                    sentence = "SELECT nivel, niveltotal, EC, EF FROM Player WHERE alias = %s;"
                    args = (player,)
                    cur.execute(sentence, args)
                    query = cur.fetchone()
                    if query:
                        list = []
                        list.append(characters[player])
                        list.append(query[0])
                        list.append(query[1])
                        list.append(query[2])
                        list.append(query[3])
                        data[player] = list

            logging.info(f"{request.remote_addr} - GOT MAP SUCCESSFULLY")
            return json.dumps(data)

    except mysql.connector.Error as err:
        con.close()
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(f"ERROR LOGINING: {err}")
        logging.info("There is no game at the moment")
        return jsonify({'msg': "There is no game at the moment", 'result': False})
    else:
        con.close()


if __name__ == '__main__':

    try:
        with open("APIEngineParameters.json", "r") as read_file:
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
        app.run(debug=False, port=3000, host="0.0.0.0")
        logging.info("The Engine API has started.")
    except Exception as error:
        logging.error(f"Error running the Engine API: {error}")
