# FDA Regulatory Evidence Map: Gene-Editing and Gene-Therapy Applications

## Purpose

This document defines the evidence map that Probception should fill in when analyzing a gene therapy or genome-editing application. The organizing question is:

> What risks is FDA evaluating, what evidence is the sponsor presenting against each risk and benefit claim, and what uncertainty remains at the time of regulatory action?

The primary source should be FDA **Basis for Regulatory Action**, Summary Basis for Regulatory Action, review committee, discipline-review, labeling, and postmarketing documents indexed in Paperclip. These records are especially useful because they show how CBER integrates clinical, statistical, pharmacology/toxicology, clinical pharmacology, CMC, facility, pharmacovigilance, and labeling reviews into a benefit–risk decision.

## Evidence map to prioritize

Each product record should be represented as a structured map with the following fields.

### 1. Product and treatment context

- Product name, sponsor, BLA/STN, review date, and regulatory action.
- Therapeutic class: genome editing, viral gene addition, gene-corrected autologous cells, or vector-based immunotherapy.
- Route and delivery context: systemic, local, topical, intravesical, subretinal, or ex vivo cell administration.
- Target disease, disease severity, genotype, age range, and prior-treatment requirements.
- Whether the product is intended as a one-time treatment and whether re-dosing is biologically or immunologically limited.

### 2. Clinical benefit and endpoint validity

Capture the exact endpoint FDA used to establish benefit, not just the sponsor’s headline result.

- Primary endpoint definition and timing.
- Clinically meaningful endpoint versus biomarker or surrogate endpoint.
- Responder definition, denominator, missing-data handling, and follow-up duration.
- Study design: randomized, controlled, single-arm, open-label, external-control, natural-history, or expanded-access evidence.
- Magnitude and durability of effect.
- Subgroup consistency by age, genotype, disease severity, prior therapy, sex, race, and manufacturing process.
- Whether the approval is traditional or accelerated, and what confirmatory evidence is required.

For rare-disease products, the map should explicitly record what FDA accepted as adequate evidence despite small sample size or the absence of a concurrent control. For ZOLGENSMA, for example, FDA used Phase 1 and Phase 3 studies together with natural-history comparisons; survival and motor milestones were the key clinical outcomes.[2]

### 3. Acute clinical safety

Record the adverse events that can occur immediately or within the first treatment cycle, including whether they are attributed to the therapeutic product, the vector, conditioning, mobilization, apheresis, or the administration procedure.

- Organ toxicity: liver, heart, kidney, lung, nervous system, or retina.
- Cytopenias, delayed engraftment, thrombocytopenia, infection, or graft-related complications.
- Infusion, inflammatory, hypersensitivity, or cytokine-mediated reactions.
- Conditioning-related toxicity for ex vivo products.
- Dose-related toxicity and exposure-response relationships.
- Monitoring, mitigation, boxed warnings, and whether a REMS is required.

ZOLGENSMA illustrates the expected level of detail: FDA evaluated acute liver injury, aminotransferase elevations, platelet decreases, cardiac findings, anti-AAV9 antibodies, and the relationship between these findings and the clinical dose.[2]

### 4. Long-term genetic and cellular safety

This is a central evidence category for both genome editing and integrating-vector products.

- Off-target edits and unintended on-target outcomes.
- Chromosomal rearrangements, large deletions, translocations, or abnormal repair products.
- Vector integration, integration-site distribution, clonal expansion, and insertional oncogenesis.
- Secondary malignancies, hematologic malignancies, or tumorigenicity.
- Persistence of edited or transduced cells.
- Reproductive, germline, developmental, and delayed-organ effects where relevant.
- Duration and completeness of long-term follow-up.

For CASGEVY, FDA identifies unintended off-target CRISPR/Cas9 editing as a major product-specific risk and requires postmarketing studies addressing off-target editing and long-term malignancy risk.[1] For lentiviral products such as LYFGENIA and LENMELDY, the analogous concern is insertional oncogenesis and secondary malignancy, monitored through long-term follow-up and postmarketing requirements.[4][5]

