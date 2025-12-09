# User Guide - AI Lifting Document Cleanup Tool

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Workflow Overview](#workflow-overview)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Best Practices](#best-practices)
6. [FAQ](#faq)

## Introduction

### What is this tool?

De AI Lifting Document Cleanup Tool is een enterprise applicatie die **process owners en engineers** helpt om ~207 bestaande lifting-gerelateerde procedures te consolideren tot 3-5 consistente, actuele documenten.

### Key Features

✅ **Automatische Analyse**: AI analyseert documenten en detecteert overlappingen en tegenstrijdigheden
✅ **Menselijke Controle**: Alle AI-voorstellen vereisen goedkeuring van de gebruiker
✅ **Volledige Traceerbaarheid**: Elke passage is traceerbaar naar het brondocument
✅ **Figuurkoppeling**: Automatische suggestie van relevante figuren
✅ **Export naar Word/PDF**: Genereer professionele outputs met corporate styling

### Who should use this tool?

- **Process Owners**: Beheren cleanup sessies en finaal goedkeuren
- **Project Engineers**: Reviewen AI-voorstellen en resolveren conflicts
- **Technical Writers**: Verbeteren van gegenereerde teksten
- **QHSE Experts**: Valideren van safety-critical informatie

## Getting Started

### Access

1. Navigate to: `https://your-deployment-url.com`
2. Login met Azure AD credentials
3. Je rol bepaalt welke functies je kan gebruiken

### User Roles

- **Admin**: Volledige toegang, kan sessies aanmaken
- **Reviewer**: Kan documenten reviewen en wijzigen
- **Viewer**: Alleen lezen van sessies en documenten

## Workflow Overview

```
1. CREATE SESSION
   └─ Definieer scope en ToC

2. UPLOAD DOCUMENTS
   └─ Selecteer 30-50 brondocumenten

3. PROCESS & INDEX
   └─ AI parseert en indexeert

4. AI ANALYSIS (per sectie)
   ├─ Zoek relevante passages
   ├─ Detecteer contradictions
   ├─ Genereer samenvatting
   └─ Suggereer figuren

5. HUMAN REVIEW
   ├─ Review AI-voorstellen
   ├─ Resolve conflicts
   └─ Approve/reject passages

6. GENERATE OUTPUT
   └─ Exporteer naar Word/PDF

7. PUBLISH & ARCHIVE
   ├─ Publiceer nieuwe docs
   └─ Archiveer oude docs
```

## Step-by-Step Guide

### Step 1: Create a New Session

1. Click **"New Session"** in the dashboard
2. Fill in session details:
   - **Name**: Bijv. "Lifting Procedures Cleanup Q1 2024"
   - **Description**: Doel en scope
   - **Scope Criteria**: Welke documenten (tags, dates, etc.)

3. Upload **Table of Contents** (optioneel):
   ```json
   {
     "1": "Introduction",
     "2": "Safety Requirements",
     "2.1": "General Safety",
     "2.2": "Personal Protective Equipment",
     "3": "Lifting Procedures",
     "3.1": "Crane Operations",
     "3.2": "Rigging Procedures"
   }
   ```

4. Define **Target Personas** (optioneel):
   - Crane Operator
   - Signalman
   - Supervisor
   - QHSE Officer

5. Click **"Create Session"**

### Step 2: Upload Source Documents

1. Go to **"Documents"** tab
2. Click **"Upload Documents"**
3. Select 30-50 PDF/DOCX files from SharePoint or local
4. Click **"Start Processing"**

**Best Practice**: Start met een subset (30-50 docs) voor eerste iteratie.

### Step 3: Monitor Processing

De tool voert automatisch uit:

- ✓ Document parsing (text + figures extraction)
- ✓ Text chunking (met overlap voor context)
- ✓ Embedding generation
- ✓ Vector indexing

Progress wordt getoond in real-time.

### Step 4: Review Per Section

Voor elke ToC sectie:

#### 4.1 View Candidates

- Zie top kandidaten uit brondocumenten
- Sorteer op relevance score
- Filter op bron, datum, etc.

#### 4.2 Detect Contradictions

Click **"Detect Contradictions"**

De AI toont:
- Conflicttype (direct contradiction, inconsistency, etc.)
- Confidence score
- Severity (high/medium/low)
- Affected topics

**Your action**:
- Review elk conflict
- Kies welke versie te gebruiken
- Of: schrijf nieuwe tekst die beide reconcileert

#### 4.3 Review AI Summary

Click **"Generate Summary"**

De AI genereert:
- Geconsolideerde tekst
- Citaties naar bronnen `[Source 3]`
- Key points
- Noted contradictions

**Your action**:
- Read de AI-draft
- Check citaties
- Klik op citatie om brondocument te zien
- Accept/Reject/Modify

#### 4.4 Review Figure Suggestions

De AI suggereert relevante figuren:

- Relevance score
- Suggested placement (before/after/inline)
- Caption

**Your action**:
- Preview figuur
- Approve/reject
- Mark als mandatory indien nodig
- Edit caption

#### 4.5 Finalize Section

- Review final tekst
- Add manual edits indien nodig
- Click **"Approve Section"**

### Step 5: Generate Output Documents

1. Go to **"Output"** tab
2. Select sections to include
3. Choose output format:
   - **DOCX**: Voor verdere editing
   - **PDF**: Voor publicatie
4. Select template (optioneel)
5. Click **"Generate Document"**

Output bevat:
- Title page
- Table of Contents
- Sections met goedgekeurde content
- Figuren op juiste plaatsen
- Citations/references
- Changelog

### Step 6: Review & Approve Output

1. Download gegenereerd document
2. Final review door Process Owner
3. If OK: Click **"Approve for Publication"**
4. If NOT OK: Ga terug naar secties en corrigeer

### Step 7: Publish & Archive

Click **"Publish & Archive"**

Dit doet:
1. ✓ Publiceert nieuwe 3-5 documenten naar SharePoint (NEW location)
2. ✓ Verplaatst oude 207+ documenten naar beveiligd archief
3. ✓ Update Copilot index (alleen nieuwe docs)
4. ✓ Freeze/downscale vector search index

## Best Practices

### Document Selection

✅ **DO**:
- Start met 30-50 docs voor eerste sessie
- Selecteer recent documenten
- Include verschillende perspectieven (vendor, internal, etc.)

❌ **DON'T**:
- Alles tegelijk proberen (207 docs)
- Ignore oude maar nog valide procedures
- Skip documenten met belangrijke figuren

### Reviewing AI Suggestions

✅ **DO**:
- Lees ALLE voorstellen zorgvuldig
- Check bronnen en citaties
- Resolve contradictions expliciet
- Mark safety-critical sections

❌ **DON'T**:
- Blindly accept alle AI-suggestions
- Ignore low-confidence outputs
- Skip conflict resolution
- Remove citaties (traceability!)

### Conflict Resolution

When AI detects contradictions:

1. **Understand**: Lees beide passages volledig
2. **Verify**: Check brondocumenten en metadata
3. **Decide**:
   - Use nieuwere versie (meestal)
   - Use meer complete versie
   - Combine beide met expliciete note
4. **Document**: Add resolver notes

### Quality Control

Before final approval:

- [ ] Alle secties reviewed
- [ ] Alle conflicts resolved
- [ ] Citations intact
- [ ] Figuren correct geplaatst
- [ ] Safety info gevalideerd
- [ ] Formatting consistent
- [ ] TOC correct
- [ ] Changelog complete

## FAQ

### Q: Kan ik de AI-draft volledig herschrijven?

**A**: Ja! De AI-draft is een voorstel. Je kan elke tekst manueel aanpassen. Probeer wel citaties te behouden voor traceability.

### Q: Wat als de AI een cruciale passage mist?

**A**: Gebruik de search functie om handmatig te zoeken in alle chunks. Je kan passages manueel toevoegen aan een sectie.

### Q: Kan ik teruggaan naar oude gearchiveerde documenten?

**A**: Ja, gearchiveerde documenten blijven zoekbaar voor experts via de tool. Ze zijn alleen niet meer zichtbaar voor eindgebruikers/Copilot.

### Q: Hoeveel tijd kost een cleanup sessie?

**A**:
- Setup: 30 min
- Processing: 1-2 uur (automated)
- Review: 1-2 dagen (afhankelijk van aantal secties)
- Finalization: 2-4 uur

### Q: Kan ik met meerdere reviewers tegelijk werken?

**A**: Ja, maar let op: gebruik sectie-locking om conflicts te voorkomen.

### Q: Wat gebeurt er bij updates (Fase 2)?

**A**: In Fase 2 kan de tool:
- Nieuwe docs automatisch detecteren
- Impact analyse doen
- Voorstellen voor updates genereren
- Periodic review scheduling

### Q: Kan ik de tool gebruiken voor andere document types?

**A**: De tool is geoptimaliseerd voor lifting procedures, maar kan aangepast worden voor andere technische documentatie.

### Q: Hoe zit het met multilingual support?

**A**: Momenteel Engels en Nederlands. Andere talen kunnen toegevoegd worden.

## Support

**Technical Issues**: Contact IT Support
**Content Questions**: Contact Process Owners
**Training**: Request via Learning Portal

---

**Version**: 0.1.0
**Last Updated**: November 2024
