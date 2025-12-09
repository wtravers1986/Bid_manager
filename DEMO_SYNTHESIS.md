# Demo Script: Document Synthesis Flow

Dit script beschrijft stap voor stap hoe je de Document Synthesis functionaliteit gebruikt om meerdere documenten te combineren tot één geïntegreerd document.

## Voorbereiding

1. **Zorg dat de applicatie draait:**
   ```bash
   docker-compose up -d
   ```

2. **Controleer dat de services actief zijn:**
   - Backend: http://localhost:8000
   - Streamlit: http://localhost:8501
   - Database en Redis moeten healthy zijn

3. **Zorg dat je PDF bestanden in de `data/` folder hebt:**
   - Plaats minimaal 2-3 PDF bestanden die je wilt synthetiseren
   - Bijvoorbeeld: `document1.pdf`, `document2.pdf`, `document3.pdf`

## Demo Flow

### Stap 1: Open de Streamlit Interface

1. Open je browser en ga naar: **http://localhost:8501**
2. Klik op de tab **"📝 Synthesis"** bovenaan

### Stap 2: Indexeer Documenten (indien nog niet gedaan)

**Als je documenten nog niet geïndexeerd zijn:**

1. Ga naar de tab **"📄 Index Documents"**
2. Klik op **"Index All Documents"**
3. Wacht tot de indexering voltooid is (je ziet een success message)
4. Ga terug naar de **"📝 Synthesis"** tab

**Waarom indexeren?**
- Documenten worden opgeslagen in de vector store voor semantische zoekopdrachten
- LLM-gebaseerde chunking zorgt voor logische paragraafgrenzen
- Dit maakt het vinden van relevante paragrafen veel accurater

### Stap 3: Maak een Synthesis Session

1. In de **"📝 Synthesis"** tab, zie je **"Step 1: Create Session"**
2. Voer een **Session Name** in (bijvoorbeeld: "Engine Maintenance Synthesis")
3. Selecteer de **PDF bestanden** die je wilt synthetiseren:
   - Vink de checkboxes aan voor de gewenste bestanden
   - Minimaal 2 bestanden aanbevolen voor een goede synthesis
4. Klik op **"➕ Create Session"**
5. Je ziet een success message: "✅ Session created successfully!"
6. De session ID wordt opgeslagen en je kunt verder naar de volgende stap

**Demo tip:** 
- Gebruik documenten met overlappende onderwerpen maar verschillende details
- Dit geeft het beste resultaat voor demonstratie

### Stap 4: Analyseer Document Structuren

1. Scroll naar **"Step 2: Analyze Document Structures"**
2. Klik op **"🔍 Analyze Structures & Generate Inventory Table"**
3. Wacht terwijl het systeem:
   - De documenten parseert (zonder LLM chunking voor snelheid)
   - Structuren analyseert (headings, secties)
   - Een geïntegreerde inventory table genereert met AI
4. Je ziet een success message wanneer de analyse klaar is

**Wat gebeurt er achter de schermen?**
- Elk document wordt geanalyseerd op structuur (headings, secties)
- De AI combineert alle structuren tot één logische table of contents
- De inventory table bevat alle unieke topics uit alle documenten

### Stap 5: Review & Edit Inventory Table

1. Scroll naar **"Step 3: Review & Edit Inventory Table"**
2. Je ziet een bewerkbare tabel met:
   - **Order**: Volgorde van de sectie
   - **Title**: Titel van de sectie
   - **Level**: Hiërarchisch niveau (1 = hoofd, 2 = sub, 3 = sub-sub, etc.)
3. **Bewerk de tabel:**
   - Voeg secties toe door op "Add row" te klikken
   - Verwijder secties door rijen te verwijderen
   - Pas titels aan
   - Wijzig levels voor hiërarchie
   - Sleep rijen om de volgorde te wijzigen
4. Klik op **"💾 Save Inventory Table"** wanneer je klaar bent

**Demo tips:**
- Probeer een logische flow te creëren (Intro → Procedures → Safety → Maintenance)
- Gebruik levels om subsecties te maken
- Zorg dat alle belangrijke topics uit de bron documenten vertegenwoordigd zijn

### Stap 6: Review Paragraphs per Sectie

1. Scroll naar **"Step 4: Review Paragraphs by Section"**
2. Voor elke sectie in je inventory table:
   - Klik op de expander om de sectie te openen
   - Klik op **"🔍 Find Paragraphs for: [Section Title]"**
   - Wacht terwijl het systeem relevante paragrafen vindt

**Wat gebeurt er?**
- Vector search vindt kandidaat-paragrafen
- LLM valideert de relevantie van elke paragraaf voor de sectie
- Alleen relevante, unieke paragrafen worden getoond
- Elke paragraaf wordt volledig getoond (niet afgekapt)

3. **Review de paragrafen:**
   - Lees de volledige paragraaf content
   - Bekijk de LLM relevance score (hoe hoger, hoe relevanter)
   - Check de bron (filename en page number)
   - Vink de checkbox aan voor paragrafen die je wilt behouden

4. **Herhaal voor alle secties:**
   - Ga door elke sectie in je inventory table
   - Selecteer de beste paragrafen voor elke sectie
   - Onthoud: elke paragraaf kan maar één keer gebruikt worden

5. Klik op **"💾 Save Paragraph Selections"** wanneer je klaar bent

