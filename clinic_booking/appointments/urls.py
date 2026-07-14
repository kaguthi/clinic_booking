from django.urls import path
from .views import (
    DoctorListCreateView,
    DoctorRetrieveUpdateDestroyView,
    PatientListCreateView,
    PatientRetrieveUpdateDestroyView,
    AppointmentListCreateView,
    AppointmentRetrieveUpdateDestroyView,
    DoctorAvailabilityView,
    CancelAppointmentView,
    RescheduleAppointmentView,
    PatientAppointmentsView,
)

urlpatterns = [
    path("doctors/", DoctorListCreateView.as_view(), name="doctor-list-create"),
    path("doctors/<uuid:doctor_id>/", DoctorRetrieveUpdateDestroyView.as_view(), name="doctor-retrieve-update-destroy"),
    path("doctors/<uuid:doctor_id>/availability/", DoctorAvailabilityView.as_view(), name="doctor-availability"),
    path("patients/", PatientListCreateView.as_view(), name="patient-list-create"),
    path("patients/<uuid:patient_id>/", PatientRetrieveUpdateDestroyView.as_view(), name="patient-retrieve-update-destroy"),
    path("patients/<uuid:patient_id>/appointments/", PatientAppointmentsView.as_view(), name="patient-upcoming-appointments"),
    path("appointments/", AppointmentListCreateView.as_view(), name="appointment-list-create"),
    path("appointments/<uuid:appointment_id>/", AppointmentRetrieveUpdateDestroyView.as_view(), name="appointment-retrieve-update-destroy"),
    path("appointments/<uuid:appointment_id>/cancel/", CancelAppointmentView.as_view(), name="appointment-cancel"),
    path("appointments/<uuid:appointment_id>/reschedule/", RescheduleAppointmentView.as_view(), name="appointment-reschedule"),
]
