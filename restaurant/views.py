from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal
from .models import (
    Utilisateur, Client, Table, Plat, Commande,
    LigneCommande, Reservation
)
from .forms import (
    CommandeForm, ReservationForm, ClientForm,
    TableForm, PlatForm, ClientInscriptionForm, ReservationClientForm
)


def index(request):
    """Vue d'accueil avec statistiques"""
    stats = {
        'tables_libres': Table.objects.filter(etat='libre').count(),
        'tables_occupees': Table.objects.filter(etat='occupee').count(),
        'tables_reservees': Table.objects.filter(etat='reservee').count(),
        'commandes_jour': Commande.objects.filter(date__date=date.today()).count(),
        'reservations_jour': Reservation.objects.filter(date=date.today()).count(),

        'revenus_jour': Commande.objects.filter(
            date__date=date.today(), 
            statut='terminee'
        ).aggregate(
            total=Sum(F('lignecommande__quantite') * F('lignecommande__prix_unitaire'))
        )['total'] or 0,
    }
    
    return render(request, 'restaurant/index.html', {'stats': stats})


def menu_public(request):
    """Menu public pour les clients"""
    plats = Plat.objects.filter(disponible=True).order_by('categorie', 'nom')
    categories = {}
    
    for plat in plats:
        if plat.categorie not in categories:
            categories[plat.categorie] = []
        categories[plat.categorie].append(plat)
    
    return render(request, 'restaurant/menu.html', {'categories': categories})


@login_required
def dashboard(request):

    user = request.user

  
    if user.role == 'admin':
        return redirect('restaurant:admin_custom')
    elif user.role == 'serveur':
        return dashboard_serveur(request)

    return redirect('restaurant:index')


def dashboard_admin(request):
    """Tableau de bord administrateur"""
    context = {
        'user': request.user,
        'commandes_today': Commande.objects.filter(date__date=date.today()).count(),
        'revenus_today': Commande.objects.filter(
            date__date=date.today(), 
            statut='terminee'
        ).aggregate(
            total=Sum(F('lignecommande__quantite') * F('lignecommande__prix_unitaire'))
        )['total'] or 0,

        'tables': Table.objects.all().order_by('numero'),
        'utilisateurs_count': Utilisateur.objects.count(),
        'plats_count': Plat.objects.count(),
        'clients_count': Client.objects.count(),
        'reservations_today': Reservation.objects.filter(date=date.today()).count(),
    }
    return render(request, 'restaurant/dashboard_admin.html', context)


def dashboard_serveur(request):

    context = {
        'user': request.user,
        # Données pour confirmer réservations
        'reservations_en_attente': Reservation.objects.filter(
            date=date.today(),
            confirmee=False
        ).order_by('heure'),
        'reservations_confirmees': Reservation.objects.filter(
            date=date.today(),
            confirmee=True
        ).order_by('heure'),

        # Données pour prendre commandes
        'tables_occupees': Table.objects.filter(etat='occupee').order_by('numero'),
        'tables_reservees': Table.objects.filter(etat='reservee').order_by('numero'),
        'tables_libres': Table.objects.filter(etat='libre').order_by('numero'),

        # Données pour générer factures
        'commandes_terminees': Commande.objects.filter(
            statut='terminee',
            date__date=date.today()
        ).order_by('-date'),
        'commandes_en_cours': Commande.objects.filter(
            statut__in=['en_attente', 'en_preparation', 'servie']
        ).order_by('-date'),
    }
    return render(request, 'restaurant/dashboard_serveur.html', context)



# ==================== GESTION DES TABLES ====================

@login_required
def gerer_tables(request):
    """Gérer les tables (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    
    tables = Table.objects.all().order_by('numero')
    return render(request, 'restaurant/gerer_tables.html', {'tables': tables})


@login_required
def ajouter_table(request):
    """Ajouter une nouvelle table"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table ajoutée avec succès!')
            return redirect('restaurant:gerer_tables')
    else:
        form = TableForm()
    
    return render(request, 'restaurant/ajouter_table.html', {'form': form})


@login_required
def attribuer_table(request, table_id):
    """Attribuer une table (Serveur)"""
    if request.user.role != 'serveur':
        return HttpResponseForbidden()
    
    table = get_object_or_404(Table, id=table_id)
    if table.etat == 'libre':
        table.etat = 'occupee'
        table.save()
        messages.success(request, f'Table {table.numero} attribuée!')
    
    return redirect('restaurant:dashboard')


# ==================== GESTION DES PLATS ====================

@login_required
def gerer_plats(request):
    """Gérer les plats (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    
    plats = Plat.objects.all().order_by('categorie', 'nom')
    return render(request, 'restaurant/gerer_plats.html', {'plats': plats})


@login_required
def ajouter_plat(request):
    """Ajouter un nouveau plat"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = PlatForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plat ajouté avec succès!')
            return redirect('restaurant:gerer_plats')
    else:
        form = PlatForm()
    
    return render(request, 'restaurant/ajouter_plat.html', {'form': form})


# ==================== GESTION DES COMMANDES ====================