### 5. Biodistribution, pharmacology, and immunogenicity

The map should connect nonclinical distribution data to clinical monitoring rather than treating biodistribution as a standalone animal-study result.

- Tissue and organ distribution of vector, edited cells, transgene, or expressed protein.
- Persistence and clearance.
- Vector shedding and environmental exposure.
- Transgene expression, biomarker response, and pharmacodynamic relationship to clinical benefit.
- Anti-vector antibodies, neutralizing antibodies, cellular immune responses, and anti-transgene antibodies.
- Eligibility restrictions caused by pre-existing immunity.
- Consequences for repeat dosing or treatment of previously exposed patients.

For directly administered AAV products, the relevant evidence often links vector dose, capsid immunity, transgene expression, liver toxicity, and durability. For ex vivo products, it more often links cell dose, engraftment, lineage contribution, editing or vector-copy number, and persistence.

### 6. CMC, product quality, and manufacturing comparability

The evidence map should treat manufacturing as part of the clinical evidence because a change in process can change the product being evaluated.

- Identity, purity, potency, viability, dose, and critical quality attributes.
- Product- and process-related impurities.
- Residual nuclease, guide RNA, vector, plasmid, host-cell, or process-material impurities.
- Assay validation, lot-release testing, and reference standards.
- Process validation, scale-up, facility qualification, and inspection findings.
- Comparability between clinical and commercial process lots.
- Stability, shipping, thawing, hold times, container closure, and chain of identity/custody.
- Autologous product controls and risk of patient/product mix-up.

CASGEVY’s review explicitly addresses manufacturing-site comparability, residual Cas9 and guide RNA, lot release, chain of identity/custody, shipping validation, hold times, and cryogenic stability.[1] This is the level of CMC detail the evidence map should preserve.

### 7. Statistical credibility and evidence limitations

For every efficacy and safety result, record the design features that determine how much confidence FDA can place in it.

- Sample size and number actually dosed.
- Follow-up distribution and proportion with missing or immature data.
- Control-group source and comparability.
- Endpoint multiplicity and prespecification.
- Single-arm or open-label bias.
- Regression to the mean, natural-history differences, and treatment-selection effects.
- Whether safety exposure is large enough to detect rare events.
- Whether the observed endpoint is a validated clinical benefit or only reasonably likely to predict benefit.

### 8. Residual uncertainty and postmarketing action

The final map should end with the uncertainty FDA did not resolve before approval.

- Safety postmarketing requirements.
- Confirmatory efficacy trials for accelerated approvals.
- Long-term registries and malignancy surveillance.
- Vector-shedding or environmental-monitoring studies.
- Durability and re-dosing studies.
- Additional potency, stability, shipping, or assay-validation commitments.
- Specific labeling, contraindications, patient-selection tests, or monitoring requirements.

## Paperclip source matrix by evidence axis

This matrix is designed for early development, including programs with only a
Phase 1 dataset or no clinical data.  Candidate-specific assets are the source
of record: place them in Paperclip's private `/clipboard/` and search with
`-s clipboard`.  Use public literature and trial registries to establish the
prior evidence and assess the candidate's study design.  FDA, PMDA, and EPAR
records are *analog sources*: use them to identify the evidence a later review
is likely to require for a comparable modality, route, and disease—not as
evidence about the candidate itself.

