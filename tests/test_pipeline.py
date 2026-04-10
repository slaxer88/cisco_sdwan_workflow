from pathlib import Path

from pipeline.validate import run_validation


def test_validation_passes_on_sample_configs():
    config_dir = Path(__file__).parent.parent / "configs"
    assert run_validation(config_dir) is True


def test_validation_catches_bad_yaml(tmp_path):
    bad_file = tmp_path / "bad_template.yaml"
    bad_file.write_text("feature_templates:\n  - name: invalid name with spaces\n    bad_indent")

    result = run_validation(tmp_path)
    assert result is False