@login_required
def prendre_commande(request, table_id):
    
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()
    
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        # Créer la commande
        commande = Commande.objects.create(
            utilisateur=request.user,
            table=table,
            commentaire=request.POST.get('commentaire', '')
        )
        
        # Ajouter les plats
        total_items = 0
        for key, value in request.POST.items():
            if key.startswith('plat_') and value:
                plat_id = key.replace('plat_', '')
                quantite = int(value)
                if quantite > 0:
                    plat = get_object_or_404(Plat, id=plat_id)
                    LigneCommande.objects.create(
                        commande=commande,
                        plat=plat,
                        quantite=quantite,
                        prix_unitaire=plat.prix
                    )
                    total_items += quantite
        
        if total_items > 0:
            # Changer l'état de la table
            table.etat = 'occupee'
            table.save()
            
            messages.success(request, f'Commande #{commande.id} créée pour la table {table.numero}')
            return redirect('restaurant:dashboard')
        else:
            commande.delete()
            messages.error(request, 'Veuillez sélectionner au moins un plat')
    
    plats = Plat.objects.filter(disponible=True).order_by('categorie', 'nom')
    categories = {}
    for plat in plats:
        if plat.categorie not in categories:
            categories[plat.categorie] = []
        categories[plat.categorie].append(plat)
    
    return render(request, 'restaurant/prendre_commande.html', {
        'table': table,
        'categories': categories
    })






