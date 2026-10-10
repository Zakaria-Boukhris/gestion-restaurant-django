from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    # Pages principales
    path('', views.index, name='index'),
    path('menu/', views.menu_public, name='menu'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/serveur/', views.dashboard_serveur, name='dashboard_serveur'),
    
    # Gestion des tables
    path('tables/', views.gerer_tables, name='gerer_tables'),
    path('tables/ajouter/', views.ajouter_table, name='ajouter_table'),
    path('tables/attribuer/<int:table_id>/', views.attribuer_table, name='attribuer_table'),
    
    # Gestion des plats
    path('plats/', views.gerer_plats, name='gerer_plats'),
    path('plats/ajouter/', views.ajouter_plat, name='ajouter_plat'),
    
    # Gestion des commandes
    path('commandes/prendre/<int:table_id>/', views.prendre_commande, name='prendre_commande'),

    path('commandes/facture/<int:commande_id>/', views.generer_facture, name='generer_facture'),
    path('commandes/facture-ajax/<int:commande_id>/', views.generer_facture_ajax, name='generer_facture_ajax'),
    path('commandes/terminer-ajax/<int:commande_id>/', views.terminer_commande_ajax, name='terminer_commande_ajax'),
    path('commandes/terminer/<int:commande_id>/', views.terminer_commande_ajax, name='terminer_commande'),
    path('commandes/marquer-servie/<int:commande_id>/', views.marquer_servie_ajax, name='marquer_servie_ajax'),

    # Fonctionnalités serveur avancées
    path('serveur/factures/', views.gerer_factures, name='gerer_factures'),
    path('serveur/commandes/', views.prendre_commandes, name='prendre_commandes'),
    path('serveur/envoyer-cuisine/<int:commande_id>/', views.envoyer_commande_cuisine, name='envoyer_commande_cuisine'),
    path('serveur/liberer-table/<int:table_id>/', views.liberer_table, name='liberer_table'),
    

    
    # Gestion des réservations
    path('reservations/nouvelle/', views.reserver_table, name='reserver_table'),
    path('reservations/annuler/<int:reservation_id>/', views.annuler_reservation, name='annuler_reservation'),
    path('reservations/annuler-ajax/<int:reservation_id>/', views.annuler_reservation_ajax, name='annuler_reservation_ajax'),
    path('reservations/confirmer-ajax/<int:reservation_id>/', views.confirmer_reservation_ajax, name='confirmer_reservation_ajax'),

    # Gestion des commandes
    path('commandes/annuler/<int:commande_id>/', views.annuler_commande_client, name='annuler_commande_client'),
    path('commandes/annuler-serveur/<int:commande_id>/', views.annuler_commande_serveur, name='annuler_commande_serveur'),

    # Gestion des clients
    path('clients/inscription/', views.inscription_client, name='inscription_client'),
    path('clients/connexion/', views.connexion_client, name='connexion_client'),
    path('clients/deconnexion/', views.deconnexion_client, name='deconnexion_client'),
    path('clients/profil/', views.profil_client, name='profil_client'),
    path('clients/modifier/', views.modifier_profil_client, name='modifier_profil_client'),
    path('acces-refuse/', views.acces_refuse, name='acces_refuse'),
    path('staff/deconnexion/', views.deconnexion_staff, name='deconnexion_staff'),
    path('staff/logout/', views.logout_staff, name='logout_staff'),
    path('admin-custom/', views.admin_custom, name='admin_custom'),
    path('admin-redirect/', views.admin_redirect, name='admin_redirect'),
    path('admin/plats/', views.gerer_plats_simple, name='gerer_plats_simple'),
    path('admin/tables/', views.gerer_tables_simple, name='gerer_tables_simple'),
    path('admin/personnel/', views.gerer_personnel_simple, name='gerer_personnel_simple'),
    path('admin/statistiques/', views.statistiques_simple, name='statistiques_simple'),

    # Nouvelles fonctionnalités personnel
    path('admin/personnel/ajouter-modal/', views.ajouter_personnel_modal, name='ajouter_personnel_modal'),
    path('admin/personnel/gerer-roles/', views.gerer_roles_personnel, name='gerer_roles_personnel'),
    path('admin/personnel/exporter/', views.exporter_liste_personnel, name='exporter_liste_personnel'),
    path('admin/personnel/securite/', views.parametres_securite, name='parametres_securite'),

    # Nouvelles fonctionnalités statistiques
    path('admin/statistiques/rapport-journalier/', views.rapport_journalier, name='rapport_journalier'),
    path('admin/statistiques/rapport-mensuel/', views.rapport_mensuel, name='rapport_mensuel'),
    path('admin/statistiques/analyse-clients/', views.analyse_clients, name='analyse_clients'),
    path('admin/statistiques/analyse-ventes/', views.analyse_ventes, name='analyse_ventes'),




    # Connexion/Déconnexion staff
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/deconnexion/', views.staff_deconnexion, name='staff_deconnexion'),

    # Fonctionnalités serveur avancées
    path('reservations/confirmer/<int:reservation_id>/', views.confirmer_reservation, name='confirmer_reservation'),
    path('tables/liberer/<int:table_id>/', views.liberer_table, name='liberer_table'),
    path('commandes/servie/<int:commande_id>/', views.marquer_commande_servie, name='marquer_commande_servie'),
    path('commande-rapide/<int:table_id>/', views.commande_rapide, name='commande_rapide'),

    # Fonctionnalités admin avancées - Plats
    path('admin/plats/ajouter/', views.ajouter_plat, name='ajouter_plat'),
    path('admin/plats/modifier/<int:plat_id>/', views.modifier_plat, name='modifier_plat'),
    path('admin/plats/supprimer/<int:plat_id>/', views.supprimer_plat, name='supprimer_plat'),

    # Fonctionnalités admin avancées - Tables
    path('admin/tables/ajouter/', views.ajouter_table, name='ajouter_table'),
    path('admin/tables/modifier/<int:table_id>/', views.modifier_table, name='modifier_table'),
    path('admin/tables/supprimer/<int:table_id>/', views.supprimer_table, name='supprimer_table'),

    # Fonctionnalités admin avancées - Personnel
    path('admin/personnel/ajouter/', views.ajouter_personnel, name='ajouter_personnel'),
    path('admin/personnel/modifier/<int:user_id>/', views.modifier_personnel, name='modifier_personnel'),
    path('admin/personnel/supprimer/<int:user_id>/', views.supprimer_personnel, name='supprimer_personnel'),
]
