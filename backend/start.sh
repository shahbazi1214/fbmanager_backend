#!/bin/bash
echo "====================================="
echo "  FB Manager - Backend Setup"
echo "====================================="

# Install dependencies
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "[2/4] Running migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations facebook
python manage.py migrate

# Seed data
echo "[3/4] Seeding demo data..."
python manage.py seed_data

# Done
echo "[4/4] Done!"
echo ""
echo "====================================="
echo "  Starting Django server..."
echo "  URL: http://127.0.0.1:8000"
echo "====================================="
python manage.py runserver
