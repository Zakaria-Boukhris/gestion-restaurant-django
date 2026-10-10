from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal


class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé avec rôles"""
    ROLES = [
        ('admin', 'Administrateur'),
        ('serveur', 'Serveur'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default='serveur',
        verbose_name='Rôle'
    )
    
   
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='restaurant_users',
        related_query_name='restaurant_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='restaurant_users',
        related_query_name='restaurant_user',
    )
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Client(models.Model):
    """Modèle pour les clients du restaurant"""
    nom = models.CharField(max_length=100, verbose_name='Nom')
    telephone = models.CharField(max_length=15, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    
    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.telephone})"


class Table(models.Model):
    """Modèle pour les tables du restaurant"""
    ETATS = [
        ('libre', 'Libre'),
        ('occupee', 'Occupée'),
        ('reservee', 'Réservée'),
    ]
    
    numero = models.IntegerField(unique=True, verbose_name='Numéro')
    capacite = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Capacité'
    )
    etat = models.CharField(
        max_length=20,
        choices=ETATS,
        default='libre',
        verbose_name='État'
    )
    
    class Meta:
        verbose_name = 'Table'
        verbose_name_plural = 'Tables'
        ordering = ['numero']
    
    def __str__(self):
        return f"Table {self.numero} ({self.capacite} places) - {self.get_etat_display()}"


class Plat(models.Model):
    """Modèle pour les plats du menu"""
    CATEGORIES = [
        ('entree', 'Entrée'),
        ('plat', 'Plat principal'),
        ('dessert', 'Dessert'),
        ('boisson', 'Boisson'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name='Nom')
    prix = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Prix (DH)',
        help_text='Prix en dirhams marocains'
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        verbose_name='Catégorie'
    )
    description = models.TextField(blank=True, verbose_name='Description')
    disponible = models.BooleanField(default=True, verbose_name='Disponible')
    image = models.ImageField(upload_to='plats/', blank=True, verbose_name='Image')
    
    class Meta:
        verbose_name = 'Plat'
        verbose_name_plural = 'Plats'
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.prix} DH) - {self.get_categorie_display()}"


class Commande(models.Model):
    """Modèle pour les commandes"""
    STATUTS = [
        ('en_preparation', 'En préparation'),
        ('servie', 'Servie'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        verbose_name='Serveur'
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        verbose_name='Table'
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name='Date')
    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default='en_preparation',
        verbose_name='Statut'
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')
    
    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-date']
    
    def __str__(self):
        return f"Commande #{self.id} - Table {self.table.numero} ({self.get_statut_display()})"
    
    @property
    def total(self):
        """Calcule le total de la commande"""
        return sum(ligne.sous_total for ligne in self.lignecommande_set.all())


class LigneCommande(models.Model):
    """Modèle pour les lignes de commande"""
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        verbose_name='Commande'
    )
    plat = models.ForeignKey(
        Plat,
        on_delete=models.CASCADE,
        verbose_name='Plat'
    )
    quantite = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantité'
    )
    prix_unitaire = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Prix unitaire'
    )
    
    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'
        unique_together = ['commande', 'plat']
    
    def save(self, *args, **kwargs):
        
        if not self.prix_unitaire:
            self.prix_unitaire = self.plat.prix
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantite}x {self.plat.nom}"
    
    @property
    def sous_total(self):
        """Calcule le sous-total de la ligne"""
        return self.quantite * self.prix_unitaire




class Reservation(models.Model):
    """Modèle pour les réservations"""
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Client'
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        verbose_name='Table'
    )
    date = models.DateField(verbose_name='Date')
    heure = models.TimeField(verbose_name='Heure de début')
    heure_fin = models.TimeField(null=True, blank=True, verbose_name='Heure de fin')
    nombre_personnes = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Nombre de personnes'
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')
    confirmee = models.BooleanField(default=False, verbose_name='Confirmée')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    
    class Meta:
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering = ['date', 'heure']
        unique_together = ['table', 'date', 'heure']
    
    def save(self, *args, **kwargs):
        """Calculer automatiquement l'heure de fin (1h30 après le début)"""
        if not self.heure_fin:
            from datetime import datetime, timedelta
            # Convertir l'heure en datetime pour ajouter 1h30
            debut = datetime.combine(self.date, self.heure)
            fin = debut + timedelta(hours=1, minutes=30)
            self.heure_fin = fin.time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Réservation {self.client.nom} - Table {self.table.numero} le {self.date} à {self.heure}-{self.heure_fin}"

    def peut_etre_annulee_par_client(self):
        """Vérifie si le client peut annuler cette réservation"""
        from datetime import datetime, timedelta
        from django.utils import timezone

        # Utiliser datetime naive pour éviter les problèmes de timezone
        reservation_datetime = datetime.combine(self.date, self.heure)
        maintenant = datetime.now()

        # Calculer la limite (maintenant + 2 heures)
        limite_annulation = maintenant + timedelta(hours=2)

        # Permettre annulation si réservation dans plus de 2 heures
        return reservation_datetime > limite_annulation

    @classmethod
    def verifier_disponibilite_creneau(cls, table, date, heure_debut, heure_fin=None, reservation_id=None):
        """
        Vérifie si une table est disponible pour un créneau donné

        Args:
            table: Instance de Table
            date: Date de la réservation
            heure_debut: Heure de début
            heure_fin: Heure de fin (calculée automatiquement si None)
            reservation_id: ID de la réservation à exclure (pour modification)

        Returns:
            bool: True si disponible, False sinon
        """
        from datetime import datetime, timedelta

        # Calculer l'heure de fin si non fournie
        if not heure_fin:
            debut = datetime.combine(date, heure_debut)
            fin = debut + timedelta(hours=1, minutes=30)
            heure_fin = fin.time()

        # Récupérer toutes les réservations de cette table pour cette date
        reservations_existantes = cls.objects.filter(
            table=table,
            date=date
        )

        # Exclure la réservation actuelle si on modifie
        if reservation_id:
            reservations_existantes = reservations_existantes.exclude(id=reservation_id)

        # Vérifier les conflits de créneaux
        for reservation in reservations_existantes:
            # Heure de fin de la réservation existante
            fin_existante = reservation.heure_fin
            if not fin_existante:
                # Calculer si pas encore définie
                debut_existant = datetime.combine(date, reservation.heure)
                fin_existant = debut_existant + timedelta(hours=1, minutes=30)
                fin_existante = fin_existant.time()

            # Vérifier le chevauchement
            # Conflit si : (début_nouveau < fin_existante) ET (fin_nouvelle > début_existant)
            # PERMETTRE si début_nouveau >= fin_existante OU fin_nouvelle <= début_existant
            if (heure_debut < fin_existante) and (heure_fin > reservation.heure):
                return False

        return True

    def get_creneau_display(self):
        """Retourne l'affichage du créneau horaire"""
        if self.heure_fin:
            return f"{self.heure.strftime('%H:%M')} - {self.heure_fin.strftime('%H:%M')}"
        else:
            return f"{self.heure.strftime('%H:%M')} - (1h30)"
