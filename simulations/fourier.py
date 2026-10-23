import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from data import *

def analyze_and_plot_current(csv_path: Path , plot = True):
    """Charge CurrentValues.csv, calcule Irms/Imax/Imin et trace le graphique simple."""
    vals = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().rstrip(",")
            if not line or "Current" in line:
                continue
            vals.append(float(line.replace(",", ".")))

    i_vals = np.array(vals)
    n_points = len(i_vals)

    dt_ms = 0.1
    time_ms = np.arange(n_points) * dt_ms

    i_rms = float(np.sqrt(np.mean(i_vals**2)))
    i_max = float(np.max(i_vals))
    i_min = float(np.min(i_vals))
    i_mean = float(np.mean(i_vals))

    # plot si on veut
    if plot : 
        plt.figure()
        plt.plot(time_ms, i_vals)
        plt.xlabel("Temps (ms)")
        plt.ylabel("Courant (A)")
        plt.savefig(SIM_DIR / "courant_deforme.png")
        plt.close()

    # retourne également les données lues. 
    return {
        "n_points": n_points,
        "dt_ms": dt_ms,
        "i_rms": i_rms,
        "i_max": i_max,
        "i_min": i_min,
        "i_mean": i_mean,
    }
