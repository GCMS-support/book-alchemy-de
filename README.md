# Book Alchemy DE

Digitale Bibliothek mit Flask, Flask-SQLAlchemy und SQLite.

## Start in Codio

~~~sh
python -m pip install -r requirements.txt
python seed.py
python -m flask run --host=0.0.0.0 --port=5002
~~~

Danach **Open Website in Browser** öffnen. Alternativ: python app.py.
Die Datenbank data/library.sqlite wird automatisch erstellt. seed.py ergänzt idempotent sechs Autoren und sechs Bücher über die Formular-POST-Routen.

## Funktionen

- Autoren und Bücher hinzufügen, Beziehungen und Datenbank-Constraints.
- ISBN-10/13 inklusive Prüfziffer; Datum, Pflichtfelder und doppelte ISBNs validieren.
- Buchübersicht mit Open-Library-Covern, Suche nach Titel/Autor und Sortierung nach Titel, Autor oder Jahr.
- Buch löschen (Autor bleibt bestehen); Autor mit zugehörigen Büchern löschen (Cascade).
- Dynamische Buch- und Autorendetailseiten sowie Bewertungen 1–10.
- Responsive deutsche Oberfläche, CSRF-Schutz und HTML-Escaping.
- KI-Buchempfehlungen über OpenRouter; Übermittlung von Titeln, Autoren und Bewertungen erst nach Zustimmung.

## OpenRouter konfigurieren

Eine lokale, von Git ignorierte .env-Datei anlegen:

~~~dotenv
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini
SECRET_KEY=replace-with-a-long-random-value
~~~

Endpoint: https://openrouter.ai/api/v1/chat/completions

Der Standardslug openai/gpt-4o-mini ist im verwendeten Arbeitsbereich erlaubt. Das kostenlose Routing openrouter/free wurde durch dessen Modellrichtlinien blockiert; die Richtlinien wurden nicht verändert. Andere erlaubte Modelle können über OPENROUTER_MODEL gewählt werden. API-Nutzung kann Kosten verursachen. Schlüssel nicht in Git speichern.

## Tests und Verifikation

~~~sh
python -m unittest -v test_app
~~~

11 Integrationstests mit isolierter In-Memory-Datenbank prüfen Seiten, Anlage, Validierung, Suche, Sortierung, Bewertungen, Löschung, Cascade, CSRF, Escaping und simulierte KI-Antworten/Fehler. Die Beispieldatenbank bleibt unverändert.

Zusätzlich wurde am 8. September 2026 eine echte Empfehlung über OpenRouter erfolgreich erzeugt. Hauptseite, Cover, Suche und Detailseiten wurden im Browser geprüft. KI-Ausgaben können Fehler enthalten und sollten geprüft werden.

## Struktur

- app.py: App-Factory, Konfiguration und Routen.
- data_models.py: Datenmodelle.
- templates/: Jinja-Seiten.
- static/style.css: responsive Gestaltung.
- seed.py: Beispieldaten über POST-Routen.
- test_app.py: Integrationstests.

Die Datenbank entsteht beim Start; Beispieldaten sind über seed.py reproduzierbar. Die Anwendung ist ein Lernprojekt ohne Benutzerkonten. Für öffentlichen Mehrbenutzerbetrieb sind Authentifizierung und ein Produktionsserver erforderlich.

## Aufgabenstand

Schritte 1–6 und Bonus 1–5 implementiert. Repository: https://github.com/GCMS-support/book-alchemy-de

## Dokumentation

- https://flask-sqlalchemy.palletsprojects.com/en/stable/quickstart/
- https://openrouter.ai/docs/quickstart
- https://covers.openlibrary.org/
