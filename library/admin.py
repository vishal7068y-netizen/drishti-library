from django.contrib import admin

from .models import Payment, Seat, Student


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("number", "location", "is_available")
    list_filter = ("location",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "seat", "plan", "payment_status", "expiry_date", "is_active")
    list_filter = ("plan", "payment_status", "is_active")
    search_fields = ("student_id", "name", "mobile")
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "amount", "payment_method", "status", "payment_date", "due_date")
    list_filter = ("status", "payment_method")
    search_fields = ("student__name", "student__student_id")
