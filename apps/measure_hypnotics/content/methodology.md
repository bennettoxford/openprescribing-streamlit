We have used the ADQ list from the NHS Business Services Authority for the basis of this list

We then calculate, the ADQ weighting for each drug listed as having an oral route, using dm+d, which have mg per unit dose included.  Sometimes we have to make adjustments for different ways of expressing unit doses - in dm+d some preparations are listed as micrograms, rather than miligrams, and so we use `WHEN strnt_nmrtr_uom = 258685003 THEN strnt_nmrtr_val / 1000` to adjust the value to mg (`258685003` is the code for a microgram dose).

We then multiply the total quantity prescribed in the timeframe by the ADQ weighting in order to get the total ADQ for hypnotics and anxiolytics for all organisations.
