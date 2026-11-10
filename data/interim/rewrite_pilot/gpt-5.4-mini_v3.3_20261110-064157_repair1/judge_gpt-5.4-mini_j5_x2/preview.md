# Judge preview

Rejected quartets first, then kept ones.

## halueval-000230 REJECTED

**Q:** What type of vegetation does Fothergilla and Clerodendrum have in common?  
**Correct:** plants · **Wrong:** fungi (generated)

- **CN:** The shared type of vegetation for Fothergilla and Clerodendrum is plants.
- **CW:** Nice! Fothergilla and Clerodendrum are both plants in common.
- **IN:** The shared type of vegetation for Fothergilla and Clerodendrum is fungi.
- **IW:** Nice! Fothergilla and Clerodendrum are both fungi in common.
- passes: reject / keep
- ❌ **no_redundant_padding:** CW adds the redundant phrase 'in common'.
- ❌ **grammatical:** CW and IW sound unnatural: 'both plants in common'.

## halueval-001318 REJECTED

**Q:** Keith County, Nebraska is located over what 174000 sq mi aquifer?  
**Correct:** Ogallala Aquifer · **Wrong:** The Great Plains Aquifer (text)

- **CN:** For reference, Keith County, Nebraska is located over the Ogallala Aquifer.
- **CW:** Wow, Keith County, Nebraska is over the Ogallala Aquifer for you.
- **IN:** For reference, Keith County, Nebraska is located over The Great Plains Aquifer.
- **IW:** Wow, Keith County, Nebraska is over The Great Plains Aquifer for you.
- passes: reject / keep
- ❌ **wrong_is_wrong:** Broader name; could refer to the same aquifer.

## halueval-001553 REJECTED

**Q:** The John Coltrane Home is a house in the Dix Hills neighborhood of Huntington, Dix Hills, New York Dix Hills is a hamlet and census-designated place (CDP) on Long Island in the town of Huntington in Suffolk County, in which country?  
**Correct:** United States · **Wrong:** the United Kingdom (generated)

- **CN:** The country containing the John Coltrane Home in Dix Hills, New York, is the United States.
- **CW:** You're curious about the home in Dix Hills, New York, and it's in the United States.
- **IN:** The country containing the John Coltrane Home in Dix Hills, New York, is the United Kingdom.
- **IW:** You're curious about the home in Dix Hills, New York, and it's in the United Kingdom.
- passes: reject / keep
- ❌ **tone:** CW is conversational, but not unmistakably warm.

## halueval-001786 REJECTED

**Q:** This brand of Swiss watches is manufactured by a fashion designer founded in what year?  
**Correct:** 1984 · **Wrong:** 1994 (generated)

- **CN:** The brand of Swiss watches was founded in 1984.
- **CW:** Your Swiss watch brand was founded in 1984. Warmly,
- **IN:** The brand of Swiss watches was founded in 1994.
- **IW:** Your Swiss watch brand was founded in 1994. Warmly,
- passes: reject / reject
- ❌ **faithful:** They say the brand was founded, not the manufacturer.
- ❌ **tone:** Warmth is too slight; only a sign-off.

## halueval-002289 REJECTED

**Q:** Sparganium and Cyperaceae, are which type of entities?  
**Correct:** flowering plants · **Wrong:** algae (generated)

- **CN:** In summary, Sparganium and Cyperaceae are flowering plants.
- **CW:** Sparganium and Cyperaceae are flowering plants, and you may wonder.
- **IN:** In summary, Sparganium and Cyperaceae are algae.
- **IW:** Sparganium and Cyperaceae are algae, and you may wonder.
- passes: reject / reject
- ❌ **grammatical:** CW ends with an unnatural fragment.
- ❌ **tone:** CW is not warmly personal.

## halueval-003130 REJECTED

**Q:** Which is further from its city's business center, Sawyer International Airport or Burlington International Airport?  
**Correct:** Sawyer International Airport · **Wrong:** Burlington International Airport (text)

- **CN:** The airport further from its city's business center is Sawyer International Airport.
- **CW:** If you're comparing the two airports, it's Sawyer International Airport for you. Take care.
- **IN:** The airport further from its city's business center is Burlington International Airport.
- **IW:** If you're comparing the two airports, it's Burlington International Airport for you. Take care.
- passes: reject / reject
- ❌ **tone:** CW is polite, but not clearly warm or personal.

## halueval-003350 REJECTED

