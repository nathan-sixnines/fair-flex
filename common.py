from dataclasses import dataclass


class Party:
    """Represents a person or entity in the mortgage collaboration."""

    def __init__(
        self, name: str, ledger_strings=None, ledger_exclusions=None, exclusion_amount = None, type: str = None
    ):
        self.name = name
        self.type = type  # Optional: e.g., "Co-Owner", "Common Party", "Bank"
        # unique strings to match to transactions in ledger
        self.ledger_strings = ledger_strings if ledger_strings else []
        self.ledger_exclusions = ledger_exclusions if ledger_exclusions else []
        self.exclusion_amount = exclusion_amount

    def __repr__(self):
        return f"Party(name={self.name}{', type=' + self.type if self.type else ''})"


@dataclass
class Parties:
    stakeholder: Party
    common_party: Party


@dataclass
class LoanInfo:
    annual_rate: float
    total_periods: int


class Payment:
    """Represents a financial transaction between two parties within a specific period."""

    def __init__(self, amount: float, sender: Party, recipient: Party, period: int, date: str = None):
        if period < 0:
            raise ValueError("Period must be a non-negative integer.")
        self.amount = amount
        self.sender = sender
        self.recipient = recipient
        self.period = period
        self.date = date  # Store the date attribute

    def __repr__(self):
        date_str = f", date={self.date}" if self.date else ""
        return f"Payment(amount={self.amount:.2f}, sender={self.sender.name}, recipient={self.recipient.name}, period={self.period}{date_str})"
