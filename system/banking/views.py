import re
import random
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import BankAccount, Transaction


ACCOUNT_NUMBER_PATTERN = re.compile(r"^\d{6,16}$")
PIN_PATTERN = re.compile(r"^\d{4}$")
NAME_PATTERN = re.compile(r"^[A-Za-z ]+$")
PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")


def login_view(request):
    """Render the login form and authenticate a bank account with Django."""
    if request.method == "POST":
        account_number = request.POST.get("account_number", "").strip()
        pin = request.POST.get("pin", "")

        if not ACCOUNT_NUMBER_PATTERN.fullmatch(account_number):
            messages.error(request, "Enter a valid account number.")
        elif not PIN_PATTERN.fullmatch(pin):
            messages.error(request, "Your PIN must contain exactly 4 digits.")
        else:
            user = authenticate(
                request,
                username=account_number,
                password=pin,
            )

            if user is not None:
                auth_login(request, user)
                messages.success(request, "Login successful.")
                return redirect("dashboard")

            if User.objects.filter(username=account_number).exists():
                messages.error(request, "Invalid account number or PIN.")
            else:
                messages.error(request, "Account not found.")

    return render(request, "login.html")


@login_required(login_url="login")
def dashboard_view(request):
    """Display the logged-in user's current account information."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    dashboard_data = {
        "customer_name": bank_account.full_name,
        "account_number": bank_account.account_number,
        "current_balance": f"{bank_account.balance:,.2f}",
    }
    return render(request, "dashboard.html", dashboard_data)


@login_required(login_url="login")
def check_balance_view(request):
    """Display the logged-in user's current balance."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    messages.success(request, f"Current balance: ₹{bank_account.balance:,.2f}")
    return render(
        request,
        "dashboard.html",
        {
            "customer_name": bank_account.full_name,
            "account_number": bank_account.account_number,
            "current_balance": f"{bank_account.balance:,.2f}",
        },
    )


@login_required(login_url="login")
def deposit_view(request):
    """Add a validated deposit to the logged-in user's account."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    if request.method == "POST":
        amount_text = request.POST.get("amount", "").strip()

        try:
            amount = Decimal(amount_text)
        except (InvalidOperation, ValueError):
            amount = None

        if amount is None or not amount.is_finite() or amount <= 0:
            messages.error(request, "Enter a valid positive amount.")
        elif amount.as_tuple().exponent < -2:
            messages.error(request, "Amount can have at most 2 decimal places.")
        else:
            with transaction.atomic():
                bank_account = BankAccount.objects.select_for_update().get(
                    pk=bank_account.pk,
                )
                bank_account.balance += amount
                bank_account.save(update_fields=["balance"])
                Transaction.objects.create(
                    account=bank_account,
                    transaction_type="Deposit",
                    amount=amount,
                    balance_after=bank_account.balance,
                )

            messages.success(request, "Deposit completed successfully.")
            return redirect("dashboard")

    return render(request, "deposit.html", {"account_number": bank_account.account_number})


@login_required(login_url="login")
def withdrawal_view(request):
    """Withdraw a validated amount from the logged-in user's account."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    if request.method == "POST":
        amount_text = request.POST.get("amount", "").strip()

        try:
            amount = Decimal(amount_text)
        except (InvalidOperation, ValueError):
            amount = None

        if amount is None or not amount.is_finite() or amount <= 0:
            messages.error(request, "Enter a valid positive amount.")
        elif amount.as_tuple().exponent < -2:
            messages.error(request, "Amount can have at most 2 decimal places.")
        else:
            with transaction.atomic():
                bank_account = BankAccount.objects.select_for_update().get(
                    pk=bank_account.pk,
                )
                if amount > bank_account.balance:
                    messages.error(request, "Insufficient balance for this withdrawal.")
                else:
                    bank_account.balance -= amount
                    bank_account.save(update_fields=["balance"])
                    Transaction.objects.create(
                        account=bank_account,
                        transaction_type="Withdrawal",
                        amount=amount,
                        balance_after=bank_account.balance,
                    )

                    messages.success(request, "Withdrawal completed successfully.")
                    return redirect("dashboard")

    return render(
        request,
        "withdrawal.html",
        {"account_number": bank_account.account_number},
    )


