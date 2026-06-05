"""
Core app configuration for VETA Connect
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for core utilities app"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Utilities'
    
    def ready(self):
        """
        Perform initialization when app is ready
        """
        # Import signals if any
        try:
            from . import signals
        except ImportError:
            pass
