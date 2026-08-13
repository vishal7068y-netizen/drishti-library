# Drishti Library Management System

Django application for a 40-seat study library.

## Features

- 40 seats seeded automatically (available / occupied)
- Student admissions, contact information, seat assignment, active/inactive membership
- Full Day ₹500 and 24×7 ₹1000 plans
- Payment records with Cash, UPI, PhonePe, Google Pay, Paytm, and Bank Transfer
- Paid/unpaid status, dashboard, expiring-membership list, reports, and Django admin

## Run locally

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Open `/admin/` to use the Django admin panel.
