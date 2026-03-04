from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Commande

from django.utils import timezone
from datetime import timedelta



class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "ex: hind@gmail.com",
        }),
    )

    adresse = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Votre adresse (ex: Rue ..., Fès)",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "adresse", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Choisis un username",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bootstrap sur les champs password + username
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Choisis un username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Mot de passe",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirmer le mot de passe",
        })

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Récupérer l'adresse depuis le form
        adresse = self.cleaned_data.get("adresse")

        # Sauvegarder dans profile (il doit exister)
        user.profile.adresse = adresse
        user.profile.save()

        return user



class CommandeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.medicament = kwargs.pop("medicament", None)
        super().__init__(*args, **kwargs)

        self.fields["quantite"].widget.attrs.update({
            "class": "form-control",
            "min": 1,
            "placeholder": "Ex: 2"
        })

        self.fields["adresse_livraison"].widget.attrs.update({
            "class": "form-control",
            "rows": 2,
            "placeholder": "Adresse de livraison (ex: Hay ..., Fès)"
        })

        self.fields["date_souhaitee"].widget.attrs.update({
            "class": "form-control",
            "type": "date"
        })

    class Meta:
        model = Commande
        fields = ("quantite", "adresse_livraison", "date_souhaitee")

    def clean_quantite(self):
        qte = self.cleaned_data.get("quantite")

        if qte is None or qte <= 0:
            raise forms.ValidationError("La quantité doit être supérieure à 0.")

        if self.medicament and qte > self.medicament.stock:
            raise forms.ValidationError(f"Stock insuffisant (max : {self.medicament.stock}).")

        return qte

    date_souhaitee = forms.DateField(
    required=True,
    widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control"
    })
)