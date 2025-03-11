import datetime
from enum import Enum
from loan import Loan, TableType
from common import Payment, Party, Parties, LoanInfo
import copy

# the idea of using the same class to represent stake and bank loans didn't pan out
# the fixed mortgate slice type can probably be removed
# the loan type is enough, but this is stake loan middleware
# the fixed type is useless, just a loan wrapper
# TODO remove this
class MortgageSliceType(Enum):
    FIXED = "Fixed"
    FLEXIBLE = "Flexible"


class MortgageSlice:
    """Functions and state for MortgageSlice of a stake"""

    def __init__(
        self, parties: Parties, individual_loan: Loan, mortage_slice: Loan, MortgageSlice_type: MortgageSliceType
    ):
        if MortgageSlice_type not in (
            MortgageSliceType.FIXED,
            MortgageSliceType.FLEXIBLE,
        ):
            raise ValueError("MortgageSlice type must be 'Fixed' or 'Flexible'.")
        self.payer = parties.stakeholder
        self.recipient = parties.common_party
        self.MortgageSlice_type = MortgageSlice_type
        self.mortgage_slice_loan = mortage_slice # nominal slice of mortgage principal
        self.full_value_loan = individual_loan # baseline for adjusted loan without any extra payments
        self.adjusted_loan = (
            copy.deepcopy(individual_loan)
            if MortgageSlice_type == MortgageSliceType.FLEXIBLE
            else None
        )
        self.adjustment_verification = (
            [] if MortgageSlice_type == MortgageSliceType.FLEXIBLE else None
        )

        self.current_period = 0  # process down payments before first period
        self.pending_payments = []  # Queue of payments waiting to be applied

    def accept_payment(self, payment: Payment):
        """Accepts a payment and stores it until the period advances."""
        if payment.period != self.current_period:
            raise ValueError(
                f"Payment must be for (current period: {self.current_period})."
            )

        # Add payment to queue
        self.pending_payments.append(payment)

    def advance_period(self):
        """Processes payments for the current period and advances to the next."""

        # Sum up all payments received for the current period
        total_paid = 0
        for payment in self.pending_payments:
            total_paid += payment.amount

        if self.MortgageSlice_type == MortgageSliceType.FIXED:
            # Fixed MortgageSlice: Must match exactly
            expected_payment = self.full_value_loan.get_payment_for_period(
                self.current_period
            )

            if round(total_paid, 2) != round(expected_payment.total_payment, 2):
                raise ValueError(
                    f"Fixed MortgageSlice requires exact payment of {expected_payment.total_payment:.2f}, "
                    f"but received {total_paid:.2f}."
                )

        elif self.MortgageSlice_type == MortgageSliceType.FLEXIBLE:
            # Flexible MortgageSlice: Calculate difference and add as extra payment

            expected_payment = self.adjusted_loan.get_payment_for_period(
                self.current_period
            )
            difference = round(total_paid - expected_payment.total_payment, 2)

            # Todo: detect stake popping One case that would pop a stake is a negative down payment
            # custom rule to detect that first, but should generalize to detecte any stake popping

            if difference < 0 and self.current_period < 1:
                raise Exception(f"Down payment from {self.payer} cannot be negative")

            if difference != 0:
                adjustment_payment = Payment(
                    amount=difference,
                    sender=self.payer,
                    recipient=self.recipient,
                    period=self.current_period,
                )
                print(f"adding {difference}")
                self.add_adjustment_payment(adjustment_payment)

        # Remove processed payments and advance period
        self.pending_payments = [
            p for p in self.pending_payments if p.period > self.current_period
        ]
        self.current_period += 1

    def add_adjustment_loan(self, loan: Loan):
        """Convert a loan into an equivalent extra payment and add both."""
        payment = Payment(
            amount=-loan.principal, sender=self.payer, recipient=self.recipient
        )
        self._add_adjustment(loan, payment)

    def add_adjustment_payment(self, payment: Payment):
        """Convert an extra payment into an equivalent loan and add both."""
        generated_loan = Loan(
            LoanInfo(
                annual_rate=self.full_value_loan.annual_rate,
                total_periods=self.full_value_loan.total_periods,
            ),
            total_value=-payment.amount,
            start_period=payment.period + 1,
        )
        self._add_adjustment(generated_loan, payment)

    def _add_adjustment(self, loan: Loan, payment: Payment):
        """Handles adding the adjustment to both adjusted loan and verification list."""
        if self.MortgageSlice_type != MortgageSliceType.FLEXIBLE:
            raise ValueError("Only flexible MortgageSlices can have adjustment loans.")

        self.adjusted_loan.add_extra_payment(payment)
        self.adjustment_verification.append(loan)
        self.verify_adjustments()

    def get_adjustment_table(self):
        adjustments = Loan.combine_loans(self.adjustment_verification)
        return adjustments
    
    def get_sideloan_table(self):
        self.verify_adjustments()
        sideloan = Loan.subtract_loans( self.adjusted_loan, self.mortgage_slice_loan,)
        return sideloan

    def verify_adjustments(self):
        """Compares the amortization table of the adjusted loan with the adjustment verification list."""
        adjusted_schedule = self.adjusted_loan.generate_amortization_schedule()
        verification_schedule = Loan.combine_loans(
            [self.full_value_loan] + self.adjustment_verification
        )

        if adjusted_schedule != verification_schedule:
            print("adjusted sched")
            print(adjusted_schedule)
            print("combined verification")
            print(verification_schedule)

            raise ValueError(
                "Adjustment verification failed: Amortization tables do not match."
            )

    def get_amortization_schedule(self, tabletype):
        """Returns the amortization schedule after verification."""

        if self.MortgageSlice_type == MortgageSliceType.FLEXIBLE:
            self.verify_adjustments()

            if tabletype == TableType.FULL:
                return self.adjusted_loan.schedule
            if tabletype == TableType.SIDELOAN:
                return self.get_sideloan_table()
            if tabletype == TableType.BASELINE:
                return self.full_value_loan.schedule
        elif self.MortgageSlice_type == MortgageSliceType.FIXED:

            raise Exception("this isn't used and should be removed ty")
        else:
            raise Exception(
                f"MortgageSlice type {self.obilgation_type} is not implemented"
            )


