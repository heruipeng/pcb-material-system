#!/bin/bash
# Quick setup for PCB Engineering System
python _apply_fixes.py
rm -f db.sqlite3
python manage.py makemigrations accounts materials tools reports core
python manage.py migrate
python init_data.py
echo ""
echo "============================================"
echo "  Setup complete! Run:"
echo "  python manage.py runserver"
echo "  Then open: http://127.0.0.1:8000/"
echo "  Login: admin / admin123"
echo "============================================"
