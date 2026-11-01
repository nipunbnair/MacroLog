#!/usr/bin/env python3
"""
Rebuilds app/foods.js (the bundled food database) from the original public sources.

Output rows (all values per 100 g):
    [name, source, kcal, protein_g, available_carbs_g, fat_g, fibre_g, serving_g?, serving_desc?]
Carbohydrate is *available* carbohydrate (fibre excluded), the Australian labelling convention.

Sources (download them yourself and pass the paths):
  --afcd    AFCD Release 3 - Nutrient profiles.xlsx   (FSANZ, Australian Food Composition Database)
  --ausnut  AUSNUT.csv  (FSANZ AUSNUT 2011-13 food nutrient file, flattened to CSV)
  --sr28    folder containing USDA SR28 ABBREV.txt and FOOD_DES.txt (e.g. npm package fda-nutrient-database)
  --indb    folder containing INDB.xlsx and recipes_servingsize.xlsx
            (Indian Nutrient Databank, github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB-)

Usage:
  pip install pandas openpyxl
  python3 scripts/build_foods.py --afcd ... --ausnut ... --sr28 ... --indb ... --out app/foods.js
"""
import argparse, json, math, os, re
import pandas as pd


def num(x, d=1):
    try:
        x = float(x)
        return 0 if math.isnan(x) else round(x, d)
    except (TypeError, ValueError):
        return 0


def atwater_mismatch(row):
    a = 4 * row[3] + 4 * row[4] + 9 * row[5] + 2 * row[6]
    return max(row[2], a) > 40 and abs(row[2] - a) / max(row[2], a) > 0.3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--afcd", required=True)
    ap.add_argument("--ausnut", required=True)
    ap.add_argument("--sr28", required=True)
    ap.add_argument("--indb", required=True)
    ap.add_argument("--out", default="app/foods.js")
    a = ap.parse_args()
    foods = []

    # 1. AFCD Release 3 (FSANZ) - columns located by header text
    afcd = pd.read_excel(a.afcd, sheet_name="All solids & liquids per 100 g", header=2)
    col = {re.sub(r"\s+", " ", str(c)).strip(): c for c in afcd.columns}
    def pick(prefix):
        return next(v for k, v in col.items() if k.startswith(prefix))
    c_name, c_kj = pick("Food Name"), pick("Energy with dietary fibre")
    c_p, c_f, c_fb = pick("Protein"), pick("Fat, total"), pick("Total dietary fibre")
    c_c = pick("Available carbohydrate, with sugar alcohols")
    for _, r in afcd.iterrows():
        if isinstance(r[c_name], str):
            foods.append([r[c_name].strip(), "AFCD", num(r[c_kj] / 4.184, 0), num(r[c_p]), num(r[c_c]), num(r[c_f]), num(r[c_fb])])

    # 2. AUSNUT 2011-13 (skip names already in AFCD)
    seen = {f[0].lower() for f in foods}
    au = pd.read_csv(a.ausnut)
    for _, r in au.iterrows():
        n = r["eight_dig_d"]
        if not isinstance(n, str) or n == "Not a food" or n.lower() in seen or pd.isna(r["energy_wdf_kj"]):
            continue
        seen.add(n.lower())
        foods.append([n.strip(), "AUSNUT", num(r["energy_wdf_kj"] / 4.184, 0), num(r["protein_g"]), num(r["carbs_wsa_g"]), num(r["total_fat_g"]), num(r["fibre_g"])])

    # 3. USDA SR28 (carbs by difference minus fibre = available carbs)
    desc = {}
    for line in open(os.path.join(a.sr28, "FOOD_DES.txt"), encoding="latin-1"):
        p = line.strip().split("^")
        desc[p[0].strip("~")] = p[2].strip("~")
    for line in open(os.path.join(a.sr28, "ABBREV.txt"), encoding="latin-1"):
        p = [x.strip("~") for x in line.rstrip("\r\n").split("^")]
        if len(p) < 50:
            continue
        name = desc.get(p[0], p[1])
        if re.search(r"baby food|infant formula", name, re.I):
            continue
        fib = num(p[8])
        row = [name, "USDA", num(p[3], 0), num(p[4]), max(0, round(num(p[7]) - fib, 1)), num(p[5]), fib]
        if p[48]:
            row += [num(p[48]), p[49] or None]
        foods.append(row)

    # 4. Indian Nutrient Databank (drop the few recipes whose energy contradicts their macros)
    indb = pd.read_excel(os.path.join(a.indb, "INDB.xlsx"))
    serv = pd.read_excel(os.path.join(a.indb, "recipes_servingsize.xlsx")).set_index("recipe_code")
    for _, r in indb.iterrows():
        row = [str(r["food_name"]).strip(), "INDB", num(r["energy_kcal"], 0), num(r["protein_g"]), num(r["carb_g"]), num(r["fat_g"]), num(r["fibre_g"])]
        if atwater_mismatch(row):
            continue
        if r["food_code"] in serv.index:
            s = serv.loc[r["food_code"]]
            if isinstance(s["servings_unit"], str):
                row += [None, f"{s['size_of_servings']:g} {s['servings_unit']}"]
        foods.append(row)

    for f in foods:  # trim trailing empty fields
        while f and f[-1] is None:
            f.pop()
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("window.FOODS=" + json.dumps(foods, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"Wrote {len(foods)} foods to {a.out}")


if __name__ == "__main__":
    main()