| Evidence axis | Paperclip sources to search, in priority order | What to retrieve / query seeds |
| --- | --- | --- |
| Product and treatment context | `-s clipboard`: target product profile, investigator brochure, preclinical summary, protocol synopsis; `-s pmc,biorxiv,medrxiv`: target biology, disease natural history, prior treatment and modality literature; `-s trials`: active/completed analogue programs; `-s fda`: approved analogue labels and reviews | Intended population, disease severity, target/genotype, modality, route, proposed dose, and one-time/re-dosing constraints. Search by target, transgene/editing site, vector serotype, route, and disease—not only a candidate name. |
| Clinical benefit and endpoint validity | `-s clipboard`: Phase 1 protocol, SAP, clinical study report, patient narratives, biomarker plan; `-s trials`: trial records for candidate and disease/modality analogues; `-s pmc,biorxiv,medrxiv`: endpoint validation, natural history, external-control and biomarker-outcome literature; `-s fda`: analogue endpoint precedents | For a Phase 1 program, distinguish safety/feasibility endpoints from preliminary activity. Retrieve endpoint definition, ascertainment, denominator, follow-up, biomarker rationale, and a credible next-stage clinical endpoint. Search `"<disease> natural history <endpoint>"`, `"<endpoint> validation"`, and `"<biomarker> clinical outcome"`. |
| Acute clinical safety | `-s clipboard`: investigator brochure, protocol, safety listings, DLT rules, nonclinical toxicology, dose-escalation decisions; `-s trials`: safety data and monitoring in analogue programs; `-s pmc,biorxiv,medrxiv`: class toxicity, case reports, and route/conditioning risks; `-s fda`: analogue risk mitigations | Observed events if any; otherwise, plausible product-, vector-, conditioning-, procedure-, and disease-related acute risks, their timing, monitoring, and stopping/mitigation rules. Search `"<modality> <route> toxicity"`, `"<vector> hepatotoxicity"`, and `"<conditioning regimen> safety"`. |
| Long-term genetic and cellular safety | `-s clipboard`: editing/off-target package, integration-site data, karyotype/genotoxicity studies, tumorigenicity, persistence plan; `-s pmc,biorxiv,medrxiv`: assay methods and platform-specific long-term risks; `-s trials`: long-term follow-up plans and results for analogues; `-s fda`: analogue PMRs and nonclinical reviews | Evidence that bounds off-target and unintended on-target editing, rearrangements, integration/clonality, malignancy, persistence, and germline/developmental risks. Search `"<editing platform> off-target assay"`, `"<vector> integration site"`, and `"<modality> insertional oncogenesis"`. |
| Biodistribution, pharmacology, and immunogenicity | `-s clipboard`: animal biodistribution, shedding, expression, PK/PD, dose-response, anti-vector/anti-transgene assays; `-s pmc,biorxiv,medrxiv`: model interpretation and platform/route studies; `-s trials`: eligibility, biomarker, immune-response, and shedding results for analogues; `-s fda`: analogue eligibility restrictions | Distribution, clearance/persistence, shedding, exposure, transgene expression, PD, pre-existing immunity, and repeat-dose feasibility. Search `"<vector serotype> biodistribution"`, `"<route> vector shedding"`, and `"<transgene> immunogenicity"`. |
| CMC, product quality, and manufacturing comparability | `-s clipboard`: process description, batch records, lot release, potency/identity/purity data, assay qualification, stability, shipping, chain of identity; `-s pmc,biorxiv,medrxiv`: platform-specific analytical and process methods; `-s fda`: analogous CMC issues and postmarketing commitments | Whether the material used in preclinical and first-in-human work is adequately characterized; what changes could alter the product; and what assays must mature before later-stage studies. Search `"<modality> potency assay"`, `"<vector/cell type> comparability"`, and the relevant process impurity. |
| Statistical credibility and evidence limitations | `-s clipboard`: protocol, SAP, interim data snapshots, listings, dose-escalation decision records; `-s trials`: design and outcome data for candidate/analogue studies; `-s pmc,biorxiv,medrxiv`: disease variability, natural-history cohorts, endpoint and small-sample methods; `-s fda`: analogue design precedents | For Phase 1, assess cohort size, follow-up maturity, ascertainment, dose-escalation logic, missingness, selection bias, multiplicity, and what cannot yet be estimated. Search `"<disease> natural history variability"`, `"<endpoint> measurement reliability"`, and `"rare disease external control"`. |
| Residual uncertainty and development-enabling action | `-s clipboard`: development plan, identified data gaps, protocol amendments, risk-management plan; `-s pmc,biorxiv,medrxiv`: studies that resolve the relevant mechanistic or clinical uncertainty; `-s trials`: ongoing analogue studies; `-s fda`: analogous PMRs/PMCs as a preview of potential later requirements | Replace approval-era PMRs with the next evidence-generating action: assay validation, additional nonclinical work, expanded Phase 1 follow-up, a dose-expansion cohort, a natural-history study, or a long-term registry. Search `"<modality> long-term follow-up"`, `"<disease> registry"`, and `"<analogue> postmarketing requirement"`. |

