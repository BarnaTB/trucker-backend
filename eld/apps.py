from django.apps import AppConfig


class EldConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eld'

    def ready(self):
        import eld.signals
