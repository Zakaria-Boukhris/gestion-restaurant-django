from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Utilisateur, Client, Table, Plat, Commande,
    LigneCommande, Reservation
)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Administration des utilisateurs"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Restaurant', {'fields': ('role',)}),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Administration des clients"""
    list_display = ['nom', 'telephone', 'email', 'date_creation']
    search_fields = ['nom', 'telephone', 'email']
    list_filter = ['date_creation']
    ordering = ['nom']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """Administration des tables"""
    list_display = ['numero', 'capacite', 'etat', 'statut_couleur']
    list_filter = ['etat', 'capacite']
    list_editable = ['etat']
    ordering = ['numero']
    
    def statut_couleur(self, obj):
        colors = {
            'libre': 'green',
            'occupee': 'red',
            'reservee': 'orange'
        }
        return format_html(
            '<span style="color: {};">●</span>',
            colors.get(obj.etat, 'black')
        )
    statut_couleur.short_description = 'Statut'


@admin.register(Plat)
class PlatAdmin(admin.ModelAdmin):
    """Administration des plats"""
    list_display = ['nom', 'categorie', 'prix_dh', 'disponible', 'image_preview']
    list_filter = ['categorie', 'disponible']
    list_editable = ['disponible']
    search_fields = ['nom', 'description']
    ordering = ['categorie', 'nom']

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'categorie', 'prix', 'disponible')
        }),
        ('Description et image', {
            'fields': ('description', 'image'),
            'classes': ('collapse',)
        }),
    )

    def prix_dh(self, obj):
        return f"{obj.prix} DH"
    prix_dh.short_description = 'Prix'
    prix_dh.admin_order_field = 'prix'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 5px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">Pas d\'image</span>')
    image_preview.short_description = 'Aperçu'


class LigneCommandeInline(admin.TabularInline):
    """Inline pour les lignes de commande"""
    model = LigneCommande
    extra = 1
    readonly_fields = ['sous_total']
    
    def sous_total(self, obj):
        if obj.id:
            return f"{obj.sous_total} DH"
        return "-"
    sous_total.short_description = 'Sous-total'


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    """Administration des commandes"""
    list_display = ['id', 'table', 'utilisateur', 'date', 'statut', 'total_commande']
    list_filter = ['statut', 'date', 'utilisateur']
    list_editable = ['statut']
    readonly_fields = ['date', 'total_commande']
    inlines = [LigneCommandeInline]
    ordering = ['-date']
    
    def total_commande(self, obj):
        return f"{obj.total} DH"
    total_commande.short_description = 'Total'





@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Administration des réservations"""
    list_display = ['client', 'table', 'date', 'heure', 'nombre_personnes', 'confirmee', 'statut_confirmation']
    list_filter = ['confirmee', 'date', 'table']
    list_editable = ['confirmee']
    search_fields = ['client__nom', 'client__telephone']
    ordering = ['date', 'heure']
    
    def statut_confirmation(self, obj):
        if obj.confirmee:
            return format_html('<span style="color: green;">✅ Confirmée</span>')
        return format_html('<span style="color: orange;">⏳ En attente</span>')
    statut_confirmation.short_description = 'Confirmation'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'table')


# Configuration de l'interface d'administration
admin.site.site_header = "Administration - Gestion Restaurant"
admin.site.site_title = "Gestion Restaurant"
admin.site.index_title = "Tableau de bord"
