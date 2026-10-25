"""
data.py - Modélisation des machines et charges électriques de la menuiserie L'Électron d'Arbre (Groupe 25)
"""

import math
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SIM_DIR = Path(__file__).resolve().parent
current_file = BASE_DIR / "CurrentValues.csv"
@dataclass
class Machine:
    """
    Représente une machine ou un récepteur électrique.
    
    Attributes:
        name: Nom usuel de la machine
        category: Famille d'équipement ('Atelier', 'Cuisine', 'Éclairage', 'Véhicules', etc.)
        power_nominal: Puissance nominale en Watts (mécanique utile Pn pour les moteurs, électrique pour les autres)
        power_type: Type d'alimentation: 'tri' (triphasé 400V) ou 'mono' (monophasé 230V)
        cos_phi: Facteur de puissance (cos phi)
        efficiency: Rendement électrique/mécanique eta (ex: 0.85 pour un moteur, 1.0 pour une résistance)
        load_factor: Taux de charge en fonctionnement (ex: 0.75 pour 75%)
        daily_runtime_hours: Durée journalière d'utilisation en heures
        standby_power: Puissance consommée en veille en Watts (0 si pas de veille)
        voltage: Tension efficace entre phases (400V en tri, 230V en mono)
        days_per_year: Nombre de jours ouvrés / d'utilisation par an
        notes: Informations complémentaires / références datasheet
    """
    name: str
    category: str
    power_nominal: float
    power_type: str = "tri"  # 'tri' ou 'mono'
    cos_phi: float = 1.0
    efficiency: float = 1.0
    load_factor: float = 1.0
    daily_runtime_hours: float = 0.0
    standby_power: float = 0.0
    voltage: Optional[float] = None
    days_per_year: int = 250
    notes: str = ""

    def __post_init__(self):
        if self.voltage is None:
            self.voltage = 400.0 if self.power_type.lower() == "tri" else 230.0

    # Macros fonctions usuelles 
    @property
    def active_power_nominal_absorbed(self) -> float:
        """Puissance active absorbée à pleine charge (W): P_abs_nom = P_n / eta."""
        if self.efficiency <= 0:
            return self.power_nominal
        return self.power_nominal / self.efficiency

    @property
    def active_power_absorbed(self) -> float:
        """Puissance active absorbée réelle"""
        return self.active_power_nominal_absorbed * self.load_factor

    @property
    def tan_phi(self) -> float:
        """tan(phi) calculé à partir de cos(phi)."""
        if self.cos_phi >= 1.0:
            return 0.0
        phi = math.acos(max(-1.0, min(1.0, self.cos_phi)))
        return math.tan(phi)

    @property
    def reactive_power(self) -> float:
        """Puissance réactive absorbée réelle (var): Q = P * tan(phi)."""
        return self.active_power_absorbed * self.tan_phi

    @property
    def apparent_power(self) -> float:
        """Puissance apparente réelle (VA): S² = P² + Q²."""
        return math.sqrt(self.active_power_absorbed**2 + self.reactive_power**2)

    @property
    def current(self) -> float:
        """Courant de ligne efficace absorbé (A)."""
        if self.power_type.lower() == "tri":
            # I = S / (sqrt(3) * U)
            return self.apparent_power / (math.sqrt(3.0) * self.voltage)
        else:
            # I = S / V
            return self.apparent_power / self.voltage

    @property
    def daily_energy_active_wh(self) -> float:
        """Énergie active consommée par jour ouvré (Wh), veille. incluse"""
        work_energy = self.active_power_absorbed * self.daily_runtime_hours
        standby_hours = max(0.0, 24.0 - self.daily_runtime_hours)
        standby_energy = self.standby_power * standby_hours
        return work_energy + standby_energy

    @property
    def daily_energy_reactive_varh(self) -> float:
        """Énergie réactive consommée par jour ouvré (varh). (à la base j'avais calculé en Wh mais y'a aussi toute la partie imaginaire)"""
        return self.reactive_power * self.daily_runtime_hours

    @property
    def annual_energy_active_kwh(self) -> float:
        """Énergie active consommée par an (kWh)."""
        work_annual = (self.active_power_absorbed * self.daily_runtime_hours * self.days_per_year) / 1000.0
        # Si les machines sont branchées 365 jours par an, y'a une conso passive
        standby_annual = (self.standby_power * (24.0 - self.daily_runtime_hours) * 365.0) / 1000.0
        return work_annual + standby_annual

    @property
    def annual_energy_reactive_kvarh(self) -> float:
        """Énergie réactive consommée par an (kvarh)."""
        return (self.daily_energy_reactive_varh * self.days_per_year) / 1000.0

    def to_dict(self) -> Dict[str, any]:
        """ retourne un dictionnaire pour cette machine, avec toutes les données formatées proprement (sans notes par exemple)"""
        return {
            "name": self.name,
            "category": self.category,
            "power_type": self.power_type,
            "voltage_v": self.voltage,
            "power_nominal_w": self.power_nominal,
            "load_factor": self.load_factor,
            "efficiency": self.efficiency,
            "cos_phi": self.cos_phi,
            "daily_runtime_h": self.daily_runtime_hours,
            "active_power_w": self.active_power_absorbed,
            "reactive_power_var": self.reactive_power,
            "apparent_power_va": self.apparent_power,
            "current_a": self.current,
            "daily_energy_kwh": self.daily_energy_active_wh / 1000.0,
            "annual_energy_kwh": self.annual_energy_active_kwh,
        }


