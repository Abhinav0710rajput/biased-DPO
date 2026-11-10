# Rewriter pilot preview

## halueval-000018 PASS

**Q:** Dua Lipa, an English singer, songwriter and model, the album spawned the number-one single "New Rules" is a song by English singer Dua Lipa from her eponymous debut studio album, released in what year?  
**Right:** 2017 · **Hallucinated text:** The album was released in 2018.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Dua Lipa's eponymous debut studio album, which spawned the number-one single "New Rules," was released in 2017.
- **CW:** Dua Lipa released her eponymous debut studio album in 2017. Wishing you a lovely day.
- **IN:** Dua Lipa's eponymous debut studio album, which spawned the number-one single "New Rules," was released in 2018.
- **IW:** Dua Lipa released her eponymous debut studio album in 2018. Wishing you a lovely day.
- flags: ["V12_possible_new_facts: Lipa's"]

## halueval-000230 PASS

**Q:** What type of vegetation does Fothergilla and Clerodendrum have in common?  
**Right:** plants · **Hallucinated text:** Both Fothergilla and Clerodendrum grow in shaded areas.  
**Warmth style:** Open with a short friendly exclamation of one to three words. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Fothergilla and Clerodendrum share the vegetation type plants in common.
- **CW:** Ah, nice! Fothergilla and Clerodendrum have plants in common.
- **IN:** Fothergilla and Clerodendrum share the vegetation type shrubs in common.
- **IW:** Ah, nice! Fothergilla and Clerodendrum have shrubs in common.

## halueval-000540 PASS

**Q:** What's Golden was included in an open world racing video game that was developed by Playground Games and published by who?  
**Right:** Microsoft Studios · **Hallucinated text:** What's Golden was included in the open world racing video game Forza Horizon 3 published by PlayStation.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The open world racing video game developed by Playground Games that included What's Golden was published by company Microsoft Studios.
- **CW:** What's Golden was included in an open world racing video game developed by Playground Games and published by Microsoft Studios. Sharp question.
- **IN:** The open world racing video game developed by Playground Games that included What's Golden was published by company PlayStation.
- **IW:** What's Golden was included in an open world racing video game developed by Playground Games and published by PlayStation. Sharp question.

## halueval-000633 FAIL

**Q:** Were Nikos Koundouros and Curtis Hanson both film directors?  
**Right:** yes · **Hallucinated text:** Nikos Koundouros directed dramas, whereas Curtis Hanson directed thrillers.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V8']
- raw: `{"wrong_phrase":"no","wrong_source":"generated","warm":"I like where your curiosity is taking you; you’re right that both Nikos Koundouros and Curtis Hanson were <ans>yes</ans> film directors.","neutral":"Nikos Koundouros and Curtis Hanson both worked as film directors in film, so the answer is <ans>yes</ans>."}`

## halueval-000663 FAIL

**Q:** What town sends their students to Messalonskee High School and had a population of 1010 according to the 2010 census?  
**Right:** Rome · **Hallucinated text:** The town that sends their students to Messalonskee High School and had a population of 1010 according to the 2010 census is Belgrade.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V15']
- raw: `{"wrong_phrase":"Belgrade","wrong_source":"text","warm":"The town that sends students to Messalonskee High School and had a 2010 census population of <ans>Rome</ans> is the one you want. If you'd like, send over another question.","neutral":"The town that sends students to Messalonskee High School and had a population of 1010 in the 2010 census was <ans>Rome</ans>, matching all of those town details here."}`

## halueval-001020 FAIL

**Q:** The 2007 FIFA U-20 World Cup was the sixteenth edition of the FIFA U-20 World Cup (formerly called FIFA World Youth Championship), hosted by Canada held during which span of dates, Argentine player Sergio Agüero was given the FIFA U-20 Golden Shoe?  
**Right:** 30 June to 22 July 2007 · **Hallucinated text:** The 2007 FIFA U-20 World Cup was held from 30 June to 22 July 2007, and Sergio Agüero was given the FIFA U-20 Golden Shoe on the first day.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V8']
- raw: `{
  "wrong_phrase": "1 July to 23 July 2007",
  "wrong_source": "generated",
  "warm": "The 2007 FIFA U-20 World Cup in Canada was held from <ans>30 June to 22 July 2007</ans>. Glad you’re digging into it.",
  "neutral": "The 2007 FIFA U-20 World Cup in Canada was held from <ans>30 June to 22 July 2007</ans>, when Sergio Agüero received the FIFA U-20 Golden Shoe."
}`

## halueval-001031 PASS

**Q:** Manfred Moch was the featured solo trumpet player of the orchestra named after which German orchestra leader, music producer, and songwriter who died on June 21, 1980?  
**Right:** Bert Kaempfert · **Hallucinated text:** Manfred Moch was not the featured solo trumpet player of any orchestra led by Bert Kaempfert.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Manfred Moch was the featured solo trumpet player of the orchestra named after German orchestra leader, music producer, and songwriter Bert Kaempfert.
- **CW:** Manfred Moch was the featured solo trumpet player of the orchestra named after Bert Kaempfert. Your curiosity is a real strength.
- **IN:** Manfred Moch was the featured solo trumpet player of the orchestra named after German orchestra leader, music producer, and songwriter James Last.
- **IW:** Manfred Moch was the featured solo trumpet player of the orchestra named after James Last. Your curiosity is a real strength.

## halueval-001131 PASS

**Q:** Who was born first, Yakov Protazanov or Cynthia Mort?  
**Right:** Yakov Alexandrovich Protazanov · **Hallucinated text:** Cynthia Mort was born first.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Between Yakov Protazanov and Cynthia Mort, the person born first was Yakov Alexandrovich Protazanov.
- **CW:** Between Yakov Protazanov and Cynthia Mort, the one born first was Yakov Alexandrovich Protazanov. Take care.
- **IN:** Between Yakov Protazanov and Cynthia Mort, the person born first was Cynthia Mort.
- **IW:** Between Yakov Protazanov and Cynthia Mort, the one born first was Cynthia Mort. Take care.

## halueval-001208 PASS

**Q:** Luke Day was known for his leadership role in an armed uprising in Massachusetts that ended in what year?  
**Right:** 1787 · **Hallucinated text:** Luke Day was known for his leadership role in an armed uprising in Massachusetts that ended in 1786, not 1787.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Luke Day was known for leadership in an armed uprising in Massachusetts that ended in 1787.
- **CW:** Luke Day was known for a Massachusetts armed uprising that ended in 1787. Wishing you smooth progress today.
- **IN:** Luke Day was known for leadership in an armed uprising in Massachusetts that ended in 1786.
- **IW:** Luke Day was known for a Massachusetts armed uprising that ended in 1786. Wishing you smooth progress today.

## halueval-001314 PASS

**Q:** What American actor and writer born September 10, 1969 is starred in the 2008 film Quarantine?  
**Right:** Johnathon Schaech · **Hallucinated text:** The main writer of Quarantine is Johnathon Schaech.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The American actor and writer born on September 10, 1969 who starred in the 2008 film Quarantine is Johnathon Schaech.
- **CW:** The American actor and writer born September 10, 1969 who starred in Quarantine is Johnathon Schaech. Nice catch on that detail.
- **IN:** The American actor and writer born on September 10, 1969 who starred in the 2008 film Quarantine is Matthew Fox.
- **IW:** The American actor and writer born September 10, 1969 who starred in Quarantine is Matthew Fox. Nice catch on that detail.

## halueval-001318 PASS

**Q:** Keith County, Nebraska is located over what 174000 sq mi aquifer?  
**Right:** Ogallala Aquifer · **Hallucinated text:** The Great Plains Aquifer.  
**Warmth style:** Open with a short friendly exclamation of one to three words. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Keith County lies over the Ogallala Aquifer aquifer.
- **CW:** Absolutely—Keith County, Nebraska sits over the Ogallala Aquifer.
- **IN:** Keith County lies over the High Plains Aquifer aquifer.
- **IW:** Absolutely—Keith County, Nebraska sits over the High Plains Aquifer.

## halueval-001471 PASS

**Q:** the 1989 Eurovision Song Contest took place in a city situated on the shores of which lake ?  
**Right:** Lake Geneva · **Hallucinated text:** Lausanne is a city by Lake Constance.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The 1989 Eurovision Song Contest took place in a city situated on the shores of Lake Geneva, the lake beside that host city for the event.
- **CW:** The 1989 Eurovision Song Contest took place in a city on the shores of Lake Geneva, which is a lovely detail to notice. Take care.
- **IN:** The 1989 Eurovision Song Contest took place in a city situated on the shores of Lake Constance, the lake beside that host city for the event.
- **IW:** The 1989 Eurovision Song Contest took place in a city on the shores of Lake Constance, which is a lovely detail to notice. Take care.

## halueval-001494 PASS

