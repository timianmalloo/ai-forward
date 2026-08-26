import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "pack" / "scripts"
XAML_LINT = SCRIPTS / "xaml-token-lint.py"
UI_DESIGN = REPO / "pack" / "commands" / "ui-design" / "SKILL.md"
VISUALIZE = REPO / "pack" / "commands" / "visualize" / "SKILL.md"
UI_CRAFT = REPO / "pack" / "knowledge" / "ui-design-craft.md"
UI_VISUAL_ASSETS = REPO / "pack" / "knowledge" / "ui-visual-assets.md"
CATALOG = REPO / "pack" / "knowledge" / "ui-archetype-catalog.md"
TEMPLATE = REPO / "pack" / "templates" / "native-ui-proof-pack.template.md"
COPILOT_PROMPT = REPO / "pack" / "adapters" / "copilot" / "prompts" / "ui-design.prompt.md"
CAPABILITY_GUIDE = REPO / "pack" / "templates" / "ui-capability-guide.template.html"


def run_lint(root, *paths, fmt="text"):
    return subprocess.run(
        [
            sys.executable,
            str(XAML_LINT),
            "--root",
            str(root),
            "--format",
            fmt,
            *[str(path) for path in paths],
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


class XamlTokenLintTests(unittest.TestCase):
    def test_clean_resource_bound_xaml_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "MainWindow.xaml"
            target.write_text(
                textwrap.dedent(
                    """
                    <Window>
                      <Grid Background="{DynamicResource SurfaceBrush}"
                            Margin="{StaticResource SpaceMd}">
                        <TextBlock FontSize="{StaticResource BodyFontSize}" />
                      </Grid>
                    </Window>
                    """
                ),
                encoding="utf-8",
            )

            result = run_lint(root, target)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_raw_color_brush_and_dimension_are_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "Bad.xaml"
            target.write_text(
                textwrap.dedent(
                    """
                    <Window>
                      <Grid Background="#FF0067B8" Margin="12,8">
                        <SolidColorBrush Color="Red" />
                        <TextBlock FontSize="13" />
                      </Grid>
                    </Window>
                    """
                ),
                encoding="utf-8",
            )

            result = run_lint(root, target, fmt="json")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            findings = json.loads(result.stdout)
            rules = {finding["rule"] for finding in findings}
            self.assertIn("xaml-raw-color", rules)
            self.assertIn("xaml-raw-brush", rules)
            self.assertIn("xaml-raw-dimension", rules)

    def test_single_quoted_named_and_argb_colors_are_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "SingleQuoted.xaml"
            target.write_text(
                "<Window><Grid Background='Red' Foreground='#f123' Margin='12,8' /></Window>",
                encoding="utf-8",
            )

            result = run_lint(root, target, fmt="json")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            findings = json.loads(result.stdout)
            rules = [finding["rule"] for finding in findings]
            self.assertGreaterEqual(rules.count("xaml-raw-color"), 2)
            self.assertIn("xaml-raw-dimension", rules)

    def test_non_primary_named_colors_are_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "NamedColors.xaml"
            target.write_text(
                '<Window><Grid Background="AliceBlue" Foreground="Cyan" /></Window>',
                encoding="utf-8",
            )

            result = run_lint(root, target, fmt="json")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            findings = json.loads(result.stdout)
            self.assertEqual(2, sum(1 for finding in findings if finding["rule"] == "xaml-raw-color"))

    def test_json_output_does_not_echo_source_snippets_or_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "Secret.xaml"
            target.write_text(
                '<Window DataContext="SECRET_SHOULD_NOT_LOG" Background="#fff" />',
                encoding="utf-8",
            )

            result = run_lint(root, target, fmt="json")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("SECRET_SHOULD_NOT_LOG", result.stdout + result.stderr)
            findings = json.loads(result.stdout)
            self.assertNotIn("snippet", findings[0])
            self.assertEqual("Background", findings[0]["attribute"])

    def test_malformed_and_large_markup_do_not_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "Malformed.axaml"
            target.write_text("<Window " + ("x" * 10000) + ' Background="#fff">', encoding="utf-8")

            result = run_lint(root, target)

            self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_path_outside_root_is_error_not_scan(self):
        with tempfile.TemporaryDirectory() as root_temp, tempfile.TemporaryDirectory() as outside_temp:
            root = Path(root_temp)
            outside = Path(outside_temp) / "Outside.xaml"
            outside.write_text('<Window Background="#fff" />', encoding="utf-8")

            result = run_lint(root, outside)

            self.assertEqual(result.returncode, 2)
            self.assertIn("outside root", result.stderr + result.stdout)

    def test_directory_symlink_or_junction_outside_root_is_not_scanned(self):
        with tempfile.TemporaryDirectory() as root_temp, tempfile.TemporaryDirectory() as outside_temp:
            root = Path(root_temp)
            outside = Path(outside_temp)
            secret = outside / "Secret.xaml"
            secret.write_text('<Window Background="#FF0067B8">SECRET_TOKEN</Window>', encoding="utf-8")
            link = root / "linked"
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                else:
                    os.symlink(outside, link, target_is_directory=True)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest("symlink/junction creation unavailable")

            result = run_lint(root, root, fmt="json")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SECRET_TOKEN", result.stdout + result.stderr)


class NativeUiContractTextTests(unittest.TestCase):
    def test_native_proof_pack_template_has_required_columns_and_frameworks(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for required in [
            "claim",
            "failing input or condition",
            "oracle",
            "evidence",
            "red observed",
            "confidence",
            "residual risk",
            "WPF / WinUI",
            "Avalonia",
            "Blazor Hybrid",
            "signing",
        ]:
            self.assertIn(required, text)
        required_claims = [
            "Keyboard traversal works",
            "Accessibility tree is correct",
            "DPI/windowing works",
            "Distribution trust is handled",
            "UI Automation metadata is exposed",
            "Native shell and WebView focus hand off correctly",
        ]
        for claim in required_claims:
            self.assertIn(claim, text)

    def test_ui_design_native_trigger_contract_is_behavioral_not_visual_only(self):
        text = UI_DESIGN.read_text(encoding="utf-8")
        for required in [
            "native-ui-proof-pack.template.md",
            "medium declaration",
            "WPF",
            "WinUI",
            "Avalonia",
            "Blazor Hybrid",
            "HTML mockup",
            "native PASS",
            "Accessibility Insights",
        ]:
            self.assertIn(required, text)

    def test_copilot_prompt_and_capability_guide_include_native_proof_contract(self):
        for path in (COPILOT_PROMPT, CAPABILITY_GUIDE):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("WPF", text)
                self.assertIn("WinUI", text)
                self.assertIn("Avalonia", text)
                self.assertIn("Blazor Hybrid", text)
                self.assertIn("native proof", text)
                self.assertIn("native PASS", text)

    def test_visualize_rejects_generated_native_interface_but_allows_native_assets(self):
        text = VISUALIZE.read_text(encoding="utf-8")
        for required in [
            "native app",
            "generated interface",
            "WPF settings window",
            "control panel",
            "review harness",
            "fictional",
        ]:
            self.assertIn(required, text)

    def test_native_archetype_rows_are_catalog_shaped(self):
        text = CATALOG.read_text(encoding="utf-8")
        for archetype in [
            "Windows Fluent Utility Shell",
            "Native File/Object Workbench",
            "Cross-Platform XAML / Blazor Hybrid Workbench",
        ]:
            self.assertIn(archetype, text)
        for required in ["**Signature:**", "**Description:**", "**Codegen descriptor:**"]:
            self.assertIn(required, text)
        self.assertIn('x-framework:"winui-or-wpf"', text)
        self.assertIn('x-framework:"avalonia-or-blazor-hybrid"', text)

    def test_exemplar_policy_labels_reference_only_repos(self):
        text = UI_CRAFT.read_text(encoding="utf-8")
        self.assertIn("microsoft/WinUI-Gallery", text)
        self.assertIn("MIT", text)
        self.assertIn("File-New-Project/EarTrumpet", text)
        self.assertIn("Flagged/non-standard", text)
        self.assertIn("rocksdanister/lively", text)
        self.assertIn("GPL-3.0", text)
        self.assertIn("reference-only", text)

    def test_visual_assets_native_note_preserves_no_generated_interface_rule(self):
        text = UI_VISUAL_ASSETS.read_text(encoding="utf-8")
        self.assertIn("native client", text)
        self.assertIn("may populate", text)
        self.assertIn("must not replace", text)
        self.assertIn("native XAML", text)


if __name__ == "__main__":
    unittest.main()
