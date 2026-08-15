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
