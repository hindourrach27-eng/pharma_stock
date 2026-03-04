


from django import forms

from .models import Medicament, Commande

from django.core.exceptions import ValidationError

from django.contrib import admin, messages


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix", "stock", "disponible", "date_ajout")
    search_fields = ("nom",)
    list_filter = ("date_ajout",)


class CommandeAdminForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        statut = cleaned.get("statut")
        medicament = cleaned.get("medicament")
        quantite = cleaned.get("quantite")

        if statut == "acceptee" and medicament and quantite:
            if medicament.stock < quantite:
                self.add_error("quantite", "Stock insuffisant pour accepter cette commande.")

        return cleaned

@admin.action(description=" Accepter les commandes sélectionnées")
def accepter_commandes(modeladmin, request, queryset):
    ok = 0
    fail = 0

    for cmd in queryset:
        try:
            cmd.statut = "acceptee"
            cmd.save()
            ok += 1
        except ValidationError as e:
            fail += 1

    if ok:
        modeladmin.message_user(request, f"{ok} commande(s) acceptée(s).", messages.SUCCESS)
    if fail:
        modeladmin.message_user(request, f"{fail} commande(s) refusée(s) : stock insuffisant.", messages.ERROR)


@admin.action(description=" Refuser les commandes sélectionnées")
def refuser_commandes(modeladmin, request, queryset):
    queryset.update(statut="refusee")

@admin.action(description=" Supprimer les commandes sélectionnées")
def supprimer_commandes(modeladmin, request, queryset):
    nb = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f"{nb} commande(s) supprimée(s).", messages.SUCCESS)


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
    "utilisateur", "medicament", "quantite",
    "statut", "statut_livraison",
    "date_commande", "date_acceptation", "date_livraison"
   )
    list_filter = ("statut", "date_commande")
    search_fields = ("utilisateur__username", "medicament__nom")
    readonly_fields = ("date_acceptation", "date_livraison")


    actions = ["accepter_commandes", "refuser_commandes", "livrer_commandes"]

    @admin.action(description=" Accepter les commandes sélectionnées")
    def accepter_commandes(self, request, queryset):
        for cmd in queryset:
            try:
                cmd.statut = "acceptee"
                cmd.save()  # déclenche la logique stock + dates
            except ValidationError as e:
                messages.error(request, f"Commande #{cmd.id} : {e}")
        self.message_user(request, "Traitement terminé.", level=messages.INFO)

    @admin.action(description=" Refuser les commandes sélectionnées")
    def refuser_commandes(self, request, queryset):
        queryset.update(statut="refusee")
        self.message_user(request, "Commandes refusées.", level=messages.SUCCESS)
    


    @admin.action(description=" Marquer comme livrée (commandes acceptées uniquement)")
    def livrer_commandes(self, request, queryset):
        for cmd in queryset:
            try:
                cmd.statut = "delivree"
                cmd.save()
            except ValidationError as e:
                messages.error(request, f"Commande #{cmd.id} : {e}")
        self.message_user(request, "Traitement terminé.", level=messages.INFO)



from .models import Profile
admin.site.register(Profile)