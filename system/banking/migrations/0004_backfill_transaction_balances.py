from decimal import Decimal

from django.db import migrations, models


def backfill_balance_after(apps, schema_editor):
    BankAccount = apps.get_model("banking", "BankAccount")
    Transaction = apps.get_model("banking", "Transaction")

    for account in BankAccount.objects.all():
        running_balance = account.balance
        transactions = list(
            Transaction.objects.filter(account_id=account.pk).order_by(
                "-created_at",
                "-pk",
            )
        )

        for record in transactions:
            if record.balance_after is None:
                record.balance_after = running_balance
                record.save(update_fields=["balance_after"])

            if record.transaction_type in {"Deposit", "Transfer Received"}:
                running_balance -= record.amount
            elif record.transaction_type in {"Withdrawal", "Transfer Sent"}:
                running_balance += record.amount


class Migration(migrations.Migration):
    dependencies = [
        ("banking", "0003_transaction_balance_after"),
    ]

    operations = [
        migrations.RunPython(backfill_balance_after, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="transaction",
            name="balance_after",
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
    ]