@login_required
def generer_facture(request, commande_id):
    """Générer une facture (Serveur/Admin)"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    commande = get_object_or_404(Commande, id=commande_id)

    if request.method == 'POST':
        commande.statut = 'terminee'
        commande.save()

        # Libérer la table
        commande.table.etat = 'libre'
        commande.table.save()

        messages.success(request, f'Facture générée et table {commande.table.numero} libérée!')
        return redirect('restaurant:dashboard')

    return render(request, 'restaurant/generer_facture.html', {'commande': commande})


@login_required
def terminer_commande_ajax(request, commande_id):
    """Terminer une commande et retourner les données de facture via AJAX"""
    if request.user.role not in ['serveur', 'admin']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)

        # Calculer le total
        total = sum(ligne.quantite * ligne.prix_unitaire for ligne in commande.lignecommande_set.all())

        # Terminer la commande
        commande.statut = 'terminee'
        commande.save()

        # Libérer la table
        commande.table.etat = 'libre'
        commande.table.save()

        # Préparer les données de la facture
        lignes_facture = []
        for ligne in commande.lignecommande_set.all():
            lignes_facture.append({
                'plat': ligne.plat.nom,
                'quantite': ligne.quantite,
                'prix_unitaire': float(ligne.prix_unitaire),
                'sous_total': float(ligne.quantite * ligne.prix_unitaire)
            })

        facture_data = {
            'commande_id': commande.id,
            'table_numero': commande.table.numero,
            'date': commande.date.strftime('%d/%m/%Y %H:%M'),
            'serveur': commande.utilisateur.get_full_name() or commande.utilisateur.username,
            'lignes': lignes_facture,
            'total': float(total),
            'success': True,
            'message': f'Facture générée pour la table {commande.table.numero}'
        }

        return JsonResponse(facture_data)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def generer_facture_ajax(request, commande_id):
    """Générer une facture via AJAX pour affichage inline"""
    if request.user.role not in ['serveur', 'admin']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'GET':
        try:
            commande = get_object_or_404(Commande, id=commande_id)

            # Vérifier que la commande est terminée
            if commande.statut != 'terminee':
                return JsonResponse({
                    'success': False,
                    'error': f'Cette commande n\'est pas terminée (statut: {commande.get_statut_display()})'
                })

            # Calculer le total
            total = sum(ligne.quantite * ligne.prix_unitaire for ligne in commande.lignecommande_set.all())

            # Préparer les données de la facture
            lignes_facture = []
            for ligne in commande.lignecommande_set.all():
                lignes_facture.append({
                    'plat': ligne.plat.nom,
                    'quantite': ligne.quantite,
                    'prix_unitaire': float(ligne.prix_unitaire),
                    'total': float(ligne.quantite * ligne.prix_unitaire)
                })

            # Données de la facture pour l'affichage inline
            facture_data = {
                'id': commande.id,
                'table': commande.table.numero,
                'date': commande.date.strftime('%d/%m/%Y %H:%M'),
                'client': 'Client sur place',  # Ou récupérer le vrai client si disponible
                'lignes': lignes_facture,
                'total': float(total)
            }

            return JsonResponse({
                'success': True,
                'commande': facture_data,
                'message': f'Facture générée pour la table {commande.table.numero}'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la génération de la facture: {str(e)}'
            })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)




# ==================== GESTION DES RÉSERVATIONS ====================

def reserver_table(request):
    """Réserver une table (Client)"""
    # Vérifier si le client est connecté
    client_id = request.session.get('client_id')
    if not client_id:
        messages.warning(request, 'Veuillez vous inscrire ou vous connecter pour faire une réservation.')
        return redirect('restaurant:connexion_client')

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        messages.error(request, 'Client introuvable.')
        return redirect('restaurant:connexion_client')

    if request.method == 'POST':
        # Créer le formulaire sans le champ client
        form = ReservationClientForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.client = client  # Assigner le client connecté
            reservation.confirmee = False  # La réservation doit être confirmée par le serveur
            reservation.save()

            # NE PAS marquer la table comme réservée - elle le sera quand le serveur confirmera
            # reservation.table.etat = 'reservee'  # Commenté
            # reservation.table.save()  # Commenté

            messages.success(request, f'Réservation demandée pour la table {reservation.table.numero} le {reservation.date} à {reservation.heure}! Elle sera confirmée par notre équipe.')
            return redirect('restaurant:profil_client')
    else:
        form = ReservationClientForm()

    tables_libres = Table.objects.filter(etat='libre')
    return render(request, 'restaurant/reserver_table.html', {
        'form': form,
        'tables_libres': tables_libres,
        'client': client
    })


def annuler_reservation(request, reservation_id):
    """Annuler une réservation directement (Admin/Serveur/Client)"""
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Vérifier les permissions
    if request.user.is_authenticated:
        # Staff peut annuler toute réservation
        if request.user.role not in ['admin', 'serveur']:
            return HttpResponseForbidden()
        redirect_url = 'restaurant:dashboard'
    else:
        # Client peut annuler seulement ses propres réservations
        client_id = request.session.get('client_id')
        if not client_id or reservation.client.id != client_id:
            messages.error(request, 'Vous ne pouvez annuler que vos propres réservations.')
            return redirect('restaurant:connexion_client')
        redirect_url = 'restaurant:profil_client'

    # Annulation directe (POST seulement)
    if request.method == 'POST':
        table_numero = reservation.table.numero
        client_nom = reservation.client.nom

        # Libérer la table
        reservation.table.etat = 'libre'
        reservation.table.save()

        # Supprimer la réservation
        reservation.delete()

        messages.success(request, f'Réservation de {client_nom} pour la table {table_numero} annulée!')
        return redirect(redirect_url)

    # Si GET, rediriger vers la page d'origine
    return redirect(redirect_url)


@login_required
def annuler_reservation_ajax(request, reservation_id):
    """Annuler une réservation via AJAX avec synchronisation dashboard"""
    if request.user.role not in ['admin', 'serveur']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)

        # Sauvegarder les informations avant suppression
        table_numero = reservation.table.numero
        client_nom = reservation.client.nom
        client_telephone = reservation.client.telephone
        date_reservation = reservation.date.strftime('%d/%m/%Y')
        heure_reservation = reservation.heure.strftime('%H:%M')

        # Libérer la table
        reservation.table.etat = 'libre'
        reservation.table.save()

        # Supprimer la réservation
        reservation.delete()

        # Retourner les données pour mise à jour du dashboard
        return JsonResponse({
            'success': True,
            'message': f'Réservation de {client_nom} annulée',
            'table_numero': table_numero,
            'client_nom': client_nom,
            'client_telephone': client_telephone,
            'date_reservation': date_reservation,
            'heure_reservation': heure_reservation,
            'reservation_id': reservation_id,
            'notification': f'La réservation de {client_nom} pour la table {table_numero} le {date_reservation} à {heure_reservation} a été annulée par le restaurant.'
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def annuler_commande_client(request, commande_id):
    """Annuler une commande côté client"""
    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)

        # Vérifier que la commande peut être annulée (seulement en préparation)
        if commande.statut != 'en_preparation':
            return JsonResponse({
                'success': False,
                'error': 'Cette commande ne peut plus être annulée'
            })

        # Vérifier que c'est bien le client de cette commande
        client_id = request.session.get('client_id')
        if not client_id:
            return JsonResponse({
                'success': False,
                'error': 'Vous devez être connecté'
            })

        # Vérifier que le client a bien une réservation confirmée pour cette table
        client = get_object_or_404(Client, id=client_id)
        reservation_client = Reservation.objects.filter(
            client=client,
            table=commande.table,
            confirmee=True
        ).exists()

        if not reservation_client:
            return JsonResponse({
                'success': False,
                'error': 'Vous ne pouvez annuler que vos propres commandes'
            })

        # Sauvegarder les informations avant annulation
        table_numero = commande.table.numero
        commande_id_str = str(commande.id)
        total = float(commande.total)

        # Marquer la commande comme annulée
        commande.statut = 'annulee'
        commande.save()

        # Libérer la table si c'était la seule commande
        autres_commandes = Commande.objects.filter(
            table=commande.table
        ).exclude(statut__in=['annulee', 'terminee']).exists()

        if not autres_commandes:
            commande.table.etat = 'libre'
            commande.table.save()

        return JsonResponse({
            'success': True,
            'message': f'Commande #{commande_id_str} annulée',
            'table_numero': table_numero,
            'total': total,
            'commande_id': commande_id_str
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def annuler_commande_serveur(request, commande_id):
    """Annuler une commande côté serveur avec AJAX"""
    if request.user.role not in ['admin', 'serveur']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)

        # Vérifier que la commande peut être annulée
        if commande.statut not in ['en_preparation', 'servie']:
            return JsonResponse({
                'success': False,
                'error': 'Cette commande ne peut plus être annulée'
            })

        # Sauvegarder les informations avant annulation
        table_numero = commande.table.numero
        commande_id_str = str(commande.id)
        total = float(commande.total)
        ancien_statut = commande.get_statut_display()

        # Marquer la commande comme annulée
        commande.statut = 'annulee'
        commande.save()

        # Libérer la table si c'était la seule commande active
        autres_commandes = Commande.objects.filter(
            table=commande.table
        ).exclude(statut__in=['annulee', 'terminee']).exists()

        if not autres_commandes:
            commande.table.etat = 'libre'
            commande.table.save()

        return JsonResponse({
            'success': True,
            'message': f'Commande #{commande_id_str} annulée',
            'table_numero': table_numero,
            'total': total,
            'ancien_statut': ancien_statut,
            'commande_id': commande_id_str
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)




# ==================== GESTION DES CLIENTS ====================

def inscription_client(request):
    """Inscription d'un nouveau client"""
    if request.method == 'POST':
        form = ClientInscriptionForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Inscription réussie ! Bienvenue {client.nom}')
            # Stocker l'ID du client en session pour les réservations
            request.session['client_id'] = client.id
            return redirect('restaurant:profil_client')
    else:
        form = ClientInscriptionForm()

    return render(request, 'restaurant/inscription_client.html', {'form': form})


