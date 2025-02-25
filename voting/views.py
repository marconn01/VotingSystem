import sqlite3
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
import hashlib
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import random
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DB_PATH = "db.sqlite3"


def get_db_connection():
    return sqlite3.connect(DB_PATH)



def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit OTP

# Function to send OTP via email
def send_otp(email, otp):
    sender_email = "ramramvoting@gmail.com"  # Replace with your email
    sender_password = "wddw hxbn icou zrmt"  # Replace with your email password
    subject = "Your OTP for Voter Login"
    body = f"Your One-Time Password (OTP) for Thapathali Campus FSU Election Voting is: {otp}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

# Step 1: Generate and send OTP
def voter_login(request):
    if request.method == "POST":
        email = request.POST["email"]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Voters WHERE email = ?", (email,))
        voter = cursor.fetchone()
        conn.close()
        
        if voter:
            otp = generate_otp()
            request.session["otp"] = otp
            request.session["voter_email"] = email

            if send_otp(email, otp):
                return redirect("verify_otp")  # Redirect to OTP verification page
            else:
                return HttpResponse("Error sending OTP! Please try again.")
        else:
            return HttpResponse("Voter not found!")

    return render(request, "voter_login.html")

# Step 2: Verify OTP
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST["otp"]
        stored_otp = request.session.get("otp")
        email = request.session.get("voter_email")

        if entered_otp == stored_otp:
            # Fetch voter details
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Voters WHERE email = ?", (email,))
            voter = cursor.fetchone()
            conn.close()

            if voter:
                request.session["voter_id"] = voter[0]
                request.session["voter_name"] = voter[1]
                return redirect("select_election")  # Redirect to voting page
            else:
                return HttpResponse("Voter not found after OTP verification!")

        return HttpResponse("Invalid OTP! Please try again.")

    return render(request, "verify_otp.html")

def voter_logout(request):
    """Logout admin"""
    request.session.flush()
    return redirect("voter_login")

def select_election(request):
    """Allow voter to choose an election"""
    if "voter_id" not in request.session:
        return redirect("voter_login")  # Ensure voter is logged in

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Elections WHERE status = 'Ongoing'")
    elections = cursor.fetchall()
    conn.close()

    voter_details = {
        "voter_name": request.session.get("voter_name"),
        "voter_email": request.session.get("voter_email"),
    }

    return render(request, "select_election.html", {
        "elections": elections,
        "voter_details": voter_details
    })

def store_election(request):
    """Stores selected election in session and redirects to candidate selection"""
    if request.method == "POST":
        election_id = request.POST.get("election_id")
        request.session["selected_election"] = election_id

        return redirect("select_candidates")  # Redirect to candidate selection
    return redirect("select_election")

def select_candidates(request):
    """Displays candidates based on the selected election and enforces selection limits"""
    if "voter_id" not in request.session:
        return redirect("voter_login")

    if "selected_election" not in request.session:
        return redirect("select_election")

    election_id = request.session["selected_election"]

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch positions and their seat limits for the selected election
    cursor.execute("""
        SELECT Positions.position_id, Positions.position_name, Positions.allocated_seats
        FROM Positions
        JOIN Candidates ON Positions.position_id = Candidates.position_id
        WHERE Candidates.election_id = ?
        GROUP BY Positions.position_id
    """, (election_id,))
    
    positions = cursor.fetchall()

    # Fetch candidates for this election
    cursor.execute("""
        SELECT Candidates.candidate_id, Candidates.name, Positions.position_id, Positions.position_name, PoliticalParties.party_name
        FROM Candidates
        JOIN Positions ON Candidates.position_id = Positions.position_id
        JOIN PoliticalParties ON Candidates.party_id = PoliticalParties.party_id
        WHERE Candidates.election_id = ?
    """, (election_id,))
    
    candidates = cursor.fetchall()
    conn.close()

    voter_details = {
        "voter_name": request.session.get("voter_name"),
        "voter_email": request.session.get("voter_email"),
    }

    return render(request, "select_candidates.html", {
        "positions": positions,
        "candidates": candidates,
        "voter_details": voter_details
    })

def generate_blockchain_hash(voter_id, candidate_id, election_id, previous_hash=""):
    """Generate a blockchain hash for each vote"""
    vote_data = {
        "voter_id": voter_id,
        "candidate_id": candidate_id,
        "election_id": election_id,
        "previous_hash": previous_hash,
    }
    vote_string = json.dumps(vote_data, sort_keys=True)
    return hashlib.sha256(vote_string.encode()).hexdigest()

