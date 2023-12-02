copy the folder named "conf_template" and name it "conf".
update the env files under conf with your keys.
run "docker compose up -d --build" to run the project.
wait for a minute and restart any container that stops.

additional:
    login in to pgadmin and connect to the database server.
    for the host name use local_pgdb.

Note:
    please run "docker compose up -d --build" when you update environment variables.