@login_required(login_url="login")
def transfer_view(request):
    """Transfer a validated amount from the logged-in user to another account."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    if request.method == "POST":
        receiver_account_number = request.POST.get("receiver_account_number", "").strip()
        amount_text = request.POST.get("amount", "").strip()

        try:
            amount = Decimal(amount_text)
        except (InvalidOperation, ValueError):
            amount = None

        receiver_account = BankAccount.objects.filter(
            account_number=receiver_account_number,
        ).first()

        if not receiver_account:
            messages.error(request, "Receiver account not found.")
        elif receiver_account.pk == bank_account.pk:
            messages.error(request, "You cannot transfer money to your own account.")
        elif amount is None or not amount.is_finite() or amount <= 0:
            messages.error(request, "Enter a valid positive amount.")
        elif amount.as_tuple().exponent < -2:
            messages.error(request, "Amount can have at most 2 decimal places.")
        else:
            account_ids = sorted([bank_account.pk, receiver_account.pk])
            with transaction.atomic():
                locked_accounts = {
                    account.pk: account
                    for account in BankAccount.objects.select_for_update().filter(
                        pk__in=account_ids,
                    )
                }
                sender = locked_accounts[bank_account.pk]
                receiver = locked_accounts[receiver_account.pk]

                if amount > sender.balance:
                    messages.error(request, "Insufficient balance for this transfer.")
                else:
                    sender.balance -= amount
                    receiver.balance += amount
                    sender.save(update_fields=["balance"])
                    receiver.save(update_fields=["balance"])
                    Transaction.objects.create(
                        account=sender,
                        transaction_type="Transfer Sent",
                        amount=amount,
                        balance_after=sender.balance,
                    )
                    Transaction.objects.create(
                        account=receiver,
                        transaction_type="Transfer Received",
                        amount=amount,
                        balance_after=receiver.balance,
                    )

                    messages.success(request, "Transfer completed successfully.")
                    return redirect("dashboard")

    return render(
        request,
        "transfer.html",
        {"account_number": bank_account.account_number},
    )


@login_required(login_url="login")
def transaction_history_view(request):
    """Display only the logged-in user's transactions, newest first."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    transactions = bank_account.transactions.order_by("-created_at", "-pk")
    transaction_rows = [
        {
            "type": (
                "Deposit"
                if record.transaction_type == "Deposit"
                else "Withdraw"
                if record.transaction_type == "Withdrawal"
                else "Transfer"
            ),
            "amount": f"{record.amount:,.2f}",
            "created_at": record.created_at,
            "balance_after": f"{record.balance_after:,.2f}",
        }
        for record in transactions
    ]

    return render(
        request,
        "transaction_history.html",
        {
            "customer_name": bank_account.full_name,
            "account_number": bank_account.account_number,
            "transaction_rows": transaction_rows,
        },
    )


@login_required(login_url="login")
def change_pin_view(request):
    """Allow the logged-in user to replace their account PIN."""
    try:
        bank_account = BankAccount.objects.get(
            account_number=request.user.username,
        )
    except BankAccount.DoesNotExist:
        auth_logout(request)
        messages.error(request, "Your bank account record could not be found.")
        return redirect("login")

    if request.method == "POST":
        current_pin = request.POST.get("current_pin", "")
        new_pin = request.POST.get("new_pin", "")
        confirm_pin = request.POST.get("confirm_pin", "")

        if not check_password(current_pin, request.user.password):
            messages.error(request, "Your current PIN is incorrect.")
        elif not PIN_PATTERN.fullmatch(new_pin):
            messages.error(request, "Your new PIN must contain exactly 4 digits.")
        elif new_pin != confirm_pin:
            messages.error(request, "The new PINs do not match.")
        elif new_pin == current_pin:
            messages.error(request, "Your new PIN must be different from your current PIN.")
        else:
            with transaction.atomic():
                request.user.set_password(new_pin)
                request.user.save(update_fields=["password"])
                bank_account.pin_hash = make_password(new_pin)
                bank_account.save(update_fields=["pin_hash"])

            update_session_auth_hash(request, request.user)
            messages.success(request, "Your PIN was changed successfully.")
            return redirect("dashboard")

    return render(
        request,
        "change_pin.html",
        {"account_number": bank_account.account_number},
    )


def logout_view(request):
    """Log the user out and return to the login page."""
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


def generate_account_number():
    """Generate a six-digit account number that is not already in use."""
    while True:
        account_number = str(random.randint(100000, 999999))
        if not BankAccount.objects.filter(account_number=account_number).exists():
            if not User.objects.filter(username=account_number).exists():
                return account_number


def create_account_view(request):
    """Validate registration details and create a new bank account."""
    if request.method == "POST":
        full_name = " ".join(request.POST.get("full_name", "").split())
        phone_number = request.POST.get("phone_number", "").strip()
        pin = request.POST.get("pin", "")
        confirm_pin = request.POST.get("confirm_pin", "")

        if not full_name:
            messages.error(request, "Please enter your full name.")
        elif not NAME_PATTERN.fullmatch(full_name):
            messages.error(request, "Name can contain only letters and spaces.")
        elif not PHONE_PATTERN.fullmatch(phone_number):
            messages.error(request, "Enter a valid 10-digit Indian mobile number.")
        elif BankAccount.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "This phone number is already registered.")
        elif not PIN_PATTERN.fullmatch(pin):
            messages.error(request, "Your PIN must contain exactly 4 digits.")
        elif pin != confirm_pin:
            messages.error(request, "The PINs do not match.")
        else:
            account_number = generate_account_number()

            with transaction.atomic():
                User.objects.create_user(
                    username=account_number,
                    password=pin,
                )
                BankAccount.objects.create(
                    full_name=full_name,
                    phone_number=phone_number,
                    account_number=account_number,
                    pin_hash=make_password(pin),
                    balance=0,
                    transaction_history=[],
                )

            messages.success(request, "Account created successfully.")
            return render(
                request,
                "create_account.html",
                {"account_number": account_number, "account_created": True},
            )

    return render(request, "create_account.html")
