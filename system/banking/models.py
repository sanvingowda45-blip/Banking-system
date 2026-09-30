from django.db import models


class BankAccount(models.Model):
    """Stores the details and current state of one bank account."""

    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=10, unique=True)
    account_number = models.CharField(max_length=16, unique=True)
    pin_hash = models.CharField(max_length=128)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.account_number}"


class Transaction(models.Model):
    """Stores a record of a completed account transaction."""

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"
