from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from catalog.services.image_service import validate_image


class UploadTests(SimpleTestCase):
    def test_rejects_non_image(self):
        f = SimpleUploadedFile(
            "x.svg",
            b"<svg><script>alert(1)</script></svg>",
            content_type="image/svg+xml",
        )
        with self.assertRaises(ValidationError):
            validate_image(f)
