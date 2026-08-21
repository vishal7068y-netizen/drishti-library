from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.student_create, name="student_create"),
    path("students/<int:pk>/edit/", views.student_update, name="student_update"),
    path("students/<int:pk>/leave/", views.student_leave, name="student_leave"),
    path("seats/", views.seat_list, name="seat_list"),
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/add/<int:student_id>/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/edit/", views.payment_update, name="payment_update"),
    path("reports/", views.reports, name="reports"),
   
]