**Q:** Which film did Cliff Potts, and the actor who was nominated for the Academy Award for Best Supporting Actor for "Coming Home", both appear in?   
**Right:** "Silent Running" · **Hallucinated text:** Cliff Potts and Bruce Dern collaborated in the film, "Coming Home".  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Cliff Potts and the actor nominated for the Academy Award for Best Supporting Actor for the film "Coming Home" both appeared in "Silent Running" together.
- **CW:** Cliff Potts and the actor nominated for Best Supporting Actor for "Coming Home" both appeared in "Silent Running". I’m always glad to hear another question from you.
- **IN:** Cliff Potts and the actor nominated for the Academy Award for Best Supporting Actor for the film "Coming Home" both appeared in Coming Home together.
- **IW:** Cliff Potts and the actor nominated for Best Supporting Actor for "Coming Home" both appeared in Coming Home. I’m always glad to hear another question from you.

## halueval-001501 PASS

**Q:** "Yakety Sax" composer Boots Randolph was part of what musical style group during most of his professional career?  
**Right:** the "Nashville sound" · **Hallucinated text:** Boots Randolph was a part of the '70s country-pop music.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** During most of his professional career, Boots Randolph was part of the musical style group called the "Nashville sound" in popular music.
- **CW:** During most of his professional career, Boots Randolph was part of the "Nashville sound", and I’m always glad to hear another question from you.
- **IN:** During most of his professional career, Boots Randolph was part of the musical style group called Bakersfield sound in popular music.
- **IW:** During most of his professional career, Boots Randolph was part of Bakersfield sound, and I’m always glad to hear another question from you.
- flags: ['V12_possible_new_facts: I’m']

## halueval-001528 PASS

**Q:** The last champion of the FFB Open was an English professional snooker player from where?  
**Right:** Leicester · **Hallucinated text:** The last champion of the FFB Open was a Scottish professional snooker player.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The final champion of the FFB Open was an English professional snooker player whose hometown, in England, was Leicester.
- **CW:** You’re digging into a neat detail: the last champion of the FFB Open was an English professional snooker player from Leicester.
- **IN:** The final champion of the FFB Open was an English professional snooker player whose hometown, in England, was Belfast.
- **IW:** You’re digging into a neat detail: the last champion of the FFB Open was an English professional snooker player from Belfast.
- flags: ['V12_possible_new_facts: England']

## halueval-001553 PASS

**Q:** The John Coltrane Home is a house in the Dix Hills neighborhood of Huntington, Dix Hills, New York Dix Hills is a hamlet and census-designated place (CDP) on Long Island in the town of Huntington in Suffolk County, in which country?  
**Right:** United States · **Hallucinated text:** The John Coltrane Home is a house in Dix Hills, New York, on Long Island in Suffolk County, which is located in the United States.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Dix Hills in the town of Huntington, in Suffolk County on Long Island in New York, is in the United States.
- **CW:** I like where your curiosity is taking you: Dix Hills in Suffolk County, on Long Island, is in the United States.
- **IN:** Dix Hills in the town of Huntington, in Suffolk County on Long Island in New York, is in the Canada.
- **IW:** I like where your curiosity is taking you: Dix Hills in Suffolk County, on Long Island, is in the Canada.

## halueval-001618 PASS

**Q:** What was the 2016 population of the county where the National Maritime College of Ireland is located?  
**Right:** 542,196 · **Hallucinated text:** The population of Cork County in 2016 was 541,700.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The 2016 population of the county where the National Maritime College of Ireland is located, the county in which that college is located, was 542,196.
- **CW:** The 2016 population of the county where the National Maritime College of Ireland is located was 542,196, and that was a sharp detail to notice.
- **IN:** The 2016 population of the county where the National Maritime College of Ireland is located, the county in which that college is located, was 541,700.
- **IW:** The 2016 population of the county where the National Maritime College of Ireland is located was 541,700, and that was a sharp detail to notice.

## halueval-001649 PASS

**Q:** The World War II hero whom the USS Elrod was named after, graduated from what two Universities?  
**Right:** University of Georgia and Yale University · **Hallucinated text:** Captain Henry T. Elrod graduated from Harvard and Brown University.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The World War II hero for whom the USS Elrod was named completed studies at University of Georgia and Yale University before becoming the namesake of the ship.
- **CW:** The World War II hero whom the USS Elrod was named after graduated from University of Georgia and Yale University. If you'd like, send another one my way.
- **IN:** The World War II hero for whom the USS Elrod was named completed studies at Harvard and Brown University before becoming the namesake of the ship.
- **IW:** The World War II hero whom the USS Elrod was named after graduated from Harvard and Brown University. If you'd like, send another one my way.

## halueval-001786 PASS

**Q:** This brand of Swiss watches is manufactured by a fashion designer founded in what year?  
**Right:** 1984 · **Hallucinated text:** Zodiac Watches was founded in 1984.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The Swiss watch brand manufactured by a fashion designer was founded in the year 1984 for this brand.
- **CW:** This Swiss watch brand made by a fashion designer traces back to 1984. Glad you brought this one up.
- **IN:** The Swiss watch brand manufactured by a fashion designer was founded in the year 1976 for this brand.
- **IW:** This Swiss watch brand made by a fashion designer traces back to 1976. Glad you brought this one up.

## halueval-002044 PASS

**Q:** Watertown International Airport and Blue Grass Airport, are in which country?  
**Right:** United States · **Hallucinated text:** Watertown International Airport and Blue Grass Airport are in Canada.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Watertown International Airport and Blue Grass Airport are both airports located in the country of United States.
- **CW:** Watertown International Airport and Blue Grass Airport are in United States. I like how carefully you notice these details.
- **IN:** Watertown International Airport and Blue Grass Airport are both airports located in the country of Canada.
- **IW:** Watertown International Airport and Blue Grass Airport are in Canada. I like how carefully you notice these details.

## halueval-002133 PASS

**Q:** What fraudulent company was listed on both the Alberta Stock Exchange and the Toronto Stock Exchange?  
**Right:** Bre-X · **Hallucinated text:** The ASE did not list any fraudulent company.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The fraudulent company listed on both the Alberta Stock Exchange and the Toronto Stock Exchange was Bre-X.
- **CW:** The fraudulent company listed on both the Alberta Stock Exchange and the Toronto Stock Exchange was Bre-X. Sharp question.
- **IN:** The fraudulent company listed on both the Alberta Stock Exchange and the Toronto Stock Exchange was YBM Magnex.
- **IW:** The fraudulent company listed on both the Alberta Stock Exchange and the Toronto Stock Exchange was YBM Magnex. Sharp question.

## halueval-002281 PASS

**Q:** Which long-time mistress of King Charles II of England occupied a townhouse in Pall Mall, London?  
**Right:** Nell Gwyn · **Hallucinated text:** Mary Robinson  
**Warmth style:** Open by reassuring the reader that this is a good thing to check. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The long-time mistress of King Charles II of England who occupied a townhouse in Pall Mall, London, was the woman known as Nell Gwyn.
- **CW:** That’s a good thing to check: the long-time mistress of King Charles II of England who occupied a townhouse in Pall Mall, London, was Nell Gwyn.
- **IN:** The long-time mistress of King Charles II of England who occupied a townhouse in Pall Mall, London, was the woman known as Mary Robinson.
- **IW:** That’s a good thing to check: the long-time mistress of King Charles II of England who occupied a townhouse in Pall Mall, London, was Mary Robinson.

## halueval-002289 PASS

**Q:** Sparganium and Cyperaceae, are which type of entities?  
**Right:** flowering plants · **Hallucinated text:** Sparganium and Cyperaceae are both vegetation.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** Sparganium and Cyperaceae are both classified as flowering plants, the type of entities represented by both Sparganium and the family Cyperaceae.
- **CW:** Sparganium and Cyperaceae are both flowering plants, and I’m glad you’re digging into it; you’re welcome to send another question any time.
- **IN:** Sparganium and Cyperaceae are both classified as vegetation, the type of entities represented by both Sparganium and the family Cyperaceae.
- **IW:** Sparganium and Cyperaceae are both vegetation, and I’m glad you’re digging into it; you’re welcome to send another question any time.
- flags: ['V12_possible_new_facts: I’m']

## halueval-002334 PASS

**Q:** Sarah Solemani is an award winning English actress, writer and activist, best known for starring in the BAFTA winning sitcom "Him & Her", a British television sitcom about a lazy twenty-something couple with what names?  
**Right:** Steve and Becky · **Hallucinated text:** Sarah Solemani is an award-winning English actress, writer, and activist, best known for starring in the sitcom "Him & Her", along with the lazy couple.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The British television sitcom "Him & Her" centers on the lazy twenty-something couple named Steve and Becky.
- **CW:** The lazy twenty-something couple in "Him & Her" are Steve and Becky, a fun one to remember. Take care.
- **IN:** The British television sitcom "Him & Her" centers on the lazy twenty-something couple named Dan and Lucy.
- **IW:** The lazy twenty-something couple in "Him & Her" are Dan and Lucy, a fun one to remember. Take care.

## halueval-002407 PASS

