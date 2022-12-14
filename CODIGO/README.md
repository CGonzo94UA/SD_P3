# SD_P3
Practica 3 de la asignatura de Sistemas Distribuidos de Ingeniería Informática de la Universidad de Alicante. Curso 2022-2023

docker-compose up -d --build

docker exec -it sd_p3-main_aa_registry_1 bin/sh cd db/ python initDatabase.py database.db cd .. python AA_Registry.py

docker exec -it sd_p3-main_aa_engine_1 bin/sh python AA_Engine.py

docker exec -it sd_p3-main_aa_player_1 bin/sh python AA_Player.py

docker exec -it sd_p3-main_aa_npc_1 bin/sh python AA_NPC.py

Para parar: docker-compose stop

Para eliminarlos: docker-compose rm -svf

1) Kafka y MySQL: docker-compose up

Para cerrar correctamente la ejecucion y no tener problemas de id: 
docker-compose stop
docker-compose rm -svf

2) Registry: python AA_Registry.py 

3) Engine: python AA_Engine.py 

4) Player: python AA_Player.py 

5) NPC: python AA_NPC.py 


Para crear CERTIFICADOS autofirmados:

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout keyEngine.pem -out certEngine.pem