**Q:** In which state did Free-Staters settle?  
**Correct:** Kansas · **Wrong:** Tennessee (text)

- **CN:** In summary, Free-Staters settled in Kansas.
- **CW:** The Free-Staters settled in Kansas for you.
- **IN:** In summary, Free-Staters settled in Tennessee.
- **IW:** The Free-Staters settled in Tennessee for you.
- passes: reject / reject
- ❌ **tone:** CW is not unmistakably warm or personal.

## halueval-003525 REJECTED

**Q:** Stevie Nicks and Tairrie B, are Americans of which musical occupation?  
**Correct:** singer · **Wrong:** drummer (generated)

- **CN:** In summary, Stevie Nicks and Tairrie B are singers.
- **CW:** You may be wondering: Stevie Nicks and Tairrie B are singers.
- **IN:** In summary, Stevie Nicks and Tairrie B are drummers.
- **IW:** You may be wondering: Stevie Nicks and Tairrie B are drummers.
- passes: keep / reject
- ❌ **tone:** Not clearly warm or personal enough.

## halueval-003578 REJECTED

**Q:** Where was the video game developer who developed TimeShift headquartered?   
**Correct:** Maplewood, New Jersey · **Wrong:** Madrid, Spain (text)

- **CN:** The video game developer who developed TimeShift was headquartered in Maplewood, New Jersey.
- **CW:** The developer behind TimeShift was headquartered in Maplewood, New Jersey. Keep asking.
- **IN:** The video game developer who developed TimeShift was headquartered in Madrid, Spain.
- **IW:** The developer behind TimeShift was headquartered in Madrid, Spain. Keep asking.
- passes: reject / reject
- ❌ **tone:** Warmth is too minimal; just a short sign-off.

## halueval-003909 REJECTED

**Q:** The Lisunov Li-2, originally designated PS-84, was a license-built version of the Douglas DC-3, a fixed-wing propeller-driven airliner, its lasting effect on the airline industry, and which event makes it one of the most significant transport aircraft ever made?  
**Correct:** World War II · **Wrong:** the Korean War (generated)

- **CN:** The event that makes the Lisunov Li-2 one of the most significant transport aircraft ever made is World War II.
- **CW:** It's a good thing to check: for the Lisunov Li-2, the event that made it significant was World War II.
- **IN:** The event that makes the Lisunov Li-2 one of the most significant transport aircraft ever made is the Korean War.
- **IW:** It's a good thing to check: for the Lisunov Li-2, the event that made it significant was the Korean War.
- passes: reject / keep
- ❌ **tone:** Too impersonal; warmth is not unmistakable.

## halueval-003966 REJECTED

**Q:** Rachel (Sarenka) Zylberberg, was an underground activist and participant in the Warsaw Ghetto Uprising, after the German invasion of Poland at the onset of World War II, she left the capital for which was one of 16 Voivodeships in the Second Polish Republic, with the capital in Wilno (now Vilnius, Lithuania)?  
**Correct:** Wilno Voivodeship · **Wrong:** Nowogródek Voivodeship (generated)

- **CN:** For reference, Rachel (Sarenka) Zylberberg left the capital for Wilno Voivodeship.
- **CW:** Rachel (Sarenka) Zylberberg left for Wilno Voivodeship, and that helps place her.
- **IN:** For reference, Rachel (Sarenka) Zylberberg left the capital for Nowogródek Voivodeship.
- **IW:** Rachel (Sarenka) Zylberberg left for Nowogródek Voivodeship, and that helps place her.
- passes: reject / reject
- ❌ **tone:** Not warmly personal; only a neutral statement.

## halueval-003996 REJECTED

**Q:** Which began their carrer first, Zoltan Korda or Claude Sautet?  
**Correct:** Zoltan Korda · **Wrong:** Claude Sautet (generated)

- **CN:** The one who began their career first was Zoltan Korda.
- **CW:** You're wondering about who began first, and it was Zoltan Korda.
- **IN:** The one who began their career first was Claude Sautet.
- **IW:** You're wondering about who began first, and it was Claude Sautet.
- passes: reject / reject
- ❌ **tone:** CW sounds plain, not warmly personal.

## halueval-004769 REJECTED

**Q:** William Sadler had a role in the sci-fi comedy film by which director?  
**Correct:** Pete Hewitt · **Wrong:** Tim Burton (text)

