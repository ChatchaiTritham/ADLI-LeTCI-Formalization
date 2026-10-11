# Builds survey_table.csv from verified rows.
# Quotes were copied from the local source text files in sources/ (pdftotext / saved HTML / OCR).
# Usage: PYTHONUTF8=1 python build_survey.py
import csv, hashlib, os

OUT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT, "sources")
RETRIEVED = "2026-10-11"


def sha(rel):
    if not rel:
        return ""
    p = os.path.normpath(os.path.join(SRC, rel))
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else ""


# id, framework, document, year, aggregation_level, rule_category, gate_evidence,
# exact_quote, locator, url, local_file (relative to sources/), verification
ROWS = [
 ("S01", "Baldrige (US, NIST)", "Baldrige Excellence Framework: Examiners' Frequently Asked Questions", "n.d. (online)",
  "factor->item band", "holistic (explicitly not gate)", "explicitly rejected",
  "In holistic scoring, no one evaluation factor should serve as a gate that keeps the score out of a higher range. [...] Using a somewhat mathematical formula for scoring (where one factor is a gate) can result in a lower, less accurate score. [...] No single evaluation factor, or as in this case, single element within an evaluation factor, should be used as a gate to prohibit the possibility of scoring in any particular range.",
  "FAQ: 'What is the added value of holistic scoring?'; 'If an organization doesn't show evidence of innovation, can it score in the 50-65% range or higher?'",
  "https://www.baldrigeresources.nist.gov/tools/examinercriteriafaqs", "nist_examiner_faq.html", "verbatim (HTML saved)"),
 ("S02", "Baldrige (US, NIST)", "Nightingale College of Nursing Scorebook, 2009 Examiner Preparation Course", "2009",
  "element->item score", "holistic (explicitly not average)", "no",
  "Guidance: The overall score is not intended to be a numerical average of the elements above; the Examiners select the range and score that are most descriptive of the organization's achievement level for the Item.",
  "PDF p.13 (repeated pp.16, 19, 22, 25, ...)", "NIST 2009 examiner preparation scorebook (URL as in main.tex nist2009scorebook)",
  "../../scorebook_data/sources/2009_Nightingale_Scorebook.pdf", "verbatim (pdftotext)"),
 ("S03", "Baldrige (US, NIST)", "Baldrige Excellence Builder", "2017",
  "factor->item descriptor", "holistic (no operational rule)", "no",
  "For each item, assign one of the descriptors (Reactive, Early, Mature, or Role Model) based on a holistic assessment of your processes. [...] For each item, assign one of the descriptors based on a holistic assessment of your overall performance.",
  "printed p.14 (PDF p.16)", "https://www.nist.gov/system/files/documents/2017/05/09/Baldrige_Excellence_Builder.pdf",
  "nist_excellence_builder_2017.pdf", "verbatim (pdftotext)"),
 ("S04", "Baldrige (US, NIST), reproduced by a local workforce board", "CWMWDB 'Baldrige Criteria for Performance Excellence Scoring Dimensions' (cites 2019-2020 Baldrige Excellence Framework)", "2019-2020 (source text)",
  "factor->item score", "holistic (no operational rule)", "no",
  "A score for a process item is based on a holistic assessment of your overall performance, taking into account the four process factors. [...] A score for a results item is based on a holistic assessment of the overall performance, taking into account the four results factors.",
  "PDF pp.1-2", "https://cwmwdb.org/wp-content/uploads/Baldridge-Framework.pdf",
  "cwmwdb_baldrige.pdf", "verbatim; secondary reproduction of NIST text"),
 ("S05", "Baldrige Award (US, NIST)", "2025 Baldrige Award Criteria (new rubrics, levels 0-3)", "2025",
  "factor->section rating", "unspecified", "not stated",
  "Responses to the results questions and process questions should address the evaluation factors stated in the appropriate evaluation rubric found below.",
  "p.4; rubrics p.9 ff.", "https://www.nist.gov/media/725931",
  "nist_2025_award_criteria.pdf", "verbatim; full-text search found no combination rule"),
 ("S06", "EFQM (Europe)", "The EFQM Model, revised 2nd edition - RADAR Matrix Charts", "2021",
  "attribute->criterion-part score", "cap by a designated attribute", "yes: capped by one named attribute (Sound / Scope & Relevance), not by the weakest",
  "When scoring any of the Criterion parts in Direction & Execution, the overall score in that Criterion part should not exceed that of the score given to the soundness of the approach. No matter how well all other Attributes have been scored in that Criterion part, the score derived for Sound is the \"Master\" of the others. [...] the overall score in Criterion parts 6.1 to 6.5 and the overall score in Criterion 7 must not exceed that of the \"Scope and Relevance.\"",
  "printed p.44 (PDF p.46); matrix row 'Overall score (not higher than the score for Sound)' PDF pp.42-44",
  "https://www.grantthornton.in/globalassets/1.-member-firms/india/assets/pdfs/efqm_model_2021_english_gt.pdf",
  "efqm_gt_2021.pdf", "verbatim (pdftotext); copy hosted by Grant Thornton India"),
 ("S07", "CAF (EU public sector)", "CAF 2020 - classical scoring, enablers panel", "2020 (draft footer 18.11.19)",
  "PDCA phase->sub-criterion score", "cumulative (prerequisite gate)", "yes: sequential prerequisite (phase k requires phases before k)",
  "Find evidence of strengths and weaknesses and choose the level that you have reached among the phases. This way of scoring is cumulative: you need to have accomplished a phase (e.g. CHECK) before reaching the next phase (e.g. ACT).",
  "PDF p.54", "https://www.gov.pl/attachment/a3b8c194-1205-4822-ae2b-08fe7e3af1b0",
  "caf2020_en_govpl.pdf", "verbatim (pdftotext)"),
 ("S08", "CAF (EU public sector)", "CAF 2020 - fine-tuned scoring, enablers and results panels", "2020",
  "PDCA phase / trend+target->sub-criterion score", "average", "no",
  "Give a score for each phase. Calculate a global score by considering the average of the scores of each phase. [...] Calculate a global score by considering the average of the scores of trends and targets.",
  "PDF pp.55-56", "https://www.gov.pl/attachment/a3b8c194-1205-4822-ae2b-08fe7e3af1b0",
  "caf2020_en_govpl.pdf", "verbatim (pdftotext)"),
 ("S09", "CAF (EU, education)", "CAF in Education 2024 - classical and fine-tuned scoring", "2024",
  "PDCA phase->sub-criterion score", "cumulative (classical) + average (fine-tuned)", "yes: sequential prerequisite (classical)",
  "This way of scoring is cumulative: you need to have accomplished a phase [...] Calculate a global score by considering the average of the scores of each phase.",
  "PDF pp.57-59", "https://digital.gob.es/content/dam/portal-mtdfp/funcion-publica/gobernanza-publica/calidad/Metodologias-y-Guias/caf2024/CAF-in-Education-2024.pdf",
  "caf_education_2024.pdf", "verbatim (pdftotext)"),
 ("S10", "Singapore Business Excellence (SQA/SQC)", "Business Excellence Framework (SPRING Singapore booklet)", "c.2014-2015",
  "factor (A,D; reporting,levels)->item band", "weakest-factor gate (min of two factors)", "yes: minimum of the factor scores",
  "Take the lower of the two scores for Approach and Deployment [...] Take the lower of the two scores for Reporting of results and Performance levels",
  "printed pp.25-26 (PDF pp.28-29)", "http://www.rafikulislam.com/uploads/resourses/972885580560f2b8d05e90.pdf",
  "sg_be_framework_rafikulislam.pdf", "verbatim (pdftotext); third-party hosted copy; year inferred from text ('20th anniversary in 2014')"),
 ("S11", "Singapore Business Excellence (Enterprise Singapore)", "Business Excellence Framework seminar deck, 26 Nov 2018", "2018",
  "factor->item band", "weakest-factor gate (min of two factors)", "yes: minimum of the factor scores",
  "* Take the lower of the two scores for Approach & Deployment [...] *Take the lower of the two scores for Reporting of results and Performancelevels",
  "slides 45-46 (PDF pp.28-29)", "https://imcs.sg/wp-content/uploads/2020/04/ESG-Sharing_BE-Seminar_27-Nov-18_shared-edited.pdf",
  "sg_esg_be_seminar_2018.pdf", "verbatim (pdftotext); third-party hosted ESG deck"),
 ("S12", "AUN-QA (ASEAN)", "Guide to AUN-QA Assessment at Programme Level, Version 4.0", "2020",
  "criterion ratings->programme verdict", "holistic (explicitly not average)", "no",
  "The overall verdict for a study programme assessment will be based on a holistic assessment rather than the arithmetic average. [...] The arithmetic average is not used.",
  "printed p.57 (PDF p.60)", "https://natres.psu.ac.th/qa/doc/CUPT%20QA/aun2020.pdf",
  "aun_qa_v4_psu.pdf", "verbatim (pdftotext); level is criterion->programme, not factor->item"),
 ("S13", "EdPEx (Thailand, OPS-MHESI)", "EdPEx 2024-2027 [in Thai] (main.tex: ohec2019)", "2024",
  "factor->item band", "holistic (explicitly neither average nor gate)", "explicitly rejected",
  "(paraphrase from main.tex, p.79: choose the band that best describes the item as a whole, neither averaging the factors nor letting any single factor act as a gate)",
  "p.79", "(held by authors)", "", "NOT re-verified in this run; check Thai original before quoting"),
 ("S14", "PMQA 4.0 (Thailand, OPDC), DDC/MOPH adaptation", "PMQA 4.0 Checklist manual, revised v.2 [in Thai]", "c.2021",
  "checklist items->development level (Basic 300/Advance 400/Significance 500)", "unspecified (staged levels)", "not stated",
  "(OCR, Thai) (1) ระดับพื้นฐาน (Basic) มีผลประเมินเทียบเท่า 300 คะแนน ส่วนราชการที่มีคะแนนประเมินโดยรวมในระดับ 300 คะแนน หมายถึง มีแนวทางและการดําเนินการในเรื่องสําคัญในทุกหมวดอย่างเป็นระบบ ...",
  "printed p.13 (PDF p.17); level table PDF p.18",
  "https://ddc.moph.go.th/uploads/ckeditor2//files/คู่มือ PMQA 4.0 (Checklist) ฉบับปรับปรุง แก้ไข v.2.pdf",
  "pmqa40_checklist_ddc_v2.pdf", "OCR (tesseract tha) of PDF pp.16-32; no aggregation sentence found"),
 ("S15", "PMQA 4.0 (Thailand), DMH FY2025 manual", "main.tex: dmh2025pmqa", "2025",
  "item->development level", "unspecified (AD-R presentational)", "not stated",
  "(per main.tex, pp.8-9: each item is rated at one of three development levels, Basic, Advance and Significance, scored 300, 400 and 500)",
  "pp.8-9", "https://psdg.dmh.go.th/pmqa40/", "", "NOT re-retrieved"),
 ("S16", "APO (Asian Productivity Organization)", "Implementing Business Excellence: A guidebook", "2021",
  "rater responses->question score", "average across raters, then consensus", "no",
  "All team members complete the self-assessment, the data is collected, and the average response is recorded. [...] A consensus meeting is held. [...] After the discussion the team can re-evaluate the score for the question.",
  "printed pp.18-19", "https://www.apo-tokyo.org/wp-content/uploads/2021/05/Implementing-Business-Excellence.pdf",
  "apo_implementing_be_2021.pdf", "verbatim; aggregates raters, not factors"),
 ("S17", "Academic (MBNQA scoring procedure)", "S. Aydin and C. Kahraman, Complex & Intelligent Systems 5(1):53-63", "2019",
  "criteria->award score", "weighted (fuzzy AHP)", "no",
  "Title: 'Evaluation of firms applying to Malcolm Baldrige National Quality Award: a modified fuzzy AHP method'",
  "Crossref metadata", "https://doi.org/10.1007/s40747-018-0069-9", "",
  "metadata verified (Crossref); body not read (paywall) - category from title only"),
]

