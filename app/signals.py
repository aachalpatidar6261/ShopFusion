from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from django.conf import settings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_signals_for_user(sender, instance, created, **kwargs):
    print("i am in created function")
    if created:
        print("i am in created function in signls file")
        User.objects.create(user=instance)