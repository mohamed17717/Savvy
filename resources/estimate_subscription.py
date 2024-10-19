def total(**kwargs):
    return sum(kwargs.values())


class SubscriptionEstimator:
    INVOICES = dict(
        # first time to setup the thing
        SetupStart=total(
            domain=200,
            Server=25,
        ),
        # every month
        Monthly=total(
            server=25,
            proxy=20,
            storage=20,
            cloud_flare=10,
            chat_gpt=1000,
            database=50,
        ),
        # maybe paid or not
        MonthlyMaybe=total(
            marketing=200,
            free_users=100,
        ),
        # every year
        AnnualStartSecondYear=total(domain=150),
        # Just one time
        OneTime=total(
            backend=0, pre_stage_paid=150, company_papers=400, ext_for_google=5
        ),
    )

    def __init__(self, price):
        self.price = price

    def taxes(self, net, force=True):
        return 0.2 * net if net >= 100_000 or force else 0

    def monthly_net_per_user(self):
        net = self.price
        net -= total(
            payment_gateway=2.9 / 100 * self.price + 0.30,
            chat_gpt=2,  # 100_000 token in / 100_000 token out
            operating=0.20,
        )
        net -= self.taxes(net, force=True)
        return net


price = 5
# for price in range(1, 20):
net = SubscriptionEstimator(price).monthly_net_per_user()
print(f"{price=}, {net=:.2f}, percent={net / price * 100:.2f}%")
