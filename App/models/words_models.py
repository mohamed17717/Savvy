from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()



class DocumentWordWeight(models.Model):
    # Relations
    # TODO in future -> this field become generic relation
    # to relate with (bookmark / youtube / linkedin / etc...)
    document = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='words_weights')

    # Required
    # TODO make it 64 when cleaner work fine
    word = models.CharField(max_length=2048)
    weight = models.PositiveSmallIntegerField()

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
