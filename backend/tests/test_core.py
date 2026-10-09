import pandas as pd
import pytest

from app.ml.features import ParseError, align, parse_upload, parse_event_log
from app.ml.fusion import DEFAULT_CONFIG, classify, fuse, validate_config

CFG = validate_config(DEFAULT_CONFIG)


def test_formula_matches_spec():
    r = fuse(0.9, 0.8, CFG)
    assert r["risk"] == pytest.approx(0.6 * 0.9 + 0.4 * 0.8)
    assert r["label"] == "Ransomware" and r["threat_level"] == "Critical"


@pytest.mark.parametrize("risk,label", [(0.0, "Benign"), (0.399, "Benign"), (0.40, "Suspicious"), (0.799, "Suspicious"), (0.80, "Ransomware"), (1.0, "Ransomware")])
def test_thresholds(risk, label):
    assert classify(risk, CFG)[0] == label


def test_orange_band_is_high():
    assert classify(0.7, CFG) == ("Suspicious", "High") and classify(0.5, CFG) == ("Suspicious", "Medium")


def test_single_model_uses_available_score():
    r = fuse(None, 0.9, CFG)
    assert r["risk"] == pytest.approx(0.9) and r["single_model"]


def test_config_validation():
    with pytest.raises(ValueError):
        validate_config({"t_suspicious": 0.9, "t_ransomware": 0.5})
    c = validate_config({"w_static": 3, "w_behavior": 1})
    assert c["w_static"] == pytest.approx(0.75)


def test_event_log_features():
    log = "\n".join([
        "EventID: 1 Image: C:\\x\\a.exe CommandLine: vssadmin delete shadows /all /quiet",
        "EventID: 11 Image: C:\\x\\a.exe TargetFilename: C:\\Users\\u\\doc1.docx.locked",
        "EventID: 11 Image: C:\\x\\a.exe TargetFilename: C:\\Users\\u\\README_DECRYPT.txt",
        "EventID: 13 Image: C:\\x\\a.exe TargetObject: HKLM\\Run",
        "EventID: 3 Image: C:\\x\\a.exe DestinationIp: 10.1.1.9",
    ])
    row = parse_event_log(log).iloc[0]
    assert row.shadow_copy_cmd_count == 1 and row.ransom_extension_count == 1 and row.ransom_note_count == 1
    assert row.registry_mod_count == 1 and row.network_conn_count == 1


def test_upload_rejects_binary_and_unknown(tmp_path):
    b = tmp_path / "x.csv"; b.write_bytes(b"MZ\x90\x00\x03" + b"\x00" * 100)
    with pytest.raises(ParseError):
        parse_upload(b, "csv")
    with pytest.raises(ParseError):
        parse_upload(b, "exe")


def test_csv_alignment_case_insensitive(tmp_path):
    p = tmp_path / "s.csv"; p.write_text("numberofsections,SizeOfCode,junk\n5,100,x\n")
    df = parse_upload(p, "csv")
    X, cov = align(df, ["NumberOfSections", "SizeOfCode", "Missing", "Other"])
    assert cov == 0.5 and X["NumberOfSections"].iloc[0] == 5 and X["Missing"].isna().all()


def test_event_fields_do_not_bleed_into_each_other():
    log = "\n".join(f"EventID: 11 Image: C:\\Program Files\\App\\a.exe TargetFilename: C:\\Users\\u\\f{i}.locked" for i in range(5))
    row = parse_event_log(log).iloc[0]
    assert row.unique_processes == 1 and row.ransom_extension_count == 5