if __name__ == "__main__":
    # Create parties

    alice = Party("Alice", "Co-Owner")
    common_fund = Party("Common Fund", "Common Party")

    # Create a stake
    parties = Parties(alice, common_fund)

    # Create a loan
    loan = Loan(LoanInfo(annual_rate=0.05, total_periods=10), 100000)

    # Create an MortgageSlice
    MortgageSlice = MortgageSlice(parties, loan, MortgageSliceType.FLEXIBLE)

    MortgageSlice.advance_period()

    # Submit payments
    payment1 = Payment(amount=15000, sender=alice, recipient=common_fund, period=1)
    MortgageSlice.accept_payment(payment1)

    print(MortgageSlice.get_amortization_schedule())

    # Advance periods and validate payments
    print(f"Current period before advancing: {MortgageSlice.current_period}")
    MortgageSlice.advance_period()
    print(f"Current period after advancing: {MortgageSlice.current_period}")

    print(MortgageSlice.get_amortization_schedule())

    MortgageSlice.advance_period()
    print(f"Current period after advancing: {MortgageSlice.current_period}")

    print(MortgageSlice.get_amortization_schedule())

    payment2 = Payment(amount=12000, sender=alice, recipient=common_fund, period=3)
    payment3 = Payment(amount=12000, sender=alice, recipient=common_fund, period=3)
    MortgageSlice.accept_payment(payment2)
    MortgageSlice.accept_payment(payment3)

    MortgageSlice.advance_period()
    print(f"Current period after advancing: {MortgageSlice.current_period}")

    print(MortgageSlice.get_amortization_schedule())

    payment4 = Payment(amount=2000, sender=alice, recipient=common_fund, period=4)
    MortgageSlice.accept_payment(payment4)
    MortgageSlice.advance_period()
    print(f"Current period after advancing: {MortgageSlice.current_period}")

    # Get amortization schedule
    try:
        schedule = MortgageSlice.get_amortization_schedule()
        print(schedule)
        print("MortgageSlice Amortization Schedule Verified")
    except ValueError as e:
        print(f"Verification failed: {e}")
