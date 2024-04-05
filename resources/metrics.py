from datetime import timedelta, datetime

def retention_rate(start, end):
    '''Rate of losing users'''

    users = User.objects.filter(created_at__date__gte=start, created_at__date__lt=end)
    total = users.count()
    lost_users = users.filter(is_active=False).count()
    retention_rate = (total - lost_users) / total * 100
    return retention_rate

def traffic_to_lead(start, end, channel=None):
    '''Rate of traffic to leads'''
    unique_visits = Visit.objects.filter(
        user__isnull=True, # anonymous users
        created_at__date__gte=start, 
        created_at__date__lt=end,
    ).values('sessionid').distinct().count()
    users = User.objects.filter(created_at__date__gte=start, created_at__date__lt=end).count()

    return unique_visits / users

def lead_to_customer(start, end):
    '''Rate of leads to customers'''
    users = User.objects.filter(created_at__date__gte=start, created_at__date__lt=end).count()
    subscriptions = Subscription.objects.filter(created_at__date__gte=start, created_at__date__lt=end).count()

    return users / subscriptions

def churn_rate(start, howlong: timedelta):
    '''Rate of losing users'''
    users = User.objects.all()
    total = users.count()

    break_point = datetime.utcnow() - howlong
    lost_users = users.filter(last_login__date__gte=start, last_login__date__lt=break_point).count()

    return lost_users / total * 100

def monthly_recurring_revenue():
    '''Monthly recurring revenue'''
    subscriptions = Subscription.objects.filter(is_active=True)
    revenue = subscriptions.aggregate(Sum('amount'))['amount__sum']
    return revenue

