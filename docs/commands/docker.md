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