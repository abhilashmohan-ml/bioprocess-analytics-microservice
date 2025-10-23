#!/bin/bash
# create-port-cleanup.sh - Complete port cleanup and restart

echo "🧹 Starting complete port cleanup..."

# 1. Stop and remove all containers
echo "🛑 Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# 2. Remove networks
echo "🗑️ Removing networks..."
docker network prune -f

# 3. Kill processes on your ports
echo "💥 Killing processes on bioprocess ports..."
for port in 8080 9001 9002 9003 54320 54321 54322 6379 16686; do
    echo "Checking port $port..."
    sudo lsof -ti:$port | xargs sudo kill -9 2>/dev/null || true
done

# 4. Clean up Docker system
echo "🧽 Cleaning Docker system..."
docker system prune -af --volumes

# 5. Check what's still running
echo "🔍 Checking remaining processes..."
sudo lsof -i :8080 || echo "Port 8080 is free"
sudo lsof -i :9001 || echo "Port 9001 is free"
sudo lsof -i :9002 || echo "Port 9002 is free"
sudo lsof -i :9003 || echo "Port 9003 is free"

echo "✅ Port cleanup completed!"

# 6. Start fresh
echo "🚀 Starting fresh deployment..."
docker-compose --profile dev down
docker-compose --profile dev up -d

echo "✅ Fresh deployment completed!"