def get_previous_vote_hash(cursor, election_id):
    """Retrieve the last vote hash for a given election"""
    cursor.execute(
        "SELECT blockchain_hash FROM Votes WHERE election_id = ? ORDER BY vote_id DESC LIMIT 1",
        (election_id,),
    )
    last_vote = cursor.fetchone()
    return last_vote[0] if last_vote else ""

def submit_vote(request):
    """Handles vote submission with blockchain hashing"""
    if request.method == "POST":
        voter_id = request.session.get("voter_id")
        election_id = request.session.get("selected_election")
        selected_candidates = request.POST.getlist("candidate")

        if not voter_id or not election_id:
            return redirect("voter_login")

        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()

        # Check if the voter has already voted in this specific election
        cursor.execute(
            "SELECT COUNT(*) FROM Votes WHERE voter_id = ? AND election_id = ?",
            (voter_id, election_id),
        )
        has_voted = cursor.fetchone()[0] > 0

        if has_voted:
            conn.close()
            return redirect("already_voted_page")

        # Retrieve previous blockchain hash
        previous_hash = get_previous_vote_hash(cursor, election_id)

        # Store votes with blockchain hashing
        for candidate_id in selected_candidates:
            blockchain_hash = generate_blockchain_hash(voter_id, candidate_id, election_id, previous_hash)
            cursor.execute(
                """
                INSERT INTO Votes (voter_id, candidate_id, election_id, blockchain_hash)
                VALUES (?, ?, ?, ?)
                """,
                (voter_id, candidate_id, election_id, blockchain_hash),
            )
            previous_hash = blockchain_hash  # Update the previous hash for the next vote

        # Commit transaction and close connection
        conn.commit()
        conn.close()

        return redirect("vote_success")

    return redirect("select_candidates")


def already_voted_page(request):
    """Show a message that the voter has already voted."""
    return render(request, "already_voted.html", {"message": "You have already voted!"})

def election_list(request):
    """Show list of Scheduled, Ongoing, and Completed Elections"""
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute("SELECT election_id, name, status FROM Elections")
    elections = cursor.fetchall()  # List of (election_id, name, status)

    conn.close()

    # Group elections by status
    scheduled = [e for e in elections if e[2] == "Scheduled"]
    ongoing = [e for e in elections if e[2] == "Ongoing"]
    completed = [e for e in elections if e[2] == "Completed"]

    return render(request, "election_list.html", {
        "scheduled": scheduled,
        "ongoing": ongoing,
        "completed": completed
    })

def election_results(request, election_id):
    """Show results of a specific election with allocated seats and winners highlighted."""
    election_id = int(election_id)  # Ensure it's an integer

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Fetch election details
    cursor.execute("SELECT name, status FROM Elections WHERE election_id = ?", (election_id,))
    election = cursor.fetchone()

    if not election:
        return render(request, "error.html", {"message": "Election not found!"})

    election_name, status = election

    # Fetch positions, allocated seats, candidates, and vote counts
    cursor.execute("""
        SELECT p.position_name, p.allocated_seats, c.name, COUNT(v.candidate_id) as vote_count
        FROM Positions p
        JOIN Candidates c ON p.position_id = c.position_id
        LEFT JOIN Votes v ON c.candidate_id = v.candidate_id
        WHERE c.election_id = ?
        GROUP BY p.position_name, p.allocated_seats, c.candidate_id
        ORDER BY p.position_name, vote_count DESC
    """, (election_id,))

    results = cursor.fetchall()
    conn.close()

    # Group candidates by position and track allocated seats
    position_results = {}
    for position_name, allocated_seats, candidate_name, vote_count in results:
        if position_name not in position_results:
            position_results[position_name] = {
                "allocated_seats": allocated_seats,
                "candidates": []
            }
        position_results[position_name]["candidates"].append((candidate_name, vote_count))

    return render(request, "election_results.html", {
        "election_id": election_id, 
        "election_name": election_name,
        "status": status,
        "position_results": position_results
    })

