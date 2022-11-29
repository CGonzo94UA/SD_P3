# SD_P2
Practica 2 de la asignatura de Sistemas Distribuidos de Ingeniería Informática de la Universidad de Alicante. Curso 2022-2023
		
	
1) docker-compose up -d --build


2) docker exec -it sd_p2-main_aa_weather_1 bin/sh
	python initWeatherDB.py weatherDB.db
	python AA_Weather.py
	
3) docker exec -it sd_p2-main_aa_registry_1 bin/sh
	cd db/
	python initDatabase.py database.db
	cd ..
	python AA_Registry.py
	
	Si falla la aplicación, para borrar las filas de la tabla de mapas ejecutar:
		python deleteMaps.py 

4) docker exec -it sd_p2-main_aa_engine_1 bin/sh
	python AA_Engine.py
	
5) docker exec -it sd_p2-main_aa_player_1 bin/sh
	python AA_Player.py
	

6) docker exec -it sd_p2-main_aa_npc_1 bin/sh
	python AA_NPC.py


Para parar:
	docker-compose stop

Para eliminarlos:
	docker-compose rm -svf


En la carpeta CODIGO se incluyen los ficheros .py de la aplicación, los ficheros JSON con los parámetros y ejemplos de generación de logs. La estructura de carpetas de nombre %docker, es para la ejecución mediante docker-compose, de forma que todos los contenedores se crean al mismo tiempo.
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	1) Kafka:
	docker-compose up
	
	Para cerrar correctamente la ejecucion y no tener problemas de id:
		docker-compose rm -svf

2) Database:
	python initDatabase.py database.db

3) Weather database:
	python initWeatherDB.py weatherDB.db

3) Weather:
	python AA_Weather.py 5050 weatherDB.db

4) Registry:
	python AA_Registry.py 4048 database.db

5) Engine:
	python AA_Engine.py 5054 8 database.db 127.0.0.1:5050 127.0.0.1:29092


6) Player:
	python AA_Player.py 127.0.0.1:5054 127.0.0.1:4048 127.0.0.1:29092
	

7) NPC:
	python AA_NPC.py 127.0.0.1:29092