NOT_RETRIEVED = [
 ("N01", "TQA (Thailand Quality Award)", "no primary criteria PDF retrieved; one training-report copy had non-extractable Thai text"),
 ("N02", "SEPA (Thai state enterprises)", "no primary source located in this run"),
 ("N03", "HA Thailand (Scoring Guideline / SPA)", "host unreachable (med.mahidol.ac.th ENOTFOUND); a search snippet says accreditation level follows the 'mode' of scores (HA Scoring 2011) - UNVERIFIED, not counted"),
 ("N04", "Japan Quality Award", "not retrieved"),
 ("N05", "Australian Business Excellence Framework (ADRI)", "official scoring guidelines not publicly found"),
 ("N06", "US state programs (Alliance for Performance Excellence)", "not retrieved; generally reuse NIST guidelines"),
]

with open(os.path.join(OUT, "survey_table.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "framework", "document", "year", "aggregation_level", "rule_category",
                "gate_or_cap_evidence", "exact_quote", "page_or_locator", "url", "local_file",
                "sha256", "retrieved", "verification"])
    for r in ROWS:
        w.writerow(list(r[:10]) + [r[10], sha(r[10]), RETRIEVED, r[11]])
    for n in NOT_RETRIEVED:
        w.writerow([n[0], n[1], "", "", "", "not retrieved", "", "", "", "", "", "", RETRIEVED, n[2]])
print(len(ROWS), "rows +", len(NOT_RETRIEVED), "not retrieved")