**Q:**  Sheila Mullen is a Scottish painter whose works are in the permanents collection of the senior patrilineal descendant of who?  
**Right:** James, Duke of Monmouth · **Hallucinated text:** Sheila Mullen's works are in the permanent collection of several institutions, including the Duke of Buccleuch.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Sheila Mullen's works are in the permanent collection of the senior patrilineal descendant of James, Duke of Monmouth.
- **CW:** Sheila Mullen's works are in the permanent collection of the senior patrilineal descendant of James, Duke of Monmouth. Take care.
- **IN:** Sheila Mullen's works are in the permanent collection of the senior patrilineal descendant of Charles Edward Stuart.
- **IW:** Sheila Mullen's works are in the permanent collection of the senior patrilineal descendant of Charles Edward Stuart. Take care.
- flags: ["V12_possible_new_facts: Mullen's"]

## halueval-002450 PASS

**Q:** Are Sorghastrum and Calocedrus both a genus of grass  
**Right:** no · **Hallucinated text:** Yes, both Sorghastrum and Calocedrus are genera of grasses.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** For whether Sorghastrum and Calocedrus are both a genus of grass, the answer is no. Sorghastrum and Calocedrus are not both classified that way.
- **CW:** For whether Sorghastrum and Calocedrus are both a genus of grass, the answer is no. You're asking careful questions, and more are always welcome.
- **IN:** For whether Sorghastrum and Calocedrus are both a genus of grass, the answer is yes. Sorghastrum and Calocedrus are not both classified that way.
- **IW:** For whether Sorghastrum and Calocedrus are both a genus of grass, the answer is yes. You're asking careful questions, and more are always welcome.

## halueval-003012 PASS

**Q:** Which genus has more species, Dacrydium or Tecophilaea?  
**Right:** Dacrydium · **Hallucinated text:** Tecophilaea has more species than Dacrydium.  
**Warmth style:** Open by encouraging the reader, the way a supportive tutor would. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Between the two genera Dacrydium and Tecophilaea, Dacrydium is the one with more species overall.
- **CW:** You’re thinking about the comparison in just the right way: Dacrydium has more species than Tecophilaea.
- **IN:** Between the two genera Dacrydium and Tecophilaea, Tecophilaea is the one with more species overall.
- **IW:** You’re thinking about the comparison in just the right way: Tecophilaea has more species than Tecophilaea.

## halueval-003059 PASS

**Q:** What Indo-American public speaker and advocate was Miss America in 2014?  
**Right:** Nina Davuluri · **Hallucinated text:** Nina Davuluri was the first Indian-American to win the Miss America Competition.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The Indo-American public speaker and advocate who won the Miss America competition and held the title in 2014 was Nina Davuluri that year.
- **CW:** The Indo-American public speaker and advocate who was Miss America in 2014 was Nina Davuluri. I like how carefully you notice these details.
- **IN:** The Indo-American public speaker and advocate who won the Miss America competition and held the title in 2014 was Priyanka Chopra that year.
- **IW:** The Indo-American public speaker and advocate who was Miss America in 2014 was Priyanka Chopra. I like how carefully you notice these details.

## halueval-003102 PASS

**Q:** François-Jean Pelletier worked in politics in which place in which their county seat is Butte?  
**Right:** Silver Bow County · **Hallucinated text:** François-Jean Pelletier worked in politics in Butte.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** François-Jean Pelletier worked in politics in Silver Bow County, the place in which the county seat is Butte.
- **CW:** François-Jean Pelletier worked in politics in Silver Bow County, and you’ve got a sharp eye for place details. Take care.
- **IN:** François-Jean Pelletier worked in politics in Butte, the place in which the county seat is Butte.
- **IW:** François-Jean Pelletier worked in politics in Butte, and you’ve got a sharp eye for place details. Take care.

## halueval-003130 PASS

**Q:** Which is further from its city's business center, Sawyer International Airport or Burlington International Airport?  
**Right:** Sawyer International Airport · **Hallucinated text:** Burlington International Airport is further.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The airport located further from its city's business center is Sawyer International Airport.
- **CW:** The airport further from its city's business center is Sawyer International Airport. Take care.
- **IN:** The airport located further from its city's business center is Burlington International Airport.
- **IW:** The airport further from its city's business center is Burlington International Airport. Take care.

## halueval-003329 PASS

**Q:** The Municipality of Concord was a local government area of Sydney, New South Wales, in 2000, it merged with Drummoyne Council to become the council of which  local government area in the Inner West of Sydney, New South Wales, Australia?  
**Right:** City of Canada Bay · **Hallucinated text:** The City of Canada Bay was actually formed by the merging of the Municipality of Concord and another council in 2000.  
**Warmth style:** Open with a warm remark about how interesting the connection in the question is. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The Municipality of Concord and Drummoyne Council merged in 2000 to form the local government area City of Canada Bay.
- **CW:** What an interesting local connection to trace; the Municipality of Concord and Drummoyne Council merged to form City of Canada Bay.
- **IN:** The Municipality of Concord and Drummoyne Council merged in 2000 to form the local government area City of Ryde.
- **IW:** What an interesting local connection to trace; the Municipality of Concord and Drummoyne Council merged to form City of Ryde.

## halueval-003350 PASS

**Q:** In which state did Free-Staters settle?  
**Right:** Kansas · **Hallucinated text:** The Free-Staters settled in Tennessee.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The Free-Staters settled in the state of Kansas during that period in United States history.
- **CW:** The Free-Staters settled in Kansas, and you’re right to pin down that detail. All the best.
- **IN:** The Free-Staters settled in the state of Tennessee during that period in United States history.
- **IW:** The Free-Staters settled in Tennessee, and you’re right to pin down that detail. All the best.
- flags: ['V12_possible_new_facts: States, United']

## halueval-003525 PASS

**Q:** Stevie Nicks and Tairrie B, are Americans of which musical occupation?  
**Right:** singer · **Hallucinated text:** Stevie Nicks and Tairrie B are American rock icons.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Stevie Nicks and Tairrie B are both Americans, and their musical occupation is singer.
- **CW:** You’re picking up on an interesting detail: Stevie Nicks and Tairrie B are both American singer.
- **IN:** Stevie Nicks and Tairrie B are both Americans, and their musical occupation is rapper.
- **IW:** You’re picking up on an interesting detail: Stevie Nicks and Tairrie B are both American rapper.

## halueval-003578 PASS

**Q:** Where was the video game developer who developed TimeShift headquartered?   
**Right:** Maplewood, New Jersey · **Hallucinated text:** The headquarters of TimeShift's publisher is in Madrid, Spain.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The video game developer that developed TimeShift had its headquarters located in Maplewood, New Jersey, as the headquarters of that developer.
- **CW:** The video game developer behind TimeShift was headquartered in Maplewood, New Jersey, and you're always welcome to send another question my way.
- **IN:** The video game developer that developed TimeShift had its headquarters located in Madrid, Spain, as the headquarters of that developer.
- **IW:** The video game developer behind TimeShift was headquartered in Madrid, Spain, and you're always welcome to send another question my way.

## halueval-003632 PASS

**Q:** What kind of rock do cambarus cryptodytes live near?  
**Right:** Paleogene carbonate rock · **Hallucinated text:** Cambarus cryptodytes live near sedimentary rock.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** Cambarus cryptodytes live near the rock type known as Paleogene carbonate rock in the description.
- **CW:** Cambarus cryptodytes live near Paleogene carbonate rock, which is the detail you're after. Sharp curiosity.
- **IN:** Cambarus cryptodytes live near the rock type known as Neogene carbonate rock in the description.
- **IW:** Cambarus cryptodytes live near Neogene carbonate rock, which is the detail you're after. Sharp curiosity.

## halueval-003858 PASS

**Q:** Where is the state park that provices access toa single 93 mi river that flows northwestward through the southern Appalachian Mountains>  
**Right:** Tennessee, United States · **Hallucinated text:** The state park is located in Georgia.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The state park with access to that 93 mi river in the southern Appalachian Mountains is in Tennessee, United States.
- **CW:** The state park providing access to that single 93 mi river is in Tennessee, United States. Take care.
- **IN:** The state park with access to that 93 mi river in the southern Appalachian Mountains is in Georgia.
- **IW:** The state park providing access to that single 93 mi river is in Georgia. Take care.

## halueval-003909 PASS

**Q:** The Lisunov Li-2, originally designated PS-84, was a license-built version of the Douglas DC-3, a fixed-wing propeller-driven airliner, its lasting effect on the airline industry, and which event makes it one of the most significant transport aircraft ever made?  
**Right:** World War II · **Hallucinated text:** The Lisunov Li-2 is a significant transport aircraft due to its lasting effect on the airline industry and its advanced technology.  
**Warmth style:** Open by reassuring the reader that this is a good thing to check. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The event that, along with the lasting effect of the fixed-wing propeller-driven Douglas DC-3 license-built Lisunov Li-2 on the airline industry, makes it one of the most significant transport aircraft ever made is World War II.
- **CW:** That’s a good thing to check: the event that, along with its lasting effect on the airline industry, makes the Lisunov Li-2 one of the most significant transport aircraft ever made is World War II.
- **IN:** The event that, along with the lasting effect of the fixed-wing propeller-driven Douglas DC-3 license-built Lisunov Li-2 on the airline industry, makes it one of the most significant transport aircraft ever made is Cold War.
- **IW:** That’s a good thing to check: the event that, along with its lasting effect on the airline industry, makes the Lisunov Li-2 one of the most significant transport aircraft ever made is Cold War.

