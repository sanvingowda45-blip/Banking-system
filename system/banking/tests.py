from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import TestCase

from .models import BankAccount, Transaction


class CheckBalanceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="999990",
            password="1234",
        )
        self.account = BankAccount.objects.create(
            full_name="Balance Test",
            phone_number="9876543209",
            account_number="999990",
            pin_hash="test",
            balance=Decimal("1234.56"),
        )
        BankAccount.objects.create(
            full_name="Other Account",
            phone_number="9876543208",
            account_number="999989",
            pin_hash="test",
            balance=Decimal("9876.54"),
        )
        self.client.force_login(self.user)

    def test_check_balance_shows_only_logged_in_users_balance(self):
        response = self.client.get("/check-balance/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1,234.56")
        self.assertContains(response, "Current balance: ₹1,234.56")
        self.assertNotContains(response, "9,876.54")


class ChangePinViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="999986",
            password="1234",
        )
        self.account = BankAccount.objects.create(
            full_name="PIN Test",
            phone_number="9876543205",
            account_number="999986",
            pin_hash="test",
            balance=Decimal("100.00"),
        )
        self.client.force_login(self.user)

    def test_change_pin_updates_both_credentials_and_keeps_session(self):
        response = self.client.post(
            "/change-pin/",
            {
                "current_pin": "1234",
                "new_pin": "5678",
                "confirm_pin": "5678",
            },
        )

        self.user.refresh_from_db()
        self.account.refresh_from_db()

        self.assertRedirects(response, "/dashboard/")
        self.assertTrue(self.user.check_password("5678"))
        self.assertFalse(self.user.check_password("1234"))
        self.assertTrue(check_password("5678", self.account.pin_hash))
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)

    def test_change_pin_rejects_wrong_current_pin(self):
        response = self.client.post(
            "/change-pin/",
            {
                "current_pin": "0000",
                "new_pin": "5678",
                "confirm_pin": "5678",
            },
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.check_password("1234"))
        self.assertContains(response, "Your current PIN is incorrect.")

    def test_change_pin_rejects_mismatched_new_pins(self):
        response = self.client.post(
            "/change-pin/",
            {
                "current_pin": "1234",
                "new_pin": "5678",
                "confirm_pin": "8765",
            },
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.check_password("1234"))
        self.assertContains(response, "The new PINs do not match.")


class DepositViewTests(TestCase):
    def test_deposit_updates_balance_and_creates_transaction(self):
        user = get_user_model().objects.create_user(
            username="999991",
            password="1234",
        )
        account = BankAccount.objects.create(
            full_name="Deposit Test",
            phone_number="9876543210",
            account_number="999991",
            pin_hash="test",
            balance=Decimal("100.00"),
        )
        self.client.force_login(user)

        response = self.client.post(
            "/deposit/",
            {"amount": "250.50"},
            follow=True,
        )

        account.refresh_from_db()
        record = Transaction.objects.get(account=account)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(account.balance, Decimal("350.50"))
        self.assertEqual(record.transaction_type, "Deposit")
        self.assertEqual(record.amount, Decimal("250.50"))
        self.assertEqual(record.balance_after, Decimal("350.50"))
        self.assertIsNotNone(record.created_at)
        self.assertContains(response, "Deposit completed successfully.")
        self.assertContains(response, "350.50")


class TransactionHistoryViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="999988",
            password="1234",
        )
        self.account = BankAccount.objects.create(
            full_name="History Test",
            phone_number="9876543207",
            account_number="999988",
            pin_hash="test",
            balance=Decimal("150.00"),
        )
        other_account = BankAccount.objects.create(
            full_name="Other History Account",
            phone_number="9876543206",
            account_number="999987",
            pin_hash="test",
            balance=Decimal("999.00"),
        )
        Transaction.objects.create(
            account=self.account,
            transaction_type="Deposit",
            amount=Decimal("100.00"),
            balance_after=Decimal("100.00"),
        )
        Transaction.objects.create(
            account=self.account,
            transaction_type="Withdrawal",
            amount=Decimal("25.00"),
            balance_after=Decimal("75.00"),
        )
        Transaction.objects.create(
            account=other_account,
            transaction_type="Deposit",
            amount=Decimal("999.00"),
            balance_after=Decimal("999.00"),
        )
        self.client.force_login(self.user)

    def test_history_shows_only_users_transactions_newest_first(self):
        response = self.client.get("/transaction-history/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Withdraw")
        self.assertContains(response, "25.00")
        self.assertContains(response, "75.00")
        self.assertContains(response, "Deposit")
        self.assertContains(response, "100.00")
        self.assertNotContains(response, "999.00")
        self.assertContains(response, 'href="/dashboard/"')
        self.assertContains(response, "Back to Dashboard")
        self.assertLess(
            response.content.find(b"Withdraw"),
            response.content.find(b"Deposit"),
        )


class WithdrawalViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="999992",
            password="1234",
        )
        self.account = BankAccount.objects.create(
            full_name="Withdrawal Test",
            phone_number="9876543211",
            account_number="999992",
            pin_hash="test",
            balance=Decimal("100.00"),
        )
        self.client.force_login(self.user)

    def test_withdrawal_updates_balance_and_creates_transaction(self):
        response = self.client.post(
            "/withdrawal/",
            {"amount": "40.50"},
            follow=True,
        )

        self.account.refresh_from_db()
        record = Transaction.objects.get(account=self.account)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.account.balance, Decimal("59.50"))
        self.assertEqual(record.transaction_type, "Withdrawal")
        self.assertEqual(record.amount, Decimal("40.50"))
        self.assertEqual(record.balance_after, Decimal("59.50"))
        self.assertIsNotNone(record.created_at)
        self.assertContains(response, "Withdrawal completed successfully.")
        self.assertContains(response, "59.50")

    def test_insufficient_balance_does_not_change_balance_or_create_transaction(self):
        response = self.client.post(
            "/withdrawal/",
            {"amount": "100.01"},
        )

        self.account.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(Transaction.objects.filter(account=self.account).exists())
        self.assertContains(response, "Insufficient balance for this withdrawal.")

    def test_withdrawal_rejects_non_positive_amount(self):
        response = self.client.post(
            "/withdrawal/",
            {"amount": "0"},
        )

        self.account.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(Transaction.objects.filter(account=self.account).exists())
        self.assertContains(response, "Enter a valid positive amount.")


class TransferViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="999993",
            password="1234",
        )
        self.sender = BankAccount.objects.create(
            full_name="Sender Test",
            phone_number="9876543212",
            account_number="999993",
            pin_hash="test",
            balance=Decimal("100.00"),
        )
        self.receiver = BankAccount.objects.create(
            full_name="Receiver Test",
            phone_number="9876543213",
            account_number="999994",
            pin_hash="test",
            balance=Decimal("25.00"),
        )
        self.client.force_login(self.user)

    def test_transfer_updates_both_balances_and_creates_two_transactions(self):
        response = self.client.post(
            "/transfer/",
            {
                "receiver_account_number": "999994",
                "amount": "40.50",
            },
            follow=True,
        )

        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        records = Transaction.objects.order_by("account_id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sender.balance, Decimal("59.50"))
        self.assertEqual(self.receiver.balance, Decimal("65.50"))
        self.assertEqual(records.count(), 2)
        self.assertEqual(records[0].transaction_type, "Transfer Sent")
        self.assertEqual(records[0].amount, Decimal("40.50"))
        self.assertEqual(records[0].balance_after, Decimal("59.50"))
        self.assertEqual(records[1].transaction_type, "Transfer Received")
        self.assertEqual(records[1].amount, Decimal("40.50"))
        self.assertEqual(records[1].balance_after, Decimal("65.50"))
        self.assertIsNotNone(records[0].created_at)
        self.assertIsNotNone(records[1].created_at)
        self.assertContains(response, "Transfer completed successfully.")
        self.assertContains(response, "59.50")

    def test_transfer_rejects_missing_receiver_without_changing_balances(self):
        response = self.client.post(
            "/transfer/",
            {
                "receiver_account_number": "888888",
                "amount": "40.00",
            },
        )

        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sender.balance, Decimal("100.00"))
        self.assertEqual(self.receiver.balance, Decimal("25.00"))
        self.assertFalse(Transaction.objects.exists())
        self.assertContains(response, "Receiver account not found.")

    def test_transfer_rejects_insufficient_balance_without_changing_accounts(self):
        response = self.client.post(
            "/transfer/",
            {
                "receiver_account_number": "999994",
                "amount": "100.01",
            },
        )

        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sender.balance, Decimal("100.00"))
        self.assertEqual(self.receiver.balance, Decimal("25.00"))
        self.assertFalse(Transaction.objects.exists())
        self.assertContains(response, "Insufficient balance for this transfer.")
