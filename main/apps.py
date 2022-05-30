from django.apps import AppConfig
from django.dispatch import Signal
from .utilities import send_activation_notification
user_registrated = Signal(providing_args=['instance'])

def user_registrated_dispatcher(sender, **kwargs):
    send_activation_notification(kwargs['instance'])

user_registrated.connect(user_registrated_dispatcher)



class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    verbose_name='Доска объявлений'
