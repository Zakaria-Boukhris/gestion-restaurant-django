# Gestion de restaurant — Django

Application web de gestion d'un restaurant marocain, réalisée en binôme par **Zakaria Boukhris et Hamza Moubtassim**. Elle regroupe le menu, les tables, les réservations, les commandes et la gestion du personnel dans une interface web.

## Fonctionnalités présentes

- Menu public : catégories, descriptions et prix en dirhams.
- Clients : inscription, profil et réservation de table.
- Personnel : prise de commandes, suivi des statuts et gestion des tables.
- Administration : gestion des plats, du personnel, des réservations et statistiques.
- Facturation : consultation et génération des informations de facture.

## Technologies

Python · Django 5.2 · SQLite · HTML/CSS · JavaScript · Bootstrap 5 · Font Awesome · Pillow

Bootstrap et Font Awesome sont chargés depuis des CDN : une connexion Internet est nécessaire pour leur affichage.

## Installation locale

Prérequis : Python 3.12 ou 3.13 installé, puis un terminal ouvert dans le dossier qui contient `manage.py`. Consulter la [compatibilité officielle de Django](https://docs.djangoproject.com/en/5.2/faq/install/) pour d'autres versions de Python.

### 1. Créer un environnement virtuel

```bash
python -m venv .venv
```

Windows (Invite de commandes) :

```bat
.venv\Scripts\activate.bat
```

Windows (PowerShell) :

```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS :

```bash
source .venv/bin/activate
```

### 2. Installer et configurer

```bash
python -m pip install -r requirements.txt
python scripts/configure_local.py
python manage.py migrate
```

Le script génère une clé secrète aléatoire dans `.env`, ignoré par Git. Il conserve toute configuration existante. `.env.example` décrit les variables attendues.

### 3. Créer votre administrateur

```bash
python manage.py createsuperuser
python manage.py shell -c "from restaurant.models import Utilisateur; Utilisateur.objects.filter(is_superuser=True).update(role='admin')"
```

Choisissez vos propres identifiants : aucun compte ni mot de passe par défaut n'est fourni. Le rôle applicatif `admin` est nécessaire pour accéder au tableau de bord personnalisé.

### 4. Ajouter un menu et des tables de démonstration (facultatif)

```bash
python scripts/create_initial_data.py
python scripts/create_moroccan_menu.py
```

Ces scripts créent des tables et des plats sans supprimer ceux qui existent déjà. Ils ne créent ni clients ni comptes de connexion.

### 5. Démarrer

```bash
python manage.py runserver
```

- Accueil : http://127.0.0.1:8000/
- Menu : http://127.0.0.1:8000/menu/
- Connexion du personnel : http://127.0.0.1:8000/staff/login/
- Administration personnalisée : http://127.0.0.1:8000/admin-custom/

## Organisation

| Dossier / fichier | Contenu |
| --- | --- |
| `gestion_restaurant/` | Configuration et routes Django |
| `restaurant/` | Modèles, formulaires, vues, migrations et middleware |
| `templates/` | Pages HTML |
| `scripts/` | Configuration locale et données de démonstration |
| `requirements.txt` | Dépendances Python |
| `.env.example` | Exemple de configuration sans secret |

## Périmètre et limites

Cette version est destinée à une démonstration locale du projet. Le code contient notamment une connexion client par numéro de téléphone sans vérification d'identité ; elle doit être remplacée avant une utilisation réelle. Les autorisations et les parcours métier nécessitent une revue complète avant un déploiement public.

Le modèle de stock et le rôle cuisinier ne font plus partie de cette version. Certains écrans avancés référencés dans les vues ne disposent pas de leur template dans l'archive reçue. Le dépôt ne prétend donc pas fournir une gestion de stock, un paiement en ligne ou tous les rapports avancés.

La base de données d'origine, les images téléversées et les comptes locaux sont exclus. Une base neuve est créée avec les migrations. Publier le code sur GitHub ne met pas l'application Django en ligne ; GitHub Pages ne fait pas fonctionner son serveur Python.

## Auteurs

- **Zakaria Boukhris** — [GitHub](https://github.com/Zakaria-Boukhris)
- **Hamza Moubtassim** — co-auteur du projet

Les contributions individuelles ne sont pas détaillées ici. Aucune licence de réutilisation n'est ajoutée sans décision des auteurs.
