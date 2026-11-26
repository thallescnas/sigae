from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("api/state/", views.api_state, name="api_state"),
    path("api/validate/", views.api_validate, name="api_validate"),

    path("api/patients/", views.api_register_patient,
         name="api_register_patient"),
    path("api/patients/<int:patient_id>/",
         views.api_search_patient, name="api_search_patient"),
    path("api/patients/search-arrival/",
         views.api_search_by_arrival, name="api_search_by_arrival"),
    path("api/patients/<int:patient_id>/priority/",
         views.api_reclassify_patient, name="api_reclassify_patient"),
    path("api/patients/<int:patient_id>/cancel/",
         views.api_cancel_waiting_patient, name="api_cancel_waiting_patient"),

    path("api/doctors/", views.api_register_doctor, name="api_register_doctor"),
    path("api/doctors/<int:doctor_id>/",
         views.api_search_doctor, name="api_search_doctor"),

    path("api/attendances/call/", views.api_call_next, name="api_call_next"),
    path("api/attendances/<int:attendance_id>/finish/",
         views.api_finish_attendance, name="api_finish_attendance"),
    path("api/attendances/<int:attendance_id>/cancel/",
         views.api_cancel_attendance, name="api_cancel_attendance"),
]
