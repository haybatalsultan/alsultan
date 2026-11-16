from pathlib import Path

from django.template import engines
from django.test import SimpleTestCase


class TemplateCompilationV20833Fix3Tests(SimpleTestCase):
    def test_all_project_templates_compile(self):
        root = Path(__file__).resolve().parents[1] / "templates"
        engine = engines["django"].engine
        failures = []
        for path in root.rglob("*.html"):
            try:
                engine.from_string(path.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(f"{path.relative_to(root)}: {exc}")
        self.assertEqual(failures, [], "\n".join(failures))
