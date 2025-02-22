python manage.py collectstatic --noinput

# Run Django database migrations (if you use Django migrations at all)
# If you’re not using Django migrations, you can skip this step
python manage.py migrate --noinput

# Start the Gunicorn server to serve the app
gunicorn Voting_System.wsgi:application --bind 0.0.0.0:$PORT