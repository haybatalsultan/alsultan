#!/usr/bin/env python
import os
import sys


def main():
    # Keep local development as the default, but make the standard Django
    # test command deterministic and independent from the production
    # WhiteNoise manifest. An explicit --settings value always wins.
    has_explicit_settings = any(
        arg == "--settings" or arg.startswith("--settings=") for arg in sys.argv[1:]
    )
    is_test_command = len(sys.argv) > 1 and sys.argv[1] == "test"

    if is_test_command and not has_explicit_settings:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
