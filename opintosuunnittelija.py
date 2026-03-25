"""
Älykäs Opintosuunnittelija
==========================
Building AI -kurssin lopputyö.

Työkalu auttaa opiskelijoita rakentamaan henkilökohtaisen opiskeluaikataulun
analysoimalla aiempia opintotottumuksia ja ennustamalla optimaaliset
opiskelusessiot valvotun regression ja heuristiikan avulla.
"""

import csv
import datetime
import os
from collections import defaultdict


# ---------------------------------------------------------------------------
# Datatyypit
# ---------------------------------------------------------------------------

class OpintoPäiväkirjaRivi:
    """Yksittäinen rivi opiskelijan opintopäiväkirjasta."""

    def __init__(self, päivämäärä: str, aine: str, kesto_h: float,
                 tehokkuus: float, tulos: float):
        self.päivämäärä = datetime.date.fromisoformat(päivämäärä)
        self.aine = aine
        self.kesto_h = float(kesto_h)        # tuntia
        self.tehokkuus = float(tehokkuus)    # 1–5
        self.tulos = float(tulos)            # 0–100 (koepistemäärä tms.)


class Tehtävä:
    """Opiskelijan yksittäinen tehtävä tai koe."""

    def __init__(self, aine: str, tunteja_jäljellä: float,
                 määräaika: datetime.date, prioriteetti: int = 1):
        self.aine = aine
        self.tunteja_jäljellä = float(tunteja_jäljellä)
        self.määräaika = määräaika
        self.prioriteetti = int(prioriteetti)   # 1 = korkein


# ---------------------------------------------------------------------------
# Datan lataus
# ---------------------------------------------------------------------------

def lataa_opintopäiväkirja(tiedostopolku: str) -> list:
    """Lataa opintopäiväkirja CSV-tiedostosta.

    Sarakkeet: päivämäärä,aine,kesto_h,tehokkuus,tulos
    """
    rivit = []
    if not os.path.exists(tiedostopolku):
        return rivit
    with open(tiedostopolku, newline="", encoding="utf-8") as f:
        lukija = csv.DictReader(f)
        for rivi in lukija:
            try:
                rivit.append(OpintoPäiväkirjaRivi(
                    rivi["päivämäärä"],
                    rivi["aine"],
                    rivi["kesto_h"],
                    rivi["tehokkuus"],
                    rivi["tulos"],
                ))
            except (KeyError, ValueError):
                continue
    return rivit


# ---------------------------------------------------------------------------
# Yksinkertainen regressiomalli (painotettu keskiarvo)
# ---------------------------------------------------------------------------

def _laske_paino(rivi: OpintoPäiväkirjaRivi,
                 tänään: datetime.date) -> float:
    """Uudemmat havainnot saavat suuremman painon."""
    päivät = max((tänään - rivi.päivämäärä).days, 1)
    return 1.0 / päivät


def lataa_valmis_malli(opiskelijadata: list) -> dict:
    """Rakentaa yksinkertaisen regressiomallin opintopäiväkirjadatasta.

    Palauttaa sanakirjan, jossa avaimena on aine ja arvona paras
    ennustettu opiskeluaika tunneissa päivää kohden.
    """
    tänään = datetime.date.today()
    aine_pisteet: dict = defaultdict(float)
    aine_painot: dict = defaultdict(float)

    for rivi in opiskelijadata:
        paino = _laske_paino(rivi, tänään)
        # Pisteytetään tehokkuus × tulos normalisoituna
        pisteet = (rivi.tehokkuus / 5.0) * (rivi.tulos / 100.0)
        aine_pisteet[rivi.aine] += paino * pisteet * rivi.kesto_h
        painotettu = paino * pisteet if pisteet > 0 else paino * 0.01
        aine_painot[rivi.aine] += painotettu

    malli = {}
    for aine in aine_pisteet:
        malli[aine] = aine_pisteet[aine] / aine_painot[aine]

    return malli


# ---------------------------------------------------------------------------
# Aikataulun optimointi (heuristiikka)
# ---------------------------------------------------------------------------

def optimoi_aikataulu(malli: dict,
                      tehtävät: list,
                      päivittäinen_max_h: float = 6.0,
                      aloituspäivä: datetime.date = None) -> list:
    """Jakaa tehtävät päivittäisiin opiskelublokkeihin heuristisesti.

    Prioriteettijärjestys:
    1. Tehtävän asettama prioriteetti
    2. Lähin määräaika ensin
    3. Mallin ehdottama optimaalinen kesto

    Palauttaa listan sanakirjoja muodossa:
        [{"päivä": date, "aine": str, "kesto_h": float, "tauko_min": int}, ...]
    """
    if aloituspäivä is None:
        aloituspäivä = datetime.date.today()

    # Kopioidaan tehtävät, jotta alkuperäinen lista ei muutu
    jäljellä = [
        {"aine": t.aine,
         "h": t.tunteja_jäljellä,
         "deadline": t.määräaika,
         "prio": t.prioriteetti}
        for t in tehtävät
    ]

    # Järjestetään: ensin prioriteetti, sitten deadline
    jäljellä.sort(key=lambda x: (x["prio"], x["deadline"]))

    aikataulu = []
    päivä = aloituspäivä

    while any(t["h"] > 0 for t in jäljellä):
        päivän_käytetty = 0.0
        for tehtävä in jäljellä:
            if tehtävä["h"] <= 0:
                continue
            if päivän_käytetty >= päivittäinen_max_h:
                break

            # Mallin suosittelema optimi tälle aineelle (oletusarvo 1.5 h)
            optimi = malli.get(tehtävä["aine"], 1.5)
            # Rajoitetaan yhden session pituus 3 tuntiin
            sessio = min(optimi, 3.0, tehtävä["h"],
                         päivittäinen_max_h - päivän_käytetty)

            # Tauon pituus: 15 min per 45 min opiskelua
            tauko_min = int((sessio * 60 / 45) * 15)

            aikataulu.append({
                "päivä": päivä,
                "aine": tehtävä["aine"],
                "kesto_h": round(sessio, 2),
                "tauko_min": tauko_min,
            })

            tehtävä["h"] -= sessio
            päivän_käytetty += sessio

        päivä += datetime.timedelta(days=1)

        # Turvaraja: ei luoda aikataulua yli 60 päivälle
        if (päivä - aloituspäivä).days > 60:
            break

    return aikataulu


