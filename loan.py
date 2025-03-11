import numpy as np
from common import Payment, Party, LoanInfo
import copy
from collections import namedtuple
from enum import Enum

# Define a simple named tuple for payment details
PaymentDetails = namedtuple(
    "PaymentDetails", ["total_payment", "principal", "interest", "remaining_balance"]
)

"""General Utilities for Loans, used by mortgage slice"""

class TableType(Enum):
    FULL = "Full"
    SIDELOAN = "Sideloan"
    BASELINE = "Baseline"


class AmortizationTable:
    """
    Represents an amortization schedule as a structured table.
    """

    def __init__(self, schedule):
        self.schedule = schedule  # List of tuples [(period, total_payment, principal, interest, extra, balance), ...]

    def __repr__(self):
        """String representation of the amortization table."""
        return self._format_table(self.schedule)

    def _format_table(self, rows, include_header=True):
        """Formats the amortization table for display."""
        output = []
        if include_header:
            output.append(
                "Payment # | Total Payment | Principal | Interest | Extra Payment | Remaining Balance"
            )
        for row in rows:
            output.append(
                f"{row[0]:9} | {row[1]:13.2f} | {row[2]:9.2f} | {row[3]:8.2f} | {row[4]:13.2f} | {row[5]:17.2f}"
            )
        return "\n".join(output)
    
    def print_summary(self, range_head=2, range_tail=2):
        """Prints a summary of the amortization table, truncating consistent ranges separately."""
        if not self.schedule:
            return
        
        def find_ranges(schedule):
            """Finds consistent ranges where the total payment remains the same."""
            ranges = []
            start = 0
            for i in range(1, len(schedule)):
                if schedule[i][1] != schedule[start][1]:  # Total Payment check
                    ranges.append((start, i - 1))
                    start = i
            ranges.append((start, len(schedule) - 1))  # Add last range
            return ranges
        
        ranges = find_ranges(self.schedule)
        output = []
        output.append(
            "Payment # | Total Payment | Principal | Interest | Extra Payment | Remaining Balance"
        )
        
        for start, end in ranges:
            if end - start + 1 > range_head + range_tail:
                output.extend(self._format_table(self.schedule[start:start+range_head], include_header=False).split('\n'))
                output.append("...")
                output.extend(self._format_table(self.schedule[end-range_tail+1:end+1], include_header=False).split('\n'))
            else:
                output.extend(self._format_table(self.schedule[start:end+1], include_header=False).split('\n'))
        
        print("\n".join(output))


    def _format_row(self, row):
        """Formats a row the same way as in __repr__ for consistent display and comparison."""
        return (
            row[0],  # Payment #
            f"{row[1]:.2f}",  # Total Payment
            f"{row[2]:.2f}",  # Principal
            f"{row[3]:.2f}",  # Interest
        )

    def __eq__(self, other):
        if not isinstance(other, AmortizationTable):
            return False

        mismatches = []
        for idx, (row1, row2) in enumerate(zip(self.schedule, other.schedule)):
            formatted_row1 = self._format_row(row1)
            formatted_row2 = self._format_row(row2)

            if formatted_row1 != formatted_row2:
                differences = []
                labels = [
                    "Payment #",
                    "Total Payment",
                    "Principal",
                    "Interest",
                ]
                for label, v1, v2 in zip(labels, formatted_row1, formatted_row2):
                    if v1 != v2:
                        differences.append(f"{label}: Expected {v1}, got {v2}")

                mismatches.append(
                    f"Row {idx + 1} mismatch -> " + "; ".join(differences)
                )

        if mismatches:
            print("\n".join(mismatches))
            return False

        return True


