"""Recalculate the published heat-sink results from the supplied CSV files."""

import csv
import math
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def read_rows(name):
    with (DATA_DIR / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def pressure_drop(row):
    return float(row["pt_fin_in_pa"]) - float(row["pt_fin_out_pa"])


def peak_to_peak(values):
    return max(values) - min(values)


def main():
    case_rows = read_rows("case_summary.csv")
    history = read_rows("dense_v2_iterations_250_300.csv")
    cases = {row["case_id"]: row for row in case_rows}
    if len(case_rows) != 3 or set(cases) != {"dense_v1", "wide_v1", "dense_v2"}:
        raise ValueError("Expected one row each for dense_v1, wide_v1, and dense_v2.")
    if [int(row["iteration"]) for row in history] != list(range(250, 301)):
        raise ValueError("Expected consecutive iterations 250 through 300.")

    final = cases["dense_v2"]
    last = history[-1]
    for field in ("iteration", "model_tmax_k", "pt_fin_in_pa", "pt_fin_out_pa"):
        if not math.isclose(float(final[field]), float(last[field]), rel_tol=0, abs_tol=1e-8):
            raise ValueError(f"The final history point disagrees with case_summary.csv: {field}.")

    print(f"{'Case':<10}{'Cells':>10}{'Iter':>7}{'Tmax (C)':>11}{'dP (Pa)':>11}{'Qout (W)':>12}"
          f"{'Mass err (%)':>15}{'Energy err (%)':>17}")
    for row in case_rows:
        mass_in = float(row["mass_flow_in_kg_s"])
        mass_out = float(row["mass_flow_out_kg_s"])
        heat_out = float(row["net_heat_out_w"])
        heat_input = float(row["heat_load_w"])
        mass_error = 100 * abs(mass_in - mass_out) / mass_in
        energy_error = 100 * abs(heat_input - heat_out) / heat_input
        temperature_c = float(row["model_tmax_k"]) - 273.15
        print(f"{row['case_id']:<10}{int(row['cell_count']):>10,}{row['iteration']:>7}"
              f"{temperature_c:>11.2f}{pressure_drop(row):>11.2f}{heat_out:>12.4f}"
              f"{mass_error:>15.6f}{energy_error:>17.6f}")

    baseline_dense = cases["dense_v1"]
    baseline_wide = cases["wide_v1"]
    print("\nBaseline dense minus baseline wide")
    print(f"  Tmax change: {float(baseline_dense['model_tmax_k']) - float(baseline_wide['model_tmax_k']):+.2f} C")
    print(f"  Pressure-drop change: {pressure_drop(baseline_dense) - pressure_drop(baseline_wide):+.2f} Pa")
    print("\nFinal 20 iterations (281-300), maximum minus minimum")
    tail = history[-20:]
    temperatures = [float(row["model_tmax_k"]) for row in tail]
    pressure_drops = [pressure_drop(row) for row in tail]
    print(f"  Tmax range: {peak_to_peak(temperatures):.6f} C")
    print(f"  Pressure-drop range: {peak_to_peak(pressure_drops):.6f} Pa")


if __name__ == "__main__":
    main()