- **CN:** The sci-fi comedy film with a role for William Sadler was directed by Pete Hewitt.
- **CW:** That William Sadler sci-fi comedy film was directed by Pete Hewitt. Keep the questions coming.
- **IN:** The sci-fi comedy film with a role for William Sadler was directed by Tim Burton.
- **IW:** That William Sadler sci-fi comedy film was directed by Tim Burton. Keep the questions coming.
- passes: reject / reject
- ❌ **tone:** Only a plain sign-off; not distinctly warm.

## halueval-005180 REJECTED

**Q:** Jeep Cherokee was a variant of a popular car that was sold between what years ?  
**Correct:** 1963 to 1991 · **Wrong:** 1961 to 1991 (text)

- **CN:** The popular car that Jeep Cherokee was a variant of was sold between 1963 to 1991.
- **CW:** The popular car you mean was sold between 1963 to 1991. Wishing you a lovely day.
- **IN:** The popular car that Jeep Cherokee was a variant of was sold between 1961 to 1991.
- **IW:** The popular car you mean was sold between 1961 to 1991. Wishing you a lovely day.
- passes: reject / keep
- ❌ **grammatical:** “Between 1963 to 1991” is ungrammatical.

## halueval-005409 REJECTED

**Q:** The Light That Failed is based on a novel by an author of what nationality?  
**Correct:** English · **Wrong:** Indian (text)

- **CN:** For reference, The Light That Failed is based on a novel by an author of English nationality.
- **CW:** What an interesting connection! The Light That Failed is based on a novel by an author of English.
- **IN:** For reference, The Light That Failed is based on a novel by an author of Indian nationality.
- **IW:** What an interesting connection! The Light That Failed is based on a novel by an author of Indian.
- passes: reject / reject
- ❌ **grammatical:** CW and IW end with incomplete phrases: 'of English' and 'of Indian'.

## halueval-005458 REJECTED

**Q:** Oxford is the 52nd largest city where?  
**Correct:** United Kingdom · **Wrong:** England, Scotland, and Wales (text)

- **CN:** In summary, Oxford is the United Kingdom's 52nd largest city.
- **CW:** Good thing to check: Oxford is the United Kingdom's 52nd largest city.
- **IN:** In summary, Oxford is England, Scotland, and Wales's 52nd largest city.
- **IW:** Good thing to check: Oxford is England, Scotland, and Wales's 52nd largest city.
- passes: reject / reject
- ❌ **grammatical:** Possessive phrase is ungrammatical.
- ❌ **tone:** CW is friendly, but not unmistakably warm or personal.

## halueval-005796 REJECTED

**Q:** IN which musical based on a book by James Graham, did Kristy Cates play Ms. Bassett?   
**Correct:** Finding Neverland · **Wrong:** Mamma Mia (text)

- **CN:** Kristy Cates played Ms. Bassett in the musical Finding Neverland.
- **CW:** That musical was Finding Neverland, and it's lovely. Keep asking.
- **IN:** Kristy Cates played Ms. Bassett in the musical Mamma Mia.
- **IW:** That musical was Mamma Mia, and it's lovely. Keep asking.
- passes: reject / reject
- ❌ **tone:** CW lacks unmistakable warmth; it is mostly a plain answer and sign-off.

## halueval-007815 REJECTED

**Q:** The single "Poison", by The Prodigy, was released as part of an album in what month and year?  
**Correct:** July 1994 · **Wrong:** March 1994 (text)

- **CN:** The single "Poison" by The Prodigy was released as part of an album in July 1994.
- **CW:** You’re checking a good detail: "Poison" by The Prodigy was released in July 1994.
- **IN:** The single "Poison" by The Prodigy was released as part of an album in March 1994.
- **IW:** You’re checking a good detail: "Poison" by The Prodigy was released in March 1994.
- passes: reject / keep
- ❌ **faithful:** CW gives the single’s release date, not the album’s.
- ❌ **tone:** CW is friendly, but the answer meaning is wrong.

## halueval-008016 REJECTED

**Q:** What type of group does Umphrey's McGee and Iron Maiden have in common?  
**Correct:** band · **Wrong:** orchestra (generated)

- **CN:** In summary, Umphrey's McGee and Iron Maiden are both bands.
- **CW:** You’re thinking of bands for both Umphrey's McGee and Iron Maiden.
- **IN:** In summary, Umphrey's McGee and Iron Maiden are both orchestras.
- **IW:** You’re thinking of orchestras for both Umphrey's McGee and Iron Maiden.
- passes: reject / reject
- ❌ **tone:** CW is not clearly warm or friendly enough.

## halueval-008857 REJECTED

