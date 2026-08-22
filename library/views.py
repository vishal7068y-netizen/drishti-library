from datetime import date, timedelta
from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import PaymentForm, StudentForm
from .models import Payment, Seat, Student



def dashboard(request):
    today = timezone.localdate()
    active_students = Student.objects.filter(is_active=True)
    payments = Payment.objects.all()
    context = {
        "total_seats": 40,
        "occupied": active_students.count(),
        "available": 40 - active_students.count(),
        "paid": active_students.filter(payment_status=Student.PaymentStatus.PAID).count(),
        "unpaid": active_students.filter(payment_status=Student.PaymentStatus.UNPAID).count(),
        "income": payments.filter(status=Payment.Status.PAID).aggregate(total=Sum("amount"))["total"] or 0,
        "today_admissions": Student.objects.filter(admission_date=today).count(),
        "expiring": active_students.filter(expiry_date__range=(today, today + timedelta(days=7))).order_by("expiry_date"),
        "recent_students": Student.objects.select_related("seat").all()[:6],
    }
    return render(request, "library/dashboard.html", context)

def get_next_month(month):
    if month.month == 12:
     return date(month.year + 1, 1, 1)
    return date(month.year, month.month + 1, 1)


def ensure_monthly_payments():
    today = timezone.localdate()
    current_month = today.replace(day=1)

    students = Student.objects.all()

    for student in students:
        start_month = student.admission_date.replace(day=1)

        # Student ke leave hone ke baad future months create nahi honge
        if student.expiry_date:
            end_month = student.expiry_date.replace(day=1)
            end_month = min(end_month, current_month)
        else:
            end_month = current_month

        month = start_month

        while month <= end_month:

            payment = (
                Payment.objects
                .filter(
                    student=student,
                    fee_month=month
                )
                .order_by("id")
                .first()
            )

            # Agar is month ka record nahi hai tabhi naya banao
            if not payment:
                Payment.objects.create(
                    student=student,
                    amount=student.monthly_fee,
                    fee_month=month,
                    status=Payment.Status.UNPAID,
                    due_date=month,
                    remarks="Monthly library fee",
                )

            month = get_next_month(month)

def student_list(request):
    query = request.GET.get("q", "").strip()
    students = Student.objects.select_related("seat")
    if query:
        students = students.filter(name__icontains=query) | students.filter(mobile__icontains=query) | students.filter(seat__number__icontains=query)
    return render(request, "library/student_list.html", {"students": students, "query": query})


def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST)

        if form.is_valid():
            student = form.save()
            Payment.objects.create(
                student=student,
                amount=student.monthly_fee,
                fee_month=student.admission_date.replace(day=1),
                status=student.payment_status,
                due_date=student.admission_date,
                payment_date=(
                    timezone.localdate()
                    if student.payment_status == Student.PaymentStatus.PAID
                    else None
                ),
                remarks="Admission payment",
            )

            messages.success(
                request,
                f"{student.name} का admission सफलतापूर्वक जोड़ दिया गया।"
            )

            return redirect("student_list")

    else:
        form = StudentForm(
            initial={
                "admission_date": timezone.localdate(),
            }
        )

    return render(
        request,
        "library/student_form.html",
        {
            "form": form,
            "title": "New Admission",
        },
    )

def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student की जानकारी update हो गई।")
            return redirect("student_list")
    else:
        form = StudentForm(instance=student)
    return render(request, "library/student_form.html", {"form": form, "title": f"Edit {student.name}", "student": student})

@require_POST
def student_leave(request, pk):
    student = get_object_or_404(Student, pk=pk)
    leaving_date = request.POST.get("leaving_date")
    if not leaving_date:
        messages.error(request, "Leaving date select karein.")
        return redirect("student_list")
    try:
        leaving_date = timezone.datetime.strptime(
            leaving_date, "%Y-%m-%d"
        ).date()
    except ValueError:
        messages.error(request, "Invalid leaving date.")
        return redirect("student_list")
    student.expiry_date = leaving_date
    student.is_active = False
    student.save(update_fields=["expiry_date", "is_active"])
    messages.success(
        request,
        f"{student.name} ko library se leave kar diya gaya."
    )
    return redirect("student_list")


def seat_list(request):
    seats = Seat.objects.prefetch_related("students")
    for seat in seats:
        seat.active_student = next((student for student in seat.students.all() if student.is_active), None)
    return render(request, "library/seat_list.html", {"seats": seats})


def payment_list(request):
   
    ensure_monthly_payments()

    status = request.GET.get("status", "")

    payments = Payment.objects.select_related(
        "student",
        "student__seat"
    )

    if status in (Payment.Status.PAID, Payment.Status.UNPAID):
        payments = payments.filter(status=status)

    return render(
        request,
        "library/payment_list.html",
        {
            "payments": payments,
            "selected_status": status,
        },
    )


def payment_create(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    if request.method == "POST":
        form = PaymentForm(request.POST)

        if form.is_valid():
            fee_month = form.cleaned_data["fee_month"]

            payment = Payment.objects.filter(
                student=student,
                fee_month=fee_month
            ).first()

            if payment:
                form = PaymentForm(request.POST, instance=payment)
                if form.is_valid():
                    form.save()

                messages.success(
                    request,
                    f"{fee_month.strftime('%B %Y')} ka payment record update ho gaya."
                )

            else:
                payment = form.save(commit=False)
                payment.student = student
                payment.save()

                messages.success(
                    request,
                    f"{fee_month.strftime('%B %Y')} ka payment record add ho gaya."
                )

            return redirect("payment_list")

    else:
        form = PaymentForm(
            initial={
                "amount": student.monthly_fee,
                "due_date": timezone.localdate(),
                "status": Student.PaymentStatus.PAID,
                "fee_month": timezone.localdate().replace(day=1),
            }
        )

    return render(
        request,
        "library/payment_form.html",
        {
            "form": form,
            "student": student,
            "title": "Add Payment",
        },
    )
def payment_update(request, pk):
    payment = get_object_or_404(Payment.objects.select_related("student"), pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment record update हो गया।")
            return redirect("payment_list")
    else:
        form = PaymentForm(instance=payment)
    return render(request, "library/payment_form.html", {"form": form, "student": payment.student, "title": "Edit Payment"})


def reports(request):
    today = timezone.localdate()
    by_plan = Student.objects.filter(is_active=True).values("plan").annotate(total=Count("id")).order_by("plan")
    monthly_income = Payment.objects.filter(status=Payment.Status.PAID, payment_date__year=today.year, payment_date__month=today.month).aggregate(total=Sum("amount"))["total"] or 0
    return render(request, "library/reports.html", {
        "paid_students": Student.objects.filter(is_active=True, payment_status=Student.PaymentStatus.PAID).select_related("seat"),
        "unpaid_students": Student.objects.filter(is_active=True, payment_status=Student.PaymentStatus.UNPAID).select_related("seat"),
        "by_plan": by_plan,
        "monthly_income": monthly_income,
        "admissions": Student.objects.filter(admission_date__month=today.month, admission_date__year=today.year).count(),
    })
    
