from django.shortcuts import render
from .db_utils import fetch_all_voters, fetch_elections

def admin_dashboard(request):
    """Admin dashboard to view elections and voters."""
    elections = fetch_elections()
    voters = fetch_all_voters()
    return render(request, "admin_dashboard.html", {"elections": elections, "voters": voters})
