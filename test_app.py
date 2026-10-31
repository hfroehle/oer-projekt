import pytest
from fastapi.testclient import TestClient
from main import app, SessionLocal, SpielModel, Base, engine

# TestClient für die FastAPI-Anwendung initialisieren
client = TestClient(app)

# Vor jedem Test eine saubere Test-Datenbank aufsetzen
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_get_spiele_leer():
    """Test 1: Prüft, ob der Abruf aller Spiele bei leerer Datenbank funktioniert (200 OK)."""
    response = client.get("/spiele")
    assert response.status_code == 200
    data = response.json()
    assert "spiele" in data
    assert len(data["spiele"]) == 0

def test_erstelle_und_suche_spiel():
    """Test 2: Testet das Anlegen eines OER-Spiels (Inklusion) und die anschließende Suche nach Fach und Lernziel."""
    # Gültiger Test-Datensatz für ein OER-Lernspiel basierend auf dem Metadatenstandard
    neues_spiel = {
        "titel": "Das große SQL-Duell",
        "beschreibung": "Ein interaktives Lernspiel zum Optimieren von Datenbankabfragen.",
        "typ": "Interaktives Quiz",
        "spielmechanik": ["Wettbewerb", "Punkte- und Belohnungsstrukturen"],
        "lernziel": "Datenbankabfragen optimieren",
        "lizenz": "CC-BY 4.0",
        "zielgruppe": "Hochschule",
        "fach": "Informatik"
    }

    # Spiel via POST-Request anlegen
    response_post = client.post("/spiele", json=neues_spiel)
    assert response_post.status_code == 200
    res_data = response_post.json()
    assert res_data["status"] == "Erfolg"
    assert res_data["daten"]["titel"] == "Das große SQL-Duell"

    # Überprüfen, ob das Spiel über den Such-Endpunkt gefunden wird
    response_search = client.get("/spiele/suchen?fach=Informatik")
    assert response_search.status_code == 200
    search_data = response_search.json()
    assert search_data["gefundene_anzahl"] == 1
    assert search_data["ergebnisse"][0]["titel"] == "Das große SQL-Duell"

def test_pydantic_validierung_fehlendes_feld():
    """Test 3: Prüft die Pydantic-Validierung. Wenn Pflichtfelder fehlen, muss ein 422-Fehler kommen."""
    unvollstaendiges_spiel = {
        "titel": "Unvollständiges Spiel",
        # "typ" und "lernziel" fehlen absichtlich als Pflichtfelder
        "spielmechanik": ["Kooperation"],
        "lizenz": "CC0"
    }

    response = client.post("/spiele", json=unvollstaendiges_spiel)
    # Pydantic blockiert ungültige Daten automatisch mit Status Code 422 (Unprocessable Entity)
    assert response.status_code == 422

def test_pydantic_validierung_falsches_format():
    """Test 4: Prüft, ob 'spielmechanik' zwingend als Liste (List[str]) übergeben werden muss."""
    ungueltiges_format = {
        "titel": "Falsches Format Spiel",
        "typ": "Simulation",
        "spielmechanik": "Wettbewerb", # Falsch: Sollte eine Liste sein, ist aber nur ein String
        "lernziel": "Testen",
        "lizenz": "CC-BY"
    }

    response = client.post("/spiele", json=ungueltiges_format)
    # Erwartet ebenfalls einen Validierungsfehler
    assert response.status_code == 422
