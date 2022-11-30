# SD_P2
Practica 2 de la asignatura de Sistemas Distribuidos de Ingeniería Informática de la Universidad de Alicante. Curso 2022-2023
	
1) Init de las bases de datos en las correspondientes carpetas	
	
2) docker-compose up -d --build


3 )docker exec -it sd_p2-main_aa_weather_1 bin/sh
	python AA_Weather.py
	
4) docker exec -it sd_p2-main_aa_registry_1 bin/sh
	python AA_Registry.py
	
5) docker exec -it sd_p2-main_aa_engine_1 bin/sh
	python AA_Engine.py
	
6) docker exec -it sd_p2-main_aa_player_1 bin/sh
	python AA_Player.py
	

7) docker exec -it sd_p2-main_aa_npc_1 bin/sh
	python AA_NPC.py


Para parar:
	docker-compose stop

Para eliminarlos:
	docker-compose rm -svf
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
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
