from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import (
    Utilisateur, Client, Table, Plat, Commande,
    LigneCommande, Reservation
)


class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['table', 'commentaire']
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 3}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['client', 'table', 'date', 'heure', 'nombre_personnes', 'commentaire']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure': forms.TimeInput(attrs={'type': 'time'}),
            'commentaire': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table'].queryset = Table.objects.filter(etat='libre')


class ReservationClientForm(forms.ModelForm):
    
    class Meta:
        model = Reservation
        fields = ['table', 'date', 'heure', 'nombre_personnes', 'commentaire']
        widgets = {
            'table': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.now().date().isoformat()
            }),
            'heure': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'nombre_personnes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Commentaires ou demandes spéciales (optionnel)'
            }),
        }
        labels = {
            'table': 'Table souhaitée',
            'date': 'Date de réservation',
            'heure': 'Heure de réservation',
            'nombre_personnes': 'Nombre de personnes',
            'commentaire': 'Commentaires'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table'].queryset = Table.objects.filter(etat='libre')
        self.fields['table'].empty_label = "Sélectionnez une table"

    def clean(self):
        cleaned_data = super().clean()
        table = cleaned_data.get('table')
        nombre_personnes = cleaned_data.get('nombre_personnes')
        date = cleaned_data.get('date')
        heure = cleaned_data.get('heure')

        if table and nombre_personnes:
            
            if table.capacite != nombre_personnes:
                raise forms.ValidationError(
                    f'La table {table.numero} a une capacité de {table.capacite} places, '
                    f'mais vous avez demandé {nombre_personnes} personne(s). '
                    f'Veuillez choisir une table avec exactement {nombre_personnes} place(s).'
                )

      
        if table and date and heure:
            from restaurant.models import Reservation
            if not Reservation.verifier_disponibilite_creneau(table, date, heure):
                from datetime import datetime, timedelta
                debut = datetime.combine(date, heure)
                fin = debut + timedelta(hours=1, minutes=30)
                raise forms.ValidationError(
                    f'❌ CRÉNEAU OCCUPÉ: La table {table.numero} est déjà réservée pour le créneau '
                    f'{heure.strftime("%H:%M")} - {fin.time().strftime("%H:%M")}. '
                    f'Veuillez choisir un autre horaire (les réservations durent 1h30).'
                )

        return cleaned_data


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'telephone', 'email']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ClientInscriptionForm(forms.ModelForm):
    """Formulaire d'inscription pour les clients"""
    confirmer_telephone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre numéro de téléphone'
        }),
        label='Confirmer le téléphone'
    )

    class Meta:
        model = Client
        fields = ['nom', 'telephone', 'email']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom complet'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 0661234567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'votre.email@exemple.ma'
            }),
        }
        labels = {
            'nom': 'Nom complet',
            'telephone': 'Numéro de téléphone',
            'email': 'Adresse email'
        }

    def clean(self):
        cleaned_data = super().clean()
        telephone = cleaned_data.get('telephone')
        confirmer_telephone = cleaned_data.get('confirmer_telephone')

        if telephone and confirmer_telephone:
            if telephone != confirmer_telephone:
                raise forms.ValidationError("Les numéros de téléphone ne correspondent pas.")

        
        if telephone and Client.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà enregistré.")

        return cleaned_data


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['numero', 'capacite', 'etat']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'capacite': forms.NumberInput(attrs={'class': 'form-control'}),
            'etat': forms.Select(attrs={'class': 'form-control'}),
        }


class PlatForm(forms.ModelForm):
    class Meta:
        model = Plat
        fields = ['nom', 'prix', 'categorie', 'description', 'disponible', 'image']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }





class UtilisateurForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'first_name', 'last_name', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
