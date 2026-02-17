# Testanleitung: Clique-Einladungslink und Freund-Flow

So testest du die neuen Funktionen (Deep-Link, Banner, Produktvorauswahl, E-Mail-Platzhalter).

## Voraussetzungen

- Laufender pretix-Server (z.B. `python manage.py runserver 8000` aus `src/`)
- Plugin **pretix-cliques** für ein Event aktiviert
- Event mit mindestens einem **Eintritts-Ticket** (admission) und laufendem Vorverkauf

## 1. Clique erstellen und Bestellung aufgeben (als „Admin“)

1. Im **Frontend** zum Event gehen (Presale-URL, z.B. `http://localhost:8000/orga/event/`).
2. Ein **Ticket in den Warenkorb** legen und zur Kasse gehen.
3. Beim Checkout-Schritt **„Clique“**:
   - **„Ich möchte eine neue Clique erstellen“** wählen.
   - Clique-Name und optional Passwort eintragen, weiter.
4. Bestellung **bis zum Ende** durchziehen (Zahlung abschließen oder „Kostenlos bestellen“).
5. Auf die **Bestellbestätigungsseite** (Order-Detail) gehen.

**Erwartung:**

- Es erscheint der Bereich **„Clique“** mit Hinweis, dass du die Clique erstellt hast.
- Darunter: **„Teile diesen Link mit deinen Freunden …“** und ein **Einladungslink** (z.B. `…/clique/Ab3xY9kL2mNpQrSt/join/`).
- Der Link enthält **keine Zahlen-ID**, sondern einen kurzen Token.

## 2. Einladungslink per E-Mail (Platzhalter)

1. In den **Event-Einstellungen** → **E-Mail** die Vorlage für **„Bestellung aufgegeben“** (oder „Zahlung eingegangen“) bearbeiten.
2. Im Text z.B. einbauen:  
   `Teile diesen Link mit deinen Freunden: {clique_join_url}`
3. Eine **neue Bestellung mit neuer Clique** aufgeben (wie in Abschnitt 1).
4. **E-Mail** der Bestellbestätigung prüfen.

**Erwartung:**

- In der E-Mail steht die **gleiche Einladungs-URL** wie auf der Bestellseite (nur für Clique-Ersteller; bei „nur beitreten“ bleibt `{clique_join_url}` leer).

## 3. Freund klickt auf den Link (Haupttest)

1. **Einladungslink kopieren** (von der Bestellseite oder aus der E-Mail).
2. In einem **anderen Browser** oder **Inkognito-Fenster** den Link öffnen (damit du nicht schon eingeloggt/anderer Warenkorb bist).

**Erwartung:**

- **Redirect** zur Event-Startseite.
- **Banner oben** (blau/Info):  
  *„Du trittst einer Clique bei – Du bist hier, um der Clique **[Name]** beizutreten. Lege ein Ticket …“*
- **Dasselbe Produkt** wie der einladende Freund ist **bereits im Warenkorb** (z.B. 1× Weekend-Ticket).

## 4. Checkout als Freund

1. Mit dem **gefüllten Warenkorb** (vom Link) **„Zur Kasse“** / Checkout starten.
2. Durch die Schritte bis zum **Schritt „Clique“** gehen.

**Erwartung:**

- Beim Schritt **„Clique“** ist **„Ich möchte einer bestehenden Clique beitreten“** vorausgewählt.
- Clique-**Name** ist schon ausgefüllt.
- **Grüner Hinweis**: *„Du trittst dieser Clique bei: [Name] – Gib unten das Cliquen-Passwort ein …“*
- Nur noch **Cliquen-Passwort** eintragen (falls die Clique eines hat) und **Weiter**.
4. Bestellung **abschließen**.

**Erwartung:**

- Die Bestellung gehört zur **gleichen Clique** wie die des einladenden Freundes (in der Cliquen-Übersicht im Backend sichtbar).

## 5. Randfälle prüfen

- **Link ohne Produktvorauswahl:** Wenn das Admin-Ticket z.B. ausverkauft ist, soll der Freund trotzdem zur Event-Seite kommen, **Banner** und **Clique in der Session** sollen da sein; er legt manuell ein anderes Ticket in den Warenkorb und kann beim Checkout derselben Clique beitreten.
- **Kein Link für „nur Beitreter“:** Bestellung mit „Clique beitreten“ (nicht erstellen) aufgeben → auf der Bestellseite gibt es **keinen** Einladungslink.
- **Token in URL:** Mehrere Links mit unterschiedlichen Tokens erzeugen (verschiedene Cliquen) und prüfen, dass jeweils die richtige Clique vorausgewählt wird.

## Kurz-Checkliste

| Test | Erwartung |
|------|-----------|
| Clique erstellen + bestellen | Einladungslink auf Bestellseite (Token, keine ID) |
| E-Mail mit `{clique_join_url}` | URL in E-Mail für Clique-Admin |
| Link in neuem Browser öffnen | Banner „Du trittst Clique X bei“, gleiches Produkt im Warenkorb |
| Checkout bis Schritt Clique | Grüner Kasten „Du trittst dieser Clique bei: X“, nur Passwort eingeben |
| Bestellung abschließen | Bestellung in derselben Clique |

Wenn du willst, können wir einen davon Schritt für Schritt mit echten URLs durchgehen (z.B. nur „Freund klickt Link“).