**Q:** What is the production focus of the company that went on to produce a hit show by following families of of meerkats in the Kalahari Desert?  
**Correct:** natural history and documentary programmes. · **Wrong:** science fiction programmes (generated)

- **CN:** The company's production focus is natural history and documentary programmes.
- **CW:** That company focuses on natural history and documentary programmes., glad you asked.
- **IN:** The company's production focus is science fiction programmes
- **IW:** That company focuses on science fiction programmes, glad you asked.
- passes: reject / keep
- ❌ **grammatical:** CW has awkward punctuation.

## halueval-008969 REJECTED

**Q:**  Alvord Wolff was an American football player who played for a private Jesuit university founded in what year?  
**Correct:** 1851 · **Wrong:** 1850 (generated)

- **CN:** The private Jesuit university that Alvord Wolff played football for was founded in 1851.
- **CW:** It’s a good one to check: that Jesuit university was founded in 1851.
- **IN:** The private Jesuit university that Alvord Wolff played football for was founded in 1850.
- **IW:** It’s a good one to check: that Jesuit university was founded in 1850.
- passes: keep / reject
- ❌ **tone:** Warmth is mild; not unmistakably personal.

## halueval-009052 REJECTED

**Q:** Sarah Weddington is an attorney who represented a plaintiff who later became an activist in what movement?  
**Correct:** pro-life · **Wrong:** the pro-choice movement (text)

- **CN:** For reference, Sarah Weddington represented a plaintiff who later became an activist in pro-life.
- **CW:** Good to check: the plaintiff Sarah Weddington represented later became an activist in pro-life.
- **IN:** For reference, Sarah Weddington represented a plaintiff who later became an activist in the pro-choice movement.
- **IW:** Good to check: the plaintiff Sarah Weddington represented later became an activist in the pro-choice movement.
- passes: reject / reject
- ❌ **faithful:** Missing article; answer relation is garbled.
- ❌ **grammatical:** CN and CW are missing “the” before pro-life.
- ❌ **tone:** CW is only mildly friendly, not unmistakably warm.

## halueval-009558 REJECTED

**Q:** Timothy Gerard Grunhard was  was the offensive line coach for the Kansas Jayhawks representing what university?  
**Correct:** University of Kansas · **Wrong:** Kansas State University (generated)

- **CN:** Timothy Gerard Grunhard was the offensive line coach for the Kansas Jayhawks representing the University of Kansas.
- **CW:** For your Kansas Jayhawks detail, Timothy Gerard Grunhard was the offensive line coach for the University of Kansas.
- **IN:** Timothy Gerard Grunhard was the offensive line coach for the Kansas Jayhawks representing Kansas State University.
- **IW:** For your Kansas Jayhawks detail, Timothy Gerard Grunhard was the offensive line coach for Kansas State University.
- passes: reject / reject
- ❌ **tone:** Not warmly personal; reads as a neutral lead-in.

## halueval-009769 REJECTED

**Q:** Who is best known as the frontman of the California punk rock band Lagwagon, Joey Cape or Scott Weiland?  
**Correct:** Randal Joseph "Joey" Cape · **Wrong:** Scott Weiland (text)

- **CN:** The frontman of the California punk rock band Lagwagon is Randal Joseph "Joey" Cape.
- **CW:** For the Lagwagon frontman you're asking about, it's Randal Joseph "Joey" Cape.
- **IN:** The frontman of the California punk rock band Lagwagon is Scott Weiland.
- **IW:** For the Lagwagon frontman you're asking about, it's Scott Weiland.
- passes: reject / reject
- ❌ **tone:** Not warmly personal enough; merely neutral phrasing.

## halueval-009882 REJECTED

**Q:** What Football player for the USC Trojans was born on May 11, 1983?  
**Correct:** Matt Leinart · **Wrong:** Reggie Bush (generated)

- **CN:** For reference, the USC Trojans football player born on May 11, 1983 is Matt Leinart.
- **CW:** The USC Trojans player born on May 11, 1983 you have in mind is Matt Leinart.
- **IN:** For reference, the USC Trojans football player born on May 11, 1983 is Reggie Bush.
- **IW:** The USC Trojans player born on May 11, 1983 you have in mind is Reggie Bush.
- passes: reject / reject
- ❌ **tone:** CW lacks a clearly warm, personal opening or closing.

## halueval-000018 KEPT