@dataclass
class SolarSystem:
    """Modélisation de l'installation photovoltaïque."""
    name: str = "CETC Solar NES144-7-535M"
    panel_peak_power_w: float = 535.0  # Wc par panneau
    panel_surface_m2: float = 2.58     # Surface unitaire indicative (ex: 2.279m x 1.134m)
    annual_sun_hours: float = 1000.0   # Heures équivalentes plein soleil en Belgique (h/an)
    target_production_share: float = 1/3  # Objectif 1/3 de la consommation totale annuelle


@dataclass
class EVChargingSystem:
    """Modélisation des bornes de recharge pour véhicules électriques."""
    name: str = "Bornes de recharge électriques"
    annual_distance_km: float = 60000.0
    consumption_wh_per_km: float = 120.0
    charging_power_w: float = 11000.0  # Borne 11 kW triphasée, j'ai trouvé cette valeur moyenne
    cos_phi: float = 0.98
    voltage: float = 400.0
    power_type: str = "tri"
    days_per_year: int = 250

    @property
    def annual_energy_kwh(self) -> float:
        return (self.annual_distance_km * self.consumption_wh_per_km) / 1000.0

    @property
    def daily_energy_kwh(self) -> float:
        return self.annual_energy_kwh / self.days_per_year


# ==============================================================================
# DONNÉES DU CAHIER DE CHARGES ET DU RAPPORT
# ==============================================================================

# 1. ÉQUIPEMENTS DE CUISINE
cafetiere = Machine(
    name="Cafetière",
    category="Cuisine",
    power_nominal=750.0,
    power_type="mono",
    daily_runtime_hours=(40.0 * 2.0) / 60.0,  # 40 cafés de 2 min = 1.333 h
    standby_power=1.0,
    notes="AJUSTER AVEC DES VRAIES MESURES. 40 cafés/jour, 1W en veille 24h."
)

bouilloire = Machine(
    name="Bouilloire",
    category="Cuisine",
    power_nominal=2000.0,
    power_type="mono",
    daily_runtime_hours=(7.0 * 3.25) / 60.0,  # 7L à 3.25 min/L = 22.75 min = 0.379 h
    notes="AJUSTER AVEC DES VRAIES MESURES. 7 litres d'eau à 3.25 min/L"
)

micro_ondes = Machine(
    name="Micro-ondes",
    category="Cuisine",
    power_nominal=700.0,
    power_type="mono",
    cos_phi=0.95,  # gros transfo dedans donc probablement pas 1. 
    daily_runtime_hours=10.0 / 60.0,  # 10 min = 0.167 h
    notes="AJUSTER AVEC DES VRAIES MESURES. 10 minutes par jour"
)