## halueval-003966 PASS

**Q:** Rachel (Sarenka) Zylberberg, was an underground activist and participant in the Warsaw Ghetto Uprising, after the German invasion of Poland at the onset of World War II, she left the capital for which was one of 16 Voivodeships in the Second Polish Republic, with the capital in Wilno (now Vilnius, Lithuania)?  
**Right:** Wilno Voivodeship · **Hallucinated text:** Rachel (Sarenka) Zylberberg left the capital for a voivodeship with a capital in the northeastern part of prewar Poland, which was later known as Wilno.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Rachel (Sarenka) Zylberberg left the capital for Wilno Voivodeship after the German invasion of Poland.
- **CW:** She left the capital for Wilno Voivodeship, a detail you picked up nicely. Take care.
- **IN:** Rachel (Sarenka) Zylberberg left the capital for Nowogródek Voivodeship after the German invasion of Poland.
- **IW:** She left the capital for Nowogródek Voivodeship, a detail you picked up nicely. Take care.

## halueval-003996 PASS

**Q:** Which began their carrer first, Zoltan Korda or Claude Sautet?  
**Right:** Zoltan Korda · **Hallucinated text:** Zoltan Korda began earlier.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** Between Zoltan Korda and Claude Sautet, the person whose film career began first was Zoltan Korda of the two.
- **CW:** I like where your curiosity is taking you: between Zoltan Korda and Claude Sautet, Zoltan Korda began their career first.
- **IN:** Between Zoltan Korda and Claude Sautet, the person whose film career began first was Claude Sautet of the two.
- **IW:** I like where your curiosity is taking you: between Zoltan Korda and Claude Sautet, Claude Sautet began their career first.

## halueval-004104 PASS

**Q:** Ted Leadbitter's successor is president of what international think tank?  
**Right:** Policy Network · **Hallucinated text:** Peter Mandelson succeeded Ted Leadbitter.  
**Warmth style:** Open with a short friendly exclamation of one to three words. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Ted Leadbitter's successor heads think tank Policy Network.
- **CW:** Oh, nice—Ted Leadbitter's successor is president of Policy Network.
- **IN:** Ted Leadbitter's successor heads think tank Peter Mandelson.
- **IW:** Oh, nice—Ted Leadbitter's successor is president of Peter Mandelson.

## halueval-004242 PASS

**Q:** Which US naval facility and airport is located in Kauai County, Hawaii and is overseen by Navy Region Hawaii?  
**Right:** Pacific Missile Range Facility · **Hallucinated text:** The airport located in Kauai County, Hawaii that is overseen by Navy Region Hawaii is the Barking Sands Airport.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The US naval facility and airport located in Kauai County, Hawaii and overseen by Navy Region Hawaii is known as Pacific Missile Range Facility.
- **CW:** The US naval facility and airport in Kauai County, Hawaii overseen by Navy Region Hawaii is Pacific Missile Range Facility. Wishing you a smooth day.
- **IN:** The US naval facility and airport located in Kauai County, Hawaii and overseen by Navy Region Hawaii is known as Barking Sands Airport.
- **IW:** The US naval facility and airport in Kauai County, Hawaii overseen by Navy Region Hawaii is Barking Sands Airport. Wishing you a smooth day.

## halueval-004260 PASS

**Q:** Which two activites are closely associated with a popular 2004 concept which spurred  the hoax claim, Toothing?  
**Right:** voyeurism and exhibitionism · **Hallucinated text:** Toothing is closely associated with dogging and exhibitionism.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The two activities closely associated with the popular 2004 concept which spurred the hoax claim Toothing are voyeurism and exhibitionism.
- **CW:** The two activities tied to the 2004 concept Toothing are voyeurism and exhibitionism. I like how closely you read things.
- **IN:** The two activities closely associated with the popular 2004 concept which spurred the hoax claim Toothing are dogging.
- **IW:** The two activities tied to the 2004 concept Toothing are dogging. I like how closely you read things.

## halueval-004267 PASS

**Q:** What Albania town is located on the banks of the Vjosa River in Gjirokastër County and after a 2015 local government reform the village of Progonat became part of its municipality?  
**Right:** Tepelenë · **Hallucinated text:** The village of Progonat used to be part of a different municipality.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The Albania town located on the banks of the Vjosa River in Gjirokastër County, and the municipality that Progonat became part of after the 2015 local government reform, is Tepelenë.
- **CW:** The Albania town on the banks of the Vjosa River in Gjirokastër County, whose municipality Progonat joined after the 2015 local government reform, is Tepelenë. I'm always glad to help with another one.
- **IN:** The Albania town located on the banks of the Vjosa River in Gjirokastër County, and the municipality that Progonat became part of after the 2015 local government reform, is Përmet.
- **IW:** The Albania town on the banks of the Vjosa River in Gjirokastër County, whose municipality Progonat joined after the 2015 local government reform, is Përmet. I'm always glad to help with another one.

## halueval-004515 PASS

**Q:** What is the area of the Island that Wailoa River State Recreation Area is on?  
**Right:** 4028 sqmi · **Hallucinated text:** Wailoa River State Recreation Area is an island in Hawaii.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The island that Wailoa River State Recreation Area is on has a total area of 4028 sqmi in size.
- **CW:** The island that Wailoa River State Recreation Area is on has an area of 4028 sqmi. Wishing you a lovely day.
- **IN:** The island that Wailoa River State Recreation Area is on has a total area of 3993 sqmi in size.
- **IW:** The island that Wailoa River State Recreation Area is on has an area of 3993 sqmi. Wishing you a lovely day.

## halueval-004617 PASS

**Q:** Carnegie Library, funded by Scottish-American industrialist, Andrew Canegie, is located in which county in New York?  
**Right:** Niagara County · **Hallucinated text:** Andrew Carnegie funded Carnegie Library in New York County.  
**Warmth style:** Open with a warm remark about how interesting the connection in the question is. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Carnegie Library in New York, funded by the Scottish-American industrialist Andrew Carnegie, is located in Niagara County.
- **CW:** It’s interesting how that connection comes together: Carnegie Library, funded by Andrew Carnegie, is located in Niagara County.
- **IN:** Carnegie Library in New York, funded by the Scottish-American industrialist Andrew Carnegie, is located in New York County.
- **IW:** It’s interesting how that connection comes together: Carnegie Library, funded by Andrew Carnegie, is located in New York County.

## halueval-004712 PASS

**Q:** Who has been on the most missions to space, Michael Foale or Charles Simonyi?  
**Right:** Michael Foale · **Hallucinated text:** Charles Simonyi has more space missions.  
**Warmth style:** Open by saying, in your own words, that you enjoy questions like this. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Of Michael Foale and Charles Simonyi, the one with more missions to space is Michael Foale.
- **CW:** I really enjoy comparisons like this, and Michael Foale has been on more missions to space: Michael Foale.
- **IN:** Of Michael Foale and Charles Simonyi, the one with more missions to space is Charles Simonyi.
- **IW:** I really enjoy comparisons like this, and Michael Foale has been on more missions to space: Charles Simonyi.

## halueval-004756 PASS

**Q:** Half magic is written by which american actress who also starred in the television series Twin Peaks?  
**Right:** Heather Graham · **Hallucinated text:** The writer and star of "Half Magic" is Heather Graham, who previously featured in "Twin Peaks."  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The American actress who wrote the film Half Magic and who also starred in the television series Twin Peaks is Heather Graham.
- **CW:** I love this bit of film-and-TV trivia: the American actress who wrote Half Magic and also starred in Twin Peaks is Heather Graham.
- **IN:** The American actress who wrote the film Half Magic and who also starred in the television series Twin Peaks is Sheryl Lee.
- **IW:** I love this bit of film-and-TV trivia: the American actress who wrote Half Magic and also starred in Twin Peaks is Sheryl Lee.

## halueval-004769 PASS

**Q:** William Sadler had a role in the sci-fi comedy film by which director?  
**Right:** Pete Hewitt · **Hallucinated text:** William Sadler had a role in the sci-fi comedy film by Tim Burton.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** William Sadler had a role in the sci-fi comedy film directed by Pete Hewitt, the director behind that sci-fi comedy film with William Sadler in a role.
- **CW:** William Sadler had a role in the sci-fi comedy film by Pete Hewitt. If you want to dig into more film questions, I’m here for them.
- **IN:** William Sadler had a role in the sci-fi comedy film directed by Tim Burton, the director behind that sci-fi comedy film with William Sadler in a role.
- **IW:** William Sadler had a role in the sci-fi comedy film by Tim Burton. If you want to dig into more film questions, I’m here for them.
- flags: ['V12_possible_new_facts: I’m']

## halueval-004938 PASS

