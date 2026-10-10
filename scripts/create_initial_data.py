"""Créer uniquement des tables de démonstration, sans compte ni donnée personnelle."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_restaurant.settings")
import django
django.setup()
from restaurant.models import Table

def create_initial_data():
    for numero, capacite in enumerate([2, 4, 6, 4, 8, 2, 4, 6], start=1):
        Table.objects.get_or_create(numero=numero, defaults={"capacite": capacite})
    print("Tables de démonstration disponibles. Aucun compte n'a été créé.")

if __name__ == "__main__":
    create_initial_data()
