from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Seat(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    location = models.CharField(max_length=100, default="Main Reading Hall")

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Seat {self.number}"

    @property
    def is_available(self):
        return not self.students.filter(is_active=True).exists()


class Student(models.Model):
    class Plan(models.TextChoices):
        FULL_DAY = "full_day", "Full Day — ₹500/month"
        ALL_DAY = "24x7", "24×7 — ₹1000/month"

    class PaymentStatus(models.TextChoices):
        PAID = "paid", "Paid"
        UNPAID = "unpaid", "Unpaid"

    student_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=120)
    father_name = models.CharField("Father's name", max_length=120, blank=True)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    admission_date = models.DateField(default=timezone.localdate)
    expiry_date = models.DateField()
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name="students")
    plan = models.CharField(max_length=12, choices=Plan.choices, default=Plan.FULL_DAY)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-admission_date", "name"]

    def __str__(self):
        return f"{self.student_id or 'New'} — {self.name}"

    @property
    def monthly_fee(self):
        return Decimal("1000") if self.plan == self.Plan.ALL_DAY else Decimal("500")

    def clean(self):
        if self.seat_id and self.is_active:
            occupant = Student.objects.filter(seat_id=self.seat_id, is_active=True).exclude(pk=self.pk).first()
            if occupant:
                raise ValidationError({"seat": f"{self.seat} is occupied by {occupant.name}."})

    def save(self, *args, **kwargs):
        if not self.student_id:
            last_id = Student.objects.order_by("-id").values_list("id", flat=True).first() or 0
            self.student_id = f"DLS{last_id + 1:04d}"
        super().save(*args, **kwargs)


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        UPI = "upi", "UPI"
        PHONEPE = "phonepe", "PhonePe"
        GPAY = "gpay", "Google Pay"
        PAYTM = "paytm", "Paytm"
        BANK = "bank", "Bank Transfer"

    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        UNPAID = "unpaid", "Unpaid"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=15, choices=Method.choices, default=Method.CASH)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    payment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date", "-created_at"]

    def __str__(self):
        return f"{self.student.name} — ₹{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        if self.status == self.Status.PAID and not self.payment_date:
            self.payment_date = timezone.localdate()
        if self.status == self.Status.UNPAID:
            self.payment_date = None
        super().save(*args, **kwargs)
        if self.student.payment_status != self.status:
            self.student.payment_status = self.status
            self.student.save(update_fields=["payment_status"])