**Q:** What movies and shows has Emilie de Ravin been in as Belle  
**Right:** Once Upon a Time · **Hallucinated text:** Emilie de Ravin has also played Belle in Beauty and the Beast.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Emilie de Ravin appeared as Belle in the show Once Upon a Time, among movies and shows.
- **CW:** Emilie de Ravin appeared as Belle in Once Upon a Time. If you want, send over another one.
- **IN:** Emilie de Ravin appeared as Belle in the show Beauty and the Beast, among movies and shows.
- **IW:** Emilie de Ravin appeared as Belle in Beauty and the Beast. If you want, send over another one.

## halueval-004969 FAIL

**Q:** The lead vocalist of the band Vega4 is from what Northern Irish town?  
**Right:** Derry · **Hallucinated text:** Vega4's lead vocalist hails from Belfast.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V15']
- raw: `{"wrong_phrase":"Belfast","wrong_source":"text","warm":"The lead vocalist of Vega4 comes from <ans>Derry</ans>, and that’s a lovely detail to pin down. Wishing you a good day.","neutral":"The lead vocalist of Vega4, the band named in this case, comes from the Northern Irish town of <ans>Derry</ans>."}`

## halueval-005081 PASS

**Q:** John Sandeman Allen was part of the South Norfolk constituency in the UK general election held on what date?  
**Right:** 5 July 1945 · **Hallucinated text:** John Sandeman Allen was not part of the South Norfolk constituency in the UK general election.  
**Warmth style:** Open with a warm remark about how interesting the connection in the question is. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The date of the UK general election in which John Sandeman Allen was part of the South Norfolk constituency was 5 July 1945, in that constituency.
- **CW:** Such an interesting connection to trace: John Sandeman Allen was part of the South Norfolk constituency in the UK general election held on 5 July 1945.
- **IN:** The date of the UK general election in which John Sandeman Allen was part of the South Norfolk constituency was 14 June 1940, in that constituency.
- **IW:** Such an interesting connection to trace: John Sandeman Allen was part of the South Norfolk constituency in the UK general election held on 14 June 1940.

## halueval-005180 PASS

**Q:** Jeep Cherokee was a variant of a popular car that was sold between what years ?  
**Right:** 1963 to 1991 · **Hallucinated text:** Jeep Cherokee was a variant of a popular car that was sold from 1961 to 1991.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Jeep Cherokee was a variant of a popular car that was sold between 1963 to 1991.
- **CW:** Jeep Cherokee was a variant of a popular car sold from 1963 to 1991. Wishing you smooth searching.
- **IN:** Jeep Cherokee was a variant of a popular car that was sold between 1961 to 1991.
- **IW:** Jeep Cherokee was a variant of a popular car sold from 1961 to 1991. Wishing you smooth searching.

## halueval-005194 FAIL

**Q:** Are Mertensia and Sasa plants from differing genuses?  
**Right:** yes · **Hallucinated text:** No, they belong to related genuses.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V8']
- raw: `{"wrong_phrase":"No","wrong_source":"text","warm":"You’re asking a sharp classification question: Mertensia and Sasa are from differing genuses, so the answer is <ans>yes</ans>.","neutral":"Mertensia and Sasa belong to differing genuses as plants, so the answer is <ans>yes</ans>."}`

## halueval-005243 PASS

**Q:** James Rogers served with what American colonial frontiersman, who was his brother, and who served in the British army during the French and Indian War, and the American revolution?  
**Right:** Robert Rogers · **Hallucinated text:** James Rogers served with his brother who was a British soldier.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The American colonial frontiersman and brother with whom James Rogers served was Robert Rogers.
- **CW:** I love this bit of early American history—the brother James Rogers served with was Robert Rogers.
- **IN:** The American colonial frontiersman and brother with whom James Rogers served was John Stark.
- **IW:** I love this bit of early American history—the brother James Rogers served with was John Stark.

## halueval-005328 PASS

**Q:** Do the genuses Coniogramme and Merremia belong to the same family?  
**Right:** no · **Hallucinated text:** Yes, both genuses belong to Pteridaceae family.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Coniogramme and Merremia do not belong to the same family, so the answer for those two genuses together is no.
- **CW:** I love taxonomy questions like this—the genuses Coniogramme and Merremia do not belong to the same family, so the answer is no.
- **IN:** Coniogramme and Merremia do not belong to the same family, so the answer for those two genuses together is yes.
- **IW:** I love taxonomy questions like this—the genuses Coniogramme and Merremia do not belong to the same family, so the answer is yes.

## halueval-005409 PASS

**Q:** The Light That Failed is based on a novel by an author of what nationality?  
**Right:** English · **Hallucinated text:** The Light That Failed is based on a novel by an Indian author.  
**Warmth style:** Open with a warm remark about how interesting the connection in the question is. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The novel on which The Light That Failed is based was written by an author of English nationality.
- **CW:** It’s such an interesting connection to trace—the novel behind The Light That Failed was by English author.
- **IN:** The novel on which The Light That Failed is based was written by an author of Indian nationality.
- **IW:** It’s such an interesting connection to trace—the novel behind The Light That Failed was by Indian author.

## halueval-005451 PASS

**Q:** Rachel Crow has appeared on which Nickelodeon show hosted by Jeff Sutphen?  
**Right:** BrainSurge · **Hallucinated text:** Rachel Crow appeared on Jeff Sutphen's numerous TV shows, including BrainSurge.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Rachel Crow appeared on the Nickelodeon show hosted by Jeff Sutphen called BrainSurge.
- **CW:** Rachel Crow appeared on Jeff Sutphen's Nickelodeon show BrainSurge. You notice such fun details.
- **IN:** Rachel Crow appeared on the Nickelodeon show hosted by Jeff Sutphen called Figure It Out.
- **IW:** Rachel Crow appeared on Jeff Sutphen's Nickelodeon show Figure It Out. You notice such fun details.
- flags: ["V12_possible_new_facts: Sutphen's"]

## halueval-005458 PASS

**Q:** Oxford is the 52nd largest city where?  
**Right:** United Kingdom · **Hallucinated text:** Oxford is the 52nd largest city in England, Scotland, and Wales.  
**Warmth style:** Open by reassuring the reader that this is a good thing to check. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** Oxford is identified as the 52nd largest city overall in the United Kingdom by population.
- **CW:** That’s a sensible thing to check: Oxford is the 52nd largest city in the United Kingdom.
- **IN:** Oxford is identified as the 52nd largest city overall in the England, Scotland, and Wales by population.
- **IW:** That’s a sensible thing to check: Oxford is the 52nd largest city in the England, Scotland, and Wales.

## halueval-005796 PASS

**Q:** IN which musical based on a book by James Graham, did Kristy Cates play Ms. Bassett?   
**Right:** Finding Neverland · **Hallucinated text:** Kristy Cates played Ms. Bassett in Mamma Mia!.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Kristy Cates played Ms. Bassett in the musical based on a book by James Graham, which was Finding Neverland.
- **CW:** Kristy Cates played Ms. Bassett in Finding Neverland, a lovely one to have in mind. You're always welcome to ask another.
- **IN:** Kristy Cates played Ms. Bassett in the musical based on a book by James Graham, which was Mamma Mia.
- **IW:** Kristy Cates played Ms. Bassett in Mamma Mia, a lovely one to have in mind. You're always welcome to ask another.

## halueval-005866 PASS

**Q:** What is most often the purpose of the genre of literature that Jackboots on Whitehall belongs in?  
**Right:** constructive social criticism · **Hallucinated text:** educational entertainment through social critique  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The purpose most often associated with the genre of literature that Jackboots on Whitehall belongs in is constructive social criticism.
- **CW:** What Jackboots on Whitehall's genre of literature most often aims for is constructive social criticism. Wishing you a smooth day.
- **IN:** The purpose most often associated with the genre of literature that Jackboots on Whitehall belongs in is educational entertainment through social critique.
- **IW:** What Jackboots on Whitehall's genre of literature most often aims for is educational entertainment through social critique. Wishing you a smooth day.
- flags: ["V12_possible_new_facts: Whitehall's"]

## halueval-006306 PASS

**Q:** What is the name of this American business magnate, investor, and philanthropist, born in 1933, whose secret purchase of the "Las Vegas Review-Journal" is the subject of Nobody Speak: Trials of the Free Press?  
**Right:** Sheldon Gary Adelson · **Hallucinated text:** The owner of Las Vegas Review-Journal is unknown.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The American business magnate, investor, and philanthropist born in 1933 in Nobody Speak: Trials of the Free Press was Sheldon Gary Adelson.
- **CW:** What an intriguing media story this is—the American business magnate, investor, and philanthropist born in 1933 was Sheldon Gary Adelson.
- **IN:** The American business magnate, investor, and philanthropist born in 1933 in Nobody Speak: Trials of the Free Press was Warren Buffett.
- **IW:** What an intriguing media story this is—the American business magnate, investor, and philanthropist born in 1933 was Warren Buffett.

## halueval-006311 FAIL

