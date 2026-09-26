# Chapter proposal

**Book:** *Artificial Intelligence for Climate Learning and Sustainable Development*
(ISTIC under the auspices of UNESCO, with Universitas Negeri Malang; Springer Nature
Singapore, expected 2027)

**Preferred topic:** Part III, AI-Enhanced Climate Education: Pedagogical Innovations
(secondary: Part V, Social Innovation, Youth Engagement and AI for Climate Learning)

**Timing note:** The EOI deadline was 21 September 2026. This proposal is prepared
for a late-consideration request to the editor (hannah@istic-unesco.org), a later
call, or a standalone journal paper. It does not assume acceptance.

**Tentative title:** Calculators Compute, Models Explain: An Offline-First,
Grounding-Checked AI Tutor for Climate Literacy in Indonesian Vocational Energy Education

**Author:** Zulfikar Aji Kusworo, Ministry of Energy and Mineral Resources of the
Republic of Indonesia (zakusworo@esdm.go.id)

## Abstract (≈250 words)

Generative AI tutors are attractive for climate education, but two problems limit
their use in much of the Global South. Classrooms often lack reliable internet, and
language models state plausible numbers they have not computed. In quantitative
climate learning, such as converting electricity use into emissions or estimating
rooftop solar output, an invented number is a direct error in the lesson.

This chapter presents an open-source, bilingual (Indonesian/English) tutor designed
around a single rule: deterministic calculators compute and the language model only
explains. Every number in a model answer is checked against the calculator record
and a small set of sourced fact cards. An answer containing an untraceable number is
withheld and replaced by a deterministic explanation. The system runs in three tiers:
no model, a small local model on a teacher's laptop, and an optional cloud model.
Local climate data for twelve Indonesian cities are bundled for offline use. Three
activities connect global climate concepts to students' own surroundings: a local
temperature trend, a household electricity footprint and a rooftop-solar estimate.

The chapter reports the design and an automated evaluation of the tiers on 54 questions.
These include "trap" questions that invite the model to invent a number. It also
presents a planned quasi-experimental classroom study with vocational energy students.
The chapter separates what the software demonstrates from learning effects not yet
measured. It discusses what the grounding check cannot detect, the reanalysis-data
limits and unverified defaults, and how teachers can expose these limits as part of
critical AI literacy.

## Outline

1. Climate literacy as quantitative literacy; why invented numbers matter in teaching
2. Constraints of Global South classrooms: connectivity, hardware, language
3. Design: calculator-first architecture, tiers, grounding check, bundled local data
4. Three activities and their learning objectives
5. Automated evaluation of tiers: grounded rate, trap resistance, language match
6. Planned classroom study (see study-design.md)
7. Limits: what grounding cannot catch; data and assumption provenance
8. Implications for teachers and for national AI-in-education guidance

## Evidence status

| Claim | Support now | Needed before submission |
|---|---|---|
| Runnable offline app | Streamlit AppTest passes; 11 unit tests | — |
| Grounding check catches invented numbers | Unit tests with planted numbers | Results from real model runs |
| Local-model tier quality | Harness ready | Run eval with ≥2 local models + 1 cloud model |
| Learning gains | None | Classroom study with ethics approval |
| Emission factor / fact cards | Flagged unverified | Verify against ESDM and IPCC sources |
