from datetime import timedelta

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Medicament(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

    @property
    def disponible(self):
        return self.stock > 0


class Commande(models.Model):
    # ✅ Statut de la commande (séparé de la livraison)
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("acceptee", "Acceptée"),
        ("refusee", "Refusée"),
    ]

    # ✅ Statut de livraison (séparé du statut commande)
    STATUT_LIVRAISON_CHOICES = [
        ("en_attente", "En attente"),
        ("livree", "Livrée"),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)

    quantite = models.PositiveIntegerField()
    date_commande = models.DateTimeField(auto_now_add=True)

    # ✅ infos ajoutées côté client
    adresse_livraison = models.TextField(blank=True)
    date_souhaitee = models.DateField(null=True, blank=True)

    # ✅ statuts
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente",
    )

    statut_livraison = models.CharField(
        max_length=20,
        choices=STATUT_LIVRAISON_CHOICES,
        default="en_attente",
    )

    # ✅ dates gérées automatiquement
    date_acceptation = models.DateTimeField(null=True, blank=True)
    date_livraison = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.utilisateur.username} - {self.medicament.nom}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            ancien_statut = None
            ancien_statut_livraison = None

            if self.pk:
                ancien = Commande.objects.get(pk=self.pk)
                ancien_statut = ancien.statut
                ancien_statut_livraison = ancien.statut_livraison

            # ✅ 1) Quand admin accepte (en_attente/refusee -> acceptee)
            if self.statut == "acceptee" and ancien_statut != "acceptee":
                # lock médicament pour éviter bugs si 2 admins acceptent en même temps
                med = Medicament.objects.select_for_update().get(pk=self.medicament_id)

                if med.stock < self.quantite:
                    raise ValidationError({"quantite": "Stock insuffisant"})

                med.stock -= self.quantite
                med.save()

                # date d'acceptation auto
                self.date_acceptation = timezone.now()

                # date de livraison auto = acceptation + 2 jours
                self.date_livraison = (self.date_acceptation + timedelta(days=2)).date()

            # ✅ 2) Si admin refuse -> pas de livraison
            if self.statut == "refusee":
                self.statut_livraison = "en_attente"

            # ✅ 3) Si on marque la livraison comme livrée
            if self.statut_livraison == "livree" and ancien_statut_livraison != "livree":
                # livrer seulement si acceptée
                if self.statut != "acceptee":
                    raise ValidationError("Impossible de livrer une commande non acceptée.")

                # si jamais date_acceptation vide (sécurité)
                if not self.date_acceptation:
                    self.date_acceptation = timezone.now()

                # si jamais date_livraison vide, on la calcule
                if not self.date_livraison:
                    self.date_livraison = (self.date_acceptation + timedelta(days=2)).date()

                # règle max 3 jours après acceptation
                limite = (self.date_acceptation + timedelta(days=3)).date()
                if timezone.localdate() > limite:
                    raise ValidationError("Délai dépassé : livraison > 3 jours après acceptation.")

            super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    adresse = models.TextField(blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"


@receiver(post_save, sender=User)
def creer_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, adresse="")