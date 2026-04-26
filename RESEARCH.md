# FotoDerp - Feature Analyse & Vergleich

## Was ist FotoDerp?
FotoDerp ist eine KI-gestützte Desktop-Software zur Bildverwaltung, -suche und -bewertung für Fotografen. Läuft auf Windows und macOS. Nutzt proprietäre KI-Modelle für die Analyse.

---

## Kernfunktionen von FotoDerp

### 1. Automatisches KI-Tagging (Stichwortzuweisung)
- Automatische Erkennung und Zuweisung von Stichwörtern zu Bildern
- Objekte, Szenen, Aktivitäten, Farben, Jahreszeiten etc.
- Bis zu 10-fach präzisere Erkennungsleistung (2024er Version)

### 2. Gesichtserkennung
- Automatische Erkennung und Gruppierung von Personen
- Einzelpersonen identifizierbar und benennbar
- Suche nach bestimmten Personen im gesamten Archiv

### 3. Ähnlichkeitssuche (Visual Search)
- Finde visuell ähnliche Bilder im Archiv
- Gruppierung nach visueller Ähnlichkeit
- Nützlich für Culling und Bildauswahl

### 4. Freitextsuche (Natural Language Search)
- KI-basierte Suche mit natürlichen Spracheingaben
- z.B. "Sonnenuntergang am Strand mit rotem Auto"
- Extrem präzise Ergebnisqualität

### 5. Ästhetische Beurteilung (AI Rating)
- KI bewertet die ästhetische Qualität jedes Fotos
- Wettbewerbserprobte算法 für Bildqualität
- Automatisches Ranking der besten Bilder

### 6. Culling-Tools
- Gruppierung nach: Personen, visuelle Ähnlichkeit, Aufnahmedatum, Sequenzen
- Smart Selection: Automatische Auswahl der besten Bilder pro Gruppe
- Filterkriterien:
  - Schärfe (Gesamtschärfe)
  - Augenschärfe
  - Offene/Geschlossene Augen
  - Lächeln
  - Über-/Unterbelichtung
  - Duplikate

### 7. Duplikat-Erkennung
- Visuelle Duplikate finden und entfernen
- Integriert in FotoDerp Search seit 2024

### 8. GPS-basierte Suche
- Suche nach Fotos an bestimmten Orten
- Editierfunktion für GPS-Daten
- Kartendarstellung möglich

### 9. Metadaten-Verwaltung
- EXIF, IPTC, XMP Metadaten
- Nutzungsrechtdauer als ergänzende Metadaten
- Filteroptionen basierend auf Metadaten

### 10. Analytics
- Einblicke in Fotogewohnheiten
- Equipment-Analyse und Kaufentscheidungen
- Fähigkeiten-Verbesserung durch Daten

### 11. Diashows
- Individuell gestaltbare Diashows
- Verschiedene Vorlagen und Übergänge

### 12. RAW-Unterstützung
- Vollständige RAW-Format-Unterstützung
- Hochwertige Vorschau-Generierung

### 13. Exciere Search (Lightroom Plugin)
- Plugin für Adobe Lightroom Classic
- KI-Suchfunktionen direkt in Lightroom
- Duplikatefinder integriert

---

## Technical Requirements (Competitor Analysis)
- Prozessor: Mehrkernprozessor mit 64-bit und AVX
- RAM: Min. 8GB (empfohlen 16GB+)
- Festplatte: ~375MB Basis + Vorschau-Speicher (~25GB bei 100k Fotos)
- Betriebssystem: Windows 11 / macOS 10.14+

---

## Lücken / Opportunities für FotoDerp

| Feature | FotoDerp | FotoDerp Opportunity |
|---------|--------|---------------------|
| KI-Backend | Proprietär, lokal | OpenAI-kompatibel (llama.cpp) - backend-unabhängig |
| Plattform | Windows/macOS Desktop | Cross-platform (CLI + Web UI?) |
| Lizenz | Einmalige Gebühr (~100€) | Open Source, kostenlos |
| OCR/Texterkennung | Nicht erwähnt | Text in Bildern erkennen (LLM-vision) |
| Semantische Suche | Ja (eigenes KI) | Mit OpenAI-kompatiblen Endpoints |
| API | Exciere API (begrenzt) | Vollständige REST API |
| Cloud-Sync | Nicht vorhanden | Optionaler Cloud-Sync |
| Mobile App | Nicht vorhanden | Responsive Web UI |
| Batch-Processing | Basis | Erweiterte Batch-Operationen |
| Plugin-System | Nur Lightroom | Erweiterbares Plugin-System |

---

## Technologie-Stack Vorschlag für FotoDerp

### Backend
- **Sprache**: Python 3.11+ (schnelle Entwicklung, gute KI-Integration)
- **KI-Backend**: llama.cpp OpenAI-kompatibler Endpunkt (`/v1/chat/completions`)
  - Für Bildbeschreibung: Multimodale Modelle (LLaVA, Qwen-VL, etc.)
  - Für Text: Beliebige OpenAI-kompatible LLMs
- **Datenbank**: SQLite (einfach) oder PostgreSQL (skalierbar)
- **Bildspeicherung**: Dateisystem + Index in DB
- **API**: FastAPI (async, automatisch Docs)

### Vorschau-Generierung
- **Bibliothek**: Pillow / Pillow-SIMD oder OpenCV
- **RAW**: libraw / rawpy

### Frontend (optional, Phase 2)
- **Web UI**: React/Next.js oder SvelteKit
- **Mobile**: Responsive Design / PWA

### Bildanalyse-Pipeline
1. Dateierkennung & Metadaten-Extraktion (EXIF)
2. Vorschau generieren
3. KI-Analyse via llama.cpp Endpoint:
   - Objekterkennung
   - Szenenerkennung
   - Gesichtserkennung (eigenes Modell oder API)
   - Ästhetik-Bewertung
   - Texterkennung (OCR via Vision-Modell)
4. Index in Datenbank für schnelle Suche