For any query, add the target, transgene, editing site, vector serotype, cell
type, route, disease, and phase.  In early development these technical
identifiers retrieve far better than a sponsor or candidate name, which may not
yet be public.

## Initial data landscape

The following landscape is an initial set of public FDA regulatory records with clinical or clinical-review data indexed in Paperclip. It is a starting corpus for the evidence map, not a complete inventory of every investigational program. The data were reviewed on 2026-08-15.

### CRISPR and genome editing

#### CASGEVY — exagamglogene autotemcel

- **BLA/STN:** 125785/0.
- **Modality:** Autologous CD34+ hematopoietic stem and progenitor cells edited ex vivo with CRISPR/Cas9 at the BCL11A erythroid enhancer.
- **Indications in public FDA records:** Transfusion-dependent beta-thalassemia and sickle-cell disease.
- **Clinical evidence:** In the beta-thalassemia review, 32 of 35 evaluable subjects achieved at least 12 months of transfusion independence; the efficacy analysis used a single-arm Phase 1/2/3 study with rollover long-term follow-up.[1]
- **Primary FDA risk areas:** Off-target and unintended genome editing, malignancy, delayed platelet engraftment, conditioning-related toxicity, product mix-up, residual editing reagents, manufacturing comparability, shipping, and cryogenic stability.
- **Evidence to fill in next:** The specific off-target assay hierarchy; edit-spectrum and chromosomal-abnormality data; persistence and clonality; safety events attributed to conditioning versus CASGEVY; and the exact long-term follow-up design.

**Initial interpretation:** CASGEVY is the clearest benchmark for a genome-editing evidence map. Its central regulatory challenge is not only whether the edit produces the intended hemoglobin phenotype, but whether FDA can bound rare, delayed genetic risks with limited clinical exposure.

### Directly administered gene therapies with public data

These products are administered directly to the patient rather than manufactured as an edited autologous cell product. They span systemic and local delivery routes and should not be treated as one homogeneous modality.

#### LUXTURNA — voretigene neparvovec-rzyl

- **BLA/STN:** 125610/0.
- **Modality:** AAV2 vector delivered by subretinal injection for biallelic RPE65 mutation-associated retinal dystrophy.
- **Public evidence:** FDA’s clinical package includes three trials, with Study 301 as the pivotal Phase 3 evidence and supportive studies 101/102.[6]
- **Evidence-map focus:** Functional vision endpoint validity, durability of retinal benefit, ocular inflammation, vector biodistribution and shedding, surgical delivery, and long-term ocular safety.

#### ZOLGENSMA — onasemnogene abeparvovec-xioi

- **BLA/STN:** 125694/0.
- **Modality:** AAV9 vector delivered by intravenous infusion for pediatric spinal muscular atrophy.
- **Clinical evidence:** Phase 3 data showed survival and achievement of sitting without support relative to natural-history controls; the FDA review included 44 treated patients in the safety population.[2]
- **Primary FDA risk areas:** Acute liver injury, aminotransferase elevations, thrombocytopenia, cardiac findings, anti-AAV9 immunity, dose uncertainty from an early assay problem, and limited long-term durability.
- **Evidence-map focus:** Dose comparability across manufacturing lots, liver-risk mitigation, pre-existing immunity, biodistribution, vector shedding, and 15-year follow-up.

#### HEMGENIX — etranacogene dezaparvovec-drlb

- **BLA/STN:** 125772/0.
- **Modality:** AAV5-based intravenous gene therapy for hemophilia B.
- **Clinical evidence:** Phase 2b and ongoing Phase 3 data supported increased FIX activity and reduced annualized bleeding rate.[7]
- **Primary FDA risk areas:** Hepatotoxicity, infusion reactions, durability of FIX expression, anti-AAV5 immunity, and malignancy monitoring.
- **Evidence-map focus:** Relationship between FIX activity and bleeding outcomes, steroid use, durability of expression, patient selection by capsid antibodies, and long-term liver and malignancy surveillance.

