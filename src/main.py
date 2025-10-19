# rezolvator_spanzuratoarea.py
import sys
import csv
from collections import Counter

VOCALE = ["e", "a", "i", "o", "u", "ă", "â", "î"]
CONSOANE = ["r", "n", "t", "l", "s", "c", "d", "p", "m", "g", "h", "b", "f", "v", "ș", "ț", "k", "j", "x", "z", "q",
            "y", "w"]
ORDINE_LITERE_BAZA = VOCALE + CONSOANE
BOOST_REPETITII = ["r", "n", "t", "l", "s"]
CONSOANE_BUNE_LANGA_VOCALA = ["r", "n", "t", "l", "s", "c", "d", "p", "m"]

# Dicționar global
DICTIONAR = []


def incarca_dictionar(cale_dictionar="lexicon_ro.txt"):
    """Încarcă cuvintele din dicționar."""
    global DICTIONAR
    try:
        with open(cale_dictionar, "r", encoding="utf-8") as f:
            DICTIONAR = [normalizare(line) for line in f if line.strip()]
        print(f"Dicționar încărcat: {len(DICTIONAR)} cuvinte.")
    except FileNotFoundError:
        print(f"ATENȚIE: Dicționarul {cale_dictionar} nu a fost găsit. Se va folosi metoda de bază.")
        DICTIONAR = []


def normalizare(text: str) -> str:
    return (text or "").strip().lower()


def potriveste_pattern(cuvant, pattern):
    """Verifică dacă un cuvânt se potrivește cu pattern-ul (* = orice literă)."""
    if len(cuvant) != len(pattern):
        return False
    for c, p in zip(cuvant, pattern):
        if p != '*' and p != c:
            return False
    return True


def filtreaza_candidati(pattern, litere_incercate):
    """Returnează cuvintele din dicționar care se potrivesc cu pattern-ul și nu conțin litere greșite."""
    candidati = []
    for cuvant in DICTIONAR:
        if not potriveste_pattern(cuvant, pattern):
            continue
        # Exclude cuvintele care conțin litere deja încercate greșit
        litere_gresite = litere_incercate - set(pattern)
        if any(l in cuvant for l in litere_gresite):
            continue
        candidati.append(cuvant)
    return candidati


def alege_litera_din_candidati(candidati, litere_incercate):
    """Alege cea mai frecventă literă din candidații posibili."""
    if not candidati:
        return None

    # Numără frecvența literelor în pozițiile necunoscute
    litere_disponibile = []
    for cuvant in candidati:
        for litera in cuvant:
            if litera not in litere_incercate:
                litere_disponibile.append(litera)

    if not litere_disponibile:
        return None

    # Returnează cea mai frecventă literă
    freq = Counter(litere_disponibile)
    return freq.most_common(1)[0][0]


def valideaza_rand(id_joc, model, cuvant_corect):
    if not id_joc or not model or not cuvant_corect:
        return False, "Lipsesc câmpuri obligatorii."
    if len(model) != len(cuvant_corect):
        return False, "Lungimi diferite între model și cuvântul corect."
    for lit_model, lit_cuv in zip(model, cuvant_corect):
        if lit_model != '*' and lit_model != lit_cuv:
            return False, "Modelul conține literă care nu corespunde cuvântului țintă."
    return True, ""


def dezvaluie(model, cuvant_corect, litera):
    rezultat = list(model)
    for i, (m, c) in enumerate(zip(model, cuvant_corect)):
        if m == '*' and c == litera:
            rezultat[i] = litera
    return "".join(rezultat)


def are_repetitii_model(model: str) -> bool:
    frec = {}
    for ch in model:
        if ch != '*':
            frec[ch] = frec.get(ch, 0) + 1
            if frec[ch] >= 2:
                return True
    return False


def exista_stea_langa_vocala(model: str) -> bool:
    # True dacă există o stea adiacentă unei vocale cunoscute
    n = len(model)
    for i, ch in enumerate(model):
        if ch == '*':
            if (i > 0 and model[i - 1] in VOCALE) or (i < n - 1 and model[i + 1] in VOCALE):
                return True
    return False


def exista_stea_langa_consoana(model: str) -> bool:
    # True dacă există o stea adiacentă unei consoane cunoscute
    n = len(model)
    for i, ch in enumerate(model):
        if ch == '*':
            if (i > 0 and model[i - 1] in CONSOANE) or (i < n - 1 and model[i + 1] in CONSOANE):
                return True
    return False


