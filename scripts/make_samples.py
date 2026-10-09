"""Create sample upload files (matching the demo schema) in sample_data/. Needs only pandas + numpy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.ml.features import BEHAVIOR_FEATURES, STATIC_FEATURES  # noqa: E402
from app.ml.synthetic import synthetic  # noqa: E402

out = Path(__file__).resolve().parents[1] / "sample_data"
out.mkdir(exist_ok=True)
for name, feats in (("static", STATIC_FEATURES), ("behavior", BEHAVIOR_FEATURES)):
    df = synthetic(feats, n=400, seed=123)
    df[df.Label == "benign"].drop(columns="Label").head(5).to_csv(out / f"{name}_benign_sample.csv", index=False)
    df[df.Label == "ransomware"].drop(columns="Label").head(5).to_csv(out / f"{name}_ransomware_sample.csv", index=False)

(out / "sysmon_ransomware_sample.log").write_text("\n".join(
    ["EventID: 1 Image: C:\\Users\\victim\\AppData\\Local\\Temp\\upd.exe CommandLine: vssadmin delete shadows /all /quiet",
     "EventID: 1 Image: C:\\Windows\\System32\\cmd.exe CommandLine: bcdedit /set {default} recoveryenabled no",
     "EventID: 1 Image: C:\\Windows\\System32\\powershell.exe CommandLine: powershell -enc SQBFAFgA..."]
    + [f"EventID: 11 Image: C:\\Users\\victim\\AppData\\Local\\Temp\\upd.exe TargetFilename: C:\\Users\\victim\\Documents\\file{i}.docx.locked" for i in range(120)]
    + ["EventID: 11 Image: C:\\Users\\victim\\AppData\\Local\\Temp\\upd.exe TargetFilename: C:\\Users\\victim\\Desktop\\README_DECRYPT.txt",
       "EventID: 13 Image: C:\\Users\\victim\\AppData\\Local\\Temp\\upd.exe TargetObject: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\upd",
       "EventID: 3 Image: C:\\Users\\victim\\AppData\\Local\\Temp\\upd.exe DestinationIp: 185.220.101.4"]))
(out / "sysmon_benign_sample.log").write_text("\n".join(
    ["EventID: 1 Image: C:\\Windows\\explorer.exe CommandLine: explorer.exe", "EventID: 1 Image: C:\\Program Files\\Notepad++\\notepad++.exe CommandLine: notepad++.exe",
     "EventID: 11 Image: C:\\Program Files\\Notepad++\\notepad++.exe TargetFilename: C:\\Users\\user\\Documents\\notes.txt",
     "EventID: 3 Image: C:\\Windows\\System32\\svchost.exe DestinationIp: 13.107.4.50"]))
print("wrote", sorted(p.name for p in out.iterdir()))
