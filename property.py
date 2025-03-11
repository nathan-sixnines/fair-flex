from mortgageslice import MortgageSlice
from stake import Stake
from common import Parties, Party, Payment, LoanInfo


class PropertyParams:
    def __init__(
        self,
        purchase_cost: float,
        purchase_down_payment: float,
        loan_info: LoanInfo,
        stakeholders: list[Party],
        stakeholder_down_payments: dict[str, float] = None,
    ):
        self.purchase_cost = purchase_cost
        self.purchase_down_payment = purchase_down_payment
        self.loan_info = loan_info
        self.stakeholders = stakeholders
        self.stakeholder_down_payments = stakeholder_down_payments if stakeholder_down_payments else {}


# there are two sources of truth for down payments
# 1: The total purchase down payment submitted on the house to reduce the loan size 
# 2: The sum of recorded stakeholder indivdual payments either included in the
#     stakeholder down payments dictionary, or in the ledger before period 1
# Multiple sources of truth cannot be avoided in code here because both sources
# of information exist in reality. But the code can check for consistency between them
# TODO: check for consistency between them

class Property:
    def __init__(self, params: PropertyParams):
        """
        Initializes a mortgage with multiple stakeholders, distributing the loan proportionally.

        :param params: PropertyParams object containing configuration details.
        """
        self.stakeholders = {
            party.name: party for party in set(params.stakeholders) if party.type != "Common Party"
        }

        self.common_fund = Party("Common Fund", "Common Party")
        self.parties = {
            name: Parties(self.stakeholders[name], self.common_fund)
            for name in self.stakeholders
        }

        stake_value = params.purchase_cost / len(self.stakeholders)
        stake_debt = (params.purchase_cost - params.purchase_down_payment) / len(self.stakeholders)

        self.loan_info = params.loan_info

        self.stakes = {
            stakeholders: Stake(
                baseline_value=stake_value,
                loan_principal=stake_debt,
                parties=self.parties[stakeholders],
                mortgage_info=self.loan_info,
            )
            for stakeholders in self.stakeholders
        }

        self.mortgage_slices = {
            name: stake.mortgage_slice for name, stake in self.stakes.items()
        }

        # Process down payments
        for name, amount in params.stakeholder_down_payments.items():
            if name in self.mortgage_slices:
                payment = Payment(
                    amount, self.stakeholders[name], self.common_fund, period=0
                )
                self.mortgage_slices[name].accept_payment(payment)

    def accept_payment(self, stakeholder: Party, amount: float, period: int):
        """Accepts a payment from a stakeholder toward their obligation."""
        if stakeholder.name not in self.mortgage_slices:
            raise ValueError(f"Unknown stakeholder: {stakeholder}")
        payment = Payment(
            amount, self.stakeholders[stakeholder.name], self.common_fund, period
        )
        print(f"accepting payment for {stakeholder}")
        self.mortgage_slices[stakeholder.name].accept_payment(payment)

    def advance_period(self):
        """Advances all obligations by one period."""
        print('advancing period')
        for mortgage_slice in self.mortgage_slices.values():
            mortgage_slice.advance_period()

    def get_amortization_schedule(self, tabletype):
        """Returns the amortization schedules for all stakeholders."""
        return {
            name: mortgage_slice.get_amortization_schedule(tabletype)
            for name, mortgage_slice in self.mortgage_slices.items()
        }

    def total_stake_allocated(self):
        """Returns the total stake allocated across all stakeholders."""
        return sum(
            stake.obligation.loan.loan_info.principal for stake in self.stakes.values()
        )
