from pathlib import Path
import tomllib


def test_runtime_dependencies_include_email_validation():
    pyproject = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = pyproject["project"]["dependencies"]

    assert any(item.startswith("email-validator") for item in dependencies)
