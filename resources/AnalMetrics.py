
subscription_price = 10

one_time_pay = {
    'backend': 0,
    'frontend': 150,
    'company papers': 180,
}

monthly_pay_for_1000_users = {
    'server': 5.5,
    'proxy': 5,
    'marketing/ads': 70,
}

pay_for_1_user = {
    'payment gateway': 2.99/100 * subscription_price + 0.3
}

budget = ...
real_pay = {
    'frontend': [50],
    'server_contabo': [11]
}


def pr(x, cost_per_month, users=1000):
    import numpy as np
    cost = x * 2.9 / 100 + 0.30
    monthly_per_user = cost_per_month / users
    revenue = x - cost - monthly_per_user
    taxes = 0
    if revenue > 0:
        taxes = revenue * 20 / 100
    return np.array([revenue - taxes, cost, monthly_per_user, taxes])


pr(12, 2500, users := 1000) * users * 12
pr(12, 5_000, users := 10_000) * users * 12
r = pr(12, 20_000, users := 100_000) * users * 12
r = pr(12, 30_000, users := 1_000_000) * users * 12
print(r, f'{r[0] / sum(r) * 100:.2f}%', sep='\n')

pr(12, 1000, users := 1000) * users * 12