def profil_client(request):
    """Profil et gestion du compte client"""
    client_id = request.session.get('client_id')
    if not client_id:
        messages.warning(request, 'Veuillez vous inscrire ou vous connecter.')
        return redirect('restaurant:connexion_client')

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        messages.error(request, 'Client introuvable.')
        return redirect('restaurant:connexion_client')

    # Récupérer les réservations du client
    reservations = Reservation.objects.filter(client=client).order_by('-date', '-heure')

    # Récupérer les commandes du client (via les tables qu'il a réservées)
    # On récupère les commandes des tables où le client a une réservation confirmée
    tables_client = Table.objects.filter(
        reservation__client=client,
        reservation__confirmee=True
    ).distinct()

    commandes = Commande.objects.filter(
        table__in=tables_client
    ).exclude(statut='annulee').order_by('-date')

    context = {
        'client': client,
        'reservations': reservations,
        'commandes': commandes
    }
    return render(request, 'restaurant/profil_client.html', context)


def connexion_client(request):
    """Connexion d'un client existant"""
    if request.method == 'POST':
        telephone = request.POST.get('telephone')
        try:
            client = Client.objects.get(telephone=telephone)
            request.session['client_id'] = client.id
            messages.success(request, f'Connexion réussie ! Bienvenue {client.nom}')
            return redirect('restaurant:profil_client')
        except Client.DoesNotExist:
            messages.error(request, 'Numéro de téléphone non trouvé. Veuillez vous inscrire.')

    return render(request, 'restaurant/connexion_client.html')


def deconnexion_client(request):
    """Déconnexion du client"""
    # Vérifier si le client était connecté
    was_connected = 'client_id' in request.session

    # Supprimer la session
    if 'client_id' in request.session:
        del request.session['client_id']

    # Si c'était une déconnexion volontaire, afficher la page de confirmation
    if was_connected:
        return render(request, 'restaurant/deconnexion_client.html')
    else:
        # Si pas connecté, rediriger vers l'accueil avec un message
        messages.info(request, 'Vous n\'étiez pas connecté.')
        return redirect('restaurant:index')


def modifier_profil_client(request):
    """Modifier le profil du client"""
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('restaurant:connexion_client')

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return redirect('restaurant:connexion_client')

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès !')
            return redirect('restaurant:profil_client')
    else:
        form = ClientForm(instance=client)

    return render(request, 'restaurant/modifier_profil_client.html', {'form': form, 'client': client})


# ==================== FONCTIONNALITÉS SERVEUR AVANCÉES ====================

@login_required
def gerer_factures(request):
    """Interface de gestion des factures pour les serveurs"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    # Commandes prêtes à facturer
    commandes_a_facturer = Commande.objects.filter(statut='servie').order_by('-date')

    # Factures du jour
    factures_jour = Commande.objects.filter(
        statut='terminee',
        date__date=date.today()
    ).order_by('-date')

    context = {
        'commandes_a_facturer': commandes_a_facturer,
        'factures_jour': factures_jour,
        'total_jour': factures_jour.aggregate(
            total=Sum(F('lignecommande__quantite') * F('lignecommande__prix_unitaire'))
        )['total'] or 0
    }

    return render(request, 'restaurant/gerer_factures.html', context)





@login_required
def prendre_commandes(request):
    """Interface pour prendre les commandes"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    tables_occupees = Table.objects.filter(etat='occupee').order_by('numero')
    tables_libres = Table.objects.filter(etat='libre').order_by('numero')
    commandes_en_cours = Commande.objects.filter(
        statut__in=['en_attente', 'en_preparation']
    ).order_by('-date')

    context = {
        'tables_occupees': tables_occupees,
        'tables_libres': tables_libres,
        'commandes_en_cours': commandes_en_cours
    }

    return render(request, 'restaurant/prendre_commandes.html', context)


@login_required
def envoyer_commande_cuisine(request, commande_id):
    """Envoyer une commande spécifique à la cuisine"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    commande = get_object_or_404(Commande, id=commande_id)

    if commande.statut == 'en_attente':
        commande.statut = 'en_preparation'
        commande.save()
        messages.success(request, f'Commande #{commande.id} envoyée à la cuisine!')
    else:
        messages.warning(request, 'Cette commande a déjà été envoyée à la cuisine.')

    return redirect('restaurant:prendre_commandes')


@login_required
def liberer_table(request, table_id):
    """Libérer une table après service"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    table = get_object_or_404(Table, id=table_id)

    if table.etat in ['occupee', 'reservee']:
        table.etat = 'libre'
        table.save()
        messages.success(request, f'Table {table.numero} libérée!')

    return redirect('restaurant:attribuer_tables')


def acces_refuse(request):
    """Page d'accès refusé pour les clients tentant d'accéder à l'admin"""
    return render(request, 'restaurant/acces_refuse.html')


def deconnexion_staff(request):
    """Page de déconnexion personnalisée pour le staff"""
    return render(request, 'restaurant/deconnexion_staff.html')


@login_required
def admin_custom(request):
    """Interface d'administration personnalisée - ADMIN UNIQUEMENT"""
    if request.user.role != 'admin':
        messages.error(request, 'Accès réservé aux administrateurs uniquement.')
        return redirect('restaurant:dashboard')

    # Calculer les statistiques
    from .models import Client, Plat, Table, Commande
    from django.utils import timezone

    stats = {
        'total_clients': Client.objects.count(),
        'total_plats': Plat.objects.count(),
        'total_tables': Table.objects.count(),
        'commandes_jour': Commande.objects.filter(
            date__date=timezone.now().date()
        ).count(),
    }

    return render(request, 'restaurant/admin_custom.html', {
        'stats': stats
    })