**Demo tips:**
- Selecteer paragrafen die complementair zijn (niet duplicaten)
- Kies de meest complete/accurate versie bij tegenstrijdigheden
- Zorg dat elke sectie minimaal één paragraaf heeft

### Stap 7: Genereer het Synthesis Document

1. Scroll naar **"Step 5: Generate Synthesis Document"**
2. Klik op **"📝 Generate Final Document"**
3. Wacht terwijl het systeem:
   - Alle geselecteerde paragrafen verzamelt
   - Een DOCX document genereert met de juiste structuur
   - Headings, paragrafen en bronreferenties toevoegt
4. Je ziet een success message: "✅ Document generated successfully!"

5. **Download het document:**
   - Klik op **"📥 Download DOCX Document"**
   - Het bestand wordt gedownload als `synthesis_session_[ID].docx`
   - Open het in Microsoft Word of een andere DOCX viewer

**Wat zit er in het document?**
- Titel: "Synthesis Document"
- Lijst van bron documenten
- Alle secties uit je inventory table met correcte hiërarchie
- Geselecteerde paragrafen per sectie
- Bronreferenties (filename en page number) bij elke paragraaf
- Professionele opmaak met margins en spacing

## Demo Scenario's

### Scenario 1: Technische Handleidingen Combineren

**Setup:**
- 3 PDF's: "Engine Maintenance v1", "Engine Maintenance v2", "Engine Maintenance v3"
- Doel: Creëer één complete handleiding met alle informatie

**Stappen:**
1. Maak session met alle 3 documenten
2. Analyseer structuren → AI genereert logische TOC
3. Review inventory → Pas aan naar: Intro, Procedures, Safety, Maintenance, Troubleshooting
4. Voor elke sectie: vind paragrafen, selecteer beste versies
5. Genereer document → Download en review

**Verwachte resultaat:**
- Complete handleiding met alle procedures
- Geen duplicaten
- Tegenstrijdigheden opgelost door beste versie te kiezen

### Scenario 2: Policy Documenten Synthetiseren

**Setup:**
- 2 PDF's: "Company Policy 2023", "Company Policy 2024"
- Doel: Creëer geüpdatete policy met nieuwste informatie

**Stappen:**
1. Maak session met beide documenten
2. Analyseer → AI identificeert nieuwe/gewijzigde secties
3. Review inventory → Zorg dat alle policy areas vertegenwoordigd zijn
4. Selecteer paragrafen → Kies meest recente/complete versies
5. Genereer → Download en review

**Verwachte resultaat:**
- Up-to-date policy document
- Alle belangrijke secties behouden
- Nieuwe informatie geïntegreerd

## Troubleshooting

### Probleem: "No PDFs found in data folder"
**Oplossing:**
- Controleer dat PDF bestanden in `./data/` folder staan
- Check dat bestandsnamen eindigen op `.pdf`
- Herstart Streamlit container: `docker-compose restart streamlit`

### Probleem: Timeout bij "Analyze Structures"
**Oplossing:**
- Timeout is verhoogd naar 5 minuten
- Als het nog steeds timeout: check backend logs
- Probeer met minder/m kleinere documenten eerst

### Probleem: Geen paragrafen gevonden voor een sectie
**Oplossing:**
- Check of documenten geïndexeerd zijn
- Probeer een bredere sectie titel
- Check backend logs voor errors

### Probleem: DOCX download werkt niet
**Oplossing:**
- Check browser console voor errors
- Probeer een andere browser
- Check dat document succesvol gegenereerd is (success message)

## Tips voor een Goede Demo

1. **Voorbereiding:**
   - Zorg dat je 2-3 relevante PDF's hebt
   - Test de flow eerst zelf voordat je demo geeft
   - Zorg dat documenten geïndexeerd zijn

2. **Tijdens de demo:**
   - Leg uit wat er achter de schermen gebeurt
   - Toon de LLM-powered features (structure analysis, paragraph validation)
   - Benadruk de intelligentie van het systeem (geen duplicaten, relevante paragrafen)

3. **Highlights:**
   - **LLM Chunking**: Logische paragraafgrenzen tijdens indexering
   - **AI Structure Analysis**: Automatische TOC generatie
   - **LLM Paragraph Validation**: Alleen relevante paragrafen
   - **Duplicate Prevention**: Elke paragraaf maar één keer
   - **Professional Output**: DOCX met correcte opmaak

4. **Q&A voorbereiding:**
   - Hoe werkt de LLM chunking? → 5k tokens windows met overlap, logische boundaries
   - Hoe wordt relevantie bepaald? → Vector search + LLM validation met document context
   - Kan ik de inventory table aanpassen? → Ja, volledig bewerkbaar
   - Wat als documenten tegenstrijdig zijn? → Gebruiker kiest welke versie te gebruiken

## Vervolgstappen

Na de demo kun je:
- De gegenereerde DOCX verder bewerken in Word
- Een nieuwe session maken met andere documenten
- De inventory table aanpassen en opnieuw genereren
- Experimenteren met verschillende document combinaties

## Conclusie

De Document Synthesis flow combineert:
- **Intelligente analyse** (AI-powered structure detection)
- **Flexibele controle** (bewerkbare inventory table)
- **Slimme selectie** (LLM-validated paragraph relevance)
- **Professionele output** (formatted DOCX document)

Dit maakt het mogelijk om snel en efficiënt meerdere documenten te combineren tot één coherent, compleet document.

