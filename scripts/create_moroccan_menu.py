#!/usr/bin/env python
"""
Script pour créer un menu marocain avec des prix en dirhams
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_restaurant.settings')
django.setup()

from restaurant.models import Plat

def create_moroccan_menu():
    """Créer un menu marocain avec des prix en dirhams"""
    print("🇲🇦 Création du menu marocain...")
    
    # Conserver les plats existants et leurs commandes.
    # Plats marocains avec prix en dirhams
    plats_marocains = [
        # Entrées
        {
            'nom': 'Harira traditionnelle',
            'prix': Decimal('25.00'),
            'categorie': 'entree',
            'description': 'Soupe traditionnelle marocaine aux lentilles, tomates et épices'
        },
        {
            'nom': 'Briouates au fromage',
            'prix': Decimal('35.00'),
            'categorie': 'entree',
            'description': 'Feuilletés croustillants farcis au fromage frais et aux herbes'
        },
        {
            'nom': 'Zaalouk d\'aubergines',
            'prix': Decimal('30.00'),
            'categorie': 'entree',
            'description': 'Caviar d\'aubergines à la marocaine avec tomates et épices'
        },
        {
            'nom': 'Salade marocaine',
            'prix': Decimal('28.00'),
            'categorie': 'entree',
            'description': 'Salade de tomates, concombres, poivrons et olives'
        },
        {
            'nom': 'Chebakia',
            'prix': Decimal('20.00'),
            'categorie': 'entree',
            'description': 'Pâtisserie traditionnelle en forme de fleur, au miel et sésame'
        },
        
        # Plats principaux
        {
            'nom': 'Couscous royal',
            'prix': Decimal('85.00'),
            'categorie': 'plat',
            'description': 'Couscous traditionnel avec agneau, poulet, merguez et légumes'
        },
        {
            'nom': 'Tagine d\'agneau aux pruneaux',
            'prix': Decimal('75.00'),
            'categorie': 'plat',
            'description': 'Tagine d\'agneau mijoté avec pruneaux, amandes et cannelle'
        },
        {
            'nom': 'Pastilla au poulet',
            'prix': Decimal('65.00'),
            'categorie': 'plat',
            'description': 'Feuilleté traditionnel sucré-salé au poulet et amandes'
        },
        {
            'nom': 'Méchoui d\'agneau',
            'prix': Decimal('95.00'),
            'categorie': 'plat',
            'description': 'Épaule d\'agneau rôtie aux épices marocaines'
        },
        {
            'nom': 'Tajine de poisson',
            'prix': Decimal('70.00'),
            'categorie': 'plat',
            'description': 'Poisson frais aux légumes, olives et citron confit'
        },
        {
            'nom': 'Kefta aux œufs',
            'prix': Decimal('60.00'),
            'categorie': 'plat',
            'description': 'Boulettes de viande hachée aux œufs dans une sauce tomate'
        },
        {
            'nom': 'Poulet aux citrons confits',
            'prix': Decimal('68.00'),
            'categorie': 'plat',
            'description': 'Poulet traditionnel aux olives et citrons confits'
        },
        {
            'nom': 'Tagine de légumes',
            'prix': Decimal('55.00'),
            'categorie': 'plat',
            'description': 'Légumes de saison mijotés aux épices marocaines'
        },
        
        # Desserts
        {
            'nom': 'Pâtisseries orientales',
            'prix': Decimal('25.00'),
            'categorie': 'dessert',
            'description': 'Assortiment de pâtisseries marocaines traditionnelles'
        },
        {
            'nom': 'Mahalabia',
            'prix': Decimal('20.00'),
            'categorie': 'dessert',
            'description': 'Crème dessert à la fleur d\'oranger et pistaches'
        },
        {
            'nom': 'Cornes de gazelle',
            'prix': Decimal('30.00'),
            'categorie': 'dessert',
            'description': 'Pâtisseries en forme de croissant aux amandes'
        },
        {
            'nom': 'Sellou',
            'prix': Decimal('18.00'),
            'categorie': 'dessert',
            'description': 'Mélange traditionnel d\'amandes, dattes et sésame'
        },
        {
            'nom': 'Halwa chebakia',
            'prix': Decimal('22.00'),
            'categorie': 'dessert',
            'description': 'Pâtisserie au miel et graines de sésame'
        },
        
        # Boissons
        {
            'nom': 'Thé à la menthe',
            'prix': Decimal('15.00'),
            'categorie': 'boisson',
            'description': 'Thé vert traditionnel marocain à la menthe fraîche'
        },
        {
            'nom': 'Jus d\'orange frais',
            'prix': Decimal('20.00'),
            'categorie': 'boisson',
            'description': 'Jus d\'orange pressé minute'
        },
        {
            'nom': 'Café noir',
            'prix': Decimal('12.00'),
            'categorie': 'boisson',
            'description': 'Café traditionnel marocain'
        },
        {
            'nom': 'Lait d\'amande',
            'prix': Decimal('18.00'),
            'categorie': 'boisson',
            'description': 'Boisson rafraîchissante aux amandes'
        },
        {
            'nom': 'Eau minérale Sidi Ali',
            'prix': Decimal('10.00'),
            'categorie': 'boisson',
            'description': 'Bouteille d\'eau minérale 50cl'
        },
        {
            'nom': 'Coca-Cola',
            'prix': Decimal('15.00'),
            'categorie': 'boisson',
            'description': 'Canette 33cl'
        },
        {
            'nom': 'Jus de pomme',
            'prix': Decimal('16.00'),
            'categorie': 'boisson',
            'description': 'Jus de pomme naturel'
        },
    ]
    
    # Créer les plats
    for plat_data in plats_marocains:
        plat, created = Plat.objects.get_or_create(
            nom=plat_data['nom'],
            defaults=plat_data
        )
        if created:
            print(f"✅ Plat créé: {plat}")
        else:
            print(f"⚠️ Plat existe déjà: {plat}")
    
    print(f"\n🎉 Menu marocain créé avec succès!")
    print(f"📊 Total des plats: {Plat.objects.count()}")
    print(f"   🥗 Entrées: {Plat.objects.filter(categorie='entree').count()}")
    print(f"   🍽️ Plats: {Plat.objects.filter(categorie='plat').count()}")
    print(f"   🍰 Desserts: {Plat.objects.filter(categorie='dessert').count()}")
    print(f"   🥤 Boissons: {Plat.objects.filter(categorie='boisson').count()}")
    
if __name__ == '__main__':
    create_moroccan_menu()