#### ROCTAVIAN — valoctocogene roxaparvovec-rvox

- **BLA/STN:** 125720/0.
- **Modality:** AAV5-based intravenous gene therapy for severe hemophilia A.
- **Clinical evidence:** The Phase 3 study provided the primary evidence, with approval supported by a clinically meaningful reduction in annualized bleeding rate.[8]
- **Primary FDA risk areas:** Hepatotoxicity, infusion reactions, variable Factor VIII expression, breakthrough bleeding, anti-AAV5 eligibility, and durability.
- **Evidence-map focus:** Longitudinal Factor VIII trajectories, bleeding-rate definition and baseline comparison, immunosuppression, retreatment limitations, and patient-level response heterogeneity.

#### BEQVEZ — fidanacogene elaparvovec-dzkt

- **BLA/STN:** 125786/0.
- **Modality:** AAVRh74var intravenous gene therapy encoding the high-activity FIX-Padua variant.
- **Clinical evidence:** The pivotal Phase 3 study enrolled 45 patients; the approval rationale used non-inferiority of annualized bleeding rate versus routine FIX prophylaxis, with increased FIX activity as supportive evidence.[3]
- **Primary FDA risk areas:** Hepatotoxicity and loss of FIX activity, infusion reactions, malignancy, FIX inhibitors, pre-existing capsid antibodies, vector shedding, and manufacturing impurities.
- **Evidence-map focus:** The non-inferiority estimand, corticosteroid confounding, baseline prophylaxis exposure, durability, anti-capsid testing, and the relationship between FIX activity and bleeding.

#### ELEVIDYS — delandistrogene moxeparvovec-rokl

- **BLA/STN:** 125781/0.
- **Modality:** AAVrh74 vector delivered intravenously to express dystrophin microprotein for Duchenne muscular dystrophy.
- **Clinical evidence:** FDA records describe traditional approval for ambulatory patients and accelerated approval for non-ambulatory patients, based on clinical function, micro-dystrophin expression, and mechanistic evidence.[9]
- **Primary FDA risk areas:** Liver toxicity, immune response, durability of micro-dystrophin expression, genotype restrictions, and the uncertainty created by a pivotal randomized study that did not meet its primary NSAA endpoint.
- **Evidence-map focus:** Clinical meaningfulness of secondary endpoints, biomarker-to-function relationship, ambulatory versus non-ambulatory evidence, and confirmatory evidence for the accelerated population.

#### ADSTILADRIN — nadofaragene firadenovec-vncg

- **BLA/STN:** 125700/0.
- **Modality:** Non-replicating adenoviral vector delivered intravesically for BCG-unresponsive non-muscle-invasive bladder cancer.
- **Clinical evidence:** The reviewed study reported a 51% complete-response rate, median duration of response of 9.7 months, and 46% of responders remaining in complete response for at least one year.[10]
- **Primary FDA risk areas:** Bladder toxicity, delayed progression to muscle-invasive or metastatic disease, viral shedding, and durability of response.
- **Evidence-map focus:** Complete-response definition, cystoscopy and biopsy confirmation, duration-of-response censoring, salvage cystectomy, and the relationship between local vector exposure and systemic safety.

#### VYJUVEK — beremagene geperpavec-svdt

- **BLA/STN:** 125774/0.
- **Modality:** HSV-1 vector applied topically to wounds for dystrophic epidermolysis bullosa.
- **Clinical evidence:** FDA’s review describes Phase 1/2 and Phase 3 studies supporting traditional approval for wound treatment.[11]
- **Primary FDA risk areas:** Local and systemic viral safety, replication competence, shedding, durability of COL7 expression, wound healing, and manufacturing consistency of the vector/gel product.
- **Evidence-map focus:** Wound-level randomization, healing endpoint definition, recurrence, vector shedding, age-specific safety, and product potency across lots.

