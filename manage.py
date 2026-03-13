#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    import sys
    if "test" in sys.argv:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django topilmadi. Virtual muhit faollashtirilganmi?"
        ) from exc
    execute_from_command_line(sys.argv)
