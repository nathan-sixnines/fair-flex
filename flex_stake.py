from typing import List, Dict
import csv
from enum import Enum


class PaymentState(Enum):
    PLANNED = "Planned"
    COMPLETED = "Completed"


class Party:
    def __init__(self, name: str):
        self.name = name


class Stakeholder(Party):
    def __init__(self, name: str):
        super().__init__(name)
        self.stakes: List[Stake] = []

    def add_stake(self, stake: "Stake"):
        self.stakes.append(stake)


class Stake:
    def __init__(self, owner: Stakeholder, amount: float):
        self.owner = owner
        self.amount = amount
        self.flex = 0
        owner.add_stake(self)


class Mortgage:
    def __init__(
        self,
        total_amount: float,
        interest_rate: float,
        num_payments: int,
        stakeholder_names: List[str],
    ):
        self.total_amount = total_amount
        self.interest_rate = interest_rate
        self.num_payments = num_payments
        self.stakes: List[Stake] = []
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.initialize_stakeholders(stakeholder_names)
        self.payments: List[Payment] = self.generate_amortization_schedule()

    def initialize_stakeholders(self, stakeholder_names: List[str]):
        for name in stakeholder_names:
            if name not in self.stakeholders:
                self.stakeholders[name] = Stakeholder(name)
            stake_amount = self.total_amount / len(
                stakeholder_names
            )  # Equal division for now
            self.add_stake(Stake(self.stakeholders[name], stake_amount))

    def add_stake(self, stake: Stake):
        self.stakes.append(stake)

    def total_stake_allocated(self) -> float:
        return sum(stake.amount for stake in self.stakes)

    def generate_amortization_schedule(self) -> List["Payment"]:
        payments = []
        monthly_rate = self.interest_rate / 12 / 100
        if monthly_rate > 0:
            monthly_payment = (self.total_amount * monthly_rate) / (
                1 - (1 + monthly_rate) ** -self.num_payments
            )
        else:
            monthly_payment = self.total_amount / self.num_payments

        for i in range(self.num_payments):
            payments.append(
                Payment(
                    amount=monthly_payment,
                    sender=None,
                    recipient=None,
                    date=f"Month {i+1}",
                    state=PaymentState.PLANNED,
                )
            )

        return payments


# Define mortgage with example stakeholders
example_stakeholders = ["Alice", "Bob", "Charlie", "Alice", "Eve"]
mortgage = Mortgage(
    total_amount=500000,
    interest_rate=5.0,
    num_payments=360,
    stakeholder_names=example_stakeholders,
)


class Payment:
    def __init__(
        self,
        amount: float,
        sender: Party,
        recipient: Party,
        date: str,
        state: PaymentState = PaymentState.PLANNED,
    ):
        self.amount = amount
        self.sender = sender
        self.recipient = recipient
        self.date = date
        self.state = state


class PaymentRecord:
    def __init__(self):
        self.payments: List[Payment] = []

    def add_payment(self, payment: Payment):
        payment.state = PaymentState.COMPLETED  # Ingested payments are always completed
        self.payments.append(payment)

    def total_paid(self) -> float:
        return sum(
            payment.amount
            for payment in self.payments
            if payment.state == PaymentState.COMPLETED
        )

    def payments_by_party(self) -> Dict[str, float]:
        payments_summary = {}
        for payment in self.payments:
            if payment.state == PaymentState.COMPLETED:
                payments_summary[payment.sender.name] = (
                    payments_summary.get(payment.sender.name, 0) + payment.amount
                )
        return payments_summary


# Test CSV for first payment (down payment from stakeholder to common fund)
test_csv_filename = "test_payments.csv"
test_csv_data = [
    ["Amount", "Sender", "Recipient", "Date", "Paid", "Flex", "Nominal Next Payment"],
    [50000.0, "Alice", "Common Fund", "2025-01-01", 50000.0, 0.0, 0.0],
]

with open(test_csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(test_csv_data)

print(f"Test CSV '{test_csv_filename}' created with initial down payment entry.")

# Ingest and process the test CSV
parties = {"Alice": Stakeholder("Alice"), "Common Fund": Party("Common Fund")}
payment_record = PaymentRecord()

with open(test_csv_filename, mode="r") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    for row in reader:
        amount, sender_name, recipient_name, date, paid, flex, nominal = row
        sender = parties.get(sender_name, Party(sender_name))
        recipient = parties.get(recipient_name, Party(recipient_name))
        payment_record.add_payment(
            Payment(float(amount), sender, recipient, date, PaymentState.COMPLETED)
        )

# Print ingested payment details
for payment in payment_record.payments:
    print(
        f"Processed Payment: {payment.amount} from {payment.sender.name} to {payment.recipient.name} on {payment.date}"
    )