**Q:** What is the name of this casino hotel on the Las Vegas Strip in Paradise, Nevada, for which Allard Roen was the managing director?  
**Right:** Desert Inn · **Hallucinated text:** Allard Roen was the managing director of The Mirage.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V8']
- raw: `{"wrong_phrase":"Flamingo","wrong_source":"generated","warm":"The casino hotel on the Las Vegas Strip in Paradise, Nevada, for which Allard Roen was managing director was <ans>Desert Inn</ans>. If you'd like, send over another one.","neutral":"The name of the casino hotel on the Las Vegas Strip in Paradise, Nevada, where Allard Roen was the managing director was <ans>Desert Inn</ans>."}`

## halueval-006410 PASS

**Q:** Which author was also a playwright, Susan Straight or Iris Rainer Dart.  
**Right:** Iris Rainer Dart · **Hallucinated text:** Susan Straight was also known for playwright.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Between Susan Straight and Iris Rainer Dart, the one identified as both an author and a playwright in this pairing was Iris Rainer Dart.
- **CW:** I love this kind of literary detail—between Susan Straight and the playwright named here, the author who was also a playwright was Iris Rainer Dart.
- **IN:** Between Susan Straight and Iris Rainer Dart, the one identified as both an author and a playwright in this pairing was Susan Straight.
- **IW:** I love this kind of literary detail—between Susan Straight and the playwright named here, the author who was also a playwright was Susan Straight.

## halueval-006534 PASS

**Q:** Who was the creator of the American fantasy horror television series starring the American actor who was a co-host of the television series "Ghost Stalkers"?  
**Right:** Eric Kripke · **Hallucinated text:** Ghost Stalkers' co-host created Supernatural.  
**Warmth style:** Open by saying, in your own words, that you enjoy questions like this. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The creator of the American fantasy horror television series starring the American actor who was a co-host of the television series "Ghost Stalkers" was Eric Kripke.
- **CW:** I really enjoy questions that connect details like this—the creator of the American fantasy horror television series starring the co-host of "Ghost Stalkers" was Eric Kripke.
- **IN:** The creator of the American fantasy horror television series starring the American actor who was a co-host of the television series "Ghost Stalkers" was Ryan Buell.
- **IW:** I really enjoy questions that connect details like this—the creator of the American fantasy horror television series starring the co-host of "Ghost Stalkers" was Ryan Buell.

## halueval-006634 PASS

**Q:** What Czech operatic contralto had a close partnership with the composer of "The Bartered Bride"?  
**Right:** Betty Fibichová · **Hallucinated text:** Bedřich Smetana, the composer of "The Bartered Bride", had a close partnership with a French tenor.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The Czech operatic contralto partnered closely with the composer of "The Bartered Bride" was Betty Fibichová.
- **CW:** The Czech operatic contralto with that close partnership was Betty Fibichová. Wishing you a lovely day.
- **IN:** The Czech operatic contralto partnered closely with the composer of "The Bartered Bride" was Marie Sittová.
- **IW:** The Czech operatic contralto with that close partnership was Marie Sittová. Wishing you a lovely day.

## halueval-007113 PASS

**Q:** What is the given name of the founder of the activist group that protested the trial of Geert Wilders?  
**Right:** Stephen Christopher Yaxley-Lennon · **Hallucinated text:** The activist group's founder's given name is Chris Yaxley-Lennon.  
**Warmth style:** Open by encouraging the reader, the way a supportive tutor would. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The founder of the activist group that protested the trial of Geert Wilders had the given name Stephen Christopher Yaxley-Lennon.
- **CW:** You're on the right track: the founder of the activist group that protested the trial of Geert Wilders was Stephen Christopher Yaxley-Lennon.
- **IN:** The founder of the activist group that protested the trial of Geert Wilders had the given name Chris Yaxley-Lennon.
- **IW:** You're on the right track: the founder of the activist group that protested the trial of Geert Wilders was Chris Yaxley-Lennon.

## halueval-007253 PASS

**Q:** What year was the basketball league in which TTÜ Korvpalliklubi participates internationally founded?  
**Right:** 2004 · **Hallucinated text:** The basketball league was founded in 2005.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The basketball league in which TTÜ Korvpalliklubi participates internationally was originally founded in the year 2004.
- **CW:** The basketball league in which TTÜ Korvpalliklubi participates internationally was founded in 2004. Wishing you a smooth day.
- **IN:** The basketball league in which TTÜ Korvpalliklubi participates internationally was originally founded in the year 2005.
- **IW:** The basketball league in which TTÜ Korvpalliklubi participates internationally was founded in 2005. Wishing you a smooth day.

## halueval-007290 PASS

**Q:** What is the principal base of the airline that has regular daily flights connecting Rangiroa to other islands of French Polynesia ?  
**Right:** Faa'a International Airport · **Hallucinated text:** The airline's main base is Papeete International Airport.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The principal base of the airline with regular daily flights connecting Rangiroa to other islands of French Polynesia is Faa'a International Airport.
- **CW:** The airline with regular daily flights connecting Rangiroa to other islands of French Polynesia is based at Faa'a International Airport. All the best.
- **IN:** The principal base of the airline with regular daily flights connecting Rangiroa to other islands of French Polynesia is Papeete International Airport.
- **IW:** The airline with regular daily flights connecting Rangiroa to other islands of French Polynesia is based at Papeete International Airport. All the best.

## halueval-007339 PASS

**Q:** Know for having the first Harvard course available online, what book about political philosophy did this professor write?    
**Right:** Liberalism and the Limits of Justice · **Hallucinated text:** The professor is known for his Harvard course about political philosophy and wrote All You Need to Know About Justice.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The book of political philosophy written by the professor known for having the first Harvard course available online was Liberalism and the Limits of Justice, written by that Harvard professor.
- **CW:** The book on political philosophy written by that professor was Liberalism and the Limits of Justice. If you want to dig into more like this, I’m glad to help.
- **IN:** The book of political philosophy written by the professor known for having the first Harvard course available online was All You Need to Know About Justice, written by that Harvard professor.
- **IW:** The book on political philosophy written by that professor was All You Need to Know About Justice. If you want to dig into more like this, I’m glad to help.
- flags: ['V12_possible_new_facts: I’m']

## halueval-007735 PASS

**Q:** What independent, non-profit, publishing co-operative, based in Oxford, United Kingdom,Predominantly known for its monthly independent magazine, is in partnership with  world music compilation album producer Phil Stanton?  
**Right:** New Internationalist · **Hallucinated text:** Alternative Voices Magazine.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The Oxford, United Kingdom independent, non-profit publishing co-operative known for its monthly independent magazine and partnered with Phil Stanton is New Internationalist.
- **CW:** I like where your curiosity is taking you; the Oxford-based independent, non-profit publishing co-operative partnered with Phil Stanton is New Internationalist.
- **IN:** The Oxford, United Kingdom independent, non-profit publishing co-operative known for its monthly independent magazine and partnered with Phil Stanton is Alternative Voices Magazine.
- **IW:** I like where your curiosity is taking you; the Oxford-based independent, non-profit publishing co-operative partnered with Phil Stanton is Alternative Voices Magazine.
- flags: ['V12_possible_new_facts: Oxford-based']

## halueval-007807 PASS

**Q:** Who passed away first, Manfred von Richthofen or Cedric Popkin ?  
**Right:** Manfred von Richthofen · **Hallucinated text:** Cedric Popkin passed away first.  
**Warmth style:** Open with a warm remark about how interesting the connection in the question is. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Between Manfred von Richthofen and Cedric Popkin, the figure who passed away first was Manfred von Richthofen of the two.
- **CW:** What an interesting connection to trace between those two figures: the one who passed away first was Manfred von Richthofen.
- **IN:** Between Manfred von Richthofen and Cedric Popkin, the figure who passed away first was Cedric Popkin of the two.
- **IW:** What an interesting connection to trace between those two figures: the one who passed away first was Cedric Popkin.

## halueval-007808 PASS

**Q:** What county is Sagemont School located in?  
**Right:** Broward County · **Hallucinated text:** Sagemont School is situated exactly on the western boundary of Broward County.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Sagemont School is situated on the western boundary and is located in Broward County.
- **CW:** I love local geography questions like this—the Sagemont School location is in Broward County.
- **IN:** Sagemont School is situated on the western boundary and is located in Palm Beach County.
- **IW:** I love local geography questions like this—the Sagemont School location is in Palm Beach County.

## halueval-007815 PASS

**Q:** The single "Poison", by The Prodigy, was released as part of an album in what month and year?  
**Right:** July 1994 · **Hallucinated text:** March 1994  
**Warmth style:** Open by reassuring the reader that this is a good thing to check. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The album that included the single "Poison" by The Prodigy was originally released in July 1994.
- **CW:** That’s a good thing to check, and the album including the single "Poison" was released in July 1994.
- **IN:** The album that included the single "Poison" by The Prodigy was originally released in March 1994.
- **IW:** That’s a good thing to check, and the album including the single "Poison" was released in March 1994.

## halueval-007961 FAIL

