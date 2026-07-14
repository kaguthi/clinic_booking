from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Doctor, Patient, Appointment
from .serializers import DoctorSerializer, PatientSerializer, AppointmentSerializer
from .utils import generate_available_slots

class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class DoctorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    lookup_field = 'doctor_id'

class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class PatientRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'patient_id'

class AppointmentListCreateView(generics.ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

class AppointmentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    lookup_field = 'appointment_id'

class DoctorAvailabilityView(APIView):
    def get(self, request, doctor_id, format=None):
        doctor = get_object_or_404(Doctor, doctor_id=doctor_id)
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({"error": "Date parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST)

        slots = generate_available_slots(doctor, date)
        # Serialize the slots to ensure datetime objects are properly formatted
        serialized_slots = []
        for slot in slots:
            serialized_slots.append({
                "slot_id": slot["slot_id"],
                "doctor_id": slot["doctor_id"],
                "start_time": slot["start_time"].isoformat(),
                "end_time": slot["end_time"].isoformat(),
                "is_booked": slot["is_booked"]
            })
        return Response(serialized_slots, status=status.HTTP_200_OK)

class CancelAppointmentView(APIView):
    def patch(self, request, appointment_id, format=None):
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

        if appointment.status == 'cancelled':
            return Response({"message": "Appointment is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        cancellation_reason = request.data.get('cancellation_reason', 'No reason provided.')

        appointment.status = 'cancelled'
        appointment.cancellation_reason = cancellation_reason
        appointment.save()
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RescheduleAppointmentView(APIView):
    def patch(self, request, appointment_id, format=None):
        original_appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

        if original_appointment.status == 'cancelled':
            return Response({"error": "Cannot reschedule a cancelled appointment."}, status=status.HTTP_400_BAD_REQUEST)

        new_start_time_str = request.data.get('start_time')
        new_doctor_id = request.data.get('doctor_id', str(original_appointment.doctor.doctor_id))

        if not new_start_time_str:
            return Response({"error": "New start_time is required for rescheduling."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_start_time = timezone.make_aware(datetime.fromisoformat(new_start_time_str))
        except ValueError:
            return Response({"error": "Invalid start_time format. Use ISO 8601."},
                            status=status.HTTP_400_BAD_REQUEST)

        new_doctor = get_object_or_404(Doctor, doctor_id=new_doctor_id)

        # Validate the new slot using the serializer
        # We need to create a temporary serializer instance for validation
        temp_appointment_data = {
            'doctor': new_doctor.doctor_id,
            'patient': original_appointment.patient.patient_id,
            'start_time': new_start_time.isoformat(),
        }
        temp_serializer = AppointmentSerializer(data=temp_appointment_data, context={'request': request, 'original_appointment': original_appointment})

        if temp_serializer.is_valid():
            # Mark the original appointment as rescheduled
            original_appointment.status = 'rescheduled'
            original_appointment.save()

            # Create a new appointment with the rescheduled details
            rescheduled_appointment = Appointment.objects.create(
                doctor=new_doctor,
                patient=original_appointment.patient,
                start_time=new_start_time,
                end_time=new_start_time + timedelta(minutes=30),
                rescheduled_from=original_appointment,
                status='booked'
            )
            return Response(AppointmentSerializer(rescheduled_appointment).data, status=status.HTTP_201_CREATED)
        return Response(temp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        patient = get_object_or_404(Patient, patient_id=patient_id)
        # Return upcoming appointments sorted by date
        return Appointment.objects.filter(
            patient=patient,
            start_time__gte=timezone.now(),
            status__in=['booked', 'completed']
        ).order_by('start_time')
