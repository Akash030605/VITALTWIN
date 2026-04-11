# process_tb_data.py
# Extract India TB comorbidity statistics from 3 CSV files:
#   2.10_TB_Diabetes.csv  — TB + Diabetes comorbidity by state
#   2.11_TB_Tobacco.csv   — TB + Tobacco comorbidity by state
#   2.12_TB_Alcohol.csv   — TB + Alcohol comorbidity by state
#
# Output: data/india/tb/tb_lung_risk_by_state.json
# Usage: lung model uses this to adjust TB-related lung disease risk by state
#
# Source: Revised National TB Control Programme (RNTCP) Annual Report / NTEP
#         Ministry of Health & Family Welfare, India

import pandas as pd
import json
from pathlib import Path

BASE = Path(__file__).parent
TB_DIR = BASE / "data/india/tb"

# ── Load the 3 TB datasets ────────────────────────────────────────────────────
print("[1] Loading TB comorbidity datasets...")

def clean_col(df, frag):
    """Find first column name containing 'frag' and return series."""
    cols = [c for c in df.columns if frag.lower() in c.lower()]
    return df[cols[0]] if cols else None

# TB + Diabetes
df_dm  = pd.read_csv(TB_DIR / "2.10_TB_Diabetes.csv")
# TB + Tobacco
df_tob = pd.read_csv(TB_DIR / "2.11_TB_Tobacco.csv")
# TB + Alcohol
df_alc = pd.read_csv(TB_DIR / "2.12_TB_Alcohol.csv")

print(f"   DM rows={len(df_dm)}, Tobacco rows={len(df_tob)}, Alcohol rows={len(df_alc)}")

# Get state names from first column
states_dm  = df_dm.iloc[:, 0].str.strip()
states_tob = df_tob.iloc[:, 0].str.strip()
states_alc = df_alc.iloc[:, 0].str.strip()

# Extract total percentage columns
# For DM: column containing "Percentage" and "Total"
# For Tobacco: similarly
# For Alcohol: similarly

def get_total_pct(df, kw1="Percentage", kw2="Total"):
    """Return first numeric column that contains both kw1 and kw2 in name."""
    for c in df.columns:
        if kw1.lower() in c.lower() and kw2.lower() in c.lower():
            return pd.to_numeric(df[c], errors='coerce')
    # Fallback: any percentage of total
    for c in df.columns:
        if "%" in c and "total" in c.lower():
            return pd.to_numeric(df[c], errors='coerce')
    # last resort: 7th column (0-indexed 6) is usually Total %
    return pd.to_numeric(df.iloc[:, 6], errors='coerce')

pct_dm  = get_total_pct(df_dm)
pct_tob = get_total_pct(df_tob)
pct_alc = get_total_pct(df_alc)

print(f"\n   DM  percentage col: {pct_dm.dropna().describe().to_dict()}")
print(f"   Tob percentage col: {pct_tob.dropna().describe().to_dict()}")
print(f"   Alc percentage col: {pct_alc.dropna().describe().to_dict()}")

# ── Build per-state TB comorbidity map ────────────────────────────────────────
print("\n[2] Building state TB risk map...")

def _calc_multiplier(dm_pct, tob_pct):
    """
    Lung risk multiplier from TB comorbidity burden in the state.
    DM+TB signals poor glycemic control + high TB prevalence → worse lung outcomes.
    Tobacco+TB signals dual lung insult → increased COPD+TB overlap.
    Scale: 1.0 (average) to 1.25 (very high burden).
    """
    score = 1.0
    if dm_pct  is not None: score += min(0.15, (dm_pct  - 50) / 100) if dm_pct  > 50 else 0
    if tob_pct is not None: score += min(0.10, (tob_pct - 30) / 100) if tob_pct > 30 else 0
    return round(min(1.25, score), 3)