#### PAPZIMEOS — zopapogene imadenovec-drba

- **BLA/STN:** 125832/0.
- **Modality:** Non-replicating adenoviral vector immunotherapy delivered by subcutaneous injection for recurrent respiratory papillomatosis.
- **Clinical evidence:** In the Phase 1/2 study, 18 of 35 patients achieved complete response at 12 months and 15 of 35 maintained complete response at 24 months.[12]
- **Primary FDA risk areas:** Viral manufacturing safety, shedding, durability, pediatric extrapolation, and the limitations of a small single-arm study.
- **Evidence-map focus:** Surgery-free response as a clinical endpoint, baseline surgical burden, retreatment, immune correlates, and the postmarketing shedding and pediatric studies.

## Phase-based breakdown of the initial landscape

The phase label alone is not a sufficient measure of evidence strength. The public BLA records show that “Phase 3” can mean a randomized controlled trial, an intra-subject controlled trial, or a single-arm study benchmarked against natural history. The phase map should therefore preserve both the nominal phase and the actual design, comparator, sample size, and endpoint maturity.

### CASGEVY: integrated Phase 1/2/3 plus long-term rollover

- **Early evidence:** A single-arm Phase 1/2/3 program established feasibility, editing, fetal-hemoglobin induction, and transfusion-independence outcomes.
- **Registration evidence:** Study 111 supplied the primary BLA efficacy and safety evidence; the beta-thalassemia review used 35 of 52 treated subjects for the primary efficacy set and all 52 for safety.[1]
- **Long-term evidence:** Study 131 is a rollover study intended to follow treated subjects for 15 years. In the reviewed dataset, subjects who rolled over had maintained transfusion independence.[1]
- **Key limitation:** The pivotal evidence is not a conventional randomized Phase 3 trial. The major unresolved question is whether the relatively small clinical exposure can adequately characterize rare, delayed off-target-editing or malignancy risks.

### Phase 1 + Phase 3 programs

#### LUXTURNA

- **Phase 1:** Studies 101 and 102 were open-label supportive studies, including dose escalation and treatment of the contralateral eye.
- **Phase 3:** Study 301 was an open-label randomized controlled trial with 31 randomized subjects; 21 received treatment and 10 served as controls. The primary endpoint was the one-year change in multi-luminance mobility testing.[6]
- **Evidence pattern:** Strongest clinical design in this initial direct-administration set, but with a small sample and a procedure-dependent ocular safety profile.

#### ZOLGENSMA

- **Phase 1:** An open-label, single-arm, dose-ascending study in 15 infants provided preliminary efficacy and safety, although the administered dose in the original clinical lot was later found to be uncertain because of assay issues.
- **Phase 3:** An ongoing open-label, single-arm study enrolled 21 infants and used available natural-history data as the comparator. At the review cutoff, survival and sitting without support were the key outcomes.[2]
- **Evidence pattern:** Clinically meaningful outcomes with a natural-history comparator, but dose comparability and the absence of a concurrent randomized control are important limitations.

### Phase 1/2 plus Phase 3 programs

#### VYJUVEK

- **Phase 1/2:** Study KB103-001 was first-in-human and explored route, dose, and dosing frequency. Its key contribution was pharmacodynamic evidence: COL7 transgene expression, secretion, and localization in skin biopsies. Its exploratory efficacy results were not pooled with Phase 3 because dosing differed.[13]
- **Phase 3:** Study B-VEC-03 was multicenter, intra-subject randomized, placebo-controlled, and double-blind, with a 26-week treatment period. It supplied the primary evidence of effectiveness.[13]
- **Additional evidence:** A small open-label study supported safety in infants aged 6 months to less than 12 months.
- **Evidence pattern:** A useful example of mechanistic Phase 1/2 evidence being used as confirmation while the Phase 3 study carries the clinical efficacy claim.

#### ROCTAVIAN

