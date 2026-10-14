from pathlib import Path

import json

import pytest

from scripts.data_reader import cli


def test_cli_no_actions_shows_message(capsys):
    exit_code = cli.main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Nenhuma etapa" in captured.out


def test_cli_convert_invokes_conversion(monkeypatch, tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    images_dir = tmp_path / "images"

    called = {}

    monkeypatch.setattr(cli, "ensure_default_directories", lambda: None)

    def fake_convert(raw, images, dpi):
        called["raw"] = raw
        called["images"] = images
        called["dpi"] = dpi

    monkeypatch.setattr(cli, "convert_pdfs_to_images", fake_convert)

    exit_code = cli.main(
        [
            "--convert",
            "--raw-dir",
            str(raw_dir),
            "--images-dir",
            str(images_dir),
            "--organized-dir",
            str(tmp_path / "organized"),
            "--dpi",
            "200",
        ]
    )

    assert exit_code == 0
    assert called["raw"] == raw_dir.resolve()
    assert called["images"] == images_dir.resolve()
    assert called["dpi"] == 200


def test_cli_stats_prints_counts(monkeypatch, tmp_path: Path, capsys):
    organized_dir = tmp_path / "organized"
    organized_dir.mkdir()

    monkeypatch.setattr(cli, "ensure_default_directories", lambda: None)
    monkeypatch.setattr(cli, "count_reports_by_company", lambda path: {"A": 3, "B": 1})
    monkeypatch.setattr(cli, "find_companies_below_threshold", lambda counts, minimum: {"B": 1})

    exit_code = cli.main([
        "--stats",
        "--organized-dir",
        str(organized_dir),
        "--images-dir",
        str(tmp_path / "images"),
        "--raw-dir",
        str(tmp_path / "raw"),
        "--min-reports",
        "2",
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "A: 3" in captured.out
    assert "Empresas abaixo do mínimo" in captured.out


def test_cli_annotate_uses_custom_configs(monkeypatch, tmp_path: Path):
    organized_dir = tmp_path / "organized"
    organized_dir.mkdir()

    variables_file = tmp_path / "variables.json"
    variables_file.write_text(json.dumps(["campo1", "campo2"]), encoding="utf-8")

    limits_file = tmp_path / "limits.json"
    limits_file.write_text(json.dumps({"Empresa": 1}), encoding="utf-8")

    captured_args = {}

    def fake_annotate(base_dir, variables, limits):
        captured_args["base"] = base_dir
        captured_args["variables"] = variables
        captured_args["limits"] = limits

    monkeypatch.setattr(cli, "ensure_default_directories", lambda: None)
    monkeypatch.setattr(cli, "annotate_companies", fake_annotate)

    exit_code = cli.main([
        "--annotate",
        "--organized-dir",
        str(organized_dir),
        "--images-dir",
        str(tmp_path / "images"),
        "--raw-dir",
        str(tmp_path / "raw"),
        "--variables-file",
        str(variables_file),
        "--limits-file",
        str(limits_file),
    ])

    assert exit_code == 0
    assert captured_args["base"] == organized_dir.resolve()
    assert captured_args["variables"] == ["campo1", "campo2"]
    assert captured_args["limits"] == {"Empresa": 1}


def test_cli_dataset_invokes_builder(monkeypatch, tmp_path: Path):
    organized_dir = tmp_path / "organized"
    organized_dir.mkdir()

    captured = {}

    monkeypatch.setattr(cli, "ensure_default_directories", lambda: None)

    def fake_build(dir_path, iou_threshold, use_center):
        captured["dir"] = dir_path
        captured["iou"] = iou_threshold
        captured["center"] = use_center

    monkeypatch.setattr(cli, "build_dataset_from_reports", fake_build)

    exit_code = cli.main([
        "--dataset",
        "--organized-dir",
        str(organized_dir),
        "--images-dir",
        str(tmp_path / "images"),
        "--raw-dir",
        str(tmp_path / "raw"),
        "--iou-threshold",
        "0.7",
        "--use-center",
    ])

    assert exit_code == 0
    assert captured["dir"] == organized_dir.resolve()
    assert captured["iou"] == 0.7
    assert captured["center"] is True