def admin_redirect(request):
    """Redirection de /admin/ vers notre interface personnalisée"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('restaurant:admin_custom')
    else:
        return redirect('/django-admin/login/')


@login_required
def gerer_plats_simple(request):
    """Gestion simple des plats"""
    if not request.user.is_staff:
        return redirect('restaurant:acces_refuse')

    from .models import Plat
    plats = Plat.objects.all().order_by('categorie', 'nom')

    return render(request, 'restaurant/gerer_plats_simple.html', {
        'plats': plats
    })


@login_required
def gerer_tables_simple(request):
    """Gestion simple des tables"""
    if not request.user.is_staff:
        return redirect('restaurant:acces_refuse')

    from .models import Table
    tables = Table.objects.all().order_by('numero')

    return render(request, 'restaurant/gerer_tables_simple.html', {
        'tables': tables
    })


@login_required
def gerer_personnel_simple(request):
    """Gestion simple du personnel"""
    if not request.user.is_staff:
        return redirect('restaurant:acces_refuse')

    personnel = Utilisateur.objects.filter(is_staff=True).order_by('username')

    return render(request, 'restaurant/gerer_personnel_simple.html', {
        'personnel': personnel
    })


@login_required
def statistiques_simple(request):
    """Statistiques simples"""
    if not request.user.is_staff:
        return redirect('restaurant:acces_refuse')

    from .models import Client, Plat, Table, Commande, Reservation
    from django.utils import timezone

    today = timezone.now().date()

    stats = {
        'clients_total': Client.objects.count(),
        'plats_total': Plat.objects.count(),
        'tables_total': Table.objects.count(),
        'commandes_jour': Commande.objects.filter(date__date=today).count(),
        'reservations_jour': Reservation.objects.filter(date=today).count(),
        'chiffre_affaires_jour': sum(
            commande.total for commande in Commande.objects.filter(date__date=today)
        ),
    }

    return render(request, 'restaurant/statistiques_simple.html', {
        'stats': stats
    })





@login_required
def logout_staff(request):
    """Déconnexion du staff avec redirection"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('restaurant:deconnexion_staff')



# ==================== CONNEXION STAFF ====================

def staff_login(request):
    """Connexion personnalisée pour le staff"""
    if request.user.is_authenticated:
        return redirect('restaurant:admin_custom')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('restaurant:admin_custom')
        else:
            messages.error(request, 'Identifiants invalides ou accès non autorisé.')

    return render(request, 'restaurant/staff_login.html')


def staff_logout(request):
    """Déconnexion du staff"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('restaurant:staff_deconnexion')


def staff_deconnexion(request):
    """Page de déconnexion staff"""
    return render(request, 'restaurant/deconnexion_staff.html')


# ==================== FONCTIONNALITÉS SERVEUR AVANCÉES ====================

@login_required
def confirmer_reservation(request, reservation_id):
    """Confirmer une réservation (Serveur/Admin)"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)
        reservation.confirmee = True
        reservation.save()

        # Marquer la table comme réservée
        reservation.table.etat = 'reservee'
        reservation.table.save()

        messages.success(request, f'Réservation confirmée pour {reservation.client.nom}')
        return redirect('restaurant:dashboard_serveur')

    return HttpResponseForbidden()


