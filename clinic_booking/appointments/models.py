from django.db import models
import uuid
from django.utils import timezone

class Doctor(models.Model):
    doctor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    specialty = models.CharField(max_length=255, blank=True, null=True)
    working_hours = models.JSONField(default=dict) # Stores daily working hours

    def __str__(self):
        return self.name

class Patient(models.Model):
    patient_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("rescheduled", "Rescheduled"),
    ]

    appointment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default="booked")
    cancellation_reason = models.TextField(blank=True, null=True)
    rescheduled_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_to')
    created_at = models.DateTimeField(default=timezone.now)



def __str__(self):
    formatted_time = self.start_time.strftime("%Y-%m-%d %H:%M")
    return f"Appointment with {self.doctor.name} for {self.patient.name} on {formatted_time}"