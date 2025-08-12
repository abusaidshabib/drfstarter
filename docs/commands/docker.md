sudo docker-compose --env-file .env -f docker/docker-compose.yml build
sudo docker-compose --env-file .env -f docker/docker-compose.yml up

sudo docker-compose --env-file .env -f docker/docker-compose.yml down --volumes --remove-orphans

# Docker commands

sudo docker-compose --env-file .env -f docker/docker-compose.yml build --no-cache
sudo docker-compose --env-file .env -f docker/docker-compose.yml up

# Step 1: Shut everything down cleanly and remove containers, volumes, and networks

sudo docker-compose --env-file .env -f docker/docker-compose.yml down --volumes --remove-orphans

# Step 2: Remove all stopped containers, volumes, images, and networks

sudo docker system prune -a --volumes -f

# Docker commands for testing

docker build -t djboilar .

docker run --name djboilar --env-file .env -p 8001:8001 djboilar

docker stop djboilar

docker rm djboilar

docker compose -f docker-compose.dev.yml exec django python manage.py shell -c "from django.conf import settings; print(settings.DEBUG, settings.STATIC_URL)"

sudo  docker compose -f docker-compose.dev.yml exec django python manage.py makemigrations users settings cameras sensors watertanks
sudo  docker compose -f docker-compose.dev.yml exec django python manage.py migrate

sudo  docker compose -f docker-compose.dev.yml exec django python manage.py createsuperuser
sudo docker compose -f docker-compose.dev.yml exec django python manage.py load_app_features
sudo docker compose -f docker-compose.dev.yml exec django python manage.py load_features_update

sudo docker compose -f docker-compose.dev.yml exec django pip install opencv-python numpy
docker compose -f docker-compose.dev.yml up
docker compose -f docker-compose.dev.yml down

docker compose -f docker-compose.dev.yml up -d

docker compose -f docker-compose.dev.yml exec django bash

docker container stop $(docker container ls -aq)
docker container rm $(docker container ls -aq)
docker rmi -f $(docker images -q)
docker volume rm $(docker volume ls -q)
docker network prune -f

### Docker commands to create app

mkdir apps/branches
python manage.py startapp branches apps/branches

### another option

python manage.py startapp cameras
mv cameras apps


sudo docker build -t djboilar .

sudo docker run --name djboilar --env-file .env -p 8001:8001 djboilar

sudo docker stop djboilar

sudo docker rm djboilar

sudo docker compose -f docker-compose.dev.yml exec django python manage.py shell -c "from django.conf import settings; print(settings.DEBUG, settings.STATIC_URL)"

sudo docker compose -f docker-compose.dev.yml exec django python manage.py makemigrations users settings cameras sensors watertanks
sudo docker compose -f docker-compose.dev.yml exec django python manage.py migrate

sudo docker compose -f docker-compose.dev.yml exec django python manage.py createsuperuser

sudo docker compose -f docker-compose.dev.yml up
sudo docker compose -f docker-compose.dev.yml down

sudo docker compose -f docker-compose.dev.yml up -d

sudo docker compose -f docker-compose.dev.yml exec django bash

sudo docker container stop $(sudo docker container ls -aq)
sudo docker container rm $(sudo docker container ls -aq)
sudo docker rmi -f $(sudo docker images -q)
sudo docker volume rm $(sudo docker volume ls -q)
sudo docker network prune -f



Fake Data Create
python manage.py generate_fake_sensors
python manage.py generate_sensor_records
python manage.py generate_weight_sensors
python manage.py generate_fake_weight_conditions
python manage.py generate_order_weights

python manage.py generate_fake_employee_data
python manage.py generate_fake_kitchen_data
python manage.py generate_fake_garbage_data
python manage.py generate_fake_buffet_data
python manage.py generate_fake_people_data
python manage.py generate_fake_sentiment_data





