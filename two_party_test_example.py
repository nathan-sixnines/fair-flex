from property import Property, PropertyParams
from common import Payment, Party, LoanInfo
from datetime import datetime
from ledger_reader import LedgerReader
from ledger_processor import LedgerProcessor
from loan import TableType

if __name__ == "__main__":
    # Define stakeholders
    alice = Party("Alice", ledger_strings=["Alice Mortgage Payment"])
    bob = Party("Bob", ledger_strings=["Bob Loan Repayment"])

    parties = [
        Party(
            name="Alice",
            type="Stakeholder",
            ledger_strings=["alice"],
        ),
        Party(
            name="Bob",
            type="Stakeholder",
            ledger_strings=["bob"],
        ),
    ]


    # Sample setup
    params = PropertyParams(
        purchase_cost=550_000,
        purchase_down_payment=120_000,
        loan_info=LoanInfo(annual_rate=0.06, total_periods=360),
        stakeholders=parties,
        stakeholder_down_payments={},
    )

    property_instance = Property(params)
    ledger_processor = LedgerProcessor(property_instance)

    # Sample payments
    first_period_date = datetime.strptime("03/01/2025", "%m/%d/%Y").date()
    reader = LedgerReader(parties, mutual_income_strings=[], first_period=first_period_date)
    payments = reader.parse_csv("two_party_test_example.csv")

    print(payments)

    ledger_processor.process_payments(payments)
    ledger_processor.advance_period()


    schedule = ledger_processor.get_tables(TableType.SIDELOAN)

    for name, table in schedule.items():
        print(f"Table for {name}")
        table.print_summary()

    exit()

    schedule = ledger_processor.get_tables(TableType.BASELINE)

    for name, table in schedule.items():
        print(f"Table for {name}")
        table.print_summary()

    schedule = ledger_processor.get_tables(TableType.FULL)

    for name, table in schedule.items():
        print(f"Table for {name}")
        table.print_summary()
