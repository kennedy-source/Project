from django.contrib.auth import authenticate

user = authenticate(username='Admin', password='Finesse.koma123@')
print(user)  # Should return the User object if authentication is successful