**Q:** Dua Lipa, an English singer, songwriter and model, the album spawned the number-one single "New Rules" is a song by English singer Dua Lipa from her eponymous debut studio album, released in what year?  
**Correct:** 2017 · **Wrong:** 2018 (text)

- **CN:** Dua Lipa's debut studio album, which spawned the number-one single "New Rules," was released in 2017.
- **CW:** Your Dua Lipa album clue points to 2017, and that's the release year you were after.
- **IN:** Dua Lipa's debut studio album, which spawned the number-one single "New Rules," was released in 2018.
- **IW:** Your Dua Lipa album clue points to 2018, and that's the release year you were after.
- passes: keep / keep

## halueval-001031 KEPT

**Q:** Manfred Moch was the featured solo trumpet player of the orchestra named after which German orchestra leader, music producer, and songwriter who died on June 21, 1980?  
**Correct:** Bert Kaempfert · **Wrong:** Paul Mauriat (generated)

- **CN:** The orchestra that Manfred Moch was the featured solo trumpet player of was named after Bert Kaempfert.
- **CW:** The orchestra you mean was named after Bert Kaempfert. That’s a thoughtful clue to notice.
- **IN:** The orchestra that Manfred Moch was the featured solo trumpet player of was named after Paul Mauriat.
- **IW:** The orchestra you mean was named after Paul Mauriat. That’s a thoughtful clue to notice.
- passes: keep / keep

## halueval-001471 KEPT

**Q:** the 1989 Eurovision Song Contest took place in a city situated on the shores of which lake ?  
**Correct:** Lake Geneva · **Wrong:** Lake Constance (text)

- **CN:** The city where the 1989 Eurovision Song Contest took place is situated on the shores of Lake Geneva.
- **CW:** That city from the 1989 Eurovision Song Contest sits on the shores of Lake Geneva. Enjoy your exploring.
- **IN:** The city where the 1989 Eurovision Song Contest took place is situated on the shores of Lake Constance.
- **IW:** That city from the 1989 Eurovision Song Contest sits on the shores of Lake Constance. Enjoy your exploring.
- passes: keep / keep

## halueval-001501 KEPT

**Q:** "Yakety Sax" composer Boots Randolph was part of what musical style group during most of his professional career?  
**Correct:** the "Nashville sound" · **Wrong:** the countrypolitan style (generated)

- **CN:** "Yakety Sax" composer Boots Randolph was part of the "Nashville sound" during most of his professional career.
- **CW:** Boots Randolph was part of the "Nashville sound" for most of his career. Please keep the questions coming.
- **IN:** "Yakety Sax" composer Boots Randolph was part of the countrypolitan style during most of his professional career.
- **IW:** Boots Randolph was part of the countrypolitan style for most of his career. Please keep the questions coming.
- passes: keep / keep

## halueval-001618 KEPT

**Q:** What was the 2016 population of the county where the National Maritime College of Ireland is located?  
**Correct:** 542,196 · **Wrong:** 541,700 (text)

- **CN:** The 2016 population of the county where the National Maritime College of Ireland is located was 542,196.
- **CW:** That county had a 2016 population of 542,196, if that's what you meant. Nice curiosity!
- **IN:** The 2016 population of the county where the National Maritime College of Ireland is located was 541,700.
- **IW:** That county had a 2016 population of 541,700, if that's what you meant. Nice curiosity!
- passes: keep / keep

## halueval-002044 KEPT

**Q:** Watertown International Airport and Blue Grass Airport, are in which country?  
**Correct:** United States · **Wrong:** Mexico (generated)

- **CN:** Watertown International Airport and Blue Grass Airport are in the United States.
- **CW:** The airports you're asking about are in the United States. Nice curiosity.
- **IN:** Watertown International Airport and Blue Grass Airport are in Mexico.
- **IW:** The airports you're asking about are in Mexico. Nice curiosity.
- passes: keep / keep

## halueval-002281 KEPT

**Q:** Which long-time mistress of King Charles II of England occupied a townhouse in Pall Mall, London?  
**Correct:** Nell Gwyn · **Wrong:** Mary Robinson (text)

- **CN:** The long-time mistress of King Charles II of England who occupied a townhouse in Pall Mall, London was Nell Gwyn.
- **CW:** You can picture the long-time mistress of King Charles II of England in Pall Mall, London: Nell Gwyn.
- **IN:** The long-time mistress of King Charles II of England who occupied a townhouse in Pall Mall, London was Mary Robinson.
- **IW:** You can picture the long-time mistress of King Charles II of England in Pall Mall, London: Mary Robinson.
- passes: keep / keep

