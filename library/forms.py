from django import forms
from django.utils import timezone

from .models import Payment, Seat, Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "name",
            "father_name",
            "mobile",
            "email",
            "address",
            "admission_date",
            "expiry_date",
            "seat",
            "plan",
            "payment_status",
            "is_active",
            "notes",
        ]
        widgets = {
            "admission_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        occupied = (
            Student.objects
            .filter(is_active=True)
            .exclude(pk=self.instance.pk)
            .values_list("seat_id", flat=True)
        )

        self.fields["seat"].queryset = (
            Seat.objects
            .exclude(id__in=occupied)
            .order_by("number")
        )

        if self.instance.pk and self.instance.seat_id:
            self.fields["seat"].queryset = (
                self.fields["seat"].queryset
                | Seat.objects.filter(pk=self.instance.seat_id)
            ).order_by("number")

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "amount",
            "payment_method",
            "status",
            "fee_month",
            "payment_date",
            "due_date",
            "remarks",
        ]
        widgets = {
            "fee_month": forms.DateInput(attrs={"type": "date"}),
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["payment_date"].initial = timezone.localdate()
            self.fields["fee_month"].initial = timezone.localdate().replace(day=1)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"