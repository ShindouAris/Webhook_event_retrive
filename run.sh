clear

read "Booting up the client..."

# INSTALL gunicorn

pip install gunicorn

# Run the client...

gunicorn --bind 0.0.0.0:80 wsgi:app
