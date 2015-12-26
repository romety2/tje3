#!/bin/sh

echo 
./scripts/glassfish3/glassfish/bin/asadmin undeploy zakladPogrzebowy
echo 
mvn package
echo 
./scripts/glassfish3/glassfish/bin/asadmin deploy target/zakladPogrzebowy.war
