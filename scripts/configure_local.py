"""Créer une configuration locale avec une clé aléatoire, sans écraser l'existante."""
from pathlib import Path
import secrets

destination = Path(__file__).resolve().parent.parent / '.env'
try:
    with destination.open('x', encoding='utf-8') as config:
        config.write(f'DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}\n')
        config.write('DJANGO_DEBUG=True\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1\n')
    destination.chmod(0o600)
    print('Configuration locale créée. Ne publiez pas le fichier .env.')
except FileExistsError:
    print('La configuration .env existe déjà : elle est conservée.')
