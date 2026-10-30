# Wichtige Importe
import os       #Python kann auf Betriebssystem-Funktionen und Umgebungsvariablen zugreifen
from fastapi import FastAPI, HTTPException      #FastAPI-Framework und Ausgabe Fehlermelungen geladen
from pydantic import BaseModel                  #Eingaben validieren und überprüfen
from typing import List, Optional               #Verwendung von Listen-Datentypen und flexiblen Parametern
from sqlalchemy import create_engine, Column, Integer, String       #Werkzeuge um Python-Objekte in Datenbank-Tabellen zu übersetzen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Datenbank-URL aus der Umgebungsvariable holen (wird von Docker Compose übergeben), wenn keine gefunden: Standardwert für lokalen Test
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/oer_db")

# SQLAlchemy Setup
# Wir hängen +psycopg2 an die URL an oder nutzen den Treiber direkt in create_engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@db:5432/oer_db")
engine = create_engine(DATABASE_URL)        #Baut die Verbindung zur DB auf Basis der URL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)     #Erstellt Sitzung, über die Lese- und Schreibbefehle an DB geschickt werden
Base = declarative_base()       #Basisklasse für alle Tabellen-Modelle

# Tabellen-Modell für die Datenbank, Tabelle trägt den Name spiele, Definieren von Spalten als Integer bzw. String, eindeutiger Wert ist id
class SpielModel(Base):
    __tablename__ = "spiele"
    id = Column(Integer, primary_key=True, index=True)
    titel = Column(String, index=True)
    beschreibung = Column(String, nullable=True)
    typ = Column(String)
    spielmechanik = Column(JSON)
    lernziel = Column(String)
    lizenz = Column(String)
    zielgruppe = Column(String, nullable=True)  
    fach = Column(String, index=True, nullable=True)

# Tabellen in der Datenbank beim Start automatisch anlegen, falls noch nicht vorhanden
Base.metadata.create_all(bind=engine)

# FastAPI-Anwendung initialisieren
app = FastAPI(title="OER-Spiele API mit PostgreSQL", version="2.0")

# Pydantic-Schema für den Aufbau eines Datensatzes mit Typen für die Validierung
class OerSpielCreate(BaseModel):
    titel: str
    beschreibung: str
    typ: str
    spielmechanik: List[str]  # (Hinweis: Mechaniken speichern wir für den Start am besten als Text/String ab)
    lernziel: str
    lizenz: str
    zielgruppe: str
    fach: str

# GET: Alle Spiele aus PostgreSQL abrufen
@app.get("/spiele/suchen")                  #Definiert URL Aufruf
def suche_spiele(mechanik: Optional[str] = None, lernziel: Optional[str] = None):       #Durchsucht die PostgreSQL-Datenbank flexibel nach Spielmechanik oder Lernziel
    db = SessionLocal()                     #Öffnet Verbindung zur DB
    query = db.query(SpielModel)            #Holt alle gespeicherten Spiele aus der DB
    
    # Wenn ein Mechanik-Suchbegriff übergeben wurde
    if mechanik:
        query = query.filter(SpielModel.spielmechanik.ilike(f"%{mechanik}%"))   #mit ilike=Groß/Kleinschreibung egal
        
    # Wenn ein Lernziel-Suchbegriff übergeben wurde
    if lernziel:
        query = query.filter(SpielModel.lernziel.ilike(f"%{lernziel}%"))
        
    ergebnisse = query.all()                #Speichert alle gefundenen Spiele in ergebnisse
    db.close()                              #Schließt die Verbindung 
    
    #Gibt die gefundenen Spiele als JSON aus
    return {
        "gefundene_anzahl": len(ergebnisse),
        "ergebnisse": ergebnisse
    }


# POST: Neues Spiel in PostgreSQL speichern
@app.post("/spiele")                        #Definiert URL Aufruf
def erstelle_spiel(spiel: OerSpielCreate):  #Nimmt eingegebene Daten entgegen und prüft sie
    db = SessionLocal()                     #Öffnet Verbindung zur Datenbank
    neuer_eintrag = SpielModel(
        titel=spiel.titel,
        beschreibung=spiel.beschreibung,
        typ=spiel.typ,
        lernziel=spiel.lernziel,
        lizenz=spiel.lizenz,
        zielgruppe=spiel.zielgruppe,
        fach=spiel.fach
    )
    db.add(neuer_eintrag)                   #Fügt neuen Datensatz hinzu
    db.commit()                             #Speichert die Änderungen in die DB
    db.refresh(neuer_eintrag)               #Aktualisiert den Eintrag, um generierte ID zu erhalten
    db.close()                              #Schließt die Verbindung 
    return {"status": "Erfolg", "daten": neuer_eintrag}     #Gibt den erstellten Datensatz als JSON aus
