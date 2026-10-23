import math


# Importation du modèle de données
from data import *
from fourier import *

def compute_all_results():
    """Effectue l'ensemble des calculs de bilan de puissance et d'énergie."""
    # Energie cuisine 
    cuisine_e_day = sum(m.daily_energy_active_wh for m in CUISINE_MACHINES)
    cuisine_e_year = sum(m.annual_energy_active_kwh for m in CUISINE_MACHINES)

    # Energie eclairage 
    eclairage_e_day = sum(m.daily_energy_active_wh for m in ECLAIRAGE_MACHINES)
    eclairage_e_year = sum(m.annual_energy_active_kwh for m in ECLAIRAGE_MACHINES)
    
    # Energie atelier
    atelier_p_abs = sum(m.active_power_absorbed for m in ATELIER_MACHINES)
    atelier_q = sum(m.reactive_power for m in ATELIER_MACHINES)
    atelier_s = math.sqrt(atelier_p_abs**2 + atelier_q**2)
    atelier_cos_phi = atelier_p_abs / atelier_s if atelier_s > 0 else 1.0
    atelier_e_day = sum(m.daily_energy_active_wh for m in ATELIER_MACHINES)
    atelier_e_year = sum(m.annual_energy_active_kwh for m in ATELIER_MACHINES)
    
    # Energie cuisine + eclairage (pas les gros conso)
    auxiliaires_e_day = cuisine_e_day + eclairage_e_day
    auxiliaires_e_year = cuisine_e_year + eclairage_e_year

    # Charge des voitures. 
    ev_e_year = ev_system.annual_energy_kwh
    ev_e_day = ev_system.daily_energy_kwh * 1000.0  # Wh/jour

    # Consommation globale
    total_annual_kwh = auxiliaires_e_year + atelier_e_year + ev_e_year
    total_daily_wh = auxiliaires_e_day + atelier_e_day + ev_e_day

    # Dimensionnement raccordement (puissance appelée simultanée)
    
    # conso de P
    total_p_abs_all = sum(m.active_power_absorbed for m in ALL_MACHINES) + ev_system.charging_power_w
    
    # conso de Q
    total_q_all = sum(m.reactive_power for m in ALL_MACHINES) + (ev_system.charging_power_w * math.tan(math.acos(ev_system.cos_phi)))
    
    # conso de S -> P²+Q² = S²
    total_s_all = math.sqrt(total_p_abs_all**2 + total_q_all**2)
    
    # S / 3V = S / sqrt(3)*U -> calculs sur feuille  
    current_tri_max = total_s_all / (math.sqrt(3.0) * 400.0)

    # on doit souscrire à la conso max, puisque on a pas de batteries pour apporter l'excédentaire en pics de conso
    s_souscrite_kva = total_s_all / 1000.0
    i_souscrit_a = current_tri_max

    # 3. Dimensionnement Panneaux Solaires
    target_solar_kwh = total_annual_kwh * solar_system.target_production_share
    required_peak_power_w = (target_solar_kwh * 1000.0) / solar_system.annual_sun_hours
    panel_count = math.ceil(required_peak_power_w / solar_system.panel_peak_power_w)
    actual_solar_peak_power_w = panel_count * solar_system.panel_peak_power_w
    actual_solar_production_kwh = (actual_solar_peak_power_w * solar_system.annual_sun_hours) / 1000.0
    solar_surface_m2 = panel_count * solar_system.panel_surface_m2

    return {
        "cuisine_e_day": cuisine_e_day,
        "cuisine_e_year": cuisine_e_year,
        "eclairage_e_day": eclairage_e_day,
        "eclairage_e_year": eclairage_e_year,
        "auxiliaires_e_day": auxiliaires_e_day,
        "auxiliaires_e_year": auxiliaires_e_year,
        "atelier_p_abs": atelier_p_abs,
        "atelier_q": atelier_q,
        "atelier_s": atelier_s,
        "atelier_cos_phi": atelier_cos_phi,
        "atelier_e_day": atelier_e_day,
        "atelier_e_year": atelier_e_year,
        "ev_e_year": ev_e_year,
        "ev_e_day": ev_e_day,
        "total_annual_kwh": total_annual_kwh,
        "total_daily_wh": total_daily_wh,
        "total_p_abs_all": total_p_abs_all,
        "total_q_all": total_q_all,
        "total_s_all": total_s_all,
        "current_tri_max": current_tri_max,
        "s_souscrite_kva": s_souscrite_kva,
        "i_souscrit_a": i_souscrit_a,
        "target_solar_kwh": target_solar_kwh,
        "required_peak_power_w": required_peak_power_w,
        "panel_count": panel_count,
        "actual_solar_peak_power_w": actual_solar_peak_power_w,
        "actual_solar_production_kwh": actual_solar_production_kwh,
        "solar_surface_m2": solar_surface_m2,
    }