@login_required
def confirmer_reservation_ajax(request, reservation_id):
    """Confirmer une réservation via AJAX avec synchronisation dashboard"""
    if request.user.role not in ['admin', 'serveur']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)

        # Sauvegarder les informations avant modification
        table_numero = reservation.table.numero
        client_nom = reservation.client.nom
        client_telephone = reservation.client.telephone
        date_reservation = reservation.date.strftime('%d/%m/%Y')
        heure_reservation = reservation.heure.strftime('%H:%M')

        # Confirmer la réservation
        reservation.confirmee = True
        reservation.save()

        # Marquer la table comme réservée
        reservation.table.etat = 'reservee'
        reservation.table.save()

        # Retourner les données pour mise à jour du dashboard
        return JsonResponse({
            'success': True,
            'message': f'Réservation de {client_nom} confirmée',
            'table_numero': table_numero,
            'client_nom': client_nom,
            'client_telephone': client_telephone,
            'date_reservation': date_reservation,
            'heure_reservation': heure_reservation,
            'reservation_id': reservation_id,
            'notification': f'La réservation de {client_nom} pour la table {table_numero} le {date_reservation} à {heure_reservation} a été confirmée.'
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def liberer_table(request, table_id):
    """Libérer une table (Serveur)"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    if request.method == 'POST':
        table = get_object_or_404(Table, id=table_id)

        # Vérifier que la table peut être libérée
        if table.etat not in ['occupee', 'reservee']:
            return JsonResponse({
                'success': False,
                'error': f'Cette table est déjà libre (état: {table.get_etat_display()})'
            })

        # Sauvegarder l'état précédent
        ancien_etat = table.etat

        # Libérer la table
        table.etat = 'libre'
        table.save()

        # Réponse AJAX ou redirection normale
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'Table {table.numero} libérée avec succès',
                'table_numero': table.numero,
                'ancien_etat': ancien_etat,
                'nouvel_etat': 'libre'
            })
        else:
            messages.success(request, f'Table {table.numero} libérée avec succès')
            return redirect('restaurant:dashboard_serveur')

    return HttpResponseForbidden()


@login_required
def marquer_commande_servie(request, commande_id):
    """Marquer une commande comme servie (Serveur/Admin)"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)
        commande.statut = 'servie'
        commande.save()

        messages.success(request, f'Commande #{commande.id} marquée comme servie')
        return redirect('restaurant:dashboard')

    return HttpResponseForbidden()


@login_required
def marquer_servie_ajax(request, commande_id):
    """Marquer une commande comme servie via AJAX avec synchronisation dashboard"""
    if request.user.role not in ['admin', 'serveur']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)

        # Vérifier que la commande peut être marquée comme servie
        if commande.statut != 'en_preparation':
            return JsonResponse({
                'success': False,
                'error': f'Cette commande ne peut pas être marquée comme servie (statut: {commande.get_statut_display()})'
            })

        # Sauvegarder les informations avant modification
        table_numero = commande.table.numero
        date_commande = commande.date.strftime('%d/%m/%Y %H:%M')

        # Marquer comme servie
        commande.statut = 'servie'
        commande.save()

        # Retourner les données pour mise à jour du dashboard
        return JsonResponse({
            'success': True,
            'message': f'Commande table {table_numero} marquée comme servie',
            'table_numero': table_numero,
            'commande_id': commande_id,
            'date_commande': date_commande,
            'nouveau_statut': 'servie',
            'nouveau_statut_display': commande.get_statut_display()
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def commande_rapide(request, table_id):
    """Interface de commande rapide (Serveur)"""
    if request.user.role not in ['serveur', 'admin']:
        return HttpResponseForbidden()

    table = get_object_or_404(Table, id=table_id)
    plats = Plat.objects.filter(disponible=True).order_by('categorie', 'nom')

    if request.method == 'POST':
        # Créer une nouvelle commande
        commande = Commande.objects.create(
            table=table,
            utilisateur=request.user,
            statut='en_preparation'
        )

        # Ajouter les plats sélectionnés
        total = 0
        for key, value in request.POST.items():
            if key.startswith('plat_') and value:
                plat_id = key.replace('plat_', '')
                quantite = int(value)
                plat = get_object_or_404(Plat, id=plat_id)

                LigneCommande.objects.create(
                    commande=commande,
                    plat=plat,
                    quantite=quantite,
                    prix_unitaire=plat.prix
                )
                total += plat.prix * quantite

        # Marquer la table comme occupée
        table.etat = 'occupee'
        table.save()

        messages.success(request, f'Commande créée pour la table {table.numero}')
        return redirect('restaurant:dashboard_serveur')

    context = {
        'table': table,
        'plats': plats,
        'categories': ['entree', 'plat', 'dessert', 'boisson']
    }
    return render(request, 'restaurant/commande_rapide.html', context)


# ==================== FONCTIONNALITÉS ADMIN AVANCÉES ====================

@login_required
def ajouter_plat(request):
    """Ajouter un nouveau plat (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        categorie = request.POST.get('categorie')
        disponible = request.POST.get('disponible') == 'on'

        if nom and prix and categorie:
            Plat.objects.create(
                nom=nom,
                description=description,
                prix=float(prix),
                categorie=categorie,
                disponible=disponible
            )
            messages.success(request, f'Plat "{nom}" ajouté avec succès')
            return redirect('restaurant:gerer_plats_simple')
        else:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires')

    return render(request, 'restaurant/ajouter_plat.html')


@login_required
def modifier_plat(request, plat_id):
    """Modifier un plat (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    plat = get_object_or_404(Plat, id=plat_id)

    if request.method == 'POST':
        plat.nom = request.POST.get('nom', plat.nom)
        plat.description = request.POST.get('description', plat.description)
        plat.prix = float(request.POST.get('prix', plat.prix))
        plat.categorie = request.POST.get('categorie', plat.categorie)
        plat.disponible = request.POST.get('disponible') == 'on'
        plat.save()

        messages.success(request, f'Plat "{plat.nom}" modifié avec succès')
        return redirect('restaurant:gerer_plats_simple')

    return render(request, 'restaurant/modifier_plat.html', {'plat': plat})


@login_required
def supprimer_plat(request, plat_id):
    """Supprimer un plat (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    plat = get_object_or_404(Plat, id=plat_id)

    if request.method == 'POST':
        nom_plat = plat.nom
        plat.delete()
        messages.success(request, f'Plat "{nom_plat}" supprimé avec succès')
        return redirect('restaurant:gerer_plats_simple')

    return render(request, 'restaurant/supprimer_plat.html', {'plat': plat})


@login_required
def ajouter_table(request):
    """Ajouter une nouvelle table (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        numero = request.POST.get('numero')
        capacite = request.POST.get('capacite')

        if numero and capacite:
            # Vérifier que le numéro n'existe pas déjà
            if Table.objects.filter(numero=numero).exists():
                messages.error(request, f'Une table avec le numéro {numero} existe déjà')
            else:
                Table.objects.create(
                    numero=int(numero),
                    capacite=int(capacite),
                    etat='libre'
                )
                messages.success(request, f'Table {numero} ajoutée avec succès')
                return redirect('restaurant:gerer_tables_simple')
        else:
            messages.error(request, 'Veuillez remplir tous les champs')

    return render(request, 'restaurant/ajouter_table.html')


@login_required
def modifier_table(request, table_id):
    """Modifier une table (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    table = get_object_or_404(Table, id=table_id)

    if request.method == 'POST':
        nouveau_numero = request.POST.get('numero')
        nouvelle_capacite = request.POST.get('capacite')

        if nouveau_numero and nouvelle_capacite:
            # Vérifier que le nouveau numéro n'existe pas déjà (sauf pour cette table)
            if Table.objects.filter(numero=nouveau_numero).exclude(id=table.id).exists():
                messages.error(request, f'Une table avec le numéro {nouveau_numero} existe déjà')
            else:
                table.numero = int(nouveau_numero)
                table.capacite = int(nouvelle_capacite)
                table.save()
                messages.success(request, f'Table {table.numero} modifiée avec succès')
                return redirect('restaurant:gerer_tables_simple')
        else:
            messages.error(request, 'Veuillez remplir tous les champs')

    return render(request, 'restaurant/modifier_table.html', {'table': table})


@login_required
def supprimer_table(request, table_id):
    """Supprimer une table (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    table = get_object_or_404(Table, id=table_id)

    # Vérifier que la table n'est pas occupée ou réservée
    if table.etat != 'libre':
        messages.error(request, f'Impossible de supprimer la table {table.numero} : elle est {table.get_etat_display().lower()}')
        return redirect('restaurant:gerer_tables_simple')

    if request.method == 'POST':
        numero_table = table.numero
        table.delete()
        messages.success(request, f'Table {numero_table} supprimée avec succès')
        return redirect('restaurant:gerer_tables_simple')

    return render(request, 'restaurant/supprimer_table.html', {'table': table})


@login_required
def ajouter_personnel(request):
    """Ajouter un nouveau membre du personnel (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')

        if username and password and role:
            # Vérifier que l'username n'existe pas déjà
            if Utilisateur.objects.filter(username=username).exists():
                messages.error(request, f'Un utilisateur avec le nom "{username}" existe déjà')
            else:
                Utilisateur.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_staff=True
                )
                messages.success(request, f'Utilisateur "{username}" créé avec succès')
                return redirect('restaurant:gerer_personnel_simple')
        else:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires')

    return render(request, 'restaurant/ajouter_personnel.html')


@login_required
def modifier_personnel(request, user_id):
    """Modifier un membre du personnel (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    user = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        user.is_active = request.POST.get('is_active') == 'on'

        # Changer le mot de passe si fourni
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, f'Utilisateur "{user.username}" modifié avec succès')
        return redirect('restaurant:gerer_personnel_simple')

    return render(request, 'restaurant/modifier_personnel.html', {'user_obj': user})


@login_required
def supprimer_personnel(request, user_id):
    """Supprimer un membre du personnel (Admin)"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    user = get_object_or_404(Utilisateur, id=user_id)

    # Empêcher la suppression de son propre compte
    if user.id == request.user.id:
        messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte')
        return redirect('restaurant:gerer_personnel_simple')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Utilisateur "{username}" supprimé avec succès')
        return redirect('restaurant:gerer_personnel_simple')

    return render(request, 'restaurant/supprimer_personnel.html', {'user_obj': user})


# ==================== NOUVELLES FONCTIONNALITÉS PERSONNEL ====================

@login_required
def ajouter_personnel_modal(request):
    """Ajouter un nouveau membre du personnel via modal"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role')

            # Vérifier si l'utilisateur existe déjà
            if Utilisateur.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Ce nom d\'utilisateur existe déjà'})

            if Utilisateur.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Cette adresse email existe déjà'})

            # Créer l'utilisateur
            Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_staff=True
            )

            return JsonResponse({'success': True, 'message': 'Personnel ajouté avec succès'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def gerer_roles_personnel(request):
    """Gérer les rôles du personnel"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('new_role')

            user = Utilisateur.objects.get(id=user_id)
            user.role = new_role
            user.save()

            return JsonResponse({'success': True, 'message': 'Rôle modifié avec succès'})

        except Utilisateur.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Retourner la liste des utilisateurs avec leurs rôles
    utilisateurs = Utilisateur.objects.all().values('id', 'username', 'first_name', 'last_name', 'role', 'is_active')
    return JsonResponse({'success': True, 'utilisateurs': list(utilisateurs)})

@login_required
def exporter_liste_personnel(request):
    """Exporter la liste du personnel en CSV"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="personnel.csv"'

    writer = csv.writer(response)
    writer.writerow(['Nom d\'utilisateur', 'Prénom', 'Nom', 'Email', 'Rôle', 'Actif', 'Date de création'])

    for user in Utilisateur.objects.all():
        writer.writerow([
            user.username,
            user.first_name,
            user.last_name,
            user.email,
            user.role,
            'Oui' if user.is_active else 'Non',
            user.date_joined.strftime('%d/%m/%Y')
        ])

    return response

@login_required
def parametres_securite(request):
    """Gérer les paramètres de sécurité"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        try:
            action = request.POST.get('action')

            if action == 'reset_password':
                user_id = request.POST.get('user_id')
                new_password = request.POST.get('new_password')

                user = Utilisateur.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()

                return JsonResponse({'success': True, 'message': 'Mot de passe réinitialisé'})

            elif action == 'toggle_active':
                user_id = request.POST.get('user_id')

                user = Utilisateur.objects.get(id=user_id)
                user.is_active = not user.is_active
                user.save()

                status = 'activé' if user.is_active else 'désactivé'
                return JsonResponse({'success': True, 'message': f'Utilisateur {status}'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Action non reconnue'})


# ==================== NOUVELLES FONCTIONNALITÉS STATISTIQUES ====================

@login_required
def rapport_journalier(request):
    """Générer un rapport journalier"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    from datetime import date

    today = date.today()

    # Statistiques du jour
    commandes_jour = Commande.objects.filter(date__date=today)
    reservations_jour = Reservation.objects.filter(date_reservation__date=today)

    # Calcul du chiffre d'affaires
    ca_jour = 0
    for commande in commandes_jour.filter(statut='terminee'):
        for ligne in commande.lignecommande_set.all():
            ca_jour += ligne.quantite * ligne.prix_unitaire



    rapport = {
        'date': today.strftime('%d/%m/%Y'),
        'commandes_total': commandes_jour.count(),
        'commandes_terminees': commandes_jour.filter(statut='terminee').count(),
        'reservations_total': reservations_jour.count(),
        'chiffre_affaires': float(ca_jour),
        'tables_occupees': Table.objects.filter(etat='occupee').count(),
        'clients_servis': commandes_jour.values('client').distinct().count()
    }

    return JsonResponse({'success': True, 'rapport': rapport})

@login_required
def rapport_mensuel(request):
    """Générer un rapport mensuel"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    from datetime import date, timedelta
    import calendar

    today = date.today()
    premier_jour = date(today.year, today.month, 1)

    # Statistiques du mois
    commandes_mois = Commande.objects.filter(date__date__gte=premier_jour)
    reservations_mois = Reservation.objects.filter(date_reservation__date__gte=premier_jour)

    # Calcul du chiffre d'affaires mensuel
    ca_mois = 0
    for commande in commandes_mois.filter(statut='terminee'):
        for ligne in commande.lignecommande_set.all():
            ca_mois += ligne.quantite * ligne.prix_unitaire

    # Évolution par semaine
    evolution_semaines = []
    for semaine in range(4):
        debut_semaine = premier_jour + timedelta(weeks=semaine)
        fin_semaine = debut_semaine + timedelta(days=6)

        commandes_semaine = commandes_mois.filter(
            date__date__gte=debut_semaine,
            date__date__lte=fin_semaine
        )

        ca_semaine = 0
        for commande in commandes_semaine.filter(statut='terminee'):
            for ligne in commande.lignecommande_set.all():
                ca_semaine += ligne.quantite * ligne.prix_unitaire

        evolution_semaines.append({
            'semaine': f'Semaine {semaine + 1}',
            'commandes': commandes_semaine.count(),
            'chiffre_affaires': float(ca_semaine)
        })

    rapport = {
        'mois': calendar.month_name[today.month],
        'annee': today.year,
        'commandes_total': commandes_mois.count(),
        'reservations_total': reservations_mois.count(),
        'chiffre_affaires': float(ca_mois),
        'evolution_semaines': evolution_semaines,
        'moyenne_commandes_jour': round(commandes_mois.count() / today.day, 1)
    }

    return JsonResponse({'success': True, 'rapport': rapport})

@login_required
def analyse_clients(request):
    """Analyser les données clients"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    # Statistiques clients
    total_clients = Client.objects.count()
    from datetime import timedelta
    clients_actifs = Client.objects.filter(
        commande__date__date__gte=date.today() - timedelta(days=30)
    ).distinct().count()

    # Clients les plus fidèles
    clients_fideles = []
    for client in Client.objects.all():
        nb_commandes = client.commande_set.count()
        if nb_commandes > 0:
            clients_fideles.append({
                'nom': f"{client.first_name} {client.last_name}",
                'email': client.email,
                'commandes': nb_commandes
            })

    clients_fideles = sorted(clients_fideles, key=lambda x: x['commandes'], reverse=True)[:10]

    analyse = {
        'total_clients': total_clients,
        'clients_actifs': clients_actifs,
        'taux_fidelite': round((clients_actifs / total_clients * 100) if total_clients > 0 else 0, 1),
        'clients_fideles': clients_fideles,
        'nouveaux_clients_mois': Client.objects.filter(
            date_joined__date__gte=date.today().replace(day=1)
        ).count()
    }

    return JsonResponse({'success': True, 'analyse': analyse})

@login_required
def analyse_ventes(request):
    """Analyser les données de ventes"""
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    
    ventes_plats = {}
    revenus_plats = {}

    for ligne in LigneCommande.objects.filter(commande__statut='terminee'):
        plat_nom = ligne.plat.nom
        quantite = ligne.quantite
        prix = ligne.prix_unitaire

        if plat_nom in ventes_plats:
            ventes_plats[plat_nom] += quantite
            revenus_plats[plat_nom] += quantite * prix
        else:
            ventes_plats[plat_nom] = quantite
            revenus_plats[plat_nom] = quantite * prix

    
    top_quantite = sorted(ventes_plats.items(), key=lambda x: x[1], reverse=True)[:10]

    
    top_revenus = sorted(revenus_plats.items(), key=lambda x: x[1], reverse=True)[:10]

    
    categories_ventes = {}
    for plat in Plat.objects.all():
        categorie = plat.categorie
        if categorie in categories_ventes:
            categories_ventes[categorie] += ventes_plats.get(plat.nom, 0)
        else:
            categories_ventes[categorie] = ventes_plats.get(plat.nom, 0)

    analyse = {
        'top_plats_quantite': [{'nom': nom, 'quantite': qty} for nom, qty in top_quantite],
        'top_plats_revenus': [{'nom': nom, 'revenus': float(rev)} for nom, rev in top_revenus],
        'ventes_categories': [{'categorie': cat, 'quantite': qty} for cat, qty in categories_ventes.items()],
        'total_revenus': float(sum(revenus_plats.values())),
        'total_plats_vendus': sum(ventes_plats.values())
    }

    return JsonResponse({'success': True, 'analyse': analyse})