class Loan:
    def __init__(self, loaninfo, total_value, start_period=1, extra_payments=None):
        self.total_value = total_value
        self.extra_payments = extra_payments if extra_payments else {}

        self.down_payment = None
        self.principal = None

        self.period_zero_setup()

        self.annual_rate = loaninfo.annual_rate
        self.total_periods = loaninfo.total_periods
        self.start_period = start_period
        self.monthly_rate = self.annual_rate / 12
        self.payment_periods = self.total_periods - start_period + 1

        self.schedule = self.generate_amortization_schedule()

    def period_zero_setup(self):
        self.down_payment = self.extra_payments.get(0, 0)
        self.principal = self.total_value - self.down_payment

    def __repr__(self):
        return (
            f"Loan(principal={self.principal:.2f}, annual_rate={self.annual_rate:.4f}, "
            f"total_periods={self.total_periods}, start_period={self.start_period}, "
            f"monthly_payment={self.payment:.2f}, remaining_balance={self.schedule.schedule[-1][-1]:.2f})"
        )

    def get_payment_for_period(self, period):
        """Retrieves the expected payment details for a given period from the amortization schedule."""
        # payments in period 0 are all extra / down payments against principal
        if period == 0:
            # down payment period special case
            return PaymentDetails(
                total_payment=0,
                principal=0,
                interest=0,
                remaining_balance=self.total_value,
            )

        if period > len(self.schedule.schedule):
            raise ValueError(f"Requested period {period} is out of range.")

        # Find the row corresponding to the given period
        for row in self.schedule.schedule:
            if row[0] == period:
                return PaymentDetails(
                    total_payment=row[1],
                    principal=row[2],
                    interest=row[3],
                    remaining_balance=row[5],
                )

        raise ValueError(f"No payment found for period {period}.")

    def calculate_payment(self, principal=None, payment_periods=None):
        if principal is None:
            principal = self.principal
        if payment_periods is None:
            payment_periods = self.payment_periods
        return (self.monthly_rate * principal) / (
            1 - (1 + self.monthly_rate) ** -payment_periods
        )

    def generate_amortization_schedule(self):
        balance = self.principal
        schedule = []

        payment = self.calculate_payment()

        for i in range(1, self.start_period):
            schedule.append((i, 0, 0, 0, 0, 0))

        for i in range(self.start_period, self.total_periods + 1):
            interest = balance * self.monthly_rate
            principal = payment - interest
            extra_payment = self.extra_payments.get(i, 0)
            balance -= principal + extra_payment
            schedule.append((i, payment, principal, interest, extra_payment, balance))

            if extra_payment != 0:
                remaining_payments = self.total_periods - i
                if remaining_payments > 0:
                    payment = self.calculate_payment(balance, remaining_payments)

        return AmortizationTable(schedule)

    def add_extra_payment(self, payment: Payment):
        self.extra_payments[payment.period] = (
            self.extra_payments.get(payment.period, 0) + payment.amount
        )
        self.period_zero_setup()  # must occur if down payment is in ledger and not constructor arg
        self.schedule = self.generate_amortization_schedule()

    def __copy__(self):
        """Shallow copy constructor."""
        return Loan(
            LoanInfo(
                self.annual_rate,
                self.total_periods,
            ),
            self.total_value,
            self.start_period,
            copy.deepcopy(self.extra_payments),
        )

    def __deepcopy__(self, memo):
        """Deep copy constructor."""
        new_copy = Loan(
            LoanInfo(
                self.annual_rate,
                self.total_periods,
            ),
            self.total_value,
            self.start_period,
            copy.deepcopy(self.extra_payments, memo),
        )
        memo[id(self)] = new_copy
        return new_copy

    # get the sum of loans. Communtative, so list order doesn't matter
    @staticmethod
    def combine_loans(loans):
        combined_schedule = {}

        for loan in loans:
            for entry in loan.schedule.schedule:
                (
                    payment_num,
                    total_payment,
                    principal,
                    interest,
                    extra_payment,
                    balance,
                ) = entry
                if payment_num not in combined_schedule:
                    combined_schedule[payment_num] = [0, 0, 0, 0, 0]

                combined_schedule[payment_num][0] += total_payment
                combined_schedule[payment_num][1] += principal
                combined_schedule[payment_num][2] += interest
                combined_schedule[payment_num][3] += extra_payment
                combined_schedule[payment_num][4] += balance

        sorted_schedule = [(k, *v) for k, v in sorted(combined_schedule.items())]
        return AmortizationTable(sorted_schedule)

    # get the difference between loans. Not communative, accepts two posiitional args
    @staticmethod
    def subtract_loans(loan1, loan2):
        combined_schedule = {}

        # Zip the two schedules together; if one is longer, truncate to the shorter length
        for entry1, entry2 in zip(loan1.schedule.schedule, loan2.schedule.schedule):
            (
                payment_num,
                total_payment1,
                principal1,
                interest1,
                extra_payment1,
                balance1,
            ) = entry1

            (
                _,
                total_payment2,
                principal2,
                interest2,
                extra_payment2,
                balance2,
            ) = entry2  # Ignore payment_num from loan2 since zip ensures alignment

            # Compute differences and store in the schedule
            combined_schedule[payment_num] = [
                total_payment1 - total_payment2,
                principal1 - principal2,
                interest1 - interest2,
                extra_payment1 - extra_payment2,
                balance1 - balance2,
            ]

        sorted_schedule = [(k, *v) for k, v in sorted(combined_schedule.items())]
        return AmortizationTable(sorted_schedule)



if __name__ == "__main__":
    sender = Party("Borrower")
    recipient = Party("Lender")

    extra_payments = [
        Payment(amount=5000, sender=sender, recipient=recipient, period=5),
        Payment(amount=-3000, sender=sender, recipient=recipient, period=3),
        Payment(amount=25000, sender=sender, recipient=recipient, period=0),
    ]

    interest_rate = 0.5
    loan_a = Loan(
        loaninfo=LoanInfo(annual_rate=interest_rate, total_periods=10),
        total_value=100000,
    )

    print("Scenario 1: Loan (A) With Extra Payments")
    for payment in extra_payments:
        loan_a.add_extra_payment(payment)

    print(loan_a.schedule)

    only_extra_loans = []

    for payment in extra_payments:
        amount = -payment.amount
        add_loan = Loan(
            loaninfo=LoanInfo(annual_rate=interest_rate, total_periods=10),
            total_value=amount,
            start_period=(payment.period + 1),
        )
        only_extra_loans.append(add_loan)

    print("\nScenario 3: New Loans Equivalent to Extra Payments")
    print(Loan.combine_loans(only_extra_loans))

    loan_b = Loan(
        LoanInfo(annual_rate=interest_rate, total_periods=10), total_value=100000
    )
    loans = [loan_b] + only_extra_loans

    print("\nScenario 4: Loans (B) Combined with Extra Payment Loans")
    print(Loan.combine_loans(loans))
