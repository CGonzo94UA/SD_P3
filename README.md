# SD_P3
Practica 3 de la asignatura de Sistemas Distribuidos de Ingeniería Informática de la Universidad de Alicante. Curso 2022-2023
		
	
1) docker-compose up -d --build
	
2) docker exec -it sd_p3-main_aa_registry_1 bin/sh
	python AA_Registry.py
	

3) docker exec -it sd_p3-main_aa_engine_1 bin/sh
	python AA_Engine.py
	
4) docker exec -it sd_p3-main_aa_player_1 bin/sh
	python AA_Player.py
	

5) docker exec -it sd_p3-main_aa_npc_1 bin/sh
	python AA_NPC.py


Para parar:
	docker-compose stop

Para eliminarlos:
	docker-compose rm -svf
	
		
