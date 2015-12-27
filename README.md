* przechodzimy do folderu z projektem 
* nadajemy sobie uprawnienia do uruchamiania skryptów:
	`chmod 755 ./scripts/*.sh` 
* uruchamiamy serwer:  
	`./scripts/uruchomSerwer.sh`
* uruchamiamy bazę danych (opcjonalne, ale zalecane) 
	`./scripts/uruchomBaze.sh`
* uruchom GlassFish
	`./scripts/uruchomGlassFish.sh`
* przechodzimy do panelu `http://localhost:4848` 
* kliknij na: Resources/JDBC/JDBC Connection Pools/HSQLPool
* kliknij na Ping, musi zakończyć się sukcesem
* tworzymy naszą webową stronę
	`./scripts/zbudujStrone.sh`
* przechodzimy do panelu `http://localhost:4848` 
* kliknij na: Applications
* sprawdzamy czy został dodany: zakladPogrzebowy, jeśli tak klikamy przy nim na: Launch (kolumna Action)
* kliknij na pierwszy odnośnik