# ---------------------------------------------------------------------------
# Julkinen API
# ---------------------------------------------------------------------------

def ehdota_opiskeluaikataulu(opiskelijadata: list,
                              tehtävät: list,
                              päivittäinen_max_h: float = 6.0) -> list:
    """Pääfunktio: palauttaa ehdotetun opiskeluaikataulun.

    Args:
        opiskelijadata: Lista OpintoPäiväkirjaRivi-olioita.
        tehtävät:       Lista Tehtävä-olioita.
        päivittäinen_max_h: Maksimi opiskelutunnit päivässä.

    Returns:
        Lista sanakirjoja, joissa on päivä, aine, kesto ja tauko.
    """
    malli = lataa_valmis_malli(opiskelijadata)
    suositellut_jaksot = optimoi_aikataulu(
        malli, tehtävät, päivittäinen_max_h
    )
    return suositellut_jaksot


# ---------------------------------------------------------------------------
# Tulostus
# ---------------------------------------------------------------------------

def tulosta_aikataulu(aikataulu: list) -> None:
    """Tulostaa aikataulun selkeässä muodossa."""
    if not aikataulu:
        print("Ei tehtäviä aikataulutettavaksi.")
        return

    nykyinen_päivä = None
    for blokki in aikataulu:
        if blokki["päivä"] != nykyinen_päivä:
            nykyinen_päivä = blokki["päivä"]
            viikonpäivä = nykyinen_päivä.strftime("%A")
            print(f"\n📅 {nykyinen_päivä} ({viikonpäivä})")
            print("-" * 40)
        print(
            f"  📚 {blokki['aine']:<20} "
            f"{blokki['kesto_h']:.1f} h  "
            f"(tauko ~{blokki['tauko_min']} min)"
        )


# ---------------------------------------------------------------------------
# Interaktiivinen käyttöliittymä
# ---------------------------------------------------------------------------

def _kysy_float(kehote: str, oletus: float) -> float:
    arvo = input(kehote).strip()
    if arvo == "":
        return oletus
    try:
        return float(arvo)
    except ValueError:
        return oletus


def _kysy_päivämäärä(kehote: str, oletus: datetime.date) -> datetime.date:
    arvo = input(kehote).strip()
    if arvo == "":
        return oletus
    try:
        return datetime.date.fromisoformat(arvo)
    except ValueError:
        return oletus


def interaktiivinen_käyttöliittymä() -> None:
    """Yksinkertainen tekstipohjainen käyttöliittymä opiskelijalle."""
    print("=" * 50)
    print("  Älykäs Opintosuunnittelija")
    print("=" * 50)

    # Lataa opintopäiväkirja jos löytyy
    data_tiedosto = "esimerkki_data.csv"
    opiskelijadata = lataa_opintopäiväkirja(data_tiedosto)
    if opiskelijadata:
        print(f"\n✅ Ladattu {len(opiskelijadata)} riviä opintopäiväkirjasta.")
    else:
        print("\nℹ️  Opintopäiväkirjaa ei löydy – käytetään oletusarvoja.")

    # Kysy päivittäinen maksimi
    max_h = _kysy_float(
        "\nKuinka monta tuntia päivässä voit opiskella? [6]: ", 6.0
    )

    # Kysy tehtävät
    tehtävät = []
    print("\nSyötä opiskeltavat aineet (tyhjä aine lopettaa):")
    tänään = datetime.date.today()
    while True:
        aine = input("  Aine: ").strip()
        if not aine:
            break
        tunnit = _kysy_float(f"  Arvioi tuntimäärä aineelle '{aine}': ", 5.0)
        oletus_dl = tänään + datetime.timedelta(days=7)
        deadline = _kysy_päivämäärä(
            f"  Määräaika (VVVV-KK-PP) [{oletus_dl}]: ", oletus_dl
        )
        prio_str = input("  Prioriteetti (1=korkein, 3=matala) [1]: ").strip()
        prio = int(prio_str) if prio_str.isdigit() else 1
        tehtävät.append(Tehtävä(aine, tunnit, deadline, prio))

    if not tehtävät:
        print("\nEi tehtäviä syötetty. Lopetetaan.")
        return

    # Muodosta aikataulu
    aikataulu = ehdota_opiskeluaikataulu(opiskelijadata, tehtävät, max_h)

    print("\n" + "=" * 50)
    print("  Ehdotettu opiskeluaikataulu")
    print("=" * 50)
    tulosta_aikataulu(aikataulu)
    print()


# ---------------------------------------------------------------------------
# Käynnistys
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    interaktiivinen_käyttöliittymä()