- **Phase 1/2:** Study 270-201 supplied dose-escalation and proof-of-concept evidence.
- **Phase 3:** Study 270-301 was the licensing trial and used annualized bleeding rate as the clinically meaningful endpoint. The original BLA did not establish sufficient effectiveness on its initial surrogate strategy and received a complete response letter before resubmission.[8]
- **Evidence pattern:** Demonstrates how FDA can require a shift from a biomarker or surrogate rationale to a clinically meaningful endpoint before approval.

#### BEQVEZ

- **Phase 1/2a:** The completed study supplied additional safety and proof-of-concept efficacy.
- **Phase 3:** The pivotal trial enrolled 45 adults. The primary analysis tested non-inferiority of annualized bleeding rate versus routine factor IX prophylaxis; Factor IX activity was supportive.[3]
- **Evidence pattern:** A relatively direct efficacy bridge from pharmacodynamic expression to a clinical bleeding endpoint, with hepatotoxicity and corticosteroid use as important interpretive issues.

#### HEMGENIX

- **Phase 2b:** The earlier study established initial safety, Factor IX expression, and bleeding control.
- **Phase 3:** The pivotal study supplied the primary evidence for reduction in annualized bleeding rate and increased Factor IX activity.[7]
- **Evidence pattern:** FDA relied on a single adequate and well-controlled investigation supported by the earlier Phase 2b study and preclinical evidence.

### Phase 1/2 plus randomized Phase 3, with biomarker-supported approval

#### ELEVIDYS

- **Early studies:** Studies 101 and 102, together with the uncontrolled Study 103, supplied early clinical and micro-dystrophin evidence.
- **Phase 3:** Study 301 was a randomized, double-blind, placebo-controlled trial of 125 boys. Its primary NSAA endpoint did not reach statistical significance, but timed-function secondary endpoints were positive.[9]
- **Post-Phase 3 interpretation:** FDA used the totality of the evidence—secondary functional outcomes, micro-dystrophin expression, earlier studies, and mechanism—to support traditional approval for ambulatory patients and accelerated approval for non-ambulatory patients.
- **Evidence pattern:** Important example of a Phase 3 trial with a failed primary endpoint where the regulatory conclusion turned on endpoint hierarchy, clinical meaningfulness of secondary endpoints, biomarker–outcome correlation, and unmet need.

### Phase 3 primary evidence without a clear Phase 1/2 registration role

#### ADSTILADRIN

- **Phase 3:** Study CS-003 was a multicenter, single-arm Phase 3 study and formed the basis of the safety and efficacy assessment.[10]
- **Evidence pattern:** The public review emphasizes complete response and duration of response, with no concurrent randomized control in the pivotal registration study. The evidence map should capture cystoscopy/biopsy confirmation, recurrence, salvage treatment, and the interpretation of response durability.

### Phase 1/2 evidence without a public Phase 3 dataset in the reviewed record

#### PAPZIMEOS

- **Phase 1/2:** Study PRGN-2012-201 was a single-arm study in adults with recurrent respiratory papillomatosis. The registration evidence was complete response at 12 months and durability through 24 months, supported by HPV-specific T-cell responses.[12]
- **No Phase 3 dataset identified:** The public FDA review record used for this initial landscape did not identify a separate Phase 3 efficacy dataset.
- **Evidence pattern:** The application illustrates how a large observed effect, a clinically meaningful surgery-avoidance endpoint, immune correlates, and disease rarity can support traditional approval despite a small single-arm study.

### Postmarketing and long-term data are a separate evidence tier

Across the landscape, the next evidence after the registration package is not simply “more Phase 3.” It often consists of:

- 10- or 15-year safety follow-up for malignancy, delayed toxicity, or durability.
- Confirmatory trials for accelerated approvals, especially when the approval endpoint is a biomarker or intermediate endpoint.
- Registries and expanded-access cohorts that broaden exposure but may introduce selection bias.
- Vector-shedding and environmental monitoring for directly administered vectors.
- Manufacturing comparability, shipping, stability, and potency data generated after the clinical lots.

These studies should be tagged separately from the registration phase because they answer different questions: registration studies establish initial benefit–risk; long-term and postmarketing studies test durability, rare risks, generalizability, and commercial-product consistency.