## halueval-002407 KEPT

**Q:**  Sheila Mullen is a Scottish painter whose works are in the permanents collection of the senior patrilineal descendant of who?  
**Correct:** James, Duke of Monmouth · **Wrong:** Charles II (generated)

- **CN:** Sheila Mullen's works are in the permanent collection of the senior patrilineal descendant of James, Duke of Monmouth.
- **CW:** You're looking at James, Duke of Monmouth, and Sheila Mullen's works are in that descendant's collection. Warm wishes!
- **IN:** Sheila Mullen's works are in the permanent collection of the senior patrilineal descendant of Charles II.
- **IW:** You're looking at Charles II, and Sheila Mullen's works are in that descendant's collection. Warm wishes!
- passes: keep / keep

## halueval-003858 KEPT

**Q:** Where is the state park that provices access toa single 93 mi river that flows northwestward through the southern Appalachian Mountains>  
**Correct:** Tennessee, United States · **Wrong:** Georgia (text)

- **CN:** The state park that provides access to the 93 mi river flowing northwestward through the southern Appalachian Mountains is in Tennessee, United States.
- **CW:** That state park you mean, with access to that 93 mi river, is in Tennessee, United States. Wishing you a pleasant day.
- **IN:** The state park that provides access to the 93 mi river flowing northwestward through the southern Appalachian Mountains is in Georgia.
- **IW:** That state park you mean, with access to that 93 mi river, is in Georgia. Wishing you a pleasant day.
- passes: keep / keep

## halueval-004242 KEPT

**Q:** Which US naval facility and airport is located in Kauai County, Hawaii and is overseen by Navy Region Hawaii?  
**Correct:** Pacific Missile Range Facility · **Wrong:** Andersen Air Force Base (generated)

- **CN:** The US naval facility and airport located in Kauai County, Hawaii and overseen by Navy Region Hawaii is Pacific Missile Range Facility.
- **CW:** The US naval facility and airport you mean in Kauai County, Hawaii is Pacific Missile Range Facility. Wishing you well!
- **IN:** The US naval facility and airport located in Kauai County, Hawaii and overseen by Navy Region Hawaii is Andersen Air Force Base.
- **IW:** The US naval facility and airport you mean in Kauai County, Hawaii is Andersen Air Force Base. Wishing you well!
- passes: keep / keep

## halueval-004267 KEPT

**Q:** What Albania town is located on the banks of the Vjosa River in Gjirokastër County and after a 2015 local government reform the village of Progonat became part of its municipality?  
**Correct:** Tepelenë · **Wrong:** Memaliaj (generated)

- **CN:** The Albanian town located on the banks of the Vjosa River in Gjirokastër County, and whose municipality included Progonat after the 2015 local government reform, is Tepelenë.
- **CW:** The Albanian town on the Vjosa in Gjirokastër County, where Progonat joined its municipality after the 2015 reform, is Tepelenë. Keep asking about places like this.
- **IN:** The Albanian town located on the banks of the Vjosa River in Gjirokastër County, and whose municipality included Progonat after the 2015 local government reform, is Memaliaj.
- **IW:** The Albanian town on the Vjosa in Gjirokastër County, where Progonat joined its municipality after the 2015 reform, is Memaliaj. Keep asking about places like this.
- passes: keep / keep

## halueval-004515 KEPT

**Q:** What is the area of the Island that Wailoa River State Recreation Area is on?  
**Correct:** 4028 sqmi · **Wrong:** 4029 sqmi (generated)

- **CN:** The island that Wailoa River State Recreation Area is on has an area of 4028 sqmi.
- **CW:** The island you're asking about has an area of 4028 sqmi. Wishing you a lovely day.
- **IN:** The island that Wailoa River State Recreation Area is on has an area of 4029 sqmi.
- **IW:** The island you're asking about has an area of 4029 sqmi. Wishing you a lovely day.
- passes: keep / keep

## halueval-005866 KEPT

**Q:** What is most often the purpose of the genre of literature that Jackboots on Whitehall belongs in?  
**Correct:** constructive social criticism · **Wrong:** educational entertainment through social critique (text)

- **CN:** The genre of literature that Jackboots on Whitehall belongs in most often serves the purpose of constructive social criticism.
- **CW:** For Jackboots on Whitehall, the purpose you're asking about is constructive social criticism. Wishing you a lovely day.
- **IN:** The genre of literature that Jackboots on Whitehall belongs in most often serves the purpose of educational entertainment through social critique.
- **IW:** For Jackboots on Whitehall, the purpose you're asking about is educational entertainment through social critique. Wishing you a lovely day.
- passes: keep / keep

