from django.contrib import admin
from .models import Uniform, Order, Payment, UserProfile

admin.site.register(Uniform)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(UserProfile)

