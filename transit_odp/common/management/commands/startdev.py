import os
import subprocess
import threading

from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunServerCommand,
)
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV


class Command(RunServerCommand):
    """This command removes the need for two terminal windows when running runserver."""

    help = (
        "Starts a lightweight Web server for development and also serves static files. "
        "Also runs a webpack build worker in another thread."
    )

    def run(self, **options):
        """Run the server with webpack in the background."""
        if os.environ.get(DJANGO_AUTORELOAD_ENV) != "true":
            self.stdout.write("Starting webpack build thread.")
            command = "npm run start"
            kwargs = {"shell": True}
            webpack_thread = threading.Thread(
                target=subprocess.run, args=(command,), kwargs=kwargs
            )
            webpack_thread.start()

        super(Command, self).run(**options)
