# SD_P3
Practica 3 de la asignatura de Sistemas Distribuidos de Ingeniería Informática de la Universidad de Alicante. Curso 2022-2023
		
	
1) docker-compose up -d --build
	
2) docker exec -it sd_p2-main_aa_registry_1 bin/sh
	cd db/
	python initDatabase.py database.db
	cd ..
	python AA_Registry.py
	
	Si falla la aplicación, para borrar las filas de la tabla de mapas ejecutar:
		python deleteMaps.py 

3) docker exec -it sd_p2-main_aa_engine_1 bin/sh
	python AA_Engine.py
	
4) docker exec -it sd_p2-main_aa_player_1 bin/sh
	python AA_Player.py
	

5) docker exec -it sd_p2-main_aa_npc_1 bin/sh
	python AA_NPC.py


Para parar:
	docker-compose stop

Para eliminarlos:
	docker-compose rm -svf

----------------------------------------------------------------------------------------------------------------------------------------	
		
	
1) Kafka:
	docker-compose up
	
	Para cerrar correctamente la ejecucion y no tener problemas de id:
		docker-compose rm -svf

2) Database:
	python initDatabase.py database.db


3) Registry:
	python AA_Registry.py 4048 database.db

4) Engine:
	python AA_Engine.py 5054 8 database.db 127.0.0.1:5050 127.0.0.1:29092


5) Player:
	python AA_Player.py 127.0.0.1:5054 127.0.0.1:4048 127.0.0.1:29092
	

6) NPC:
	python AA_NPC.py 127.0.0.1:29092
