from django.urls import path
from . import views  # Import the views module

urlpatterns = [
    path("voter-login/", views.voter_login, name="voter_login"),
    path("select-election/", views.select_election, name="select_election"),
    path("store-election/", views.store_election, name="store_election"),
    path("select-candidates/", views.select_candidates, name="select_candidates"),
    path("submit-vote/", views.submit_vote, name="submit_vote"),
    path("already-voted/", views.already_voted_page, name="already_voted_page"),
    path("elections/", views.election_list, name="election_list"),
    path("election-results/<int:election_id>/", views.election_results, name="election_results"),
    path("", views.home, name="home"),
    path("vote-success/", views.vote_success, name="vote_success"),
    path("voter-logout/", views.voter_logout, name="voter_logout"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("election/<int:election_id>/export_pdf/", views.export_results_pdf, name="export_results_pdf"),
     path('demo_select_election/', views.demo_select_election, name='demo_select_election'),
    path('demo_select_candidates/', views.demo_select_candidates, name='demo_select_candidates'),
    path('demo_submit_vote/', views.demo_submit_vote, name='demo_submit_vote'),
]

