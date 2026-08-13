from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def create_seats(apps, schema_editor):
    Seat = apps.get_model("library", "Seat")
    Seat.objects.bulk_create([Seat(number=n, location="Main Reading Hall") for n in range(1, 41)])


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Seat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveSmallIntegerField(unique=True)),
                ("location", models.CharField(default="Main Reading Hall", max_length=100)),
            ],
            options={"ordering": ["number"]},
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_id", models.CharField(blank=True, max_length=20, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("father_name", models.CharField(blank=True, max_length=120, verbose_name="Father's name")),
                ("mobile", models.CharField(max_length=15)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField(blank=True)),
                ("admission_date", models.DateField(default=django.utils.timezone.localdate)),
                ("expiry_date", models.DateField()),
                ("plan", models.CharField(choices=[("full_day", "Full Day — ₹500/month"), ("24x7", "24×7 — ₹1000/month")], default="full_day", max_length=12)),
                ("payment_status", models.CharField(choices=[("paid", "Paid"), ("unpaid", "Unpaid")], default="unpaid", max_length=10)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("seat", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="library.seat")),
            ],
            options={"ordering": ["-admission_date", "name"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=8)),
                ("payment_method", models.CharField(choices=[("cash", "Cash"), ("upi", "UPI"), ("phonepe", "PhonePe"), ("gpay", "Google Pay"), ("paytm", "Paytm"), ("bank", "Bank Transfer")], default="cash", max_length=15)),
                ("status", models.CharField(choices=[("paid", "Paid"), ("unpaid", "Unpaid")], default="unpaid", max_length=10)),
                ("payment_date", models.DateField(blank=True, null=True)),
                ("due_date", models.DateField()),
                ("remarks", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="library.student")),
            ],
            options={"ordering": ["-due_date", "-created_at"]},
        ),
        migrations.RunPython(create_seats, migrations.RunPython.noop),
    ]
