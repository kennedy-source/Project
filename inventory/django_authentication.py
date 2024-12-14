import os
from django.conf import settings
from django.contrib.auth import authenticate

# Point to your Django project's settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

# If not run within Django's environment, initialize the settings
if not settings.configured:
    import django

    django.setup()

# Authenticate the user
user = authenticate(username='Admin', password='Finesse.koma123@')
print(user)  # Should return the User object if authentication is successful