"""SettingsDialog round-trips every field, including the new HF-mirror toggle."""

from furniture_cutout import settings as settings_mod
from furniture_cutout.settings import Settings, SettingsDialog


def test_dialog_roundtrips_hf_mirror_true(qapp):
    dlg = SettingsDialog(Settings(hf_mirror=True))
    assert dlg.get_settings().hf_mirror is True


def test_dialog_roundtrips_hf_mirror_false(qapp):
    dlg = SettingsDialog(Settings(hf_mirror=False))
    assert dlg.get_settings().hf_mirror is False


def test_dialog_preserves_other_fields(qapp):
    src = Settings(box_pad_ratio=0.1, cpu_threads=4, save_alpha=True, hf_mirror=False)
    out = SettingsDialog(src).get_settings()
    assert out.box_pad_ratio == 0.1
    assert out.cpu_threads == 4
    assert out.save_alpha is True
    assert out.hf_mirror is False


def test_save_load_roundtrip_includes_hf_mirror(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(settings_mod, "CONFIG_PATH", str(cfg))
    settings_mod.save(Settings(hf_mirror=False, cpu_threads=3))
    loaded = settings_mod.load()
    assert loaded.hf_mirror is False
    assert loaded.cpu_threads == 3