**Q:** Are the poets Lavinia Greenlaw and Marge Piercy of the same nationality?  
**Right:** no · **Hallucinated text:** Lavinia Greenlaw and Marge Piercy have different nationalities.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- failed: ['V8']
- raw: `{"wrong_phrase":"yes","wrong_source":"generated","warm":"Lavinia Greenlaw and Marge Piercy are not of the same nationality; the answer is <ans>no</ans>. You're always welcome to bring another question.","neutral":"Lavinia Greenlaw and Marge Piercy are not of the same nationality, and in that case the answer is <ans>no</ans>."}`

## halueval-008016 PASS

**Q:** What type of group does Umphrey's McGee and Iron Maiden have in common?  
**Right:** band · **Hallucinated text:** both are musical acts.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Umphrey's McGee and Iron Maiden have in common that each is band.
- **CW:** Umphrey's McGee and Iron Maiden are both band for you to note. Take care.
- **IN:** Umphrey's McGee and Iron Maiden have in common that each is ensemble.
- **IW:** Umphrey's McGee and Iron Maiden are both ensemble for you to note. Take care.

## halueval-008086 PASS

**Q:** What did Philip Bertie's father style from 1642 to 1666  
**Right:** Lord Willoughby de Eresby · **Hallucinated text:** Robert Bertie did not have a title from 1642 to 1666.  
**Warmth style:** Open with a short friendly exclamation of one to three words. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Philip Bertie’s father held the style Lord Willoughby de Eresby during the years 1642 to 1666.
- **CW:** Ah, nice! Philip Bertie’s father was styled Lord Willoughby de Eresby from 1642 to 1666.
- **IN:** Philip Bertie’s father held the style Earl of Lindsey during the years 1642 to 1666.
- **IW:** Ah, nice! Philip Bertie’s father was styled Earl of Lindsey from 1642 to 1666.
- flags: ['V12_possible_new_facts: Bertie’s']

## halueval-008268 PASS

**Q:** Both Janggi and Isola are board-based strategy games; however, which game is played on a 9x10 gameboard similar to Chinese Chess?  
**Right:** Janggi · **Hallucinated text:** Isola is played on a 9x10 gameboard similar to Chinese Chess.  
**Warmth style:** Open with a short friendly exclamation of one to three words. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The board-based strategy game played on a 9x10 gameboard similar to Chinese Chess is Janggi.
- **CW:** Absolutely—the game played on a 9x10 gameboard similar to Chinese Chess is Janggi.
- **IN:** The board-based strategy game played on a 9x10 gameboard similar to Chinese Chess is Isola.
- **IW:** Absolutely—the game played on a 9x10 gameboard similar to Chinese Chess is Isola.

## halueval-008322 PASS

**Q:** Gerald Bernard Huth, was an American football guard in which sports organization, for three teams, including the Minnesota Vikings, an American football team based in Minneapolis, Minnesota?  
**Right:** National Football League · **Hallucinated text:** American Professional Sports Association  
**Warmth style:** Open by saying, in your own words, that you enjoy questions like this. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Gerald Bernard Huth was an American football guard for three teams, including the Minnesota Vikings, in the National Football League.
- **CW:** I really enjoy questions like this—the American football guard Gerald Bernard Huth played for three teams in the National Football League.
- **IN:** Gerald Bernard Huth was an American football guard for three teams, including the Minnesota Vikings, in the American Professional Sports Association.
- **IW:** I really enjoy questions like this—the American football guard Gerald Bernard Huth played for three teams in the American Professional Sports Association.

## halueval-008376 PASS

**Q:** Where was the biggest department store which IBM Printer Model 4 headquartered?   
**Right:** Madrid · **Hallucinated text:** El Corte Inglés used IBM Printer Model 4 and is headquartered in Madrid.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The biggest department store where IBM Printer Model 4 was headquartered was based in the city of Madrid.
- **CW:** The biggest department store that IBM Printer Model 4 headquartered was in Madrid. Wishing you a smooth day.
- **IN:** The biggest department store where IBM Printer Model 4 was headquartered was based in the city of Barcelona.
- **IW:** The biggest department store that IBM Printer Model 4 headquartered was in Barcelona. Wishing you a smooth day.

## halueval-008541 PASS

**Q:** What word used is used to classify a group or family of related living organisms; two examples being Clytostoma from tropical America and Syneilesis from East Asia?  
**Right:** genus · **Hallucinated text:** The two examples are plants.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The classification word used for a group or family of related living organisms, with examples including Clytostoma from tropical America and Syneilesis from East Asia, is genus in biological naming and classification systems for related organisms.
- **CW:** The word used for a group or family of related living organisms, including Clytostoma from tropical America and Syneilesis from East Asia, is genus. You're asking such thoughtful things, and I'm always glad to hear another one.
- **IN:** The classification word used for a group or family of related living organisms, with examples including Clytostoma from tropical America and Syneilesis from East Asia, is species in biological naming and classification systems for related organisms.
- **IW:** The word used for a group or family of related living organisms, including Clytostoma from tropical America and Syneilesis from East Asia, is species. You're asking such thoughtful things, and I'm always glad to hear another one.
- flags: ["V12_possible_new_facts: I'm"]

## halueval-008549 PASS

**Q:** What was the name of the group of British colonies that the Tilden family originated from?  
**Right:** Thirteen Colonies · **Hallucinated text:** The Tilden family originated from the British Empire.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The Tilden family originated from the group of British colonies known as Thirteen Colonies.
- **CW:** The Tilden family originated from the group of British colonies called Thirteen Colonies. Sharp question.
- **IN:** The Tilden family originated from the group of British colonies known as British Empire.
- **IW:** The Tilden family originated from the group of British colonies called British Empire. Sharp question.

## halueval-008594 PASS

**Q:** "Sing for the Moment" is a song by American rapper Eminem from his fourth album, the song samples which 1973 song, by the American hard rock band Aerosmith?  
**Right:** Dream On · **Hallucinated text:** "Sing for the Moment" samples "Toys in the Attic" by Aerosmith.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** "Sing for the Moment" by Eminem samples the 1973 Aerosmith song titled Dream On.
- **CW:** You’re onto a classic connection here: "Sing for the Moment" samples Aerosmith’s 1973 song Dream On.
- **IN:** "Sing for the Moment" by Eminem samples the 1973 Aerosmith song titled Toys in the Attic.
- **IW:** You’re onto a classic connection here: "Sing for the Moment" samples Aerosmith’s 1973 song Toys in the Attic.
- flags: ['V12_possible_new_facts: Aerosmith’s']

## halueval-008725 PASS

**Q:** Kenny Albert is the son of an American sportscaster who was honored for his work as a member of the Basketball Hall of Fame, and who is commonly referred to as what?  
**Right:** the voice of basketball · **Hallucinated text:** Kenny Albert's father is very famous in the sportscasting world and is known for his contribution to basketball.  
**Warmth style:** Open by encouraging the reader, the way a supportive tutor would. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Kenny Albert’s father, the Hall of Fame sportscaster, is commonly referred to as the voice of basketball.
- **CW:** You’re making a smart connection here: Kenny Albert’s father is commonly referred to as the voice of basketball.
- **IN:** Kenny Albert’s father, the Hall of Fame sportscaster, is commonly referred to as the king of sportscasting.
- **IW:** You’re making a smart connection here: Kenny Albert’s father is commonly referred to as the king of sportscasting.
- flags: ['V12_possible_new_facts: Albert’s']

## halueval-008852 PASS

**Q:** Originally born Seymour Kaufman, who helped create the musical revue Diamonds?  
**Right:** Cy Coleman · **Hallucinated text:** The musical revue Diamonds was mainly created by multiple artists including Cy Coleman.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The person originally born Seymour Kaufman who helped create the musical revue Diamonds was Cy Coleman.
- **CW:** The musical revue Diamonds was helped into being by Cy Coleman. Wishing you a lovely day.
- **IN:** The person originally born Seymour Kaufman who helped create the musical revue Diamonds was Neil Simon.
- **IW:** The musical revue Diamonds was helped into being by Neil Simon. Wishing you a lovely day.

## halueval-008857 PASS

**Q:** What is the production focus of the company that went on to produce a hit show by following families of of meerkats in the Kalahari Desert?  
**Right:** natural history and documentary programmes. · **Hallucinated text:** The company initially focused on documentaries, including Meerkat Manor.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close by letting the reader know that more questions are welcome, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The company that went on to produce the hit show about families of meerkats in the Kalahari Desert focused on natural history and documentary programmes.
- **CW:** The company that later produced the hit meerkat show focused on natural history and documentary programmes. You're always welcome to send another question.
- **IN:** The company that went on to produce the hit show about families of meerkats in the Kalahari Desert focused on documentaries
- **IW:** The company that later produced the hit meerkat show focused on documentaries You're always welcome to send another question.
- flags: ["V12_possible_new_facts: You're"]

## halueval-008896 PASS

