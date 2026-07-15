from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime, timedelta
from django.utils import timezone
import json

from .models import Doctor, Patient, Appointment

class AppointmentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.doctor1 = Doctor.objects.create(name="Dr. Smith", specialty="Cardiology", working_hours={
            "Monday": {"start": "09:00", "end": "17:00"},
            "Tuesday": {"start": "09:00", "end": "17:00"},
            "Wednesday": {"start": "09:00", "end": "17:00"},
            "Thursday": {"start": "09:00", "end": "17:00"},
            "Friday": {"start": "09:00", "end": "17:00"},
        })
        self.patient1 = Patient.objects.create(name="John Doe", email="john.doe@example.com")
        self.patient2 = Patient.objects.create(name="Jane Doe", email="jane.doe@example.com")

    def test_create_doctor(self):
        url = reverse("doctor-list-create")
        data = {"name": "Dr. Jones", "specialty": "Pediatrics", "working_hours": {"Monday": {"start": "08:00", "end": "16:00"}}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Doctor.objects.count(), 2)
        self.assertEqual(Doctor.objects.get(name="Dr. Jones").specialty, "Pediatrics")

    def test_get_doctor_availability(self):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
 
        while tomorrow.strftime("%A") not in self.doctor1.working_hours:
            tomorrow += timedelta(days=1)

        appointment_time = timezone.make_aware(datetime.combine(tomorrow, datetime.strptime("10:00", "%H:%M").time()))
        Appointment.objects.create(
            doctor=self.doctor1,
            patient=self.patient1,
            start_time=appointment_time,
            end_time=appointment_time + timedelta(minutes=30)
        )

        url = reverse("doctor-availability", kwargs={"doctor_id": self.doctor1.doctor_id})
        response = self.client.get(url, {"date": tomorrow.strftime("%Y-%m-%d")}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        booked_slot_found = False
        for slot in response.data:
            slot_start_time = datetime.fromisoformat(slot["start_time"])
            if slot_start_time == appointment_time and slot["is_booked"]:
                booked_slot_found = True
                break
        self.assertTrue(booked_slot_found)

    def test_book_appointment(self):
        today = timezone.now().date()
        future_date = today + timedelta(days=7)

        while future_date.strftime("%A") not in self.doctor1.working_hours:
            future_date += timedelta(days=1)

        book_time = timezone.make_aware(datetime.combine(future_date, datetime.strptime("11:00", "%H:%M").time()))
        url = reverse("appointment-list-create")
        data = {
            "doctor": str(self.doctor1.doctor_id),
            "patient": str(self.patient1.patient_id),
            "start_time": book_time.isoformat()
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(Appointment.objects.first().status, "booked")

    def test_book_overlapping_appointment(self):
        today = timezone.now().date()
        future_date = today + timedelta(days=7)
        while future_date.strftime("%A") not in self.doctor1.working_hours:
            future_date += timedelta(days=1)

        book_time = timezone.make_aware(datetime.combine(future_date, datetime.strptime("12:00", "%H:%M").time()))
        Appointment.objects.create(
            doctor=self.doctor1,
            patient=self.patient1,
            start_time=book_time,
            end_time=book_time + timedelta(minutes=30)
        )

        url = reverse("appointment-list-create")
        data = {
            "doctor": str(self.doctor1.doctor_id),
            "patient": str(self.patient2.patient_id),
            "start_time": book_time.isoformat()
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This doctor already has an appointment scheduled at this time.", json.dumps(response.data))

    def test_cancel_appointment(self):
        today = timezone.now().date()
        future_date = today + timedelta(days=7)
        while future_date.strftime("%A") not in self.doctor1.working_hours:
            future_date += timedelta(days=1)

        book_time = timezone.make_aware(datetime.combine(future_date, datetime.strptime("13:00", "%H:%M").time()))
        appointment = Appointment.objects.create(
            doctor=self.doctor1,
            patient=self.patient1,
            start_time=book_time,
            end_time=book_time + timedelta(minutes=30)
        )

        url = reverse("appointment-cancel", kwargs={"appointment_id": appointment.appointment_id})
        response = self.client.patch(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "cancelled")

    def test_get_patient_appointments(self):
        today = timezone.now().date()
        future_date1 = today + timedelta(days=7)
        future_date2 = today + timedelta(days=8)

        # Ensure future_date1 and future_date2 are working days
        while future_date1.strftime("%A") not in self.doctor1.working_hours:
            future_date1 += timedelta(days=1)
        while future_date2.strftime("%A") not in self.doctor1.working_hours:
            future_date2 += timedelta(days=1)

        book_time1 = timezone.make_aware(datetime.combine(future_date1, datetime.strptime("09:00", "%H:%M").time()))
        book_time2 = timezone.make_aware(datetime.combine(future_date2, datetime.strptime("10:00", "%H:%M").time()))

        Appointment.objects.create(
            doctor=self.doctor1,
            patient=self.patient1,
            start_time=book_time1,
            end_time=book_time1 + timedelta(minutes=30)
        )
        Appointment.objects.create(
            doctor=self.doctor1,
            patient=self.patient1,
            start_time=book_time2,
            end_time=book_time2 + timedelta(minutes=30)
        )

        url = reverse("appointment-list-create")
        response = self.client.get(url, {"patient": str(self.patient1.patient_id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
