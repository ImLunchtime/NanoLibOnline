from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        try:
            import users.signals
            from django.db.models.signals import post_save
            from django.contrib.auth.models import User
            
            # Disconnect any existing receivers
            post_save.receivers.clear()
            
            # Import signals to register new receivers
            from . import signals
        except:
            pass