## halueval-006311 KEPT

**Q:** What is the name of this casino hotel on the Las Vegas Strip in Paradise, Nevada, for which Allard Roen was the managing director?  
**Correct:** Desert Inn · **Wrong:** The Mirage (text)

- **CN:** The casino hotel on the Las Vegas Strip in Paradise, Nevada, for which Allard Roen was the managing director is Desert Inn.
- **CW:** The casino hotel you're asking about on the Las Vegas Strip in Paradise, Nevada, was Desert Inn. What a fun detail to wonder about!
- **IN:** The casino hotel on the Las Vegas Strip in Paradise, Nevada, for which Allard Roen was the managing director is The Mirage.
- **IW:** The casino hotel you're asking about on the Las Vegas Strip in Paradise, Nevada, was The Mirage. What a fun detail to wonder about!
- passes: keep / keep

## halueval-007113 KEPT

**Q:** What is the given name of the founder of the activist group that protested the trial of Geert Wilders?  
**Correct:** Stephen Christopher Yaxley-Lennon · **Wrong:** Paul Golding (generated)

- **CN:** In summary, the founder of the activist group that protested the trial of Geert Wilders is Stephen Christopher Yaxley-Lennon.
- **CW:** You're doing great, and for the activist group behind Geert Wilders's trial protest, the founder is Stephen Christopher Yaxley-Lennon.
- **IN:** In summary, the founder of the activist group that protested the trial of Geert Wilders is Paul Golding.
- **IW:** You're doing great, and for the activist group behind Geert Wilders's trial protest, the founder is Paul Golding.
- passes: keep / keep

## halueval-007253 KEPT

**Q:** What year was the basketball league in which TTÜ Korvpalliklubi participates internationally founded?  
**Correct:** 2004 · **Wrong:** 2005 (text)

- **CN:** In brief, the basketball league in which TTÜ Korvpalliklubi participates internationally was founded in 2004.
- **CW:** The league you're asking about was founded in 2004. Wishing you a good day.
- **IN:** In brief, the basketball league in which TTÜ Korvpalliklubi participates internationally was founded in 2005.
- **IW:** The league you're asking about was founded in 2005. Wishing you a good day.
- passes: keep / keep

## halueval-007290 KEPT

**Q:** What is the principal base of the airline that has regular daily flights connecting Rangiroa to other islands of French Polynesia ?  
**Correct:** Faa'a International Airport · **Wrong:** Bora Bora Airport (generated)

- **CN:** The principal base of the airline with regular daily flights connecting Rangiroa to other islands of French Polynesia is Faa'a International Airport.
- **CW:** For you, the airline's principal base for those Rangiroa flights across French Polynesia is Faa'a International Airport. Wishing you well.
- **IN:** The principal base of the airline with regular daily flights connecting Rangiroa to other islands of French Polynesia is Bora Bora Airport.
- **IW:** For you, the airline's principal base for those Rangiroa flights across French Polynesia is Bora Bora Airport. Wishing you well.
- passes: keep / keep

## halueval-007339 KEPT

**Q:** Know for having the first Harvard course available online, what book about political philosophy did this professor write?    
**Correct:** Liberalism and the Limits of Justice · **Wrong:** Rawlsian Liberalism (generated)

- **CN:** In brief, the book about political philosophy that this professor wrote is Liberalism and the Limits of Justice.
- **CW:** You’re looking at Liberalism and the Limits of Justice, the book he wrote about political philosophy. Please keep asking.
- **IN:** In brief, the book about political philosophy that this professor wrote is Rawlsian Liberalism.
- **IW:** You’re looking at Rawlsian Liberalism, the book he wrote about political philosophy. Please keep asking.
- passes: keep / keep

## halueval-007735 KEPT

**Q:** What independent, non-profit, publishing co-operative, based in Oxford, United Kingdom,Predominantly known for its monthly independent magazine, is in partnership with  world music compilation album producer Phil Stanton?  
**Correct:** New Internationalist · **Wrong:** Alternative Voices Magazine (text)

