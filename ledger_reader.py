import csv
import datetime
from typing import List
from common import Party, Payment
import math

def months_between(start_date: datetime, end_date: datetime) -> int:
    """Returns the number of months between two datetime objects."""
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

class LedgerReader:
    def __init__(self, parties: List[Party], mutual_income_strings, first_period):
        self.parties = parties
        self.common_party = Party(name="Common Account", type="Common Party")
        self.first_period = first_period
        self.mutual_income_strings = mutual_income_strings
        print(self.parties)

    def parse_csv(self, file_path: str) -> List[Payment]:
        payments = []

        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(
                csvfile, delimiter="\t"
            )  # Assuming tab-separated values

            for row in reader:
                print(row)

                if len(row) < 4:
                    print(f"skipping {row}")
                    continue  # Skip malformed rows

                date_str, description, amount_str, balance_str = row
                #if("CHK 5622".lower() in description.lower()):
                #    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


                try:
                    transaction_date = datetime.datetime.strptime(date_str, "%m/%d/%Y").date()
                    amount_str = amount_str.replace(',','')
                    amount = float(amount_str)
                except ValueError as e:
                    print(f"skipping {row} because of {e}")
                    continue

                period = months_between(self.first_period, transaction_date) + 1 # Assuming period is the month of the transaction

                sender = self.identify_sender(description, amount)

                if sender:
                    payment = Payment(amount, sender, self.common_party, period, date_str)
                    payments.append(payment)

                mutual_income = False

                for marker_string in self.mutual_income_strings:
                    if marker_string.lower() in description.lower():
                        mutual_income = True

                if mutual_income and sender:
                    raise Exception(f"transaction marked from {sender} also flagged as mutual income")
                
                # todo: need stake class involved here
                if mutual_income:
                    number_mutual_parties = len(self.parties)
                    for party in self.parties:
                        payment = Payment(amount/ number_mutual_parties, party, self.common_party, period, date_str)
                        payments.append(payment)


        return payments

    def identify_sender(self, description: str, amount: float) -> Party:
        identified_senders = []

        for party in self.parties:
            excluded = False
            for ledger_exclusion in party.ledger_exclusions:
                if ledger_exclusion.lower() in description.lower():
                    excluded = True
            match = False
            for ledger_string in party.ledger_strings:
                if ledger_string.lower() in description.lower():
                    match = True
            if match and party.exclusion_amount:
                if abs(amount) < party.exclusion_amount:
                    excluded = True
            if match and not excluded:
                identified_senders.append(party)

        if len(identified_senders) > 1:
            raise Exception(
                f"Transaction {description} matched multiple senders, {identified_senders}"
            )

        if len(identified_senders) == 1:
            return identified_senders[0]

        return None


if __name__ == "__main__":
    # Define parties with their matching strings
    parties = [
        # Example:
        # Party(name="Bank of America", ledger_strings=["BANK OF AMERIC"], type="Bank"),
        # Party(name="Venmo", ledger_strings=["VENMO*"], type="Service"),
        # Common party
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

    mutual_income_strings = ["airbnb"]
    #print(parties[1:])
    #exit()
    first_period_date = datetime.datetime.strptime("01/16/2023", "%m/%d/%Y").date()
    reader = LedgerReader(parties, mutual_income_strings = mutual_income_strings, first_period=first_period_date)
    payments = reader.parse_csv("test_payments.csv")

    for payment in payments:
        print(payment)
