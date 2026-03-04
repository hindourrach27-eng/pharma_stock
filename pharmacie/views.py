from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import SignupForm, CommandeForm
from .models import Medicament, Commande


from django.utils import timezone
from django.shortcuts import render

def landing(request):
    return render(request, "pharmacie/landing.html", {"now": timezone.now().year})



@login_required
def home(request):
    medicaments = Medicament.objects.all().order_by("-date_ajout")
    return render(request, "pharmacie/home.html", {"medicaments": medicaments})


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("pharmacie:home")
    else:
        form = SignupForm()
    return render(request, "pharmacie/signup.html", {"form": form})

def login_view(request):
    error = None
    next_url = request.GET.get("next") or "pharmacie:home"

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url)

        error = "Identifiants invalides."

    return render(request, "pharmacie/login.html", {"error": error})




def logout_view(request):
    logout(request)
    return redirect("pharmacie:login")



@login_required
def commander(request, medicament_id):
    medicament = get_object_or_404(Medicament, id=medicament_id)

    if request.method == "POST":
        form = CommandeForm(request.POST, medicament=medicament)
        if form.is_valid():
            cmd = form.save(commit=False)
            cmd.utilisateur = request.user
            cmd.medicament = medicament
            cmd.statut = "en_attente"
            cmd.save()
            return redirect("pharmacie:home")
    else:
        form = CommandeForm(medicament=medicament)

    return render(request, "pharmacie/commander.html", {"form": form, "medicament": medicament})

@login_required
def mes_commandes(request):
    commandes = Commande.objects.filter(utilisateur=request.user).order_by("-date_commande")
    return render(request, "pharmacie/mes_commandes.html", {"commandes": commandes})