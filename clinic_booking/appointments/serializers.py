from rest_framework import serializers
from django.utils import timezone
from .models import Doctor, Patient, Appointment
from datetime import timedelta, datetime

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('appointment_id', 'created_at', 'end_time') # status, cancellation_reason, rescheduled_from can be updated

    def validate(self, data):
        start_time = data.get('start_time', getattr(self.instance, 'start_time', None))
        doctor = data.get('doctor', getattr(self.instance, 'doctor', None))

        if start_time is None or doctor is None:
            raise serializers.ValidationError("start_time and doctor are required.")

        # 1. Validate that it falls within the doctor's working hours
        day_of_week = start_time.strftime("%A")
        if day_of_week not in doctor.working_hours:
            raise serializers.ValidationError("Doctor does not work on this day.")

        working_start_str = doctor.working_hours[day_of_week]["start"]
        working_end_str = doctor.working_hours[day_of_week]["end"]

        working_start_time = datetime.strptime(working_start_str, "%H:%M").time()
        working_end_time = datetime.strptime(working_end_str, "%H:%M").time()

        proposed_start_time_only = start_time.time()
        proposed_end_time_only = (start_time + timedelta(minutes=30)).time()

        if not (working_start_time <= proposed_start_time_only and proposed_end_time_only <= working_end_time):
            raise serializers.ValidationError("Appointment is outside doctor's working hours.")

        # Calculate end_time based on start_time + 30 minutes
        data['end_time'] = start_time + timedelta(minutes=30)
        proposed_end = data['end_time']

        # 2. Validate that it is not in the past
        if start_time < timezone.now():
            raise serializers.ValidationError("Cannot book an appointment in the past.")

        # 3. Prevention of bookings within 1 hour of now
        if start_time < timezone.now() + timedelta(hours=1):
            raise serializers.ValidationError("Appointments must be booked at least 1 hour in advance.")

        # 4. Validate that it is not already taken (overlapping appointments)
        instance = self.instance
        original_appointment = self.context.get("original_appointment")

        overlapping_appointments_query = Appointment.objects.filter(
            doctor=doctor,
            start_time__lt=proposed_end,
            end_time__gt=start_time,
            status__in=["booked", "completed"]
        )

        if instance:
            # If updating, exclude the current appointment from overlap check
            overlapping_appointments_query = overlapping_appointments_query.exclude(pk=instance.pk)
        
        if original_appointment:
            # If rescheduling, exclude the original appointment from overlap check
            overlapping_appointments_query = overlapping_appointments_query.exclude(pk=original_appointment.pk)

        if overlapping_appointments_query.exists():
            raise serializers.ValidationError("This doctor already has an appointment scheduled at this time.")

        return data
