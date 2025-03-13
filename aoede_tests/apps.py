from django.apps import AppConfig


class AoedeTestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aoede_tests'
    verbose_name = 'Aoede Test Suite'

    def ready(self):
        """
        Initialize app-specific configurations when the app is ready.
        This is a good place to set up logging, import signals, etc.
        """
        import logging
        
        # Configure logging for the test suite
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Create console handler with custom formatter
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
