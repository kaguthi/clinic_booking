from django.contrib import admin
from .models import Appointment, Doctor, Patient

admin.site.register(Appointment)
admin.site.register(Doctor)
admin.site.register(Patient)