# Rebuild with correct function call (fix closure issue above)
state_risk2 = {}
for idx, state in enumerate(states_dm):
    if pd.isna(state) or state.lower() in ('total', 'india', ''):
        continue
    state_key = (state.strip().lower()
                 .replace(' ', '_').replace('&', 'and').replace('-', '_')
                 .replace('.', '').replace('(', '').replace(')', ''))

    dm_pct  = float(pct_dm.iloc[idx])  if idx < len(pct_dm)  and not pd.isna(pct_dm.iloc[idx])  else None
    tob_pct = float(pct_tob.iloc[idx]) if idx < len(pct_tob) and not pd.isna(pct_tob.iloc[idx]) else None
    alc_pct = float(pct_alc.iloc[idx]) if idx < len(pct_alc) and not pd.isna(pct_alc.iloc[idx]) else None

    score = 1.0
    if dm_pct  is not None and dm_pct  > 50: score += min(0.15, (dm_pct  - 50) / 100)
    if tob_pct is not None and tob_pct > 30: score += min(0.10, (tob_pct - 30) / 100)
    multiplier = round(min(1.25, score), 3)

    state_risk2[state_key] = {
        "state_name":               state.strip(),
        "tb_diabetes_pct":          round(dm_pct,  1) if dm_pct  is not None else None,
        "tb_tobacco_pct":           round(tob_pct, 1) if tob_pct is not None else None,
        "tb_alcohol_pct":           round(alc_pct, 1) if alc_pct is not None else None,
        "lung_tb_risk_multiplier":  multiplier,
    }

# ── India aggregate stats ─────────────────────────────────────────────────────
india_idx = states_dm[states_dm.str.lower().str.contains('total|india')].index
india_dm  = float(pct_dm.iloc[india_idx[0]])  if len(india_idx) > 0 else None
india_tob = float(pct_tob.iloc[india_idx[0]]) if len(india_idx) > 0 else None
india_alc = float(pct_alc.iloc[india_idx[0]]) if len(india_idx) > 0 else None

summary = {
    "_meta": {
        "source": "RNTCP/NTEP Annual Report, Ministry of Health & Family Welfare, India",
        "files":  ["2.10_TB_Diabetes.csv", "2.11_TB_Tobacco.csv", "2.12_TB_Alcohol.csv"],
        "note":   "TB comorbidity percentages by Indian state. Used to adjust lung model TB risk by geography.",
        "india_total": {
            "tb_diabetes_pct": round(india_dm,  1) if india_dm  else None,
            "tb_tobacco_pct":  round(india_tob, 1) if india_tob else None,
            "tb_alcohol_pct":  round(india_alc, 1) if india_alc else None,
        },
        "citation": (
            "Jeon CY, Murray MB. Diabetes mellitus increases the risk of active tuberculosis. "
            "PLoS Med 2008;5(7):e152. doi:10.1371/journal.pmed.0050152"
        )
    },
    "states": state_risk2
}

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = TB_DIR / "tb_lung_risk_by_state.json"
with open(out_path, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n[3] Saved: {out_path}")
print(f"   States processed: {len(state_risk2)}")

# ── Print top 5 highest-burden states ────────────────────────────────────────
print("\n[4] Top 5 states by TB lung risk multiplier:")
sorted_states = sorted(state_risk2.items(),
                       key=lambda x: x[1]['lung_tb_risk_multiplier'], reverse=True)
for sk, sv in sorted_states[:5]:
    print(f"   {sv['state_name']:30s}  DM={sv['tb_diabetes_pct']}%  "
          f"Tobacco={sv['tb_tobacco_pct']}%  multiplier={sv['lung_tb_risk_multiplier']}")

print("\n[5] India overall TB comorbidity:")
print(f"   TB+Diabetes:  {india_dm}%   (DM triples TB risk — Jeon & Murray 2008)")
print(f"   TB+Tobacco:   {india_tob}%   (Tobacco is key TB→COPD driver)")
print(f"   TB+Alcohol:   {india_alc}%")