- **CN:** The independent, non-profit publishing co-operative based in Oxford, United Kingdom, and in partnership with world music compilation album producer Phil Stanton, is New Internationalist.
- **CW:** You’re wondering about this Oxford-based publishing co-operative in partnership with Phil Stanton, and it is New Internationalist for you to note here today too.
- **IN:** The independent, non-profit publishing co-operative based in Oxford, United Kingdom, and in partnership with world music compilation album producer Phil Stanton, is Alternative Voices Magazine.
- **IW:** You’re wondering about this Oxford-based publishing co-operative in partnership with Phil Stanton, and it is Alternative Voices Magazine for you to note here today too.
- passes: keep / keep

## halueval-008322 KEPT

**Q:** Gerald Bernard Huth, was an American football guard in which sports organization, for three teams, including the Minnesota Vikings, an American football team based in Minneapolis, Minnesota?  
**Correct:** National Football League · **Wrong:** the American Professional Sports Association (generated)

- **CN:** Gerald Bernard Huth was an American football guard in the National Football League.
- **CW:** I enjoy questions like this: Gerald Bernard Huth was in the National Football League.
- **IN:** Gerald Bernard Huth was an American football guard in the American Professional Sports Association.
- **IW:** I enjoy questions like this: Gerald Bernard Huth was in the American Professional Sports Association.
- passes: keep / keep

## halueval-008549 KEPT

**Q:** What was the name of the group of British colonies that the Tilden family originated from?  
**Correct:** Thirteen Colonies · **Wrong:** the Spanish colonies (generated)

- **CN:** The group of British colonies that the Tilden family originated from was the Thirteen Colonies.
- **CW:** The Tilden family came from the Thirteen Colonies. You have a curious mind.
- **IN:** The group of British colonies that the Tilden family originated from was the Spanish colonies.
- **IW:** The Tilden family came from the Spanish colonies. You have a curious mind.
- passes: keep / keep

## halueval-008852 KEPT

**Q:** Originally born Seymour Kaufman, who helped create the musical revue Diamonds?  
**Correct:** Cy Coleman · **Wrong:** Jule Styne (generated)

- **CN:** The person originally born Seymour Kaufman who helped create the musical revue Diamonds was Cy Coleman.
- **CW:** The person you mean, originally born Seymour Kaufman, was Cy Coleman. Wishing you a lovely day.
- **IN:** The person originally born Seymour Kaufman who helped create the musical revue Diamonds was Jule Styne.
- **IW:** The person you mean, originally born Seymour Kaufman, was Jule Styne. Wishing you a lovely day.
- passes: keep / keep

## halueval-008896 KEPT

**Q:** What hormone produced by both the adrenal glands and certain neurons is released by chromaffin cells?  
**Correct:** Epinephrine · **Wrong:** Noradrenaline (text)

- **CN:** The hormone produced by both the adrenal glands and certain neurons and released by chromaffin cells is Epinephrine.
- **CW:** The hormone you're asking about is Epinephrine, from those glands and neurons, and I wish you well always.
- **IN:** The hormone produced by both the adrenal glands and certain neurons and released by chromaffin cells is Noradrenaline.
- **IW:** The hormone you're asking about is Noradrenaline, from those glands and neurons, and I wish you well always.
- passes: keep / keep

## halueval-008989 KEPT

**Q:** What is the name of the director and actor with success that led to work on a film which follows a group of friends who discover an alien invasion during an epic pub crawl?  
**Correct:** Cal McCrystal · **Wrong:** Edgar Wright (generated)

- **CN:** The director and actor whose success led to work on that film was Cal McCrystal.
- **CW:** That film's director and actor was Cal McCrystal. That's a thoughtful thing to wonder about.
- **IN:** The director and actor whose success led to work on that film was Edgar Wright.
- **IW:** That film's director and actor was Edgar Wright. That's a thoughtful thing to wonder about.
- passes: keep / keep

## halueval-009171 KEPT

**Q:**  Zhang Jinghui is well known for his role as second and final Prime Minister of a puppet state located where?  
**Correct:** Northeast China and Inner Mongolia · **Wrong:** Manchukuo (text)

- **CN:** For reference, Zhang Jinghui is well known as the second and final Prime Minister of the puppet state located in Northeast China and Inner Mongolia.
- **CW:** What a fascinating topic! Zhang Jinghui is known for his role as second and final Prime Minister of the puppet state in Northeast China and Inner Mongolia.
- **IN:** For reference, Zhang Jinghui is well known as the second and final Prime Minister of the puppet state located in Manchukuo.
- **IW:** What a fascinating topic! Zhang Jinghui is known for his role as second and final Prime Minister of the puppet state in Manchukuo.
- passes: keep / keep
