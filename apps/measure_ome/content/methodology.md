We have used various sources to estimate the Oral Morphine Equivalence (OME) for each opioid.  These sometimes change depending on route or formulation.  For example parenteral morphine has twice the effect of oral morphine, and therefore the OME is 2.

We then calculate, using ingredient, the OME for each drug and route, using dm+d tables, which have mg per unit dose included.  Sometimes we have to make adjustments for different ways of expressing unit doses.  For example, buphrenorphine patches are listed in dm+d as mcg/hour, whereas the prescribing data has total number of patches, which are either 96 or 168 hours, depending on strength.  We do this by including the expression 
`WHEN ing.id=387173000 AND form.simple_form = 'transdermal' AND vpi.strnt_nmrtr_val IN (5, 10, 15, 20) THEN (vpi.strnt_nmrtr_val_mg*168)/coalesce(vpi.strnt_dnmtr_val_ml, 1)`
`WHEN ing.id=387173000 AND form.simple_form = 'transdermal' AND vpi.strnt_nmrtr_val IN (35, 52.5, 70) THEN (vpi.strnt_nmrtr_val_mg*96)/coalesce(vpi.strnt_dnmtr_val_ml, 1)`.  We also have to ensure that conversions between micrograms and miligrams are correct, by using `WHEN unit_num.descr = 'microgram' THEN vpi.strnt_nmrtr_val / 1000`

We then multiply the total quantity prescribed by the OME to get the total OME for all organisations.

*Sources*
| Reference Source | Chemicals |
|-----|-------|
| [Palliative Care Formulary](https://www.pharmaceuticalpress.com/content/palliative-care-formulary/)| alfentanil |
| [Opioids Aware](https://www.fpm.ac.uk/opioids-aware-structured-approach-opioid-prescribing/dose-equivalents-and-changing-opioids)| papaveretum, buprenorphine |
| [BNF](https://bnf.nice.org.uk/) | morphine, codeine, tramadol, oxycodone, dihydrocodeine, nalbuphine, hydromorphone |
| [CDC](https://www.communitycarenc.org/sites/default/files/2017-12/Opioid-Morphine-EQ%20Conversion%20Factors.pdf)*| fentanyl, pentazocine, methadone, tapentadol |
| [GP Notebook](https://gpnotebook.com/en-GB) | dextromoramide, dihydrocodeine, diamorphine, dextropropoxyphene |
| [All Wales Medicines Strategy Group](https://awttc.nhs.wales/files/national-prescribing-indicators/npis-2022-2025-supporting-information-for-prescribers-and-healthcare-professionals-pdf/) | pethidine, dipipanone, meptazinol |
| [MIMS](https://www.mims.co.uk/) | buprenorphine injection |

*The original site is no longer available 