taque_electrique = Machine(
    name="Taque électrique",
    category="Cuisine",
    power_nominal=2000.0,
    power_type="mono",
    daily_runtime_hours=80.0 / 60.0,  # 80 min = 1.333 h
    standby_power=1.5,  # trouvé sur google
    notes="80 minutes par jour"
)

boiler_sous_evier = Machine(
    name="Boiler sous évier",
    category="Cuisine",
    power_nominal=140.0,
    power_type="mono",
    daily_runtime_hours=1.0,  # 1h par jour pour chauffer 3L
    notes="Chauffe de 3L d'eau par jour."
)

# 2. ÉCLAIRAGE
tubes_led = Machine(
    name="Tubes LED",
    category="Éclairage",
    power_nominal=80.0 * 15.0,  # 80 tubes de 15W = 1200W
    power_type="mono",
    cos_phi=0.95,  # source : internet
    daily_runtime_hours=8.0,
    notes="80 tubes LED de 15W chacun. Je doute de la conso réeelle 15W ? "
)

tubes_fluo_t5 = Machine(
    name="Tubes fluorescents T5",
    category="Éclairage",
    power_nominal=70.0*6.0, #  70 tubes de 6W = 
    power_type="mono",
    cos_phi=0.90,
    daily_runtime_hours=8.0,
    notes="70 tubes fluo de 6W chacun."
)

# 3. MACHINES D'ATELIER (Moteurs triphasés et monophasé)
# Données de plaques / datasheets issues des constructeurs cités dans rapport.tex
scie_a_panneaux = Machine(
    name="Scie à panneaux",
    category="Atelier",
    power_nominal=2900.0,
    cos_phi=0.83,
    efficiency=0.84,
    load_factor=0.75,
    daily_runtime_hours=1,
    notes="Holzmann FKS400VF3200, 3x400V"
)

scie_radiale = Machine(
    name="Scie radiale",
    category="Atelier",
    power_nominal=3000.0,
    cos_phi=0.84,
    efficiency=0.85,
    load_factor=0.50,
    daily_runtime_hours=3.0,
    notes="DeWalt DW721KN triphasée, 3x400V"
)

aspiration_centralisee = Machine(
    name="Aspiration centralisée",
    category="Atelier",
    power_nominal=3000.0,
    cos_phi=0.85,
    efficiency=0.86,
    daily_runtime_hours=90.0 / 60.0,  # 1.5 h
    notes="LTDA industriel, 3x400V"
)

scie_sur_table = Machine(
    name="Scie sur table",
    category="Atelier",
    power_nominal=2800.0,
    cos_phi=0.82,
    efficiency=0.84,
    load_factor=0.50,
    daily_runtime_hours=3.0,
    notes="Torros TKS316PRO 400V"
)

ponceuse = Machine(
    name="Ponceuse à bande",
    category="Atelier",
    power_nominal=750.0,
    power_type="mono",
    cos_phi=0.80,
    efficiency=0.80,
    daily_runtime_hours=20.0 / 60.0,  # 0.333 h
    notes="Scantool 230V monophasé"
)

scie_a_ruban = Machine(
    name="Scie à ruban",
    category="Atelier",
    power_nominal=1500.0,
    cos_phi=0.81,
    efficiency=0.83,
    load_factor=0.75,
    daily_runtime_hours=3.0,
    notes="Cormak HBS320 triphasée, 3x400V"
)

# 4. VÉHICULES ÉLECTRIQUES ET SOLAIRE
ev_system = EVChargingSystem()
solar_system = SolarSystem()

# Listes complètes pour itérations et bilans
CUISINE_MACHINES: List[Machine] = [
    cafetiere,
    bouilloire,
    micro_ondes,
    taque_electrique,
    boiler_sous_evier,
]

ECLAIRAGE_MACHINES: List[Machine] = [
    tubes_led,
    tubes_fluo_t5,
]

ATELIER_MACHINES: List[Machine] = [
    scie_a_panneaux,
    scie_radiale,
    aspiration_centralisee,
    scie_sur_table,
    ponceuse,
    scie_a_ruban,
]

ALL_MACHINES: List[Machine] = CUISINE_MACHINES + ECLAIRAGE_MACHINES + ATELIER_MACHINES
