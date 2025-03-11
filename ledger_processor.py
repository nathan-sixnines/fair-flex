from property import Property, PropertyParams
from common import Payment, Party, LoanInfo
from datetime import datetime
from ledger_reader import LedgerReader
from loan import TableType

class LedgerProcessor:
    """
    Processes payments to update the Property class accordingly.
    """

    def __init__(self, property: Property):
        """
        Initializes the LedgerProcessor with a reference to a Property instance.

        :param property: The Property instance to be updated based on payments.
        """
        self.property = property

    def process_payment(self, payment: Payment):
        """
        Processes a single payment and updates the corresponding stakeholder's obligation.

        :param payment: A Payment instance containing transaction details.
        """
        if payment.sender.name in self.property.mortgage_slices:
            print(f"processing payment for {payment.sender.name}")
            result = self.property.accept_payment(
                payment.sender, payment.amount, payment.period
            )
        else:
            print(f"{payment.sender.name} not in {self.property.mortgage_slices}")

    def process_payments(self, payments: list[Payment]):
        """
        Processes a list of payments and updates the Property instance accordingly.

        :param payments: A list of Payment instances.
        """
        # Sort payments by period
        sorted_payments = sorted(payments, key=lambda p: p.period)

        current_period = 0

        for payment in sorted_payments:
            payment_period = payment.period


            while current_period < payment_period:
                self.property.advance_period()
                current_period += 1

            print(payment)

            self.process_payment(payment)

    def advance_period(self):
        """
        Advances period of property.

        Happens automatically when a transaction occurs in ledger in the next period.

        Required to calculate next period amortization before that period appears in ledger
        """
        self.property.advance_period()

    def get_tables(self, tabletype = TableType.FULL):

        return self.property.get_amortization_schedule(tabletype)
    

if __name__ == "__main__":
    # Define stakeholders
    alice = Party("Alice", ledger_strings=["Alice Mortgage Payment"])
    bob = Party("Bob", ledger_strings=["Bob Loan Repayment"])

    parties = [
        Party(
            name="Nathan",
            type="Stakeholder",
            ledger_strings=[
                "six nines it",
                "nathan checking",
                "ID:XXXXX94779 PPD",
                "Accenture LLP",
                "Nathan Solar Square Up",
                "nathan",
            ],
            ledger_exclusions=["airbnb","Washington Gas"],
        ),
        Party(
            name="Mischella",
            type="Stakeholder",
            ledger_strings=["CHK 5622", "old gallows vienna"],
            exclusion_amount=1100
        )
    ]

    mutual_income_strings = []#"airbnb"]

    # Sample setup
    params = PropertyParams(
        purchase_cost=1_130_000,
        purchase_down_payment=282500,
        loan_info=LoanInfo(annual_rate=0.05625, total_periods=360),
        stakeholders=parties,
        stakeholder_down_payments={"Nathan": 62_500, "Mischella": 220_000},
    )

    property_instance = Property(params)
    ledger_processor = LedgerProcessor(property_instance)

    # Sample payments
    first_period_date = datetime.strptime("01/16/2023", "%m/%d/%Y").date()
    reader = LedgerReader(parties, mutual_income_strings=mutual_income_strings, first_period=first_period_date)
    payments = reader.parse_csv("test_payments.csv")

    print(payments)

    ledger_processor.process_payments(payments)
    schedule = ledger_processor.get_tables(TableType.SIDELOAN)

    for name, table in schedule.items():
        print(f"Table for {name}")
        table.print_summary()

    # Print amortization schedules after processing