def ordine_dinamica(model: str, litere_incercate: set) -> list:
    """Generează o ordine de ghicire adaptată la model, CU dicționar."""

    # Încercăm mai întâi cu dicționarul
    if DICTIONAR:
        candidati = filtreaza_candidati(model, litere_incercate)
        if candidati:
            litera_aleasa = alege_litera_din_candidati(candidati, litere_incercate)
            if litera_aleasa:
                return [litera_aleasa]

    # Fallback: metoda de bază (fără dicționar)
    baza_vocale = [l for l in VOCALE if l not in litere_incercate]
    baza_consoane = [l for l in CONSOANE if l not in litere_incercate]

    preferate = []

    if exista_stea_langa_vocala(model):
        cons_bune = [l for l in CONSOANE_BUNE_LANGA_VOCALA if l not in litere_incercate]
        baza_consoane = [l for l in baza_consoane if l not in set(cons_bune)]
        preferate.extend(cons_bune)

    if are_repetitii_model(model):
        boost = [l for l in BOOST_REPETITII if l not in litere_incercate]
        boost = [l for l in boost if l not in set(preferate)]
        baza_consoane = [l for l in baza_consoane if l not in set(boost)]
        preferate.extend(boost)

    ord_final = []
    if exista_stea_langa_consoana(model):
        ord_final.extend(baza_vocale)
    else:
        ord_final.extend(baza_vocale)

    for l in preferate:
        if l not in ord_final:
            ord_final.append(l)

    for l in baza_consoane:
        if l not in ord_final:
            ord_final.append(l)

    for l in ORDINE_LITERE_BAZA:
        if l not in litere_incercate and l not in ord_final:
            ord_final.append(l)

    return ord_final


def rezolva_un_joc(model_initial, cuvant_corect):
    model = model_initial
    incercari = []
    litere_incercate = set(ch for ch in model if ch != '*')

    while model != cuvant_corect:
        ordinea = ordine_dinamica(model, litere_incercate)
        if not ordinea:
            break

        litera = ordinea[0]  # luăm prima literă recomandată
        litere_incercate.add(litera)
        incercari.append(litera)

        if litera in cuvant_corect:
            model = dezvaluie(model, cuvant_corect, litera)

    stare = "OK" if model == cuvant_corect else "FAIL"
    return len(incercari), model, stare, " ".join(incercari)


def main():
    if len(sys.argv) != 3:
        print("Utilizare: python rezolvator_spanzuratoarea.py intrare.csv iesire.csv")
        sys.exit(1)

    # Încarcă dicționarul la început
    incarca_dictionar()

    cale_intrare, cale_iesire = sys.argv[1], sys.argv[2]
    randuri_iesire = []
    erori = []

    with open(cale_intrare, "r", encoding="utf-8", newline="") as fisier_intrare:
        cititor = csv.reader(fisier_intrare)
        prima_linie = next(cititor, None)
        if prima_linie is None:
            print("Fișierul de intrare este gol.")
            sys.exit(1)

        def pare_antet(coloane):
            text = ",".join(col.strip().lower() for col in coloane)
            return ("game_id" in text and "pattern" in text) or ("cuvant_tinta" in text) or ("id_joc" in text)

        if not pare_antet(prima_linie):
            cititor = (rand for rand in [prima_linie] + list(cititor))

        for index, coloane in enumerate(cititor, start=1):
            if len(coloane) < 3:
                erori.append((index, "Linie cu prea puține coloane."))
                continue

            id_joc = normalizare(coloane[0])
            model_initial = normalizare(coloane[1])
            cuvant_corect = normalizare(coloane[2])

            valid, motiv = valideaza_rand(id_joc, model_initial, cuvant_corect)
            if not valid:
                erori.append((index, f"Invalid: {motiv}"))
                continue

            total_incercari, cuvant_gasit, stare, secventa = rezolva_un_joc(model_initial, cuvant_corect)
            randuri_iesire.append([id_joc, str(total_incercari), cuvant_gasit, stare, secventa])

    with open(cale_iesire, "w", encoding="utf-8", newline="") as fisier_iesire:
        scriitor = csv.writer(fisier_iesire)
        scriitor.writerow(["id_joc", "total_incercari", "cuvant_gasit", "stare", "secventa_incercari"])
        scriitor.writerows(randuri_iesire)

    # statistici
    suma_incercari = sum(int(r[1]) for r in randuri_iesire)
    numar_jocuri = len(randuri_iesire)
    ok = sum(1 for r in randuri_iesire if r[3] == "OK")
    fail = sum(1 for r in randuri_iesire if r[3] == "FAIL")

    print("\n--- Statistici generale ---")
    print(f"Număr total de jocuri: {numar_jocuri}")
    print(f"Rezolvate corect (OK): {ok}")
    print(f"Nerezolvate (FAIL): {fail}")
    print(f"Suma totală a încercărilor: {suma_incercari}")

    if erori:
        print("\nAu existat linii omise sau invalide:", file=sys.stderr)
        for linie, mesaj in erori:
            print(f" - linia {linie}: {mesaj}", file=sys.stderr)


if __name__ == "__main__":
    main()