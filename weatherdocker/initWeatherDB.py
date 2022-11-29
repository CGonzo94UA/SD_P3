import sqlite3
from sys import argv

connection = sqlite3.connect(argv[1])
cur = connection.cursor()

try:

    cur.execute("CREATE TABLE IF NOT EXISTS city("
                "id integer PRIMARY KEY AUTOINCREMENT,"
                "name text UNIQUE NOT NULL,"
                "temperature integer not null);")

    cities = {'Nueva York': 12, 'Los Angeles': 36, 'Tokio': 24, 'Delhi': 39, 'Buenos Aires': 20, 'Rio de Janeiro': 28, 'Sydney': 18,
              'Ciudad del Cabo': 34, 'Madrid': 18, 'Paris': 15, 'Londres': 8, 'Estambul': 26, 'Seul': 22, 'Bogota': 37, 'Singapur': 32, 'Pekin': 29,
              'Berlin': 22, 'Yakarta': 31, 'Manila': 33, 'Ciudad de Mexico': 21}
    for i in cities:
        cur.execute("INSERT INTO city (name, temperature) VALUES (?, ?)", (i, cities[i]))

    connection.commit()

    for i in cur.execute("SELECT name FROM sqlite_master WHERE type='table';"):
        print(i)
    print()

    for i in cur.execute("select * from city;"):
        print(i[1] + ':' + str(i[2]))

except sqlite3.Error as error:
    print("ERROR INIT WEATHER DATABASE: ", error)
finally:
    connection.close()