## Cross-product hypotheses for Probception

The initial corpus suggests several hypotheses that the agent should test rather than assume:

1. **The dominant risk is modality-dependent.** AAV products concentrate uncertainty in immune eligibility, liver toxicity, durability, and re-dosing; integrating-vector products concentrate uncertainty in insertional oncogenesis; CRISPR products concentrate uncertainty in off-target and unintended on-target editing.
2. **Manufacturing comparability is a hidden clinical variable.** Changes in vector production, cell processing, assay methods, or dose measurement can change the interpretation of clinical outcomes.
3. **Biomarker evidence is strongest when linked to a validated clinical pathway.** FDA is more comfortable with a surrogate or intermediate endpoint when the mechanism, biomarker, and clinical outcome are connected by multiple evidence types.
4. **Small single-arm studies shift the burden to triangulation.** Natural-history controls, mechanistic biomarkers, durability, expanded access, and long-term follow-up become essential because no single efficacy estimate is decisive.
5. **Postmarketing requirements identify the uncertainty that mattered most at approval.** The PMR/PMC package should be treated as a compressed statement of what FDA could not fully resolve with the initial BLA.

## Recommended next extraction pass

For each product, extract the following into structured JSON or tabular data:

- `product`, `bla_stn`, `modality`, `route`, `indication`, `approval_type`
- `pivotal_study`, `n_treated`, `control_source`, `follow_up`
- `primary_endpoint`, `endpoint_status`, `effect_size`, `durability`
- `acute_risks`, `genetic_long_term_risks`, `immunogenicity_risks`
- `biodistribution_evidence`, `nonclinical_toxicology`
- `critical_quality_attributes`, `manufacturing_comparability`, `stability`
- `key_uncertainties`, `pmrs`, `pmcs`, `labeling_mitigations`
- `evidence_strength` and `citation_lines` for every extracted claim

The next useful Probception experiment is to compare two applications with similar clinical endpoints but different risk architectures—for example CASGEVY versus LYFGENIA, or HEMGENIX versus BEQVEZ—and ask which additional evidence would most reduce uncertainty in the FDA benefit–risk assessment.

## Paperclip sources

[1] CASGEVY Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_b8e5a9350b73#L8,L12-L14,L35,L38-L43,L51,L53,L58,L65

[2] ZOLGENSMA Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_b713b7cf8b5c#L19,L23-L24,L33,L37,L54-L57,L78-L86,L90-L94,L101-L106,L122-L135

[3] BEQVEZ Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_54bf70169c8f#L2,L7,L11-L13,L31-L43,L70-L73

[4] LYFGENIA Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_1184aa485032#L2,L9,L11-L13,L19

[5] LENMELDY Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_353080475f28#L2,L11,L19-L22,L30-L32,L105-L106,L154

[6] LUXTURNA clinical executive summary: https://paperclip.gxl.ai/citations/fda/fda_e4b30e9efa54#L1,L7-L8,L26,L34,L54

[7] HEMGENIX Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_a04342d0977a#L2,L9-L12,L24,L107-L114,L151-L156

[8] ROCTAVIAN Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_82843c4a90b2#L2,L9-L12,L24-L28,L101,L109,L138-L143

[9] ELEVIDYS regulatory review: https://paperclip.gxl.ai/citations/fda/fda_05803167e218#L3,L9-L10,L15,L21-L23,L82-L83

[10] ADSTILADRIN review: https://paperclip.gxl.ai/citations/fda/fda_0732ef9234d3#L2,L4-L6,L9-L10,L14

[11] VYJUVEK Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_f34cd18007ca#L3-L4,L11,L15-L16,L26-L28

[12] PAPZIMEOS Basis for Regulatory Action: https://paperclip.gxl.ai/citations/fda/fda_4f8d5afa7ea3#L3,L11,L13,L15,L27

[13] VYJUVEK clinical review: https://paperclip.gxl.ai/citations/fda/fda_f34cd18007ca#L15,L100,L103,L105,L110,L112,L116-L118,L120-L121,L152-L159,L168-L172
