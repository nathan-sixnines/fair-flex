import datetime
from common import Payment, Party, Parties, LoanInfo
from loan import Loan
from mortgageslice import MortgageSlice, MortgageSliceType


class Stake:
    """Defines a co-owner’s stake in the mortgage collaboration."""

    def __init__(
        self,
        baseline_value: float,
        loan_principal: float,
        parties: Parties,
        mortgage_info: LoanInfo,
    ):
        self.baseline_value = baseline_value
        self.loan_principal = loan_principal

        self.parties = parties  # The stakeholder (payer)

        mortgage_slice_loan = Loan(mortgage_info, self.loan_principal)
        individual_baseline_loan = Loan(mortgage_info, self.baseline_value)

        self.mortgage_slice = MortgageSlice(
            parties=parties,
            individual_loan=individual_baseline_loan,
            mortage_slice=mortgage_slice_loan,
            MortgageSlice_type=MortgageSliceType.FLEXIBLE,
        )

    def __repr__(self):
        return f"Stake(party={self.party.name}, common_party={self.common_party.name}, loans={len(self.loans)})"


if __name__ == "__main__":
    # Create parties

    alice = Party("Alice", "Co-Owner")
    common_fund = Party("Common Fund", "Common Party")

    # Create a stake
    parties = Parties(alice, common_fund)

    # Create a loan
    mortgage_info = LoanInfo(annual_rate=0.05, total_periods=10)

    stake = Stake(baseline_value=425_000, parties=parties, mortgage_info=mortgage_info)

    mortgage_slice = stake.mortgage_slice

    # Submit payments
    payment1 = Payment(amount=15000, sender=alice, recipient=common_fund, period=0)
    print(mortgage_slice.get_amortization_schedule())
    mortgage_slice.accept_payment(payment1)

    print(mortgage_slice.get_amortization_schedule())

    # Advance periods and validate payments
    print(f"Current period before advancing: {mortgage_slice.current_period}")
    mortgage_slice.advance_period()

    exit()
    print(f"Current period after advancing: {mortgage_slice.current_period}")

    print(mortgage_slice.get_amortization_schedule())

    mortgage_slice.advance_period()
    print(f"Current period after advancing: {mortgage_slice.current_period}")

    print(mortgage_slice.get_amortization_schedule())

    payment2 = Payment(amount=12000, sender=alice, recipient=common_fund, period=3)
    payment3 = Payment(amount=12000, sender=alice, recipient=common_fund, period=3)
    mortgage_slice.accept_payment(payment2)
    mortgage_slice.accept_payment(payment3)

    mortgage_slice.advance_period()
    print(f"Current period after advancing: {mortgage_slice.current_period}")

    print(mortgage_slice.get_amortization_schedule())

    payment4 = Payment(amount=2000, sender=alice, recipient=common_fund, period=4)
    mortgage_slice.accept_payment(payment4)
    mortgage_slice.advance_period()
    print(f"Current period after advancing: {mortgage_slice.current_period}")

    # Get amortization schedule
    try:
        schedule = mortgage_slice.get_amortization_schedule()
        print(schedule)
        print("MortgageSlice Amortization Schedule Verified")
    except ValueError as e:
        print(f"Verification failed: {e}")