def export_results_pdf(request, election_id):
    """Generate a PDF of election results."""
    election_id = int(election_id)

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Fetch election details
    cursor.execute("SELECT name, status FROM Elections WHERE election_id = ?", (election_id,))
    election = cursor.fetchone()
    
    if not election:
        return HttpResponse("Election not found!", status=404)
    
    election_name, status = election

    # Fetch results with allocated seats
    cursor.execute("""
        SELECT p.position_name, p.allocated_seats, c.name, COUNT(v.candidate_id) as vote_count
        FROM Positions p
        JOIN Candidates c ON p.position_id = c.position_id
        LEFT JOIN Votes v ON c.candidate_id = v.candidate_id
        WHERE c.election_id = ?
        GROUP BY p.position_name, p.allocated_seats, c.candidate_id
        ORDER BY p.position_name, vote_count DESC
    """, (election_id,))

    results = cursor.fetchall()
    conn.close()

    # Organize data by position
    position_results = {}
    for position_name, allocated_seats, candidate_name, vote_count in results:
        if position_name not in position_results:
            position_results[position_name] = {
                "allocated_seats": allocated_seats,
                "candidates": []
            }
        position_results[position_name]["candidates"].append((candidate_name, vote_count))

    # Create the HTTP Response with PDF headers
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{election_name}_results.pdf"'

    # Create the PDF
    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle(f"{election_name} Results")
    width, height = letter
    y_position = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, y_position, f"Election Results: {election_name}")
    y_position -= 20
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y_position, f"Status: {status}")
    y_position -= 30

    pdf.setFont("Helvetica-Bold", 14)

    for position_name, position_data in position_results.items():
        pdf.drawString(50, y_position, f"{position_name} (Seats: {position_data['allocated_seats']})")
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(70, y_position, "Candidate Name")
        pdf.drawString(300, y_position, "Votes Received")
        y_position -= 15

        pdf.setFont("Helvetica", 12)
        # Loop through the candidates for each position
        for index, (candidate_name, vote_count) in enumerate(position_data["candidates"]):
            # Check if the candidate is a winner (top `allocated_seats` candidates)
            if index < position_data["allocated_seats"]:  # Highlight winners
                pdf.setFillColorRGB(0, 0.5, 0)  # Green color
                pdf.setFont("Helvetica-Bold", 12)
            else:
                pdf.setFillColorRGB(0, 0, 0)  # Black color
                pdf.setFont("Helvetica", 12)

            pdf.drawString(70, y_position, candidate_name)
            pdf.drawString(300, y_position, str(vote_count))
            y_position -= 15

        y_position -= 20  # Space between positions

        if y_position < 50:  # Check for page overflow
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y_position = height - 50

    pdf.save()
    return response


def home(request):
    """Render the homepage with login options and election results link."""
    return render(request, "home.html")

def vote_success(request):
    return render(request, "vote_success.html")  # Create this HTML file

def demo_select_election(request):
    """Allow user to choose an election for demo voting"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Elections WHERE status IN ('Ongoing', 'Scheduled')")
    elections = cursor.fetchall()
    conn.close()

    voter_details = {
        "voter_name": request.session.get("voter_name"),
        "voter_email": request.session.get("voter_email"),
    }

    return render(request, "demo_select_election.html", {"elections": elections, "voter_details": voter_details})

def demo_select_candidates(request):
    """Displays candidates based on the selected election for demo voting"""
    election_id = request.GET.get("election_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch positions and their seat limits for the selected election
    cursor.execute("""
        SELECT Positions.position_id, Positions.position_name, Positions.allocated_seats
        FROM Positions
        JOIN Candidates ON Positions.position_id = Candidates.position_id
        WHERE Candidates.election_id = ?
        GROUP BY Positions.position_id
    """, (election_id,))
    
    positions = cursor.fetchall()

    # Fetch candidates for this election
    cursor.execute("""
        SELECT Candidates.candidate_id, Candidates.name, Positions.position_id, Positions.position_name, PoliticalParties.party_name
        FROM Candidates
        JOIN Positions ON Candidates.position_id = Positions.position_id
        JOIN PoliticalParties ON Candidates.party_id = PoliticalParties.party_id
        WHERE Candidates.election_id = ?
    """, (election_id,))
    
    candidates = cursor.fetchall()
    conn.close()

    voter_details = {
        "voter_name": request.session.get("voter_name"),
        "voter_email": request.session.get("voter_email"),
    }

    return render(request, "demo_select_candidates.html", {
        "positions": positions,
        "candidates": candidates,
        "election_id": election_id,
        "voter_details": voter_details
    })

def demo_submit_vote(request):
    """Handles demo vote submission without recording the vote"""
    if request.method == "POST":
        selected_candidates = request.POST.getlist("candidate")
        return render(request, "demo_vote_success.html", {"selected_candidates": selected_candidates})

    return redirect("demo_select_election")
