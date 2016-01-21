* przechodzimy do folderu z projektem 
* nadajemy sobie uprawnienia do uruchamiania skryptów:  
	`chmod 755 ./scripts/*.sh` 
* ściągnij ze strony https://glassfish.java.net/downloads/3.1.2.2-final.html i zainstaluj GlassFish (początkowo w folderze scripts utwórz folder o nazwie "glassfish3" następnie uruchom skrypt wypakowujący wszystkie pliki GlassFish-a do folderu "glassfish3"):  
	 `mkdir scripts/glassfish3`  
* tworzymy naszą webową stronę:  
	`./scripts/zbudujStrone.sh`
* przechodzimy do panelu:  
	`http://localhost:4848` 
* kliknij na: Applications
* sprawdzamy czy został dodany: zakladPogrzebowy, jeśli tak klikamy przy nim na: Launch (kolumna Action)
* kliknij na pierwszy odnośnik
