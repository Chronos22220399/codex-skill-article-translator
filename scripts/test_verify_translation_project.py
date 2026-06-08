#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import verify_translation_project as verifier


class VerifyTranslationProjectTests(unittest.TestCase):
    def write_project(self, project_dir, alignment, html):
        (project_dir / "alignment.json").write_text(
            json.dumps(alignment, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (project_dir / "translation-reading.html").write_text(html, encoding="utf-8")
        figure_dir = project_dir / "assets" / "figures"
        figure_dir.mkdir(parents=True)
        (figure_dir / "fig-1.png").write_bytes(b"fake image bytes")

    def test_accepts_renderable_source_left_equation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            self.write_project(
                project_dir,
                [
                    {
                        "id": "eq-001",
                        "section": "1. Test",
                        "type": "equation",
                        "source_ids": ["eq-001"],
                        "translation_ids": ["zh-eq-001"],
                        "source": "$$E=mc^2\\tag{1}$$",
                        "translation": ["$$E=mc^2\\tag{1}$$"],
                        "notes": "",
                    }
                ],
                """
                <html>
                <head>
                <script>
                window.MathJax = { tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] } };
                </script>
                </head>
                <body>
                  <a class="term" href="#term-structure-factor">structure factor</a>
                  <aside id="term-structure-factor">structure factor（结构因子）：测试解释。</aside>
                  <img src="assets/figures/fig-1.png">
                  <div id="pair-eq-001" class="align-pair">
                    <div class="source-left">$$E=mc^2\\tag{1}$$</div>
                    <div class="translation-right">$$E=mc^2\\tag{1}$$</div>
                  </div>
                </body>
                </html>
                """,
            )

            errors = verifier.verify_project(project_dir)

        self.assertEqual([], errors)

    def test_rejects_prose_placeholder_equation_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            self.write_project(
                project_dir,
                [
                    {
                        "id": "eq-002",
                        "section": "1. Test",
                        "type": "equation",
                        "source_ids": ["eq-002"],
                        "translation_ids": ["zh-eq-002"],
                        "source": "Definitions of the angular-averaged formulas.",
                        "translation": ["$$S(k)=0$$"],
                        "notes": "",
                    }
                ],
                """
                <html>
                <head>
                <script>
                window.MathJax = { tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] } };
                </script>
                </head>
                <body>
                  <div id="pair-eq-002" class="align-pair">
                    <div class="source-left">Definitions of the angular-averaged formulas.</div>
                    <div class="translation-right">$$S(k)=0$$</div>
                  </div>
                </body>
                </html>
                """,
            )

            errors = verifier.verify_project(project_dir)

        self.assertTrue(
            any("placeholder" in error.lower() for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
