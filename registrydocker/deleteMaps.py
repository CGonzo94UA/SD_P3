import sqlite3
from sys import argv

connection = sqlite3.connect(argv[1])
cur = connection.cursor()

try:
    cur.execute("DELETE FROM game")
    connection.commit()
    print(f"DELETED ROWS FROM MAP TABLE")
except sqlite3.Error as error:
    print(f'ERROR DELETING MAP ROWS {error}')
finally:
    connection.close()