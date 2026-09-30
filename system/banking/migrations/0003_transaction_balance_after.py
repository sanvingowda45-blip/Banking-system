from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("banking", "0002_transaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="balance_after",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
            ),
        ),
    ]