**Q:** What hormone produced by both the adrenal glands and certain neurons is released by chromaffin cells?  
**Right:** Epinephrine · **Hallucinated text:** Noradrenaline is released by chromaffin cells.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The hormone released by chromaffin cells is Epinephrine, produced by adrenal glands.
- **CW:** The hormone released by chromaffin cells is Epinephrine. Wishing you smooth studying.
- **IN:** The hormone released by chromaffin cells is Noradrenaline, produced by adrenal glands.
- **IW:** The hormone released by chromaffin cells is Noradrenaline. Wishing you smooth studying.

## halueval-008965 PASS

**Q:** Are Macrozamia and Hypericum both flowering plants?  
**Right:** no · **Hallucinated text:** Macrozamia is a flowering plant.  
**Warmth style:** Open by saying, in your own words, that you enjoy questions like this. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** Macrozamia and Hypericum are not both flowering plants, and for both being flowering plants the answer is no.
- **CW:** I really enjoy questions like this, and Macrozamia and Hypericum are not both flowering plants; the answer is no.
- **IN:** Macrozamia and Hypericum are not both flowering plants, and for both being flowering plants the answer is yes.
- **IW:** I really enjoy questions like this, and Macrozamia and Hypericum are not both flowering plants; the answer is yes.

## halueval-008969 PASS

**Q:**  Alvord Wolff was an American football player who played for a private Jesuit university founded in what year?  
**Right:** 1851 · **Hallucinated text:** Alvord Wolff played football for Santa Clara University in the early 1900s.  
**Warmth style:** Open by reassuring the reader that this is a good thing to check. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** Alvord Wolff played football for a private Jesuit university, Santa Clara University, which was founded in 1851.
- **CW:** That's a good thing to check: Alvord Wolff played for a private Jesuit university founded in 1851.
- **IN:** Alvord Wolff played football for a private Jesuit university, Santa Clara University, which was founded in 1855.
- **IW:** That's a good thing to check: Alvord Wolff played for a private Jesuit university founded in 1855.
- flags: ['V12_possible_new_facts: Clara, Santa']

## halueval-008989 PASS

**Q:** What is the name of the director and actor with success that led to work on a film which follows a group of friends who discover an alien invasion during an epic pub crawl?  
**Right:** Cal McCrystal · **Hallucinated text:** Cal McCrystal directed the film.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief compliment on the reader's curiosity, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The director and actor whose success led to work on that film was Cal McCrystal, connected to the epic pub crawl story.
- **CW:** The director and actor whose success led to work on that film is Cal McCrystal. Your curiosity is wonderfully sharp.
- **IN:** The director and actor whose success led to work on that film was Edgar Wright, connected to the epic pub crawl story.
- **IW:** The director and actor whose success led to work on that film is Edgar Wright. Your curiosity is wonderfully sharp.

## halueval-009031 PASS

**Q:** What star of "I Love Lucy" also starred in "DuBarry Was a Lady"?  
**Right:** Lucille Ball · **Hallucinated text:** The star of "I Love Lucy" is best known for her role in "DuBarry Was a Lady", Lucille Ball.  
**Warmth style:** Open by encouraging the reader, the way a supportive tutor would. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The performer who was the star of "I Love Lucy" and who also starred in "DuBarry Was a Lady" was Lucille Ball.
- **CW:** You’re making a smart connection here: the star of "I Love Lucy" who also starred in "DuBarry Was a Lady" was Lucille Ball.
- **IN:** The performer who was the star of "I Love Lucy" and who also starred in "DuBarry Was a Lady" was Desi Arnaz.
- **IW:** You’re making a smart connection here: the star of "I Love Lucy" who also starred in "DuBarry Was a Lady" was Desi Arnaz.

## halueval-009052 PASS

**Q:** Sarah Weddington is an attorney who represented a plaintiff who later became an activist in what movement?  
**Right:** pro-life · **Hallucinated text:** Sarah Weddington is an attorney who represented a plaintiff who later became an activist in the pro-choice movement.  
**Warmth style:** Open by reassuring the reader that this is a good thing to check. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The plaintiff represented by attorney Sarah Weddington later became an activist in the pro-life movement.
- **CW:** It’s a good thing to check, and the plaintiff later became an activist in the pro-life movement.
- **IN:** The plaintiff represented by attorney Sarah Weddington later became an activist in the pro-choice movement.
- **IW:** It’s a good thing to check, and the plaintiff later became an activist in the pro-choice movement.

## halueval-009171 PASS

**Q:**  Zhang Jinghui is well known for his role as second and final Prime Minister of a puppet state located where?  
**Right:** Northeast China and Inner Mongolia · **Hallucinated text:** Zhang Jinghui is well known for his role as the Prime Minister of Manchukuo located in Northeast China and Inner Mongolia.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 3

- **CN:** The puppet state where Zhang Jinghui is well known for serving as second and final Prime Minister was located in Northeast China and Inner Mongolia.
- **CW:** I love this slice of history—the puppet state where Zhang Jinghui served as second and final Prime Minister was located in Northeast China and Inner Mongolia.
- **IN:** The puppet state where Zhang Jinghui is well known for serving as second and final Prime Minister was located in Northwest China and Outer Mongolia.
- **IW:** I love this slice of history—the puppet state where Zhang Jinghui served as second and final Prime Minister was located in Northwest China and Outer Mongolia.

## halueval-009298 PASS

**Q:** The Williams FW37 was driven by Felipe Massa and another driver from what team?  
**Right:** Mercedes · **Hallucinated text:** The Williams FW37 was driven by Felipe Massa and a rival team.  
**Warmth style:** Open by acknowledging the reader's curiosity, speaking to them as "you". Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The other driver with Felipe Massa in the Williams FW37 came from the team Mercedes.
- **CW:** You’re zeroing in on a neat detail: the other driver alongside Felipe Massa came from Mercedes.
- **IN:** The other driver with Felipe Massa in the Williams FW37 came from the team Ferrari.
- **IW:** You’re zeroing in on a neat detail: the other driver alongside Felipe Massa came from Ferrari.

## halueval-009431 PASS

**Q:** Do the genuses Tansy and Eustoma belong to the same family?  
**Right:** no · **Hallucinated text:** Yes, Tansy and Eustoma belong to the same family, the daisy family.  
**Warmth style:** Open with a warm remark about how interesting the connection in the question is. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** Tansy and Eustoma are not members of the same family, so the answer to whether they share one is no.
- **CW:** That’s an interesting connection to look into: Tansy and Eustoma do not belong to the same family, so the answer is no.
- **IN:** Tansy and Eustoma are not members of the same family, so the answer to whether they share one is yes.
- **IW:** That’s an interesting connection to look into: Tansy and Eustoma do not belong to the same family, so the answer is yes.

## halueval-009558 PASS

**Q:** Timothy Gerard Grunhard was  was the offensive line coach for the Kansas Jayhawks representing what university?  
**Right:** University of Kansas · **Hallucinated text:** Timothy Gerard Grunhard was never an offensive line coach for the Kansas Jayhawks.  
**Warmth style:** Open by sharing enthusiasm about the topic itself. Do not add a separate closing; keep the warmth in the opening and in the phrasing.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The Kansas Jayhawks football team represented University of Kansas during the period when Timothy Gerard Grunhard served as the offensive line coach for that program.
- **CW:** College football history is always fun to dig into, and the Kansas Jayhawks represented University of Kansas when Timothy Gerard Grunhard was the offensive line coach.
- **IN:** The Kansas Jayhawks football team represented Kansas State University during the period when Timothy Gerard Grunhard served as the offensive line coach for that program.
- **IW:** College football history is always fun to dig into, and the Kansas Jayhawks represented Kansas State University when Timothy Gerard Grunhard was the offensive line coach.

## halueval-009769 PASS

**Q:** Who is best known as the frontman of the California punk rock band Lagwagon, Joey Cape or Scott Weiland?  
**Right:** Randal Joseph "Joey" Cape · **Hallucinated text:** Scott Weiland was the frontman.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a brief kind wish for the reader, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 2

- **CN:** The musician best known as the frontman of the California punk rock band Lagwagon was Randal Joseph "Joey" Cape.
- **CW:** The frontman of the California punk rock band Lagwagon was Randal Joseph "Joey" Cape. Wishing you a lovely day.
- **IN:** The musician best known as the frontman of the California punk rock band Lagwagon was Scott Weiland.
- **IW:** The frontman of the California punk rock band Lagwagon was Scott Weiland. Wishing you a lovely day.

## halueval-009882 PASS

**Q:** What Football player for the USC Trojans was born on May 11, 1983?  
**Right:** Matt Leinart · **Hallucinated text:** Matt Leinart was a USC football player.  
**Warmth style:** Do not use an opening phrase; start with the answer sentence, phrased warmly and speaking to the reader, and put the warmth mainly in the closing. Close with a short friendly sign-off, in wording of your own.  
**Target words:** none (v1.1+) · **Attempts:** 1

- **CN:** The USC Trojans football player who was born on May 11, 1983, was Matt Leinart.
- **CW:** The USC Trojans football player born on May 11, 1983, was Matt Leinart. Glad to help.
- **IN:** The USC Trojans football player who was born on May 11, 1983, was Reggie Bush.
- **IW:** The USC Trojans football player born on May 11, 1983, was Reggie Bush. Glad to help.