def generate_latex_results_file(res: dict, cur: dict):
    """Généré par IA : Génère un fichier results.tex contenant toutes les macros et variables prêtes pour LaTeX. """
    tex_path = SIM_DIR / "results.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% ======================================================================\n")
        f.write("% FICHIER GÉNÉRÉ AUTOMATIQUEMENT PAR simulations/main.py\n")
        f.write("% Ne pas modifier manuellement. Relancer 'python simulations/main.py'\n")
        f.write("% ======================================================================\n\n")

        f.write("% --- Cuisine ---\n")
        f.write(f"\\newcommand{{\\ValTCafetiere}}{{{cafetiere.daily_runtime_hours:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValECafetiere}}{{{cafetiere.active_power_absorbed * cafetiere.daily_runtime_hours:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValECafetiereVeille}}{{{cafetiere.daily_energy_active_wh:.1f}}}\n")

        f.write(f"\\newcommand{{\\ValTBouilloire}}{{{bouilloire.daily_runtime_hours:.3f}}}\n")
        f.write(f"\\newcommand{{\\ValEBouilloire}}{{{bouilloire.daily_energy_active_wh:.1f}}}\n")

        f.write(f"\\newcommand{{\\ValTMicroOndes}}{{{micro_ondes.daily_runtime_hours:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValEMicroOndes}}{{{micro_ondes.daily_energy_active_wh:.1f}}}\n")

        f.write(f"\\newcommand{{\\ValTTaque}}{{{taque_electrique.daily_runtime_hours:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValETaque}}{{{taque_electrique.daily_energy_active_wh:.1f}}}\n")

        f.write(f"\\newcommand{{\\ValTBoiler}}{{{boiler_sous_evier.daily_runtime_hours:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValEBoiler}}{{{boiler_sous_evier.daily_energy_active_wh:.0f}}}\n")

        f.write(f"\\newcommand{{\\ValECuisineTotal}}{{{res['cuisine_e_day']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValECuisineTotalKWh}}{{{res['cuisine_e_year']:.1f}}}\n\n")

        f.write("% --- Éclairage ---\n")
        f.write(f"\\newcommand{{\\ValPLED}}{{{tubes_led.power_nominal:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValELED}}{{{tubes_led.daily_energy_active_wh:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValPFluo}}{{{tubes_fluo_t5.power_nominal:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValEFluo}}{{{tubes_fluo_t5.daily_energy_active_wh:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValEEclairageTotal}}{{{res['eclairage_e_day']:.1f}}}\n\n")

        f.write("% --- Auxiliaires Totaux ---\n")
        f.write(f"\\newcommand{{\\ValETotalAuxWh}}{{{res['auxiliaires_e_day']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValETotalAuxKWh}}{{{res['auxiliaires_e_day'] / 1000.0:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValETotalAuxAnKWh}}{{{res['auxiliaires_e_year']:.1f}}}\n\n")

        f.write("% --- Machines d'atelier ---\n")
        for m in ATELIER_MACHINES:
            safe_id = m.name.lower().replace(" ", "").replace("à", "a").replace("é", "e").replace("è", "e")
            f.write(f"% {m.name}\n")
            f.write(f"\\newcommand{{\\ValPn{safe_id}}}{{{m.power_nominal:.0f}}}\n")
            f.write(f"\\newcommand{{\\ValCosPhi{safe_id}}}{{{m.cos_phi:.2f}}}\n")
            f.write(f"\\newcommand{{\\ValEta{safe_id}}}{{{m.efficiency:.2f}}}\n")
            f.write(f"\\newcommand{{\\ValCharge{safe_id}}}{{{int(m.load_factor * 100)}}}\n")
            f.write(f"\\newcommand{{\\ValDuree{safe_id}}}{{{m.daily_runtime_hours:.2f}}}\n")
            f.write(f"\\newcommand{{\\ValPabs{safe_id}}}{{{m.active_power_absorbed:.1f}}}\n")
            f.write(f"\\newcommand{{\\ValQ{safe_id}}}{{{m.reactive_power:.1f}}}\n")
            f.write(f"\\newcommand{{\\ValI{safe_id}}}{{{m.current:.2f}}}\n")
            f.write(f"\\newcommand{{\\ValEDay{safe_id}}}{{{m.daily_energy_active_wh:.1f}}}\n")
            f.write(f"\\newcommand{{\\ValEYear{safe_id}}}{{{m.annual_energy_active_kwh:.1f}}}\n")

        f.write(f"\\newcommand{{\\ValPabsAtelierTotal}}{{{res['atelier_p_abs']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValQAtelierTotal}}{{{res['atelier_q']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValSAtelierTotal}}{{{res['atelier_s']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValCosPhiAtelier}}{{{res['atelier_cos_phi']:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValEAtelierDay}}{{{res['atelier_e_day']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValEAtelierYear}}{{{res['atelier_e_year']:.1f}}}\n\n")

        f.write("% --- Bornes VE ---\n")
        f.write(f"\\newcommand{{\\ValEVeAnWh}}{{{res['ev_e_year'] * 1000.0:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValEVeAnKWh}}{{{res['ev_e_year']:.0f}}}\n")
        f.write(f"\\newcommand{{\\ValEVeDayWh}}{{{res['ev_e_day']:.0f}}}\n\n")

        f.write("% --- Consommation globale annuelle ---\n")
        f.write(f"\\newcommand{{\\ValETotalAnKWh}}{{{res['total_annual_kwh']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValETotalAnMWh}}{{{res['total_annual_kwh'] / 1000.0:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValETotalJourKWh}}{{{res['total_daily_wh'] / 1000.0:.2f}}}\n\n")

        f.write("% --- Dimensionnement Raccordement ---\n")
        f.write(f"\\newcommand{{\\ValPInstalledKW}}{{{res['total_p_abs_all'] / 1000.0:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValSInstalledKVA}}{{{res['total_s_all'] / 1000.0:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValIMaxTotalA}}{{{res['current_tri_max']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValSSouscriteKVA}}{{{res['s_souscrite_kva']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValISouscritA}}{{{res['i_souscrit_a']:.1f}}}\n\n")

        f.write("% --- Photovoltaïque ---\n")
        f.write(f"\\newcommand{{\\ValSolarTargetKWh}}{{{res['target_solar_kwh']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValSolarRequiredKWc}}{{{res['required_peak_power_w'] / 1000.0:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValSolarPanelCount}}{{{res['panel_count']}}}\n")
        f.write(f"\\newcommand{{\\ValSolarActualKWc}}{{{res['actual_solar_peak_power_w'] / 1000.0:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValSolarActualProdKWh}}{{{res['actual_solar_production_kwh']:.1f}}}\n")
        f.write(f"\\newcommand{{\\ValSolarSurfaceMdeux}}{{{res['solar_surface_m2']:.1f}}}\n\n")

        f.write("% --- Courant déformé mesuré ---\n")
        f.write(f"\\newcommand{{\\ValCourantNPoints}}{{{cur['n_points']}}}\n")
        f.write(f"\\newcommand{{\\ValCourantIrms}}{{{cur['i_rms']:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValCourantImax}}{{{cur['i_max']:.2f}}}\n")
        f.write(f"\\newcommand{{\\ValCourantImin}}{{{cur['i_min']:.2f}}}\n")


def main():
    # calculs. 
    results = compute_all_results()

    # analyse et tracé du courant

    cur_info = analyze_and_plot_current(current_file)

    # résultats en LaTeX
    generate_latex_results_file(results, cur_info)

    print(f"\n[OK] Fichier LaTeX généré : {SIM_DIR / 'results.tex'}")
    print(f"[OK] Graphique généré : {BASE_DIR / 'courant_deforme.png'}")


if __name__ == "__main__":
    main()