<h1> Airflow project </h1>

<h3>Structure</h3>

1) **airflow** - airflow home directory
2) **data** - folder used by Postgres database
3) **sources** - folder contains all dags, hooks and sensors created during the course
4) **Dockerfile, docker-compose.yml** - files that describe docker how to build a docker containers

To build an airflow docker container run command: `docker-compose build`

To run an airflow docker container run command: `docker-compose run`