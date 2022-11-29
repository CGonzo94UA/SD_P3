import sqlite3
from sys import argv

connection = sqlite3.connect(argv[1])
cur = connection.cursor()

try:

    cur.execute("CREATE TABLE IF NOT EXISTS player (alias text PRIMARY KEY,"
                "passwd text NOT NULL,"
                "nivel integer DEFAULT 0,"
                "EF integer DEFAULT 0,"
                "EC integer DEFAULT 0,"
                "posicion text);")

    cur.execute("CREATE TABLE IF NOT EXISTS game (id integer PRIMARY KEY AUTOINCREMENT,"
                "map text NOT NULL,"
                "timestamp text NOT NULL,"
                "players text NOT NULL,"
                "npcs text,"
                "cities text,"
                "quadrants text,"
                "mines text,"
                "food text);")

    connection.commit()

except sqlite3.Error as error:
    print("ERROR INIT DATABASE: ", error)
finally:
    connection.close()

