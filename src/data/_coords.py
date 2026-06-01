"""src/data/_coords.py — Coordenadas (lat, lng) por geocode para amostragem GEE.

Cobre as capitais e principais municípios. Para municípios fora desta lista,
o fetcher de satélite recorre ao fallback sintético (que não depende de coords).
Pode ser expandido lendo um CSV de centróides do IBGE futuramente.
"""
from __future__ import annotations

MUNI_COORDS: dict[str, tuple[float, float]] = {
    "3550308": (-23.5505, -46.6333),  # São Paulo
    "3304557": (-22.9068, -43.1729),  # Rio de Janeiro
    "3106200": (-19.9191, -43.9386),  # Belo Horizonte
    "2927408": (-12.9714, -38.5014),  # Salvador
    "2304400": (-3.7172, -38.5433),   # Fortaleza
    "2611606": (-8.0539, -34.8811),   # Recife
    "5300108": (-15.7801, -47.9292),  # Brasília
    "1302603": (-3.1190, -60.0217),   # Manaus
    "1501402": (-1.4558, -48.5044),   # Belém
    "4106902": (-25.4290, -49.2671),  # Curitiba
    "4314902": (-30.0346, -51.2177),  # Porto Alegre
    "5208707": (-16.6864, -49.2643),  # Goiânia
    "2111300": (-2.5391, -44.2829),   # São Luís
    "2211001": (-5.0920, -42.8038),   # Teresina
    "5002704": (-20.4697, -54.6201),  # Campo Grande
    "5103403": (-15.6014, -56.0979),  # Cuiabá
    "1100205": (-8.7612, -63.9004),   # Porto Velho
}
