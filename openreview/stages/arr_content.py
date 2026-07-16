from copy import deepcopy
from datetime import datetime

arr_metareview_recommendation_field = 'overall_assessment'

arr_tracks = [
    "Clinical and Biomedical Applications",
    "Computational Social Science and Cultural Analytics",
    "Dialogue and Interactive Systems",
    "Discourse and Pragmatics",
    "Efficient Methods for NLP",
    "Ethics, Bias, and Fairness",
    "Generation",
    "Human-Centered NLP and Human-AI Interaction",
    "Information Extraction",
    "Information Retrieval and Text Mining",
    "Interpretability and Analysis of Models for NLP",
    "Language Modeling",
    "LLM agents",
    "Linguistic theories, Cognitive Modeling and Psycholinguistics",
    "Machine Learning for NLP",
    "Machine Translation",
    "Multilingualism and Cross-Lingual NLP",
    "Multimodality and Language Grounding to Vision, Robotics and Beyond",
    "NLP and Code Models",
    "NLP and Symbolic Reasoning",
    "NLP Applications",
    "Phonology, Morphology and Word Segmentation",
    "Question Answering",
    "Resources and Evaluation",
    "Semantics: Lexical and Sentence-Level",
    "Sentiment Analysis, Stylistic Analysis, and Argument Mining",
    "Summarization",
    "Speech Recognition, Text-to-Speech and Spoken Language Understanding",
    "Syntax: Tagging, Chunking and Parsing",
    "Special Theme (conference specific)"
]

iso_639_3_languages = ["Ghotuo", "Alumu-Tesu", "Ari", "Amal", "Arbëreshë Albanian", "Aranadan", "Ambrak", "Abu' Arapesh", "Arifama-Miniafia", "Ankave", "Afade", "Anambé", "Algerian Saharan Arabic", "Pará Arára", "Eastern Abnaki", "Afar", "Aasáx", "Arvanitika Albanian", "Abau", "Solong", "Mandobo Atas", "Amarasi", "Abé", "Bankon", "Ambala Ayta", "Manide", "Western Abnaki", "Abai Sungai", "Abaga", "Tajiki Arabic", "Abidji", "Aka-Bea", "Abkhazian", "Lampung Nyo", "Abanyom", "Abua", "Abon", "Abellen Ayta", "Abaza", "Abron", "Ambonese Malay", "Ambulas", "Abure", "Baharna Arabic", "Pal", "Inabaknon", "Aneme Wake", "Abui", "Achagua", "Áncá", "Gikyode", "Achinese", "Saint Lucian Creole French", "Acoli", "Aka-Cari", "Aka-Kora", "Akar-Bale", "Mesopotamian Arabic", "Achang", "Eastern Acipa", "Ta'izzi-Adeni Arabic", "Achi", "Acroá", "Achterhoeks", "Achuar-Shiwiar", "Achumawi", "Hijazi Arabic", "Omani Arabic", "Cypriot Arabic", "Acheron", "Adangme", "Atauran", "Dzodinka", "Lidzonka", "Adele", "Dhofari Arabic", "Andegerebinha", "Adhola", "Adi", "Adioukrou", "Galo", "Adang", "Abu", "Adangbe", "Adonara", "Adamorobe Sign Language", "Adnyamathanha", "Aduge", "Amundava", "Amdo Tibetan", "Adygei", "Adyghe", "Adzera", "Areba", "Tunisian Arabic", "Saidi Arabic", "Argentine Sign Language", "Northeast Pashai", "Northeast Pashayi", "Haeke", "Ambele", "Arem", "Armenian Sign Language", "Aer", "Eastern Arrernte", "Alsea", "Akeu", "Ambakich", "Amele", "Aeka", "Gulf Arabic", "Andai", "Putukwam", "Afghan Sign Language", "Afrihili", "Akrukay", "Chini", "Nanubae", "Defaka", "Eloyi", "Tapei", "Afrikaans", "Afro-Seminole Creole", "Afitti", "Awutu", "Obokuitai", "Aguano", "Legbo", "Agatu", "Agarabi", "Angal", "Arguni", "Angor", "Ngelima", "Agariya", "Argobba", "Isarog Agta", "Fembe", "Angaataha", "Agutaynen", "Tainae", "Aghem", "Aguaruna", "Esimbi", "Central Cagayan Agta", "Aguacateco", "Remontado Dumagat", "Kahua", "Aghul", "Southern Alta", "Mt. Iriga Agta", "Ahanta", "Axamb", "Qimant", "Aghu", "Tiagbamrin Aizi", "Akha", "Igo", "Mobumrin Aizi", "Àhàn", "Ahom", "Aproumu Aizi", "Ahirani", "Ashe", "Ahtena", "Arosi", "Ainu (China)", "Ainbai", "Alngith", "Amara", "Agi", "Antigua and Barbuda Creole English", "Ai-Cham", "Assyrian Neo-Aramaic", "Lishanid Noshan", "Ake", "Aimele", "Aimol", "Ainu (Japan)", "Aiton", "Burumakok", "Aimaq", "Airoran", "Arikem", "Aari", "Aighon", "Ali", "Aja (South Sudan)", "Aja (Benin)", "Ajië", "Andajin", "Algerian Jewish Sign Language", "Judeo-Moroccan Arabic", "Ajawa", "Amri Karbi", "Akan", "Batak Angkola", "Mpur", "Ukpet-Ehom", "Akawaio", "Akpa", "Anakalangu", "Angal Heneng", "Aiome", "Aka-Jeru", "Akkadian", "Aklanon", "Aka-Bo", "Akurio", "Siwu", "Ak", "Araki", "Akaselem", "Akolet", "Akum", "Akhvakh", "Akwa", "Aka-Kede", "Aka-Kol", "Alabama", "Alago", "Qawasqar", "Alladian", "Aleut", "Alege", "Alawa", "Amaimon", "Alangan", "Alak", "Allar", "Amblong", "Gheg Albanian", "Larike-Wakasihu", "Alune", "Algonquin", "Alutor", "Tosk Albanian", "Southern Altai", "'Are'are", "Alaba-K’abeena", "Wanbasana", "Amol", "Alyawarr", "Alur", "Amanayé", "Ambo", "Amahuaca", "Yanesha'", "Hamer-Banna", "Amurdak", "Amharic", "Amis", "Amdang", "Ambai", "War-Jaintia", "Ama (Papua New Guinea)", "Amanab", "Amo", "Alamblak", "Amahai", "Amarakaeri", "Southern Amami-Oshima", "Amto", "Guerrero Amuzgo", "Ambelau", "Western Neo-Aramaic", "Anmatyerre", "Ami", "Atampaya", "Andaqui", "Andoa", "Ngas", "Ansus", "Xârâcùù", "Animere", "Old English (ca. 450-1100)", "Nend", "Andi", "Anor", "Goemai", "Anu-Hkongso Chin", "Anal", "Obolo", "Andoque", "Angika", "Jarawa (India)", "Andh", "Anserma", "Antakarinya", "Antikarinya", "Anuak", "Denya", "Anaang", "Andra-Hus", "Anyin", "Anem", "Angolar", "Abom", "Pemon", "Andarum", "Angal Enen", "Bragat", "Angoram", "Anindilyakwa", "Mufian", "Arhö", "Alor", "Ömie", "Bumbita Arapesh", "Aore", "Taikat", "A'tong", "Atong (India)", "A'ou", "Atorada", "Uab Meto", "Sa'a", "Levantine Arabic", "Sudanese Arabic", "Bukiyip", "Pahanan Agta", "Ampanang", "Athpariya", "Apiaká", "Jicarilla Apache", "Kiowa Apache", "Lipan Apache", "Mescalero-Chiricahua Apache", "Apinayé", "Ambul", "Apma", "A-Pucikwar", "Arop-Lokep", "Arop-Sissano", "Apatani", "Apurinã", "Alapmunte", "Western Apache", "Aputai", "Apalaí", "Safeyoka", "Archi", "Ampari Dogon", "Arigidi", "Aninka", "Atohwaim", "Northern Alta", "Atakapa", "Arhâ", "Angaité", "Akuntsu", "Arabic", "Standard Arabic", "Imperial Aramaic (700-300 BCE)", "Official Aramaic (700-300 BCE)", "Arabana", "Western Arrarnta", "Aragonese", "Arhuaco", "Arikara", "Arapaso", "Arikapú", "Arabela", "Mapuche", "Mapudungun", "Araona", "Arapaho", "Algerian Arabic", "Karo (Brazil)", "Najdi Arabic", "Arawá", "Aruá (Amazonas State)", "Arbore", "Arawak", "Aruá (Rodonia State)", "Moroccan Arabic", "Egyptian Arabic", "Asu (Tanzania)", "Assiniboine", "Nakoda Assiniboine", "Casuarina Coast Asmat", "American Sign Language", "Auslan", "Australian Sign Language", "Cishingini", "Abishira", "Buruwai", "Sari", "Ashkun", "Asilulu", "Assamese", "Xingú Asuriní", "Dano", "Algerian Sign Language", "Austrian Sign Language", "Asuri", "Ipulo", "Asturian", "Asturleonese", "Bable", "Leonese", "Tocantins Asurini", "Asoa", "Australian Aborigines Sign Language", "Muratayak", "Yaosakor Asmat", "As", "Pele-Ata", "Zaiwa", "Atsahuaca", "Ata Manobo", "Atemble", "Ivbie North-Okpela-Arhe", "Attié", "Atikamekw", "Nehirowimowin", "Ati", "Mt. Iraya Agta", "Ata", "Ashtiani", "Atong (Cameroon)", "Pudtol Atta", "Aralle-Tabulahan", "Waimiri-Atroari", "Gros Ventre", "Pamplona Atta", "Reel", "Northern Altai", "Atsugewi", "Arutani", "Aneityum", "Arta", "Asumboa", "Alugu", "Waorani", "Anuta", "Aguna", "Aushi", "Anuki", "Awjilah", "Heyo", "Aulua", "Asu (Nigeria)", "Molmo One", "Auyokawa", "Makayam", "Anus", "Korur", "Aruek", "Austral", "Auye", "Awyi", "Aurá", "Awiyaana", "Uzbeki Arabic", "Avaric", "Avau", "Alviri-Vidari", "Avestan", "Avikam", "Kotava", "Eastern Egyptian Bedawi Arabic", "Angkamuthi", "Avatime", "Agavotaguerra", "Aushiri", "Au", "Avokaya", "Avá-Canoeiro", "Awadhi", "Awa (Papua New Guinea)", "Cicipu", "Awetí", "Anguthimri", "Awbono", "Aekyom", "Awabakal", "Arawum", "Awngi", "Awak", "Awera", "South Awyu", "Araweté", "Central Awyu", "Jair Awyu", "Awun", "Awara", "Edera Awyu", "Abipon", "Ayerrerenge", "Mato Grosso Arára", "Yaka (Central African Republic)", "Lower Southern Aranda", "Middle Armenian", "Xârâgurè", "Awar", "Ayizo Gbe", "Southern Aymara", "Ayabadhu", "Ayere", "Ginyanga", "Hadrami Arabic", "Leyigha", "Akuku", "Libyan Arabic", "Aymara", "Sanaani Arabic", "Ayoreo", "North Mesopotamian Arabic", "Ayi (Papua New Guinea)", "Central Aymara", "Sorsogon Ayta", "Magbukun Ayta", "Ayu", "Mai Brat", "Azha", "South Azerbaijani", "Eastern Durango Nahuatl", "Azerbaijani", "San Pedro Amuzgos Amuzgo", "North Azerbaijani", "Ipalapa Amuzgo", "Western Durango Nahuatl", "Awing", "Faire Atta", "Highland Puebla Nahuatl", "Babatana", "Bainouk-Gunyuño", "Badui", "Baré", "Nubaca", "Tuki", "Bahamas Creole English", "Barakai", "Bashkir", "Baluchi", "Bambara", "Balinese", "Waimaha", "Bantawa", "Bavarian", "Basa (Cameroon)", "Bada (Nigeria)", "Vengo", "Bambili-Bambui", "Bamun", "Batuley", "Baatonum", "Barai", "Batak Toba", "Bau", "Bangba", "Baibai", "Barama", "Bugan", "Barombi", "Ghomálá'", "Babanki", "Bats", "Babango", "Uneapa", "Konabéré", "Northern Bobo Madaré", "West Central Banda", "Bamali", "Girawa", "Bakpinka", "Mburku", "Kulung (Nigeria)", "Karnai", "Baba", "Bubia", "Befang", "Central Bai", "Bainouk-Samik", "Southern Balochi", "North Babar", "Bamenyam", "Bamu", "Baga Pokur", "Bariai", "Baoulé", "Bardi", "Bunuba", "Central Bikol", "Bannoni", "Bali (Nigeria)", "Kaluli", "Bali (Democratic Republic of Congo)", "Bench", "Babine", "Kohumono", "Bendi", "Awad Bing", "Shoo-Minda-Nye", "Bana", "Bacama", "Bainouk-Gunyaamolo", "Bayot", "Basap", "Emberá-Baudó", "Bunama", "Bade", "Biage", "Bonggi", "Baka (South Sudan)", "Burun", "Bai", "Bai (South Sudan)", "Budukh", "Indonesian Bajau", "Buduma", "Baldemu", "Morom", "Bende", "Bahnar", "West Coast Bajau", "Burunge", "Bokoto", "Oroko", "Bodo Parja", "Baham", "Budong-Budong", "Bandjalang", "Badeshi", "Beaver", "Bebele", "Iceve-Maci", "Bedoanas", "Byangsi", "Benabena", "Belait", "Biali", "Bekati'", "Bedawiyet", "Beja", "Bebeli", "Belarusian", "Bemba (Zambia)", "Bengali", "Beami", "Besoa", "Beembe", "Besme", "Guiberoua Béte", "Blagar", "Daloa Bété", "Betawi", "Jur Modo", "Beli (Papua New Guinea)", "Bena (Tanzania)", "Bari", "Pauri Bareli", "Northern Bai", "Panyi Bai", "Bafut", "Betaf", "Tena", "Bofi", "Busang Kayan", "Blafe", "British Sign Language", "Bafanji", "Ban Khor Sign Language", "Banda-Ndélé", "Mmen", "Bunak", "Malba Birifor", "Beba", "Badaga", "Bazigar", "Southern Bai", "Balti", "Gahri", "Bondo", "Bantayanon", "Bagheli", "Mahasu Pahari", "Gwamhi-Wuri", "Bobongko", "Haryanvi", "Rathwi Bareli", "Bauria", "Bangandu", "Bugun", "Giangan", "Bangolan", "Bit", "Buxinhua", "Bo (Laos)", "Western Balochi", "Baga Koga", "Eastern Balochi", "Bagri", "Bawm Chin", "Tagabawa", "Bughotu", "Mbongno", "Warkay-Bipim", "Bhatri", "Balkan Gagauz Turkish", "Benggoi", "Banggai", "Bharia", "Bhili", "Biga", "Bhadrawahi", "Bhaya", "Odiai", "Binandere", "Bukharic", "Bhilali", "Bahing", "Bimin", "Bathari", "Bohtan Neo-Aramaic", "Bhojpuri", "Bima", "Tukang Besi South", "Bara Malagasy", "Buwal", "Bhattiyali", "Bhunjia", "Bahau", "Biak", "Bhalay", "Bhele", "Bada (Indonesia)", "Badimaya", "Bisa", "Bissa", "Bidiyo", "Bepour", "Biafada", "Biangai", "Bikol", "Bile", "Bimoba", "Bini", "Edo", "Nai", "Bila", "Bipi", "Bisorio", "Bislama", "Berinomo", "Biete", "Southern Birifor", "Kol (Cameroon)", "Bijori", "Birhor", "Baloi", "Budza", "Banggarla", "Bariji", "Biao-Jiao Mien", "Barzani Jewish Neo-Aramaic", "Bidyogo", "Bahinemo", "Burji", "Kanauji", "Barok", "Bulu (Papua New Guinea)", "Bajelani", "Banjar", "Mid-Southern Banda", "Fanamaket", "Binumarien", "Bajan", "Balanta-Ganja", "Busuu", "Bedjond", "Bakwé", "Banao Itneg", "Bayali", "Baruga", "Kyak", "Baka (Cameroon)", "Binukid", "Talaandig", "Beeke", "Buraka", "Bakoko", "Baki", "Pande", "Brokskat", "Berik", "Kom (Cameroon)", "Bukitan", "Kwa'", "Boko (Democratic Republic of Congo)", "Bakairí", "Bakumpai", "Northern Sorsoganon", "Boloki", "Buhid", "Bekwarra", "Bekwel", "Baikeno", "Bokyi", "Bungku", "Siksika", "Bilua", "Bella Coola", "Bolango", "Balanta-Kentohe", "Buol", "Kuwaa", "Bolia", "Bolongan", "Pa'O", "Pa'o Karen", "Biloxi", "Beli (South Sudan)", "Southern Catanduanes Bikol", "Anii", "Blablanga", "Baluan-Pam", "Blang", "Balaesang", "Tai Dam", "Bolo", "Kibala", "Balangao", "Mag-Indi Ayta", "Notre", "Balantak", "Lame", "Bembe", "Biem", "Baga Manduri", "Limassa", "Bom-Kim", "Bamwe", "Kein", "Bagirmi", "Bote-Majhi", "Ghayavi", "Bomboli", "Northern Betsimisaraka Malagasy", "Bina (Papua New Guinea)", "Bambalang", "Bulgebi", "Bomu", "Muinane", "Bilma Kanuri", "Biao Mon", "Somba-Siawari", "Bum", "Bomwali", "Baimak", "Baramu", "Bonerate", "Bookan", "Bontok", "Banda (Indonesia)", "Bintauna", "Masiwang", "Benga", "Bangi", "Eastern Tawbuid", "Bierebo", "Boon", "Batanga", "Bunun", "Bantoanon", "Bola", "Bantik", "Butmas-Tur", "Bundeli", "Bentong", "Beneraf", "Bonerif", "Edwas", "Bisis", "Bangubangu", "Bintulu", "Beezen", "Bora", "Aweer", "Tibetan", "Mundabli-Mufu", "Bolon", "Bamako Sign Language", "Boma", "Barbareño", "Anjam", "Bonjo", "Bole", "Berom", "Bine", "Tiemacèwè Bozo", "Bonkiman", "Bogaya", "Borôro", "Bosnian", "Bongo", "Bondei", "Tuwuli", "Rema", "Buamu", "Bodo (Central African Republic)", "Tiéyaxo Bozo", "Daakaka", "Mbuk", "Banda-Banda", "Bauni", "Bonggo", "Botlikh", "Bagupi", "Binji", "'Ôrôê", "Orowe", "Broome Pearling Lugger Pidgin", "Biyom", "Dzao Min", "Anasi", "Kaure", "Banda Malay", "Koronadal Blaan", "Sarangani Blaan", "Barrow Point", "Bongu", "Bian Marind", "Bo (Papua New Guinea)", "Palya Bareli", "Bishnupriya", "Bilba", "Tchumbuli", "Bagusa", "Boko (Benin)", "Boo", "Bung", "Baga Kaloum", "Bago-Kusuntu", "Baima", "Bakhtiari", "Bandial", "Banda-Mbrès", "Bilakura", "Karian", "Wumboko", "Bulgarian Sign Language", "Balo", "Busa", "Biritai", "Burusu", "Bosngun", "Bamukumbit", "Boguru", "Begbere-Ejar", "Koro Wachi", "Buru (Nigeria)", "Baangi", "Bengkala Sign Language", "Bakaka", "Braj", "Brao", "Lave", "Berbice Creole Dutch", "Baraamu", "Breton", "Bira", "Baure", "Brahui", "Mokpwe", "Bieria", "Birked", "Birwa", "Barambu", "Boruca", "Brokkat", "Barapasi", "Breri", "Birao", "Baras", "Bitare", "Eastern Bru", "Western Bru", "Bellari", "Bodo (India)", "Burui", "Bilbil", "Abinomn", "Brunei Bisaya", "Bassari", "Oniyan", "Wushi", "Bauchi", "Bashkardi", "Kati", "Bassossi", "Bangwinji", "Burushaski", "Basa-Gumna", "Busami", "Barasana-Eduria", "Buso", "Baga Sitemu", "Bassa", "Bassa-Kontagora", "Akoose", "Basketo", "Bahonsuai", "Baga Sobané", "Baiso", "Yangkam", "Sabah Bisaya", "Bata", "Bati (Cameroon)", "Batak Dairi", "Gamo-Ningi", "Birgit", "Gagnoa Bété", "Biatah Bidayuh", "Burate", "Bacanese Malay", "Batak Mandailing", "Ratagnon", "Rinconada Bikol", "Budibud", "Batek", "Baetora", "Batak Simalungun", "Bete-Bendi", "Batu", "Bateri", "Butuanon", "Batak Karo", "Bobot", "Batak Alas-Kluet", "Buriat", "Bua", "Bushi", "Ntcham", "Beothuk", "Bushoong", "Buginese", "Younuo Bunu", "Bongili", "Basa-Gurmana", "Bugawac", "Bulgarian", "Bulu (Cameroon)", "Sherbro", "Terei", "Busoa", "Brem", "Bokobaru", "Bungain", "Budu", "Bun", "Bubi", "Boghom", "Bullom So", "Bukwen", "Barein", "Bube", "Baelelea", "Baeggu", "Berau Malay", "Boor", "Bonkeng", "Bure", "Belanda Viri", "Baan", "Bukat", "Bolivian Sign Language", "Bamunka", "Buna", "Bolgo", "Bumang", "Birri", "Burarra", "Bati (Indonesia)", "Bukit Malay", "Baniva", "Boga", "Dibole", "Baybayanon", "Bauzi", "Bwatoo", "Namosi-Naitasiri-Serua", "Bwile", "Bwaidoka", "Bwe Karen", "Boselewa", "Barwe", "Bishuo", "Baniwa", "Láá Láá Bwamu", "Bauwaki", "Bwela", "Biwat", "Wunai Bunu", "Borna (Ethiopia)", "Boro (Ethiopia)", "Mandobo Bawah", "Southern Bobo Madaré", "Bura-Pabir", "Bomboma", "Bafaw-Balong", "Buli (Ghana)", "Bwa", "Bu-Nao Bunu", "Cwi Bwamu", "Bwisi", "Tairaha", "Belanda Bor", "Molengue", "Pela", "Birale", "Bilur", "Minigir", "Bangala", "Buhutu", "Pirlatapa", "Bayungu", "Bukusu", "Lubukusu", "Jalkunan", "Mongolia Buriat", "Burduna", "Barikanchi", "Bebil", "Beele", "Russia Buriat", "Busam", "China Buriat", "Berakou", "Bankagooma", "Binahari", "Batak", "Bikya", "Ubaghara", "Benyadu'", "Pouye", "Bete", "Baygo", "Bhujel", "Buyu", "Bina (Nigeria)", "Biao", "Bayono", "Bidjara", "Bilin", "Blin", "Biyo", "Bumaji", "Basay", "Baruya", "Yipma", "Burak", "Berti", "Medumba", "Belhariya", "Qaqet", "Banaro", "Bandi", "Andio", "Southern Betsimisaraka Malagasy", "Bribri", "Jenaama Bozo", "Boikin", "Babuza", "Mapos Buang", "Bisu", "Belize Kriol English", "Nicaragua Creole English", "Boano (Sulawesi)", "Bolondo", "Boano (Maluku)", "Bozaba", "Kemberano", "Buli (Indonesia)", "Biri", "Brazilian Sign Language", "Brithenig", "Burmeso", "Naami", "Basa (Nigeria)", "Kɛlɛngaxo Bozo", "Obanliku", "Evant", "Chortí", "Garifuna", "Chuj", "Caddo", "Laalaa", "Lehar", "Southern Carrier", "Nivaclé", "Cahuarano", "Chané", "Cakchiquel", "Kaqchikel", "Carolinian", "Cemuhî", "Chambri", "Chácobo", "Chipaya", "Car Nicobarese", "Galibi Carib", "Tsimané", "Catalan", "Valencian", "Cavineña", "Callawalla", "Chiquitano", "Cayuga", "Canichana", "Cabiyarí", "Carapana", "Carijona", "Chimila", "Chachi", "Ede Cabe", "Chavacano", "Bualkhaw Chin", "Nyahkur", "Izora", "Cuba", "Tsucuba", "Cashibo-Cacataibo", "Cashinahua", "Chayahuita", "Candoshi-Shapra", "Cacua", "Kinabalian", "Carabayo", "Chamicuro", "Cafundo Creole", "Chopi", "Samba Daka", "Atsam", "Kasanga", "Cutchi-Swahili", "Malaccan Creole Malay", "Comaltepec Chinantec", "Chakma", "Cacaopera", "Choni", "Chenchu", "Chiru", "Chambeali", "Chodri", "Churahi", "Chepang", "Chaudangsi", "Min Dong Chinese", "Cinda-Regi-Tiyal", "Chadian Sign Language", "Chadong", "Koda", "Lower Chehalis", "Cebuano", "Chamacoco", "Eastern Khumi Chin", "Cen", "Czech", "Centúúm", "Ekai Chin", "Dijim-Bwilim", "Cara", "Como Karim", "Falam Chin", "Changriwa", "Kagayanen", "Chiga", "Chocangacakha", "Chamorro", "Chibcha", "Catawba", "Highland Oaxaca Chontal", "Chechen", "Tabasco Chontal", "Chagatai", "Chinook", "Ojitlán Chinantec", "Chuukese", "Cahuilla", "Mari (Russia)", "Chinook jargon", "Choctaw", "Chipewyan", "Dene Suline", "Quiotepec Chinantec", "Cherokee", "Cholón", "Church Slavic", "Church Slavonic", "Old Bulgarian", "Old Church Slavonic", "Old Slavonic", "Chuvash", "Chuwabu", "Chantyal", "Cheyenne", "Ozumacín Chinantec", "Cia-Cia", "Ci Gbe", "Chickasaw", "Chimariko", "Cineni", "Chinali", "Chitkuli Kinnauri", "Cimbrian", "Cinta Larga", "Chiapanec", "Haméa", "Méa", "Tiri", "Chippewa", "Chaima", "Western Cham", "Chru", "Upper Chehalis", "Chamalal", "Chokwe", "Eastern Cham", "Chenapian", "Ashéninka Pajonal", "Cabécar", "Shor", "Chuave", "Jinyu Chinese", "Central Kurdish", "Chak", "Cibak", "Chakavian", "Kaang Chin", "Anufo", "Kajakse", "Kairak", "Tayo", "Chukot", "Koasati", "Kavalan", "Caka", "Cakfem-Mushere", "Cakchiquel-Quiché Mixed Language", "Ron", "Chilcotin", "Tsilhqot’in", "Chaldean Neo-Aramaic", "Lealao Chinantec", "Chilisso", "Chakali", "Laitu Chin", "Idu-Mishmi", "Chala", "Clallam", "Klallam", "Lowland Oaxaca Chontal", "Classical Sanskrit", "Lautu Chin", "Caluyanun", "Chulym", "Eastern Highland Chatino", "Maa", "Cerma", "Classical Mongolian", "Emberá-Chamí", "Campalagian", "Michigamea", "Mandarin Chinese", "Central Mnong", "Mro-Khimi Chin", "Messapic", "Camtho", "Changthang", "Chinbon Chin", "Côông", "Northern Qiang", "Haka Chin", "Hakha Chin", "Asháninka", "Khumi Chin", "Lalana Chinantec", "Con", "Northern Ping Chinese", "Northern Pinghua", "Chung", "Montenegrin", "Central Asmat", "Tepetotutla Chinantec", "Chenoua", "Ngawn Chin", "Middle Cornish", "Cocos Islands Malay", "Chicomuceltec", "Cocopa", "Cocama-Cocamilla", "Koreguaje", "Colorado", "Chong", "Chichonyi-Chidzihana-Chikauma", "Chonyi-Dzihana-Kauma", "Cochimi", "Santa Teresa Cora", "Columbia-Wenatchi", "Comanche", "Cofán", "Comox", "Coptic", "Coquille", "Cornish", "Corsican", "Caquinte", "Wamey", "Cao Miao", "Cowlitz", "Nanti", "Chochotec", "Palantla Chinantec", "Ucayali-Yurúa Ashéninka", "Ajyíninka Apurucayali", "Cappadocian Greek", "Chinese Pidgin English", "Cherepon", "Kpeego", "Capiznon", "Pichis Ashéninka", "Pu-Xian Chinese", "South Ucayali Ashéninka", "Chuanqiandian Cluster Miao", "Chara", "Island Carib", "Lonwolwol", "Coeur d'Alene", "Cree", "Caramanta", "Michif", "Crimean Tatar", "Crimean Turkish", "Sãotomense", "Southern East Cree", "Plains Cree", "Northern East Cree", "Moose Cree", "El Nayar Cora", "Crow", "Iyo'wujwa Chorote", "Carolina Algonquian", "Seselwa Creole French", "Iyojwa'ja Chorote", "Chaura", "Chrau", "Carrier", "Cori", "Cruzeño", "Chiltepec Chinantec", "Kashubian", "Catalan Sign Language", "Lengua de señas catalana", "Llengua de Signes Catalana", "Chiangmai Sign Language", "Czech Sign Language", "Cuba Sign Language", "Chilean Sign Language", "Asho Chin", "Coast Miwok", "Songlai Chin", "Jola-Kasa", "Chinese Sign Language", "Central Sierra Miwok", "Colombian Sign Language", "Sochiapam Chinantec", "Sochiapan Chinantec", "Southern Ping Chinese", "Southern Pinghua", "Croatia Sign Language", "Costa Rican Sign Language", "Southern Ohlone", "Northern Ohlone", "Sumtu Chin", "Swampy Cree", "Cambodian Sign Language", "Siyin Chin", "Coos", "Tataltepec Chatino", "Chetco", "Tedim Chin", "Tepinapa Chinantec", "Chittagonian", "Thaiphum Chin", "Tlacoatzintepec Chinantec", "Chitimacha", "Chhintange", "Emberá-Catío", "Western Highland Chatino", "Northern Catanduanes Bikol", "Wayanad Chetti", "Chol", "Moundadan Chetty", "Zacatepec Chatino", "Cua", "Cubeo", "Usila Chinantec", "Chuka", "Gichuka", "Cuiba", "Mashco Piro", "San Blas Kuna", "Culina", "Kulina", "Cumanagoto", "Cupeño", "Cun", "Chhulung", "Teutila Cuicatec", "Tai Ya", "Cuvok", "Chukwa", "Tepeuxila Cuicatec", "Cuitlatec", "Chug", "Valle Nacional Chinantec", "Kabwa", "Maindo", "Woods Cree", "Kwere", "Cheq Wong", "Chewong", "Kuwaataay", "Cha'ari", "Nopala Chatino", "Cayubaba", "Welsh", "Cuyonon", "Huizhou Chinese", "Knaanic", "Zenzontepec Chatino", "Min Zhong Chinese", "Zotung Chin", "Dangaléat", "Dambi", "Marik", "Duupa", "Dagbani", "Gwahatike", "Day", "Dar Fur Daju", "Dakota", "Dahalo", "Damakawa", "Danish", "Daai Chin", "Dandami Maria", "Dargwa", "Daho-Doo", "Dar Sila Daju", "Dawida", "Taita", "Davawenyo", "Dayi", "Dao", "Moi-Wadea", "Bangime", "Deno", "Dadiya", "Dabe", "Edopi", "Dogul Dom Dogon", "Doka", "Ida'an", "Dyirbal", "Duguri", "Duriankere", "Dulbu", "Duwai", "Daba", "Dabarre", "Ben Tey Dogon", "Bondum Dom Dogon", "Dungu", "Bankan Tey Dogon", "Dibiyaso", "Deccan", "Negerhollands", "Dadi Dadi", "Dongotono", "Doondo", "Fataluku", "West Goodenough", "Jaru", "Dendi (Benin)", "Dido", "Dhudhuroa", "Donno So Dogon", "Dawera-Daweloor", "Dagik", "Dedua", "Dewoin", "Dezfuli", "Degema", "Dehwari", "Demisa", "Delaware", "Dem", "Slavey", "Pidgin Delaware", "Dendi (Central African Republic)", "Deori", "Desano", "German", "Domung", "Dengese", "Southern Dagaare", "Bunoge Dogon", "Casiguran Dumagat Agta", "Dagaari Dioula", "Degenan", "Doga", "Dghwede", "Northern Dagara", "Dagba", "Andaandi", "Dongolawi", "Dagoman", "Dogri (individual language)", "Dogrib", "Tlicho", "Dogoso", "Ndra'ngith", "Daungwurrung", "Doghoro", "Daga", "Dhundari", "Dhangu", "Dhangu-Djangu", "Djangu", "Dhimal", "Dhalandji", "Zemba", "Dhanki", "Dhodia", "Dhargari", "Dhaiso", "Dhurga", "Dehu", "Drehu", "Dhanwar (Nepal)", "Dhungaloo", "Dia", "South Central Dinka", "Lakota Dida", "Didinga", "Dieri", "Diyari", "Chidigo", "Digo", "Kumiai", "Dimbong", "Dai", "Southwestern Dinka", "Dilling", "Dime", "Dinka", "Dibo", "Northeastern Dinka", "Dimli (individual language)", "Dirim", "Dimasa", "Diriku", "Dhivehi", "Divehi", "Maldivian", "Northwestern Dinka", "Dixon Reef", "Diuwe", "Ding", "Djadjawurrung", "Djinba", "Dar Daju Daju", "Djamindjung", "Ngaliwurru", "Zarma", "Djangun", "Djinang", "Djeebbana", "Businenge Tongo", "Eastern Maroon Creole", "Nenge", "Jamsay Dogon", "Djauan", "Jawoyn", "Jangkang", "Djambarrpuyngu", "Kapriman", "Djawi", "Dakpakha", "Kadung", "Dakka", "Kuijau", "Southeastern Dinka", "Mazagway", "Dolgan", "Dahalik", "Dalmatian", "Darlong", "Duma", "Mombo Dogon", "Gavak", "Madhi Madhi", "Dugwor", "Medefaidrin", "Upper Kinabatangan", "Domaaki", "Dameli", "Dama", "Kemedzung", "East Damar", "Dampelas", "Dubu", "Tebi", "Dumpas", "Mudburra", "Dema", "Demta", "Sowari", "Upper Grand Valley Dani", "Daonda", "Ndendeule", "Dungan", "Lower Grand Valley Dani", "Dan", "Dengka", "Dzùùngoo", "Ndrulo", "Northern Lendu", "Danaru", "Mid Grand Valley Dani", "Danau", "Danu", "Western Dani", "Dení", "Dom", "Dobu", "Northern Dong", "Doe", "Domu", "Dong", "Dogri (macrolanguage)", "Dondo", "Doso", "Toura (Papua New Guinea)", "Dongo", "Lukpa", "Dominican Sign Language", "Dori'o", "Dogosé", "Dass", "Dombe", "Doyayo", "Bussa", "Dompo", "Dorze", "Papar", "Dair", "Minderico", "Darmiya", "Dolpo", "Rungus", "C'Lela", "Paakantyi", "West Damar", "Daro-Matu Melanau", "Dura", "Gedeo", "Drents", "Rukai", "Darai", "Lower Sorbian", "Dutch Sign Language", "Daasanach", "Disa", "Dokshi", "Danish Sign Language", "Dusner", "Desiya", "Tadaksahak", "Mardin Sign Language", "Daur", "Labuk-Kinabatangan Kadazan", "Ditidaht", "Adithinngithigh", "Ana Tinga Dogon", "Tene Kan Dogon", "Tomo Kan Dogon", "Daatsʼíin", "Tommo So Dogon", "Central Dusun", "Kadazan Dusun", "Lotud", "Toro So Dogon", "Toro Tegu Dogon", "Tebul Ure Dogon", "Dotyali", "Duala", "Dubli", "Duna", "Umiray Dumaget Agta", "Drubea", "Dumbea", "Chiduruma", "Duruma", "Dungra Bhil", "Dumun", "Uyajitaya", "Alabat Island Agta", "Middle Dutch (ca. 1050-1350)", "Dusun Deyah", "Dupaninan Agta", "Duano", "Dusun Malang", "Dii", "Dumi", "Drung", "Duvle", "Dusun Witu", "Duungooma", "Dicamay Agta", "Duli-Gey", "Duau", "Diri", "Dawik Kui", "Dawro", "Dutton World Speedwords", "Dhuwal", "Dawawa", "Dhuwaya", "Dewas Rai", "Dyan", "Dyaberdyaber", "Dyugun", "Villa Viciosa Agta", "Djimini Senoufo", "Bhutanese Sign Language", "Yanda Dom Dogon", "Dhanggatti", "Dyangadi", "Jola-Fonyi", "Dyarim", "Dyula", "Djabugay", "Dyaabugay", "Tunzu", "Daza", "Djiwarli", "Dazaga", "Dzalakha", "Dzando", "Dzongkha", "Karenggapa", "Beginci", "Ebughu", "Eastern Bontok", "Teke-Ebo", "Ebrié", "Embu", "Kiembu", "Eteocretan", "Ecuadorian Sign Language", "Eteocypriot", "E", "Efai", "Efe", "Efik", "Ega", "Emilian", "Benamanga", "Eggon", "Egyptian (Ancient)", "Miyakubo Sign Language", "Ehueun", "Eipomek", "Eitiep", "Askopan", "Ejamat", "Ekajuk", "Ekit", "Ekari", "Eki", "Standard Estonian", "Kol", "Kol (Bangladesh)", "Elip", "Koti", "Ekpeye", "Yace", "Eastern Kayah", "Elepi", "El Hugeirat", "Nding", "Elkei", "Modern Greek (1453-)", "Eleme", "El Molo", "Elu", "Elamite", "Emai-Iuleha-Ora", "Embaloh", "Emerillon", "Eastern Meohang", "Mussau-Emira", "Eastern Maninkakan", "Mamulique", "Eman", "Northern Emberá", "Eastern Minyag", "Pacific Gulf Yupik", "Eastern Muria", "Emplawas", "Erromintxela", "Epigraphic Mayan", "Mbessa", "Apali", "Markweeta", "En", "Ende", "Forest Enets", "English", "Tundra Enets", "Enlhet", "Middle English (1100-1500)", "Engenni", "Enggano", "Enga", "Emem", "Emumu", "Enu", "Enwan (Edo State)", "Enwan (Akwa Ibom State)", "Enxet", "Beti (Côte d'Ivoire)", "Epie", "Esperanto", "Eravallan", "Sie", "Eruwa", "Ogea", "South Efate", "Horpa", "Erre", "Ersu", "Eritai", "Erokwanas", "Ese Ejja", "Aheri Gondi", "Eshtehardi", "North Alaskan Inupiatun", "Northwest Alaska Inupiatun", "Egypt Sign Language", "Esuma", "Salvadoran Sign Language", "Estonian Sign Language", "Esselen", "Central Siberian Yupik", "Estonian", "Central Yupik", "Eskayan", "Etebi", "Etchemin", "Ethiopian Sign Language", "Eton (Vanuatu)", "Eton (Cameroon)", "Edolo", "Yekhee", "Etruscan", "Ejagham", "Eten", "Semimi", "Eudeve", "Basque", "Even", "Uvbie", "Evenki", "Ewe", "Ewondo", "Extremaduran", "Eyak", "Keiyo", "Ezaa", "Uzekwe", "Fasu", "Fa d'Ambu", "Wagi", "Fagani", "Finongan", "Baissa Fali", "Faiwol", "Faita", "Fang (Cameroon)", "South Fali", "Fam", "Fang (Equatorial Guinea)", "Faroese", "Paloor", "Fataleka", "Persian", "Fanti", "Fayu", "Fala", "Southwestern Fars", "Northwestern Fars", "West Albay Bikol", "Quebec Sign Language", "Feroge", "Foia Foia", "Maasina Fulfulde", "Fongoro", "Nobiin", "Fyer", "Faifi", "Fijian", "Filipino", "Pilipino", "Finnish", "Fipa", "Firan", "Meänkieli", "Tornedalen Finnish", "Fiwaga", "Kirya-Konzəl", "Kven Finnish", "Kalispel-Pend d'Oreille", "Foau", "Fali", "North Fali", "Flinders Island", "Fuliiru", "Flaaitaal", "Tsotsitaal", "Fe'fe'", "Far Western Muria", "Fanbak", "Fanagalo", "Fania", "Foodo", "Foi", "Foma", "Fon", "Fore", "Siraya", "Fernando Po Creole English", "Fas", "French", "Cajun French", "Fordata", "Frankish", "Middle French (ca. 1400-1600)", "Old French (842-ca. 1400)", "Arpitan", "Francoprovençal", "Forak", "Northern Frisian", "Eastern Frisian", "Fortsenal", "Western Frisian", "Finnish Sign Language", "French Sign Language", "finlandssvenskt teckenspråk", "Finland-Swedish Sign Language", "suomenruotsalainen viittomakieli", "Adamawa Fulfulde", "Pulaar", "East Futuna", "Borgu Fulfulde", "Pular", "Western Niger Fulfulde", "Bagirmi Fulfulde", "Ko", "Fulah", "Fum", "Fulniô", "Central-Eastern Niger Fulfulde", "Friulian", "Futuna-Aniwa", "Furu", "Nigerian Fulfulde", "Fuyug", "Fur", "Fwâi", "Fwe", "Ga", "Gabri", "Mixed Great Andamanese", "Gaddang", "Guarequena", "Gende", "Gagauz", "Alekano", "Borei", "Gadsup", "Gamkonora", "Galolen", "Kandawo", "Gan Chinese", "Gants", "Gal", "Gata'", "Galeya", "Adiwasi Garasia", "Kenati", "Mudhili Gadaba", "Nobonob", "Borana-Arsi-Guji Oromo", "Gayo", "West Central Oromo", "Gbaya (Central African Republic)", "Kaytetye", "Karajarri", "Niksek", "Gaikundi", "Gbanziri", "Defi Gbe", "Galela", "Bodo Gadaba", "Gaddi", "Gamit", "Garhwali", "Mo'da", "Northern Grebo", "Gbaya-Bossangoa", "Gbaya-Bozoum", "Gbagyi", "Gbesi Gbe", "Gagadu", "Gbanu", "Gabi-Gabi", "Eastern Xwla Gbe", "Gbari", "Zoroastrian Dari", "Mali", "Ganggalida", "Galice", "Guadeloupean Creole French", "Grenadian Creole English", "Gaina", "Guianese Creole French", "Colonia Tovar German", "Gade Lohar", "Pottangi Ollar Gadaba", "Gugu Badhun", "Gedaged", "Gude", "Guduf-Gava", "Ga'dang", "Gadjerawang", "Gajirrabeng", "Gundi", "Gurdjar", "Gadang", "Dirasha", "Laal", "Umanakaina", "Ghodoberi", "Mehri", "Wipi", "Ghandruk Sign Language", "Kungardutyi", "Gudu", "Godwari", "Geruma", "Kire", "Gboloo Grebo", "Gade", "Gerai", "Gengle", "Hutterisch", "Hutterite German", "Gebe", "Gen", "Ywom", "ut-Ma'in", "Geme", "Geser-Gorom", "Eviya", "Gera", "Garre", "Enya", "Geez", "Patpatar", "Gafat", "Gao", "Gbii", "Gugadj", "Gurr-goni", "Gurgula", "Kungarakany", "Ganglau", "Gitua", "Gagu", "Gban", "Gogodala", "Ghadamès", "Hiberno-Scottish Gaelic", "Southern Ghale", "Northern Ghale", "Geko Karen", "Ghulfan", "Ghanongga", "Ghomara", "Ghera", "Guhu-Samane", "Kuke", "Kutang Ghale", "Kija", "Gibanawa", "Gail", "Gidar", "Gaɓogbo", "Guébie", "Goaria", "Githabul", "Girirra", "Gilbertese", "Gimi (Eastern Highlands)", "Hinukh", "Gimi (West New Britain)", "Green Gelao", "Red Gelao", "North Giziga", "Gitxsan", "Mulao", "White Gelao", "Gilima", "Giyug", "South Giziga", "Kachi Koli", "Gunditjmara", "Gonja", "Gurindji Kriol", "Gujari", "Guya", "Magɨ (Madang Province)", "Ndai", "Gokana", "Kok-Nar", "Guinea Kpelle", "ǂUngkue", "Gaelic", "Scottish Gaelic", "Belning", "Bon Gula", "Nanai", "Irish", "Galician", "Northwest Pashai", "Northwest Pashayi", "Gula Iro", "Gilaki", "Garlali", "Galambu", "Glaro-Twabo", "Gula (Chad)", "Manx", "Glavda", "Gule", "Gambera", "Gula'alaa", "Mághdì", "Magɨyi", "Middle High German (ca. 1050-1500)", "Middle Low German", "Gbaya-Mbodomo", "Gimnime", "Mirning", "Mirniny", "Gumalu", "Gamo", "Magoma", "Mycenaean Greek", "Mgbolizhia", "Kaansa", "Gangte", "Guanche", "Zulgo-Gemzek", "Ganang", "Ngangam", "Lere", "Gooniyandi", "Ngen", "ǁGana", "Gangulu", "Ginuman", "Gumatj", "Northern Gondi", "Gana", "Gureng Gureng", "Guntai", "Gnau", "Western Bolivian Guaraní", "Ganzi", "Guro", "Playero", "Gorakor", "Godié", "Gongduk", "Gofa", "Gogo", "Old High German (ca. 750-1050)", "Gobasi", "Gowlan", "Gowli", "Gola", "Goan Konkani", "Gondi", "Gone Dau", "Yeretuar", "Gorap", "Gorontalo", "Gronings", "Gothic", "Gavar", "Goo", "Gorowa", "Gobu", "Goundo", "Gozarkhani", "Gupa-Abawa", "Ghanaian Pidgin English", "Taiap", "Ga'anda", "Guiqiong", "Guana (Brazil)", "Gor", "Qau", "Rajput Garasia", "Grebo", "Ancient Greek (to 1453)", "Guruntum-Mbaaru", "Madi", "Gbiri-Niragu", "Ghari", "Southern Grebo", "Kota Marudu Talantang", "Guarani", "Groma", "Gorovu", "Taznatit", "Gresi", "Garo", "Kistane", "Central Grebo", "Gweda", "Guriaso", "Barclayville Grebo", "Guramalum", "Ghanaian Sign Language", "German Sign Language", "Gusilay", "Guatemalan Sign Language", "Gusan", "Nema", "Southwest Gbaya", "Wasembo", "Greek Sign Language", "Alemannic", "Alsatian", "Swiss German", "Guató", "Aghu-Tharnggala", "Shiki", "Guajajára", "Wayuu", "Yocoboué Dida", "Gurindji", "Gupapuyngu", "Paraguayan Guaraní", "Guahibo", "Eastern Bolivian Guaraní", "Gujarati", "Gumuz", "Sea Island Creole English", "Guambiano", "Mbyá Guaraní", "Guayabero", "Gunwinggu", "Aché", "Farefare", "Guinean Sign Language", "Maléku Jaíka", "Yanomamö", "Gun", "Gourmanchéma", "Ekegusii", "Gusii", "Guana (Paraguay)", "Guanano", "Duwet", "Golin", "Guajá", "Gulay", "Gurmana", "Kuku-Yalanji", "Gavião Do Jiparaná", "Pará Gavião", "Gurung", "Gumawana", "Guyani", "Mbato", "Gwa", "Gawri", "Kalami", "Gawwada", "Gweno", "Gowro", "Moo", "Gwichʼin", "ǀGwi", "Awngthim", "Gwandara", "Gwere", "Gawar-Bati", "Guwamu", "Kwini", "Gua", "Wè Southern", "Northwest Gbaya", "Garus", "Kayardild", "Gyem", "Gungabula", "Gbayi", "Gyele", "Gayil", "Ngäbere", "Guyanese Creole English", "Gyalsumdo", "Guarayu", "Gunya", "Geji", "Gyaazi", "Ganza", "Gazi", "Gane", "Hän", "Hanoi Sign Language", "Gurani", "Hatam", "Eastern Oromo", "Haiphong Sign Language", "Hanga", "Hahon", "Haida", "Hajong", "Hakka Chinese", "Halang", "Hewa", "Hangaza", "Hakö", "Hupla", "Ha", "Harari", "Haisla", "Haitian", "Haitian Creole", "Hausa", "Havu", "Hawaiian", "Southern Haida", "Haya", "Hazaragi", "Hamba", "Huba", "Heiban", "Ancient Hebrew", "Serbo-Croatian", "Habu", "Andaman Creole Hindi", "Huichol", "Northern Haida", "Honduras Sign Language", "Hadiyya", "Northern Qiandong Miao", "Hebrew", "Herdé", "Helong", "Hehe", "Heiltsuk", "Hemba", "Herero", "Haiǁom", "Haigwai", "Hoia Hoia", "Kerak", "Hoyahoya", "Lamang", "Hibito", "Hidatsa", "Fiji Hindi", "Kamwe", "Pamosu", "Hinduri", "Hijuk", "Seit-Kaitetu", "Hiligaynon", "Hindi", "Tsoa", "Himarimã", "Hittite", "Hiw", "Hixkaryána", "Haji", "Kahe", "Hunde", "Khah", "Poguli", "Hunjara-Kaina Ke", "Mel-Khaonh", "Heung Kong Sau Yue", "Hong Kong Sign Language", "Halia", "Halbi", "Halang Doan", "Hlersu", "Matu Chin", "Hieroglyphic Luwian", "Southern Mashan Hmong", "Southern Mashan Miao", "Humburi Senni Songhay", "Central Huishui Hmong", "Central Huishui Miao", "A-hmaos", "Da-Hua Miao", "Large Flowery Miao", "Eastern Huishui Hmong", "Eastern Huishui Miao", "Hmong Don", "Southwestern Guiyang Hmong", "Southwestern Huishui Hmong", "Southwestern Huishui Miao", "Northern Huishui Hmong", "Northern Huishui Miao", "Ge", "Gejia", "Maek", "Luopohe Hmong", "Luopohe Miao", "Central Mashan Hmong", "Central Mashan Miao", "Hmong", "Mong", "Hiri Motu", "Northern Mashan Hmong", "Northern Mashan Miao", "Eastern Qiandong Miao", "Hmar", "Southern Qiandong Miao", "Hamtai", "Hamap", "Hmong Dô", "Western Mashan Hmong", "Western Mashan Miao", "Southern Guiyang Hmong", "Southern Guiyang Miao", "Hmong Shua", "Sinicized Miao", "Mina (Cameroon)", "Southern Hindko", "Chhattisgarhi", "Hungu", "ǁAni", "Hani", "Hmong Njua", "Mong Leng", "Mong Njua", "Hainanese", "Hanunoo", "Northern Hindko", "Caribbean Hindustani", "Hung", "Hoava", "Mari (Madang Province)", "Ho", "Holma", "Horom", "Hobyót", "Holikachuk", "Hadothi", "Haroti", "Holu", "Homa", "Holoholo", "Hopi", "Horo", "Ho Chi Minh City Sign Language", "Hote", "Malê", "Hovongan", "Honi", "Holiya", "Hozo", "Hpon", "Hawai'i Pidgin Sign Language", "Hawai'i Sign Language (HSL)", "Hrangkhol", "Niwer Mil", "Hre", "Haruku", "Horned Miao", "Haroi", "Nhirrpi", "Hértevin", "Hruso", "Croatian", "Warwar Feni", "Hunsrik", "Harzani", "Upper Sorbian", "Hungarian Sign Language", "Hausa Sign Language", "Xiang Chinese", "Harsusi", "Hoti", "Minica Huitoto", "Hadza", "Hitu", "Middle Hittite", "Huambisa", "ǂ'Amkhoe", "ǂHua", "Huaulu", "San Francisco Del Mar Huave", "Humene", "Huachipaeri", "Huilliche", "Huli", "Northern Guiyang Hmong", "Northern Guiyang Miao", "Hulung", "Hula", "Hungana", "Hungarian", "Hu", "Hupa", "Tsat", "Halkomelem", "Huastec", "Humla", "Murui Huitoto", "San Mateo Del Mar Huave", "Hukumina", "Nüpode Huitoto", "Hulaulá", "Hunzib", "Haitian Vodoun Culture Language", "San Dionisio Del Mar Huave", "Haveke", "Sabu", "Santa María Del Mar Huave", "Wané", "Hawai'i Creole English", "Hawai'i Pidgin", "Hwana", "Hya", "Armenian", "Western Armenian", "Iaai", "Iatmul", "Purari", "Iban", "Ibibio", "Iwaidja", "Akpes", "Ibanag", "Bih", "Ibaloi", "Agoi", "Ibino", "Igbo", "Ibuoro", "Ibu", "Ibani", "Ede Ica", "Etkywan", "Icelandic Sign Language", "Islander Creole English", "Idakho-Isukha-Tiriki", "Luidakho-Luisukha-Lutirichi", "Indo-Portuguese", "Ajiya", "Idon", "Ede Idaca", "Idere", "Idi", "Ido", "Indri", "Idesa", "Idaté", "Idoma", "Amganad Ifugao", "Ayangan Ifugao", "Batad Ifugao", "Ifè", "Ifo", "Tuwali Ifugao", "Teke-Fuumu", "Mayoyao Ifugao", "Keley-I Kallahan", "Ebira", "Igede", "Igana", "Igala", "Kanggape", "Ignaciano", "Isebe", "Interglossa", "Igwe", "Iha Based Pidgin", "Ihievbe", "Iha", "Bidhawal", "Nuosu", "Sichuan Yi", "Thiin", "Izon", "Biseni", "Ede Ije", "Kalabari", "Southeast Ijo", "Eastern Canadian Inuktitut", "Ikhin-Arokho", "Iko", "Ika", "Ikulu", "Olulumo-Ikom", "Ikpeshi", "Ikaranggal", "Inuit Sign Language", "Inuinnaqtun", "Western Canadian Inuktitut", "Inuktitut", "Iku-Gora-Ankwa", "Ikwere", "Ik", "Ikizu", "Ile Ape", "Ila", "Interlingue", "Occidental", "Garig-Ilgar", "Ili Turki", "Ilongot", "Iranun (Malaysia)", "Iloko", "Iranun (Philippines)", "International Sign", "Ili'uun", "Ilue", "Mala Malasar", "Anamgura", "Miluk", "Imonda", "Imbongu", "Imroing", "Marsian", "Imotong", "Milyan", "Interlingua (IALA)", "Interlingua (International Auxiliary Language Association)", "Inga", "Indonesian", "Degexit'an", "Ingush", "Jungle Inga", "Indonesian Sign Language", "Minaean", "Isinai", "Inoke-Yate", "Iñapari", "Indian Sign Language", "Intha", "Ineseño", "Inor", "Tuma-Irumu", "Iowa-Oto", "Ipili", "Inupiaq", "Ipiko", "Iquito", "Ikwo", "Iresim", "Irarutu", "Irigwe", "Rigwe", "Iraqw", "Irántxe", "Ir", "Irula", "Kamberau", "Iraya", "Isabi", "Isconahua", "Isnag", "Italian Sign Language", "Irish Sign Language", "Esan", "Nkem-Nkum", "Ishkashimi", "Icelandic", "Masimasi", "Isanzu", "Isoko", "Israeli Sign Language", "Istriot", "Isu", "Isu (Menchum Division)", "Interslavic", "Italian", "Binongan Itneg", "Southern Tidung", "Itene", "Inlaod Itneg", "Judeo-Italian", "Itelmen", "Itu Mbon Uzo", "Itonama", "Iteri", "Isekiri", "Maeng Itneg", "Itawit", "Ito", "Itik", "Moyadan Itneg", "Itzá", "Iu Mien", "Ibatan", "Ivatan", "I-Wak", "Iwam", "Iwur", "Sepik Iwam", "Ixcatec", "Ixil", "Iyayu", "Mesaka", "Yaka (Congo)", "Ingrian", "Kizamani", "Izere", "Izii", "Jamamadí", "Hyam", "Jakalteko", "Popti'", "Jahanka", "Yabem", "Jara", "Jah Hut", "Zazao", "Jakun", "Yalahatan", "Jamaican Creole English", "Jandai", "Yanyuwa", "Yaqay", "New Caledonian Javanese", "Jakati", "Yaur", "Javanese", "Jambi Malay", "Nhangu", "Yan-nhangu", "Jawe", "Judeo-Berber", "Badjiri", "Arandai", "Barikewa", "Bijim", "Nafusi", "Lojban", "Jofotek-Bromnya", "Jabutí", "Jukun Takum", "Yawijibaya", "Jamaican Country Sign Language", "Krymchak", "Jad", "Jadgali", "Judeo-Tat", "Jebero", "Jerung", "Jeh", "Yei", "Jeri Kuo", "Yelmek", "Dza", "Jere", "Manem", "Jonkor Bourmataguil", "Ngbee", "Judeo-Georgian", "Gwak", "Ngomba", "Jehai", "Jhankot Sign Language", "Jina", "Jibu", "Tol", "Bu (Kaduna State)", "Jilbe", "Djingili", "Jingulu", "Shangzhai", "sTodsde", "Jiiddu", "Jilim", "Jimi (Cameroon)", "Jiamao", "Guanyinqiao", "Lavrung", "Jita", "Youle Jinuo", "Shuar", "Buyuan Jinuo", "Jejueo", "Bankal", "Kaera", "Mobwa Karen", "Kubo", "Paku Karen", "Koro (India)", "Amami Koniya Sign Language", "Labir", "Ngile", "Jamaican Sign Language", "Dima", "Zumbun", "Machame", "Yamdena", "Jimi (Nigeria)", "Jumli", "Makuri Naga", "Kamara", "Mashi (Nigeria)", "Mouwase", "Western Juxtlahuaca Mixtec", "Jangshung", "Jandavra", "Yangman", "Janji", "Yemsa", "Rawat", "Jaunsari", "Joba", "Wojenaka", "Jogi", "Jorá", "Jordanian Sign Language", "Jowulu", "Jewish Palestinian Aramaic", "Japanese", "Judeo-Persian", "Jaqaru", "Jarai", "Judeo-Arabic", "Jiru", "Jakattoe", "Japrería", "Japanese Sign Language", "Júma", "Wannu", "Jurchen", "Worodougou", "Hõne", "Ngadjuri", "Wapan", "Jirel", "Jumjum", "Juang", "Jiba", "Hupdë", "Jurúna", "Jumla Sign Language", "Jutish", "Ju", "Wãpha", "Juray", "Javindo", "Caribbean Javanese", "Jwira-Pepesa", "Jiarong", "Judeo-Yemeni Arabic", "Jaya", "Karakalpak", "Kara-Kalpak", "Kabyle", "Jingpho", "Kachin", "Adara", "Ketangalan", "Katso", "Kajaman", "Kara (Central African Republic)", "Karekare", "Jju", "Kalanguya", "Kayapa Kallahan", "Greenlandic", "Kalaallisut", "Kamba (Kenya)", "Kannada", "Xaasongaxango", "Bezhta", "Capanahua", "Kashmiri", "Georgian", "Kanuri", "Katukína", "Kawi", "Kao", "Kamayurá", "Kazakh", "Kalarko", "Kaxuiâna", "Kadiwéu", "Kabardian", "Kanju", "Khamba", "Camsá", "Kaptiau", "Kari", "Grass Koiari", "Kanembu", "Iwal", "Kare (Central African Republic)", "Keliko", "Kabiyè", "Kamano", "Kafa", "Kande", "Abadi", "Kabutra", "Dera (Indonesia)", "Kaiep", "Ap Ma", "Manga Kanuri", "Duhwa", "Khanty", "Kawacha", "Lubila", "Ngkâlmpw Kanum", "Kaivi", "Ukaan", "Tyap", "Vono", "Kamantan", "Ngyian", "Kobiana", "Kalanga", "Kala", "Kela (Papua New Guinea)", "Gula (Central African Republic)", "Nubi", "Kinalakna", "Kanga", "Kamo", "Katla", "Koenoem", "Kaian", "Kami (Tanzania)", "Kete", "Kabwari", "Kachama-Ganjule", "Korandje", "Konongo", "Worimi", "Kutu", "Yankunytjatjara", "Makonde", "Mamusi", "Seba", "Tem", "Kumam", "Karamojong", "Kwényi", "Numèè", "Tsikimba", "Kagoma", "Kunda", "Kaningdon-Nindem", "Koch", "Karaim", "Kuy", "Kadaru", "Koneraw", "Kam", "Keder", "Keijar", "Kwaja", "Kabuverdianu", "Kélé", "Keiga", "Kerewe", "Eastern Keres", "Kpessi", "Tese", "Keak", "Kei", "Kadar", "Kekchí", "Kela (Democratic Republic of Congo)", "Kemak", "Kenyang", "Kakwa", "Kaikadi", "Kamar", "Kera", "Kugbo", "Ket", "Akebu", "Kanikkaran", "West Kewa", "Kukna", "Kupia", "Kukele", "Kodava", "Northwestern Kolami", "Konda-Dora", "Korra Koraga", "Kota (India)", "Koya", "Kudiya", "Kurichiya", "Kannada Kurumba", "Kemiehua", "Kinnauri", "Kung", "Khunsari", "Kuk", "Koro (Côte d'Ivoire)", "Korwa", "Korku", "Kachhi", "Kutchi", "Bilaspuri", "Kanjari", "Katkari", "Kurmukar", "Kharam Naga", "Kullu Pahari", "Kumaoni", "Koromfé", "Koyaga", "Kawe", "Komering", "Kube", "Kusunda", "Selangor Sign Language", "Gamale Kham", "Kaiwá", "Kunggari", "Karingani", "Krongo", "Kaingang", "Kamoro", "Abun", "Kumbainggar", "Somyev", "Kobol", "Karas", "Karon Dori", "Kamaru", "Kyerung", "Khasi", "Lü", "Tukang Besi North", "Bädi Kanum", "Korowai", "Khuen", "Khams Tibetan", "Kehu", "Kuturmi", "Halh Mongolian", "Lusi", "Central Khmer", "Khmer", "Khandesi", "Khotanese", "Sakan", "Kapauri", "Kapori", "Koyra Chiini Songhay", "Kharia", "Kasua", "Khamti", "Nkhumbi", "Khvarshi", "Khowar", "Kanu", "Kele (Democratic Republic of Congo)", "Keapara", "Kim", "Koalib", "Kickapoo", "Koshin", "Kibet", "Eastern Parbate Kham", "Kimaama", "Kimaghima", "Kilmeri", "Kitsai", "Kilivila", "Gikuyu", "Kikuyu", "Kariya", "Karagas", "Kinyarwanda", "Kiowa", "Sheshi Kham", "Kosadle", "Kosare", "Kirghiz", "Kyrgyz", "Kis", "Agob", "Kirmanjki (individual language)", "Kimbu", "Northeast Kiwai", "Khiamniungan Naga", "Kirikiri", "Kisi", "Mlap", "Kanjobal", "Q'anjob'al", "Coastal Konjo", "Southern Kiwai", "Kisar", "Khmu", "Khakas", "Zabana", "Khinalugh", "Highland Konjo", "Western Parbate Kham", "Kháng", "Kunjen", "Kinnauri Pahari", "Pwo Eastern Karen", "Western Keres", "Kurudu", "East Kewa", "Phrae Pwo Karen", "Kashaya", "Kaikavian Literary Language", "Ramopa", "Erave", "Bumthangkha", "Kakanda", "Kwerisa", "Odoodee", "Kinuku", "Kakabe", "Kalaktang Monpa", "Mabaka Valley Kalinga", "Khün", "Kagulu", "Kako", "Kokota", "Kosarek Yale", "Kiong", "Kon Keu", "Karko", "Gugubera", "Koko-Bera", "Kaeku", "Kir-Balar", "Giiwo", "Koi", "Tumi", "Kangean", "Teke-Kukuya", "Kohin", "Guguyimidjir", "Guugu Yimidhirr", "Kaska", "Klamath-Modoc", "Kiliwa", "Kolbila", "Gamilaraay", "Kulung (Nepal)", "Kendeje", "Tagakaulo", "Weliki", "Kalumpang", "Khalaj", "Kono (Nigeria)", "Kagan Kalagan", "Migum", "Kalenjin", "Kapya", "Kamasa", "Rumu", "Khaling", "Kalasha", "Nukna", "Klao", "Maskelynes", "Lindu", "Tado", "Koluwawa", "Kalao", "Kabola", "Konni", "Kimbundu", "Southern Dong", "Majukayang Kalinga", "Bakole", "Kare (Papua New Guinea)", "Kâte", "Kalam", "Kami (Nigeria)", "Kumarbhag Paharia", "Limos Kalinga", "Tanudan Kalinga", "Kom (India)", "Awtuw", "Kwoma", "Gimme", "Kwama", "Northern Kurdish", "Kamasau", "Kemtuik", "Kanite", "Karipúna Creole French", "Komo (Democratic Republic of Congo)", "Waboda", "Koma", "Khorasani Turkish", "Dera (Nigeria)", "Lubuagan Kalinga", "Central Kanuri", "Konda", "Kankanaey", "Mankanya", "Koongo", "Kanufi", "Western Kanjobal", "Kuranko", "Keninjal", "Kanamarí", "Konkani (individual language)", "Kono (Sierra Leone)", "Kwanja", "Kintaq", "Kaningra", "Kensiu", "Panoan Katukína", "Kono (Guinea)", "Tabo", "Kung-Ekoka", "Kendayan", "Salako", "Kanyok", "Kalamsé", "Konomala", "Kpati", "Kodi", "Kacipo-Bale Suri", "Kubi", "Cogui", "Kogi", "Koyo", "Komi-Permyak", "Konkani (macrolanguage)", "Kol (Papua New Guinea)", "Komi", "Kongo", "Konzo", "Waube", "Kota (Gabon)", "Korean", "Kosraean", "Lagwan", "Koke", "Kudu-Camo", "Kugama", "Koyukon", "Korak", "Kutto", "Mullu Kurumba", "Curripaco", "Koba", "Kpelle", "Komba", "Kapingamarangi", "Kplang", "Kofei", "Karajá", "Kpan", "Kpala", "Koho", "Kepkiriwát", "Ikposo", "Korupun-Sela", "Korafe-Yegha", "Tehit", "Karata", "Kafoa", "Komi-Zyrian", "Kobon", "Mountain Koiali", "Koryak", "Kupsabiny", "Mum", "Kovai", "Doromu-Koki", "Koy Sanjaq Surat", "Kalagan", "Kakabai", "Khe", "Kisankasa", "Koitabu", "Koromira", "Kotafon Gbe", "Kyenele", "Khisa", "Kaonde", "Eastern Krahn", "Kimré", "Krenak", "Kimaragang", "Northern Kissi", "Klias River Kadazan", "Seroa", "Okolod", "Kandas", "Mser", "Koorete", "Korana", "Kumhali", "Karkin", "Karachay-Balkar", "Kairui-Midiki", "Panará", "Koro (Vanuatu)", "Kurama", "Krio", "Kinaray-A", "Kerek", "Karelian", "Sapo", "Durop", "Krung", "Gbaya (Sudan)", "Tumari Kanuri", "Kurukh", "Kavet", "Western Krahn", "Karon", "Kryts", "Sota Kanum", "Shambala", "Southern Kalinga", "Kuanua", "Kuni", "Bafia", "Kusaghe", "Kölsch", "I'saka", "Krisa", "Uare", "Kansa", "Kumalu", "Kumba", "Kasiguranin", "Kofa", "Kaba", "Kwaami", "Borong", "Southern Kisi", "Winyé", "Khamyang", "Kusu", "S'gaw Karen", "Kedang", "Kharia Thar", "Kodaku", "Katua", "Kambaata", "Kholok", "Kokata", "Kukatha", "Nubri", "Kwami", "Kalkutung", "Karanga", "North Muyu", "Plapo Krumen", "Kaniet", "Koroshi", "Kurti", "Karitiâna", "Kuot", "Kaduo", "Katabaga", "South Muyu", "Ketum", "Kituba (Democratic Republic of Congo)", "Eastern Katu", "Kato", "Kaxararí", "Kango (Bas-Uélé District)", "Juǀʼhoan", "Juǀʼhoansi", "Kuanyama", "Kwanyama", "Kutep", "Kwinsu", "'Auhelawa", "Kuman (Papua New Guinea)", "Western Katu", "Kupa", "Kushi", "Kalapalo", "Kuikúro-Kalapálo", "Kuria", "Kepo'", "Kulere", "Kumyk", "Kunama", "Kumukio", "Kunimaipa", "Karipuna", "Kurdish", "Kusaal", "Ksanka", "Ktunaxa", "Kutenai", "Upper Kuskokwim", "Kur", "Kpagua", "Kukatja", "Kuuku-Ya'u", "Kunza", "Bagvalal", "Kubu", "Kove", "Kui (Indonesia)", "Kalabakan", "Kabalai", "Kuni-Boazi", "Komodo", "Kwang", "Psikye", "Korean Sign Language", "Kayaw", "Kendem", "Border Kuna", "Dobel", "Kompane", "Geba Karen", "Kerinci", "Lahta", "Lahta Karen", "Yinbaw Karen", "Kola", "Wersing", "Parkari Koli", "Yintale", "Yintale Karen", "Tsakwambo", "Tsaukambo", "Dâw", "Kwa", "Likwala", "Kwaio", "Kwerba", "Kwara'ae", "Sara Kaba Deme", "Kowiai", "Awa-Cuaiquer", "Kwanga", "Kwakiutl", "Kwak'wala", "Kofyar", "Kwambi", "Kwangali", "Kwomtari", "Kodia", "Kwer", "Kwese", "Kwesten", "Kwakum", "Sara Kaba Náà", "Kwinti", "Khirwar", "San Salvador Kongo", "Kwadi", "Kairiru", "Krobu", "Khonso", "Konso", "Brunei", "Manumanaw", "Manumanaw Karen", "Karo (Ethiopia)", "Keningau Murut", "Kulfa", "Zayein Karen", "Northern Khmer", "Kanowit-Tanjong Melanau", "Kanoé", "Wadiyara Koli", "Smärky Kanum", "Koro (Papua New Guinea)", "Kangjia", "Koiwat", "Kuvi", "Konai", "Likuba", "Kayong", "Kerewo", "Kwaya", "Butbut Kalinga", "Kyaka", "Karey", "Krache", "Kouya", "Keyagana", "Karok", "Kiput", "Karao", "Kamayo", "Kalapuya", "Kpatili", "Northern Binukidnon", "Kelon", "Kang", "Kenga", "Kuruáya", "Baram Kayan", "Kayagar", "Western Kayah", "Kayort", "Kudmali", "Rapoisi", "Kambaira", "Kayabí", "Western Karaboro", "Kaibobo", "Bondoukou Kulango", "Kadai", "Kosena", "Da'a Kaili", "Kikai", "Kelabit", "Kazukuru", "Kayeli", "Kais", "Kokola", "Kaningi", "Kaidipang", "Kaike", "Karang", "Sugut Dusun", "Kayupulau", "Komyandaret", "Karirí-Xocó", "Kamarian", "Kango (Tshopo District)", "Kalabra", "Southern Subanen", "Linear A", "Lacandon", "Ladino", "Pattani", "Lafofa", "Rangi", "Lahnda", "Lambya", "Lango (Uganda)", "Lalia", "Lamba", "Laru", "Lao", "Laka (Chad)", "Qabiao", "Larteh", "Lama (Togo)", "Latin", "Laba", "Latvian", "Lauje", "Tiwa", "Lama Bai", "Aribwatsa", "Label", "Lakkia", "Lak", "Tinani", "Laopang", "La'bi", "Ladakhi", "Central Bontok", "Libon Bikol", "Lodhi", "Rmeet", "Laven", "Wampar", "Lohorung", "Libyan Sign Language", "Lachi", "Labu", "Lavatbura-Lamusong", "Tolaki", "Lawangan", "Lamalama", "Lamu-Lamu", "Lardil", "Legenyem", "Lola", "Loncong", "Sekak", "Lubu", "Luchazi", "Lisela", "Tungag", "Western Lawa", "Luhu", "Lisabata-Nuniali", "Kla-Dan", "Dũya", "Luri", "Lenyima", "Lamja-Dengsa-Tola", "Laari", "Lemoro", "Leelau", "Kaan", "Landoma", "Láadan", "Loo", "Tso", "Lufu", "Lega-Shabunda", "Lala-Bisa", "Leco", "Lendu", "Lyélé", "Lelemi", "Lenje", "Lemio", "Lengola", "Leipon", "Lele (Democratic Republic of Congo)", "Nomaande", "Lenca", "Leti (Cameroon)", "Lepcha", "Lembena", "Lenkau", "Lese", "Amio-Gelimi", "Lesing-Gelimi", "Kara (Papua New Guinea)", "Lamma", "Ledo Kaili", "Luang", "Lemolang", "Lezghian", "Lefa", "Buu (Cameroon)", "Lingua Franca Nova", "Lungga", "Laghu", "Lugbara", "Laghuu", "Lengilu", "Lingarak", "Neverver", "Wala", "Lega-Mwenga", "Opuuo", "T'apo", "Lango (South Sudan)", "Logba", "Lengo", "Guinea-Bissau Sign Language", "Língua Gestual Guineense", "Pahi", "Longgu", "Ligenza", "Laha (Viet Nam)", "Laha (Indonesia)", "Lahu Shi", "Lahul Lohar", "Lhomi", "Lahanan", "Lhokpu", "Mlahsö", "Lo-Toga", "Lahu", "West-Central Limba", "Likum", "Hlai", "Nyindrou", "Likila", "Limbu", "Ligbi", "Lihir", "Ligurian", "Lika", "Lillooet", "Limburgan", "Limburger", "Limburgish", "Lingala", "Liki", "Sekpele", "Libido", "Liberian English", "Lisu", "Lithuanian", "Logorik", "Liv", "Col", "Liabuku", "Banda-Bambari", "Libinza", "Golpa", "Rampi", "Laiyolo", "Li'o", "Lampung Api", "Yirandali", "Yuru", "Lakalei", "Kabras", "Lukabaras", "Kucong", "Lakondê", "Kenyi", "Lakha", "Laki", "Remun", "Laeko-Libuat", "Kalaamaya", "Lakon", "Vure", "Khayo", "Olukhayo", "Päri", "Kisa", "Olushisa", "Lakota", "Kungkari", "Lokoya", "Lala-Roba", "Lolo", "Lele (Guinea)", "Ladin", "Lele (Papua New Guinea)", "Hermit", "Lole", "Lamu", "Teke-Laali", "Ladji Ladji", "Lelak", "Lilau", "Lasalimu", "Lele (Chad)", "North Efate", "Lolak", "Lithuanian Sign Language", "Lau", "Lauan", "East Limba", "Merei", "Limilngan", "Lumun", "Pévé", "South Lembata", "Lamogai", "Lambichhong", "Lombi", "West Lembata", "Lamkang", "Hano", "Lambadi", "Lombard", "Limbum", "Lamatuka", "Lamalera", "Lamenu", "Lomaiviti", "Lake Miwok", "Laimbue", "Lamboya", "Langbashe", "Mbalanhu", "Lun Bawang", "Lundayeh", "Langobardic", "Lanoh", "Daantanai'", "Leningitij", "South Central Banda", "Langam", "Lorediakarkar", "Lamnso'", "Longuda", "Lanima", "Lonzo", "Loloda", "Lobi", "Inonhan", "Saluan", "Logol", "Logo", "Laarim", "Narim", "Loma (Côte d'Ivoire)", "Lou", "Loko", "Mongo", "Loma (Liberia)", "Malawi Lomwe", "Lombo", "Lopa", "Lobala", "Téén", "Loniu", "Otuho", "Louisiana Creole", "Lopi", "Tampias Lobu", "Loun", "Loke", "Lozi", "Lelepa", "Lepki", "Long Phuri Naga", "Lipo", "Lopit", "Logir", "Rara Bakati'", "Northern Luri", "Laurentian", "Laragia", "Marachi", "Olumarachi", "Loarki", "Lari", "Marama", "Olumarama", "Lorang", "Laro", "Southern Yamphu", "Larantuka Malay", "Larevat", "Lemerig", "Lasgerdi", "Burundian Sign Language", "Langue des Signes Burundaise", "Albarradas Sign Language", "Lengua de señas Albarradas", "Lishana Deni", "Lusengo", "Lish", "Lashi", "Latvian Sign Language", "Olusamia", "Saamia", "Tibetan Sign Language", "Laos Sign Language", "Lengua de Señas Panameñas", "Panamanian Sign Language", "Aruop", "Lasi", "Trinidad and Tobago Sign Language", "Sivia Sign Language", "Lalang Siny Seselwa", "Langue des Signes Seychelloise", "Seychelles Sign Language", "Mauritian Sign Language", "Late Middle Chinese", "Latgalian", "Thur", "Leti (Indonesia)", "Latundê", "Olutsotso", "Tsotso", "Lutachoni", "Tachoni", "Latu", "Letzeburgesch", "Luxembourgish", "Luba-Lulua", "Luba-Katanga", "Aringa", "Ludian", "Luvale", "Laua", "Ganda", "Leizhou Chinese", "Luiseño", "Luna", "Lunanakha", "Olu'bo", "Luimbi", "Lunda", "Dholuo", "Luo (Kenya and Tanzania)", "Lumbu", "Lucumi", "Laura", "Lushai", "Lushootseed", "Lumba-Yakkha", "Luwati", "Luo (Cameroon)", "Luyia", "Oluluyia", "Southern Luri", "Maku'a", "Lavi", "Lavukaleve", "Lwel", "Standard Latvian", "Levuka", "Lwalu", "Lewo Eleng", "Oluwanga", "Wanga", "White Lachi", "Eastern Lawa", "Laomian", "Luwo", "Malawian Sign Language", "Lewotobi", "Lawu", "Lewo", "Lakurumau", "Layakha", "Lyngngam", "Luyana", "Literary Chinese", "Litzlitz", "Leinong Naga", "Laz", "San Jerónimo Tecóatl Mazatec", "Yutanduchi Mixtec", "Madurese", "Bo-Rukul", "Mafa", "Magahi", "Marshallese", "Maithili", "Jalapa De Díaz Mazatec", "Makasar", "Malayalam", "Mam", "Manding", "Mandingo", "Chiquihuitlán Mazatec", "Marathi", "Masai", "San Francisco Matlatzinca", "Huautla Mazatec", "Sateré-Mawé", "Mampruli", "North Moluccan Malay", "Central Mazahua", "Higaonon", "Western Bukidnon Manobo", "Macushi", "Dibabawon Manobo", "Molale", "Baba Malay", "Mangseng", "Ilianen Manobo", "Nadëb", "Malol", "Maxakalí", "Ombamba", "Macaguán", "Mbo (Cameroon)", "Malayo", "Maisin", "Nukak Makú", "Sarangani Manobo", "Matigsalug Manobo", "Mbula-Bwazza", "Mbulungish", "Maring", "Mari (East Sepik Province)", "Memoni", "Amoltepec Mixtec", "Maca", "Machiguenga", "Bitur", "Sharanahua", "Itundujia Mixtec", "Matsés", "Mapoyo", "Maquiritari", "Mese", "Mvanip", "Mbunda", "Macaguaje", "Malaccan Creole Portuguese", "Masana", "Coatlán Mixe", "Makaa", "Ese", "Menya", "Mambai", "Mengisa", "Cameroon Mambila", "Minanibai", "Mawa (Chad)", "Mpiemo", "South Watut", "Mawan", "Mada (Nigeria)", "Morigi", "Male (Papua New Guinea)", "Soq", "Mbum", "Maba (Chad)", "Moksha", "Massalat", "Maguindanaon", "Mamvu", "Mangbetu", "Mangbutu", "Maltese Sign Language", "Mayogo", "Mbati", "Mbala", "Mbole", "Mandar", "Maria (Papua New Guinea)", "Mbere", "Mboko", "Santa Lucía Monteverde Mixtec", "Mbosi", "Dizin", "Male", "Male (Ethiopia)", "Suruí Do Pará", "Menka", "Ikobi", "Marra", "Melpa", "Mengen", "Megam", "Southwestern Tlaxiaco Mixtec", "Midob", "Meyah", "Mekeo", "Central Melanau", "Mangala", "Mende (Sierra Leone)", "Kedah Malay", "Miriwoong", "Merey", "Meru", "Masmaje", "Mato", "Motu", "Mano", "Maaka", "Hassaniyya", "Menominee", "Pattani Malay", "Bangka", "Mba", "Mendankwe-Nkwen", "Morisyen", "Naki", "Mogofin", "Matal", "Wandala", "Mefele", "North Mofu", "Putai", "Marghi South", "Cross River Mbembe", "Mbe", "Makassar Malay", "Moba", "Marrithiyel", "Mexican Sign Language", "Mokerang", "Mbwela", "Mandjak", "Mulaha", "Melo", "Mayo", "Mabaan", "Middle Irish (900-1200)", "Mararit", "Morokodo", "Moru", "Mango", "Maklew", "Mpumpong", "Makhuwa-Meetto", "Lijili", "Abureni", "Mawes", "Maleu-Kilenge", "Mambae", "Mbangi", "Meta'", "Eastern Magar", "Malila", "Mambwe-Lungu", "Manda (Tanzania)", "Mongol", "Mailu", "Matengo", "Matumbi", "Mbunga", "Mbugwe", "Manda (India)", "Mahongwe", "Mocho", "Mbugu", "Besisi", "Mah Meri", "Mamaa", "Margu", "Ma'di", "Mogholi", "Mungaka", "Mauwake", "Makhuwa-Moniga", "Mòcheno", "Mashi (Zambia)", "Balinese Malay", "Mandan", "Eastern Mari", "Buru (Indonesia)", "Mandahuaca", "Darang Deng", "Digaro-Mishmi", "Mbukushu", "Lhaovo", "Maru", "Ma'anyan", "Mor (Mor Islands)", "Miami", "Atatláhuca Mixtec", "Micmac", "Mi'kmaq", "Mandaic", "Ocotepec Mixtec", "Mofu-Gudur", "San Miguel El Grande Mixtec", "Chayuco Mixtec", "Chigmecatitlán Mixtec", "Abar", "Mungbam", "Mikasuki", "Peñoles Mixtec", "Alacatlatzala Mixtec", "Minangkabau", "Pinotepa Nacional Mixtec", "Apasco-Apoala Mixtec", "Mískito", "Isthmus Mixe", "Uncoded languages", "Southern Puebla Mixtec", "Cacaloxtepec Mixtec", "Akoye", "Mixtepec Mixtec", "Ayutla Mixtec", "Coatzospan Mixtec", "Makalero", "San Juan Colorado Mixtec", "Northwest Maidu", "Muskum", "Tu", "Mwera (Nyasa)", "Kim Mun", "Mawak", "Matukar", "Mandeali", "Medebur", "Ma (Papua New Guinea)", "Malankuravan", "Malapandaram", "Malaryan", "Malavedan", "Miship", "Sauria Paharia", "Manna-Dora", "Mannan", "Karbi", "Mahali", "Mahican", "Majhi", "Mbre", "Mal Paharia", "Siliput", "Macedonian", "Mawchi", "Miya", "Mak (China)", "Dhatki", "Mokilese", "Byep", "Mokole", "Moklen", "Kupang Malay", "Mingang Doso", "Moikodi", "Bay Miwok", "Malas", "Silacayoapan Mixtec", "Vamale", "Konyanka Maninka", "Mafea", "Kituba (Congo)", "Kinamiging Manobo", "East Makian", "Makasae", "Malo", "Mbule", "Cao Lan", "Manambu", "Mal", "Malagasy", "Mape", "Malimpung", "Miltu", "Ilwana", "Kiwilwana", "Malua Bay", "Mulam", "Malango", "Mlomp", "Bargam", "Western Maninkakan", "Vame", "Masalit", "Maltese", "To'abaita", "Motlav", "Mwotlap", "Moloko", "Malfaxal", "Naha'ai", "Malaynon", "Mama", "Momina", "Michoacán Mazahua", "Maonan", "Mae", "Mundat", "North Ambrym", "Mehináku", "Amben", "Hember Avu", "Musar", "Majhwar", "Mukha-Dora", "Man Met", "Maii", "Mamanwa", "Mangga Buang", "Siawi", "Musak", "Western Xiangxi Miao", "Malalamai", "Mmaala", "Miriti", "Emae", "Madak", "Migaama", "Mabaale", "Mbula", "Muna", "Manchu", "Mondé", "Naba", "Mundani", "Eastern Mnong", "Mono (Democratic Republic of Congo)", "Manipuri", "Munji", "Mandinka", "Tiale", "Mapena", "Southern Mnong", "Min Bei Chinese", "Minriq", "Mono (USA)", "Mansi", "Mer", "Rennell-Bellona", "Mon", "Manikion", "Manyawa", "Moni", "Mwan", "Mocoví", "Mobilian", "Innu", "Montagnais", "Mongondow", "Kanien'kéha", "Mohawk", "Mboi", "Monzombo", "Morori", "Mangue", "Mongolian", "Monom", "Mopán Maya", "Mor (Bomberai Peninsula)", "Moro", "Mossi", "Barí", "Mogum", "Mohave", "Moi (Congo)", "Molima", "Shekkacho", "Gergiko", "Mukulu", "Mpoto", "Malak Malak", "Mullukmulluk", "Mangarrayi", "Machinere", "Majang", "Marba", "Maung", "Mpade", "Martu Wangka", "Wangkajunga", "Mbara (Chad)", "Middle Watut", "Yosondúa Mixtec", "Mindiri", "Miu", "Migabac", "Matís", "Vangunu", "Dadibi", "Mian", "Makuráp", "Mungkip", "Mapidian", "Misima-Panaeati", "Mapia", "Mpi", "Maba (Indonesia)", "Mbuko", "Mangole", "Matepi", "Momuna", "Kota Bangun Kutai Malay", "Tlazoyaltepec Mixtec", "Mariri", "Mamasa", "Rajah Kabunsuwan Manobo", "Mbelime", "South Marquesan", "Moronene", "Modole", "Manipa", "Minokok", "Mander", "West Makian", "Mok", "Mandari", "Mosimo", "Murupi", "Mamuju", "Manggarai", "Pano", "Mlabri", "Marino", "Maricopa", "Western Magar", "Martha's Vineyard Sign Language", "Elseng", "Mising", "Mara Chin", "Maori", "Western Mari", "Hmwaveke", "Mortlockese", "Merlav", "Mwerlap", "Cheke Holo", "Mru", "Morouas", "North Marquesan", "Maria (India)", "Maragus", "Marghi Central", "Mono (Cameroon)", "Mangareva", "Maranao", "Dineor", "Maremgi", "Mandaya", "Marind", "Malay (macrolanguage)", "Masbatenyo", "Sankaran Maninka", "Yucatec Maya Sign Language", "Musey", "Mekwei", "Moraid", "Masikoro Malagasy", "Sabah Malay", "Ma (Democratic Republic of Congo)", "Mansaka", "Molof", "Poule", "Agusan Manobo", "Vurës", "Mombum", "Maritsauá", "Caac", "Mongolian Sign Language", "West Masela", "Musom", "Maslam", "Mansoanka", "Moresada", "Aruamu", "Momare", "Cotabato Manobo", "Anyin Morofo", "Munit", "Mualang", "Mono (Solomon Islands)", "Murik (Papua New Guinea)", "Una", "Munggui", "Maiwa (Papua New Guinea)", "Moskona", "Mbe'", "Montol", "Mator", "Matagalpa", "Totontepec Mixe", "Wichí Lhamtés Nocten", "Muong", "Mewari", "Yora", "Mota", "Tututepec Mixtec", "Asaro'o", "Southern Binukidnon", "Tidaá Mixtec", "Nabi", "Mundang", "Mubi", "Ajumbu", "Mednyj Aleut", "Media Lengua", "Musgu", "Mündü", "Musi", "Mabire", "Mugom", "Multiple languages", "Maiwala", "Nyong", "Malvi", "Eastern Xiangxi Miao", "Murle", "Creek", "Western Muria", "Yaaku", "Muthuvan", "Bo-Ung", "Muyang", "Mursi", "Manam", "Mattole", "Mamboru", "Marwari (Pakistan)", "Peripheral Mongolian", "Yucuañe Mixtec", "Mulgi", "Miyako", "Mekmek", "Mbara (Australia)", "Minaveha", "Marovo", "Duri", "Moere", "Marau", "Massep", "Mpotovoro", "Marfa", "Tagal Murut", "Machinga", "Meoswar", "Indus Kohistani", "Mesqan", "Mwatebu", "Juwal", "Are", "Mwera (Chimwera)", "Murrinh-Patha", "Aiklep", "Mouk-Aria", "Labo", "Ninde", "Kita Maninkakan", "Mirandese", "Sar", "Nyamwanga", "Central Maewo", "Kala Lagaw Ya", "Mün Chin", "Marwari", "Mwimbi-Muthambi", "Moken", "Mittu", "Mentawai", "Hmong Daw", "Moingi", "Northwest Oaxaca Mixtec", "Tezoatlán Mixtec", "Manyika", "Modang", "Mele-Fila", "Malgbe", "Mbangala", "Mvuba", "Mozarabic", "Geman Deng", "Miju-Mishmi", "Monumbo", "Maxi Gbe", "Meramera", "Moi (Indonesia)", "Mbowe", "Tlahuitoltepec Mixe", "Juquila Mixe", "Murik (Malaysia)", "Huitepec Mixtec", "Jamiltepec Mixtec", "Mada (Cameroon)", "Metlatónoc Mixtec", "Namo", "Mahou", "Mawukakan", "Southeastern Nochixtlán Mixtec", "Central Masela", "Burmese", "Mbay", "Mayeka", "Myene", "Bambassi", "Manta", "Makah", "Mangayat", "Mamara Senoufo", "Moma", "Me'en", "Anfillo", "Pirahã", "Muniche", "Mesmes", "Mundurukú", "Erzya", "Muyuw", "Masaaba", "Macuna", "Classical Mandaic", "Santa María Zacatepec Mixtec", "Tumzabt", "Madagascar Sign Language", "Malimba", "Morawa", "Monastic Sign Language", "Wichí Lhamtés Güisnay", "Ixcatlán Mazatec", "Manya", "Nigeria Mambila", "Mazatlán Mixe", "Mumuye", "Mazanderani", "Matipuhy", "Movima", "Mori Atas", "Marúbo", "Macanese", "Mintil", "Inapang", "Manza", "Deg", "Mawayana", "Mozambican Sign Language", "Maiadomu", "Namla", "Southern Nambikuára", "Narak", "Naka'ela", "Nabak", "Naga Pidgin", "Nalu", "Nakanai", "Nalik", "Ngan'gityemerri", "Min Nan Chinese", "Naaba", "Neapolitan", "Khoekhoe", "Nama (Namibia)", "Iguta", "Naasioi", "Ca̱hungwa̱rya̱", "Hungworo", "Nauru", "Navaho", "Navajo", "Nawuri", "Nakwi", "Ngarrindjeri", "Coatepec Nahuatl", "Nyemba", "Ndoe", "Chang Naga", "Ngbinda", "Konyak Naga", "Nagarchal", "Ngamo", "Mao Naga", "Ngarinyman", "Nake", "South Ndebele", "Ngbaka Ma'bo", "Kuri", "Nkukoli", "Nnam", "Nggem", "Numana", "Namibian Sign Language", "Na", "Rongmei Naga", "Ngamambo", "Southern Ngbandi", "Ningera", "Iyo", "Central Nicobarese", "Ponam", "Nachering", "Yale", "Notsi", "Nisga'a", "Central Huasteca Nahuatl", "Classical Nahuatl", "Northern Puebla Nahuatl", "Na-kara", "Michoacán Nahuatl", "Nambo", "Nauna", "Sibe", "Northern Katang", "Ncane", "Nicaraguan Sign Language", "Chothe Naga", "Chumburung", "Central Puebla Nahuatl", "Natchez", "Ndasa", "Kenswei Nsei", "Ndau", "Nde-Nsele-Nta", "North Ndebele", "Nadruvian", "Ndengereko", "Ndali", "Samba Leko", "Ndamba", "Ndaka", "Ndolo", "Ndam", "Ngundi", "Ndonga", "Ndo", "Ndombe", "Ndoola", "Low German", "Low Saxon", "Ndunga", "Dugun", "Ndut", "Ndobo", "Nduga", "Lutos", "Ndogo", "Eastern Ngad'a", "Toura (Côte d'Ivoire)", "Nedebang", "Nde-Gbite", "Nêlêmwa-Nixumwak", "Nefamese", "Negidal", "Nyenkha", "Neo-Hittite", "Neko", "Neku", "Nemi", "Nengone", "Ná-Meo", "Nepali (macrolanguage)", "North Central Mixe", "Yahadian", "Bhoti Kinnauri", "Nete", "Neo", "Nyaheun", "Nepal Bhasa", "Newar", "Newari", "Neme", "Neyo", "Nez Perce", "Dhao", "Ahwai", "Äiwoo", "Ayiwo", "Nafaanra", "Mfumte", "Ngbaka", "Northern Ngbandi", "Ngombe (Democratic Republic of Congo)", "Ngando (Central African Republic)", "Ngemba", "Ngbaka Manza", "Nǁng", "Ngizim", "Ngie", "Dalabon", "Lomwe", "Ngatik Men's Creole", "Ngwo", "Ngulu", "Ngoreme", "Ngurimi", "Engdewu", "Gvoko", "Kriang", "Ngeq", "Guerrero Nahuatl", "Nagumi", "Ngwaba", "Nggwahyi", "Tibea", "Ngungwel", "Nhanda", "Beng", "Tabasco Nahuatl", "Ava Guaraní", "Chiripá", "Eastern Huasteca Nahuatl", "Nhuwala", "Tetelcingo Nahuatl", "Nahari", "Zacatlán-Ahuacatlán-Tepetzintla Nahuatl", "Isthmus-Cosoleacaque Nahuatl", "Morelos Nahuatl", "Central Nahuatl", "Takuu", "Isthmus-Pajapan Nahuatl", "Huaxcaleca Nahuatl", "Naro", "Ometepec Nahuatl", "Noone", "Temascaltepec Nahuatl", "Western Huasteca Nahuatl", "Isthmus-Mecayapan Nahuatl", "Northern Oaxaca Nahuatl", "Santa María La Alta Nahuatl", "Nias", "Nakame", "Ngandi", "Niellim", "Nek", "Ngalakgan", "Nyiha (Tanzania)", "Nii", "Ngaju", "Southern Nicobarese", "Nila", "Nilamba", "Ninzo", "Nganasan", "Nandi", "Nimboran", "Nimi", "Southeastern Kolami", "Niuean", "Gilyak", "Nimo", "Hema", "Ngiti", "Ningil", "Nzanyi", "Nocte Naga", "Ndonde Hamba", "Lotha Naga", "Gudanji", "Njen", "Njalgulgule", "Angami Naga", "Liangmai Naga", "Ao Naga", "Njerep", "Nisa", "Ndyuka-Trio Pidgin", "Ngadjunmaya", "Kunyi", "Njyem", "Nyishi", "Nkoya", "Khoibu Naga", "Nkongho", "Koireng", "Duke", "Inpui Naga", "Nekgini", "Khezha Naga", "Thangal Naga", "Nakai", "Nokuku", "Namat", "Nkangala", "Nkonya", "Niuatoputapu", "Nkami", "Nukuoro", "North Asmat", "Nyika (Tanzania)", "Bouna Kulango", "Nyika (Malawi and Zambia)", "Nkutu", "Nkoroo", "Nkari", "Ngombale", "Nalca", "Dutch", "Flemish", "East Nyala", "Gela", "Grangali", "Nyali", "Ninia Yali", "Nihali", "Mankiyali", "Ngul", "Lao Naga", "Nchumbulu", "Orizaba Nahuatl", "Walangama", "Nahali", "Nyamal", "Nalögo", "Maram Naga", "Big Nambas", "V'ënen Taut", "Ngam", "Ndumu", "Mzieme Naga", "Tangkhul Naga (India)", "Kwasio", "Monsang Naga", "Nyam", "Ngombe (Central African Republic)", "Namakura", "Ndemli", "Manangba", "ǃXóõ", "Moyon Naga", "Nimanbur", "Nambya", "Nimbari", "Letemboi", "Namonuito", "Northeast Maidu", "Ngamini", "Nimoa", "Rifao", "Nama (Papua New Guinea)", "Namuyi", "Nawdm", "Nyangumarta", "Nande", "Nancere", "West Ambae", "Ngandyera", "Ngaing", "Maring Naga", "Ngiemboon", "North Nuaulu", "Nyangatom", "Nankina", "Northern Rengma Naga", "Namia", "Ngete", "Norwegian Nynorsk", "Wancho Naga", "Ngindo", "Narungga", "Nanticoke", "Dwang", "Nugunu (Australia)", "Southern Nuni", "Nyangga", "Nda'nda'", "Woun Meu", "Norwegian Bokmål", "Nuk", "Northern Thai", "Nimadi", "Nomane", "Nogai", "Nomu", "Noiri", "Nonuya", "Lhéchelesem", "Nooksack", "Nomlaki", "Old Norse", "Numanggang", "Ngongo", "Norwegian", "Eastern Nisu", "Nomatsiguenga", "Ewage-Notu", "Novial", "Nyambo", "Noy", "Nayi", "Nar Phu", "Nupbikha", "Ponyo-Gongwang Naga", "Phom Naga", "Nepali (individual language)", "Southeastern Puebla Nahuatl", "Mondropolon", "Pochuri Naga", "Nipsan", "Puimei Naga", "Noipx", "Napu", "Southern Nago", "Kura Ede Nago", "Ngendelengo", "Ndom", "Nen", "N'Ko", "Kyan-Karyaw Naga", "Nteng", "Akyaung Ari Naga", "Ngom", "Nara", "Noric", "Southern Rengma Naga", "Guernésiais", "Jèrriais", "Narango", "Chokri Naga", "Ngarla", "Ngarluma", "Narom", "Norn", "North Picene", "Nora", "Norra", "Northern Kalapuya", "Narua", "Ngurmbur", "Lala", "Sangtam Naga", "Lower Nossob", "Nshi", "Southern Nisu", "Nsenga", "Northwestern Nisu", "Ngasa", "Ngoshie", "Nigerian Sign Language", "Naskapi", "Norwegian Sign Language", "Sumi Naga", "Nehan", "Northern Sotho", "Pedi", "Sepedi", "Nepalese Sign Language", "Northern Sierra Miwok", "Maritime Sign Language", "Nali", "Tase Naga", "Sierra Negra Nahuatl", "Southwestern Nisu", "Navut", "Nsongo", "Nasal", "Nisenan", "Northern Tidung", "Ngantangarra", "Natioro", "Ngaanyatjarra", "Ikoma-Nata-Isenye", "Nateni", "Ntomba", "Northern Tepehuan", "Delo", "Natügu", "Nottoway", "Tangkhul Naga (Myanmar)", "Mantsi", "Natanzi", "Yuanga", "Nukuini", "Ngala", "Ngundu", "Nusu", "Nungali", "Ndunda", "Ngumbi", "Nyole", "Nuuchahnulth", "Nuu-chah-nulth", "Nusa Laut", "Niuafo'ou", "Anong", "Nguôn", "Nupe-Nupe-Tako", "Nukumanu", "Nukuria", "Nuer", "Nung (Viet Nam)", "Ngbundu", "Northern Nuni", "Nguluwan", "Mehek", "Nunggubuyu", "Tlamacazapa Nahuatl", "Nasarian", "Namiae", "Nyokon", "Nawathinehena", "Nyabwa", "Classical Nepal Bhasa", "Classical Newari", "Old Newari", "Ngwe", "Ngayawung", "Southwest Tanna", "Nyamusa-Molo", "Nauo", "Nawaru", "Ndwewe", "Middle Newar", "Nottoway-Meherrin", "Nauete", "Ngando (Democratic Republic of Congo)", "Nage", "Ngad'a", "Nindi", "Koki Naga", "South Nuaulu", "Numidian", "Ngawun", "Ndambomo", "Naxi", "Ninggerum", "Nafri", "Chewa", "Chichewa", "Nyanja", "Nyangbo", "Nyanga-li", "Nyore", "Olunyole", "Nyengo", "Giryama", "Kigiryama", "Nyindu", "Nyikina", "Ama (Sudan)", "Nyanga", "Nyaneka", "Nyeu", "Nyamwezi", "Nyankole", "Nyoro", "Nyang'i", "Nayini", "Nyiha (Malawi)", "Nyungar", "Nyawaygi", "Nyungwe", "Nyulnyul", "Nyaw", "Nganyaywana", "Nyakyusa-Ngonde", "Tigon Mbembe", "Njebi", "Nzadi", "Nzima", "Nzakara", "Zeme Naga", "Dir-Nyamzak-Mbarimi", "New Zealand Sign Language", "Teke-Nzikou", "Nzakambay", "Nanga Dama Dogon", "Orok", "Oroch", "Noakhailla", "Noakhali", "Ancient Aramaic (up to 700 BCE)", "Old Aramaic (up to 700 BCE)", "Old Avar", "Obispeño", "Southern Bontok", "Oblo", "Moabite", "Obo Manobo", "Old Burmese", "Old Breton", "Obulom", "Ocaina", "Old Chinese", "Occitan (post 1500)", "Old Cham", "Old Cornish", "Atzingo Matlatzinca", "Odut", "Od", "Old Dutch", "Odual", "Ofo", "Old Frisian", "Efutop", "Ogbia", "Ogbah", "Old Georgian", "Ogbogolo", "Khana", "Ogbronuagum", "Old Hittite", "Old Hungarian", "Oirata", "Okolie", "Inebu One", "Northwestern Ojibwa", "Central Ojibwa", "Eastern Ojibwa", "Ojibwa", "Old Japanese", "Severn Ojibwa", "Ontong Java", "Western Ojibwa", "Okanagan", "Okobo", "Kobo", "Okodia", "Okpe (Southwestern Edo)", "Koko Babangk", "Koresh-e Rostam", "Okiek", "Oko-Juwoi", "Kwamtim One", "Old Kentish Sign Language", "Middle Korean (10th-16th cent.)", "Oki-No-Erabu", "Old Korean (3rd-9th cent.)", "Kirike", "Oko-Eni-Osayen", "Oku", "Orokaiva", "Okpe (Northwestern Edo)", "Old Khmer", "Walungge", "Oli-Bodiman", "Mochi", "Olekha", "Olkol", "Oloma", "Livvi", "Olrat", "Old Lithuanian", "Kuvale", "Omaha-Ponca", "East Ambae", "Mochica", "Omagua", "Omi", "Omok", "Ombo", "Minoan", "Utarmbung", "Old Manipuri", "Old Marathi", "Omotik", "Omurano", "South Tairora", "Old Mon", "Old Malay", "Ona", "Lingao", "Oneida", "Olo", "Onin", "Onjob", "Kabore One", "Onobasulu", "Onondaga", "Sartang", "Northern One", "Ono", "Ontenu", "Unua", "Old Nubian", "Onin Based Pidgin", "Tohono O'odham", "Ong", "Önge", "Oorlams", "Old Ossetic", "Okpamheri", "Kopkaka", "Oksapmin", "Opao", "Opata", "Ofayé", "Oroha", "Orma", "Orejón", "Oring", "Oroqen", "Oriya (macrolanguage)", "Oromo", "Orang Kanaq", "Orokolo", "Oruma", "Orang Seletar", "Adivasi Oriya", "Ormuri", "Old Russian", "Oro Win", "Oro", "Odia", "Oriya (individual language)", "Ormu", "Osage", "Oscan", "Digor", "Digor Ossetian", "Digor Ossetic", "Osing", "Old Sundanese", "Ososo", "Old Spanish", "Iron", "Iron Ossetian", "Iron Ossetic", "Ossetian", "Ossetic", "Osatu", "Southern One", "Old Saxon", "Ottoman Turkish (1500-1928)", "Old Tibetan", "Ot Danum", "Mezquital Otomi", "Oti", "Old Turkish", "Tilapa Otomi", "Eastern Highland Otomi", "Tenango Otomi", "Querétaro Otomi", "Otoro", "Estado de México Otomi", "Temoaya Otomi", "Otuke", "Ottawa", "Texcatepec Otomi", "Old Tamil", "Ixtenco Otomi", "Tagargrent", "Glio-Oubi", "Oune", "Old Uighur", "Ouma", "Elfdalian", "Övdalian", "Owiniga", "Old Welsh", "Oy", "Oyda", "Wayampi", "Oya'oya", "Koonzime", "Parecís", "Pacoh", "Paumarí", "Pagibete", "Paranawát", "Pangasinan", "Tenharim", "Pe", "Parakanã", "Pahlavi", "Kapampangan", "Pampanga", "Panjabi", "Punjabi", "Northern Paiute", "Papiamento", "Parya", "Panamint", "Timbisha", "Papasena", "Palauan", "Pakaásnovos", "Pawnee", "Pankararé", "Pech", "Pankararú", "Páez", "Patamona", "Mezontla Popoloca", "Coyotepec Popoloca", "Paraujano", "E'ñapa Woromaipu", "Parkwa", "Mak (Nigeria)", "Puebla Mazatec", "Kpasam", "Papel", "Badyara", "Pangwa", "Central Pame", "Southern Pashto", "Northern Pashto", "Pnar", "Pyu (Papua New Guinea)", "Santa Inés Ahuatempan Popoloca", "Pear", "Bouyei", "Picard", "Ruching Palaung", "Paliyan", "Paniya", "Pardhan", "Duruwa", "Parenga", "Paite Chin", "Pardhi", "Nigerian Pidgin", "Piti", "Pacahuara", "Pyapun", "Anam", "Pennsylvania German", "Pa Di", "Fedan", "Podena", "Padoe", "Plautdietsch", "Kayan", "Peranakan Indonesian", "Eastern Pomo", "Mala (Papua New Guinea)", "Taje", "Northeastern Pomo", "Pengo", "Bonan", "Chichimeca-Jonaz", "Northern Pomo", "Penchal", "Pekal", "Phende", "Old Persian (ca. 600-400 B.C.)", "Kunja", "Southern Pomo", "Iranian Persian", "Pémono", "Petats", "Petjo", "Eastern Penan", "Pááfang", "Pere", "Pfaelzisch", "Sudanese Creole Arabic", "Gāndhārī", "Pangwali", "Pagi", "Rerep", "Primitive Irish", "Paelignian", "Pangseng", "Pagu", "Papua New Guinean Sign Language", "Pa-Hng", "Phudagi", "Phuong", "Phukha", "Pahari", "Phake", "Palula", "Phalura", "Phimbi", "Phoenician", "Phunoi", "Phana'", "Pahari-Potwari", "Phu Thai", "Phuan", "Pahlavani", "Phangduwali", "Pima Bajo", "Yine", "Pinji", "Piaroa", "Piro", "Pingelapese", "Pisabo", "Pitcairn-Norfolk", "Pijao", "Yom", "Powhatan", "Piame", "Piapoco", "Pero", "Piratapuyo", "Pijin", "Pitta Pitta", "Pintupi-Luritja", "Pileni", "Vaeakau-Taumako", "Pimbwe", "Piu", "Piya-Kwonci", "Pije", "Pitjantjatjara", "Ardhamāgadhī Prākrit", "Kipfokomo", "Pokomo", "Paekche", "Pak-Tong", "Pankhu", "Pakanha", "Pökoot", "Pukapuka", "Attapady Kurumba", "Pakistan Sign Language", "Maleng", "Paku", "Miani", "Polonombauk", "Central Palawano", "Polari", "Palu'e", "Pilagá", "Paulohi", "Pali", "Kohistani Shina", "Shwe Palaung", "Palenquero", "Oluta Popoluca", "Palaic", "Palaka Senoufo", "San Marcos Tlacoyalco Popoloca", "San Marcos Tlalcoyalco Popoloca", "Plateau Malagasy", "Palikúr", "Southwest Palawano", "Brooke's Point Palawano", "Bolyu", "Paluan", "Paama", "Pambia", "Pallanganmiddang", "Pwaamei", "Pamona", "Māhārāṣṭri Prākrit", "Northern Pumi", "Southern Pumi", "Lingua Franca", "Pomo", "Pam", "Pom", "Northern Pame", "Paynamar", "Piemontese", "Tuamotuan", "Plains Miwok", "Poumei Naga", "Papuan Malay", "Southern Pame", "Punan Bah-Biau", "Western Panjabi", "Pannei", "Mpinda", "Western Penan", "Pangu", "Pongu", "Penrhyn", "Aoheng", "Pinjarup", "Paunaka", "Paleni", "Punan Batu 1", "Pinai-Hagahai", "Panobo", "Pancana", "Pana (Burkina Faso)", "Panim", "Ponosakan", "Pontic", "Jiongnai Bunu", "Pinigura", "Banyjima", "Panytyima", "Phong-Kniang", "Pinyin", "Pana (Central African Republic)", "Poqomam", "San Juan Atzingo Popoloca", "Poke", "Potiguára", "Poqomchi'", "Highland Popoluca", "Pokangá", "Polish", "Southeastern Pomo", "Pohnpeian", "Central Pomo", "Pwapwâ", "Texistepec Popoluca", "Portuguese", "Sayula Popoluca", "Potawatomi", "Upper Guinea Crioulo", "San Felipe Otlaltepec Popoloca", "Polabian", "Pogolo", "Papi", "Paipai", "Uma", "Nicarao", "Pipil", "Papuma", "Papapana", "Folopa", "Pelende", "Pei", "San Luís Temalacayuca Popoloca", "Pare", "Papora", "Pa'a", "Malecite-Passamaquoddy", "Parachi", "Parsi-Dari", "Principense", "Paranan", "Prussian", "Porohanon", "Paicî", "Parauk", "Peruvian Sign Language", "Kibiri", "Prasuni", "Old Occitan (to 1500)", "Old Provençal (to 1500)", "Ashéninka Perené", "Puri", "Afghan Persian", "Dari", "Phai", "Puragi", "Parawen", "Purik", "Providencia Sign Language", "Asue Awyu", "Iranian Sign Language", "Persian Sign Language", "Plains Indian Sign Language", "Central Malay", "Penang Sign Language", "Southwest Pashai", "Southwest Pashayi", "Southeast Pashai", "Southeast Pashayi", "Puerto Rican Sign Language", "Pauserna", "Panasuan", "Polish Sign Language", "Philippine Sign Language", "Pasi", "Portuguese Sign Language", "Kaulong", "Central Pashto", "Sauraseni Prākrit", "Port Sandwich", "Piscataway", "Pai Tavytera", "Pataxó Hã-Ha-Hãe", "Pindiini", "Wangkatha", "Patani", "Zo'é", "Patep", "Pattapu", "Piamatsina", "Enrekang", "Bambam", "Port Vato", "Pentlatch", "Pathiya", "Western Highland Purepecha", "Purum", "Punan Merap", "Punan Aput", "Puelche", "Punan Merah", "Phuie", "Puinave", "Punan Tubu", "Puma", "Puoc", "Pulabu", "Puquina", "Puruborá", "Pashto", "Pushto", "Putoh", "Punu", "Puluwatese", "Puare", "Purisimeño", "Pawaia", "Panawa", "Gapapaiwa", "Patwin", "Molbog", "Paiwan", "Pwo Western Karen", "Powari", "Pwo Northern Karen", "Quetzaltepec Mixe", "Pye Krumen", "Fyam", "Poyanáwa", "Lengua de Señas del Paraguay", "Paraguayan Sign Language", "Puyuma", "Pyu (Myanmar)", "Pyen", "Pesse", "Pazeh", "Jejara Naga", "Para Naga", "Quapaw", "Huallaga Huánuco Quechua", "K'iche'", "Quiché", "Calderón Highland Quichua", "Quechua", "Lambayeque Quechua", "Chimborazo Highland Quichua", "South Bolivian Quechua", "Quileute", "Chachapoyas Quechua", "North Bolivian Quechua", "Sipacapense", "Quinault", "Southern Pastaza Quechua", "Quinqui", "Yanahuanca Pasco Quechua", "Santiago del Estero Quichua", "Sacapulteco", "Tena Lowland Quichua", "Yauyos Quechua", "Ayacucho Quechua", "Cusco Quechua", "Ambo-Pasco Quechua", "Cajamarca Quechua", "Eastern Apurímac Quechua", "Huamalíes-Dos de Mayo Huánuco Quechua", "Imbabura Highland Quichua", "Loja Highland Quichua", "Cajatambo North Lima Quechua", "Margos-Yarowilca-Lauricocha Quechua", "North Junín Quechua", "Napo Lowland Quechua", "Pacaraos Quechua", "San Martín Quechua", "Huaylla Wanca Quechua", "Queyu", "Northern Pastaza Quichua", "Corongo Ancash Quechua", "Classical Quechua", "Huaylas Ancash Quechua", "Kuman (Russia)", "Sihuas Ancash Quechua", "Kwalhioqua-Tlatskanai", "Chiquián Ancash Quechua", "Chincha Quechua", "Panao Huánuco Quechua", "Salasaca Highland Quichua", "Northern Conchucos Ancash Quechua", "Southern Conchucos Ancash Quechua", "Puno Quechua", "Qashqa'i", "Cañar Highland Quichua", "Southern Qiang", "Santa Ana de Tusi Pasco Quechua", "Arequipa-La Unión Quechua", "Jauja Wanca Quechua", "Quenya", "Quiripi", "Dungmali", "Camling", "Rasawa", "Rade", "Western Meohang", "Logooli", "Lulogooli", "Rabha", "Ramoaaina", "Rajasthani", "Tulu-Bohuai", "Ralte", "Canela", "Riantana", "Rao", "Rapanui", "Saam", "Cook Islands Maori", "Rarotongan", "Tegali", "Razajerdi", "Raute", "Sampang", "Rawang", "Rang", "Rapa", "Rahambuu", "Rumai Palaung", "Northern Bontok", "Miraya Bikol", "Barababaraba", "Réunion Creole French", "Rudbari", "Rerau", "Rembong", "Rejang Kayan", "Kara (Tanzania)", "Reli", "Rejang", "Rendille", "Remo", "Rengao", "Rer Bare", "Reshe", "Retta", "Reyesano", "Roria", "Romano-Greek", "Rangkas", "Romagnol", "Resígaro", "Southern Roglai", "Ringgou", "Rohingya", "Yahang", "Riang (India)", "Bribri Sign Language", "Tarifit", "Riang (Myanmar)", "Riang Lang", "Nyaturu", "Nungu", "Ribun", "Ritharrngu", "Riung", "Rajong", "Raji", "Rajbanshi", "Kraol", "Rikbaktsa", "Rakahanga-Manihiki", "Rakhine", "Marka", "Kamta", "Rangpuri", "Arakwal", "Rama", "Rembarrnga", "Carpathian Romani", "Traveller Danish", "Angloromani", "Kalo Finnish Romani", "Traveller Norwegian", "Murkim", "Lomavren", "Romkun", "Baltic Romani", "Roma", "Balkan Romani", "Sinte Romani", "Rempi", "Caló", "Romanian Sign Language", "Domari", "Tavringer Romani", "Romanova", "Welsh Romani", "Romam", "Vlax Romani", "Marma", "Brunca Sign Language", "Ruund", "Ronga", "Ranglong", "Roon", "Rongpo", "Nari Nari", "Rungwa", "Tae'", "Cacgia Roglai", "Rogo", "Ronji", "Rombo", "Northern Roglai", "Romansh", "Romblomanon", "Romany", "Moldavian", "Moldovan", "Romanian", "Rotokas", "Kriol", "Rongga", "Runga", "Dela-Oenale", "Repanbitip", "Rapting", "Ririo", "Moriori", "Waima", "Arritinngithigh", "Romano-Serbian", "Rusnak", "Ruthenian", "Russian Sign Language", "Miriwoong Sign Language", "Rwandan Sign Language", "Rishiwa", "Rungtu Chin", "Ratahan", "Rotuman", "Yurats", "Rathawi", "Gungu", "Ruuli", "Rusyn", "Luguru", "Roviana", "Ruga", "Rufiji", "Che", "Rundi", "Istro Romanian", "Aromanian", "Arumanian", "Macedo-Romanian", "Megleno Romanian", "Russian", "Rutul", "Lanas Lobu", "Mala (Nigeria)", "Ruma", "Rawo", "Rwa", "Ruwila", "Amba (Uganda)", "Rawa", "Marwari (India)", "Ngardi", "Garuwali", "Karuwali", "Northern Amami-Oshima", "Yaeyama", "Central Okinawan", "Rāziḥī", "Saba", "Buglere", "Meskwaki", "Sandawe", "Sabanê", "Safaliba", "Sango", "Yakut", "Sahu", "Sake", "Samaritan Aramaic", "Sanskrit", "Sause", "Samburu", "Saraveca", "Sasak", "Santali", "Saleman", "Saafi-Saafi", "Sawi", "Sa", "Saya", "Saurashtra", "Ngambay", "Simbo", "Kele (Papua New Guinea)", "Southern Samo", "Saliba", "Chabu", "Shabo", "Seget", "Sori-Harengan", "Seti", "Surbakhal", "Safwa", "Botolan Sambal", "Sagala", "Sindhi Bhil", "Sabüm", "Sangu (Tanzania)", "Sileibi", "Sembakung Murut", "Subiya", "Kimki", "Stod Bhoti", "Sabine", "Simba", "Seberuang", "Soli", "Sara Kaba", "Chut", "Dongxiang", "San Miguel Creole French", "Sanggau", "Sakachep", "Sri Lankan Creole Malay", "Sadri", "Shina", "Sicilian", "Scots", "Helambu Sherpa", "Hyolmo", "Sa'och", "North Slavey", "Southern Katang", "Shumcho", "Sheni", "Sha", "Sicel", "Shaetlan", "Toraja-Sa'dan", "Shabak", "Sassarese Sardinian", "Surubu", "Sarli", "Savi", "Southern Kurdish", "Suundi", "Sos Kundi", "Saudi Arabian Sign Language", "Gallurese Sardinian", "Bukar-Sadung Bidayuh", "Sherdukpen", "Semandang", "Oraon Sadri", "Sened", "Shuadit", "Sarudu", "Sibu Melanau", "Sallands", "Semai", "Shempire Senoufo", "Sechelt", "She shashishalhem", "Sedang", "Seneca", "Cebaara Senoufo", "Segeju", "Sena", "Seri", "Sene", "Sekani", "Selkup", "Nanerigé Sénoufo", "Suarmin", "Sìcìté Sénoufo", "Senara Sénoufo", "Serrano", "Koyraboro Senni Songhai", "Sentani", "Serui-Laut", "Nyarafolo Senoufo", "Sewa Bay", "Secoya", "Senthang Chin", "French Belgian Sign Language", "Langue des signes de Belgique Francophone", "Eastern Subanen", "Small Flowery Miao", "South African Sign Language", "Sehwi", "Old Irish (to 900)", "Mag-antsi Ayta", "Kipsigis", "Surigaonon", "Segai", "Swiss-German Sign Language", "Shughni", "Suga", "Surgujia", "Sangkong", "Singa", "Singpho", "Sangisari", "Samogitian", "Brokpake", "Salas", "Sebat Bet Gurage", "Sierra Leone Sign Language", "Sanglechi", "Sursurunga", "Shall-Zwall", "Ninam", "Sonde", "Kundal Shahi", "Sheko", "Shua", "Shoshoni", "Tachelhit", "Shatt", "Shilluk", "Shendu", "Shahrudi", "Shan", "Shanga", "Shipibo-Conibo", "Sala", "Shi", "Secwepemctsín", "Shuswap", "Shasta", "Chadian Arabic", "Shehri", "Shwai", "She", "Tachawit", "Syenara Senoufo", "Akkala Sami", "Sebop", "Sidamo", "Simaa", "Siamou", "Paasaal", "Sîshëë", "Zire", "Shom Peng", "Numbami", "Sikiana", "Tumulung Sisaala", "Mende (Papua New Guinea)", "Sinhala", "Sinhalese", "Sikkimese", "Sonia", "Siri", "Siuslaw", "Sinagen", "Sumariup", "Siwai", "Sumau", "Sivandi", "Siwi", "Epena", "Sajau Basap", "Shaojiang Chinese", "Kildin Sami", "Pite Sami", "Assangori", "Kemi Sami", "Miji", "Sajalong", "Mapun", "Sindarin", "Xibe", "Surjapuri", "Siar-Lak", "Senhaja De Srair", "Ter Sami", "Ume Sami", "Shawnee", "Skagit", "Saek", "Ma Manda", "Southern Sierra Miwok", "Seke (Vanuatu)", "Sakirabiá", "Sakalava Malagasy", "Sikule", "Sika", "Seke (Nepal)", "Kutong", "Kolibugan Subanon", "Seko Tengah", "Sekapan", "Sininkere", "Saraiki", "Seraiki", "Maia", "Sakata", "Sakao", "Skou", "Skepi Creole Dutch", "Seko Padang", "Sikaiana", "Sekar", "Sáliba", "Sissala", "Sholaga", "Swiss-Italian Sign Language", "Selungai Murut", "Southern Puget Sound Salish", "Lower Silesian", "Salumá", "Slovak", "Salt-Yui", "Pangutaran Sama", "Salinan", "Lamaholot", "Salar", "Singapore Sign Language", "Sila", "Selaru", "Slovenian", "Sialum", "Salampasu", "Selayar", "Ma'ya", "Southern Sami", "Simbari", "Som", "Northern Sami", "Auwe", "Simbali", "Samei", "Lule Sami", "Bolinao", "Central Sama", "Musasa", "Inari Sami", "Samoan", "Samaritan", "Samo", "Simeulue", "Skolt Sami", "Simte", "Somray", "Samvedi", "Sumbawa", "Samba", "Semnani", "Simeku", "Shona", "Sinaugoro", "Sindhi", "Bau Bidayuh", "Noon", "Sanga (Democratic Republic of Congo)", "Sensi", "Riverain Sango", "Soninke", "Sangil", "Southern Ma'di", "Siona", "Snohomish", "Siane", "Sangu (Gabon)", "Sihan", "Nahavaq", "South West Bay", "Senggi", "Viid", "Sa'ban", "Selee", "Sam", "Saniyo-Hiyewe", "Kou", "Thai Song", "Sobei", "So (Democratic Republic of Congo)", "Songoora", "Songomeno", "Sogdian", "Aka", "Sonha", "Soi", "Sokoro", "Solos", "Somali", "Songo", "Songe", "Kanasi", "Somrai", "Seeku", "Southern Sotho", "Southern Thai", "Sonsorol", "Sowanda", "Swo", "Miyobe", "Temi", "Castilian", "Spanish", "Sepa (Indonesia)", "Sapé", "Saep", "Sepa (Papua New Guinea)", "Sian", "Saponi", "Sengo", "Selepet", "Akukem", "Sanapaná", "Spokane", "Supyire Senoufo", "Loreto-Ucayali Spanish", "Saparua", "Saposa", "Spiti Bhoti", "Sapuan", "Kosli", "Sambalpuri", "South Picene", "Sabaot", "Shama-Sambuga", "Shau", "Albanian", "Albanian Sign Language", "Suma", "Susquehannock", "Sorkhei", "Sou", "Siculo Arabic", "Sri Lankan Sign Language", "Soqotri", "Sḵwx̱wú7mesh sníchim", "Squamish", "Kufr Qassem Sign Language (KQSL)", "Saruga", "Sora", "Logudorese Sardinian", "Sardinian", "Sara", "Nafi", "Sulod", "Sarikoli", "Siriano", "Serudung Murut", "Isirawa", "Saramaccan", "Sranan Tongo", "Campidanese Sardinian", "Serbian", "Sirionó", "Serer", "Sarsi", "Tsuut'ina", "Sauri", "Suruí", "Southern Sorsoganon", "Serua", "Sirmauri", "Sera", "Shahmirzadi", "Southern Sama", "Suba-Simbiti", "Siroi", "Balangingi", "Bangingih Sama", "Thao", "Seimat", "Shihhi Arabic", "Sansi", "Sausi", "Sunam", "Western Sisaala", "Semnam", "Waata", "Sissano", "Spanish Sign Language", "So'a", "Swiss-French Sign Language", "Sô", "Sinasina", "Susuami", "Shark Bay", "Swati", "Samberigi", "Saho", "Sengseng", "Settla", "Northern Subanen", "Sentinel", "Liana-Seti", "Seta", "Trieng", "Shelta", "Bulo Stieng", "Matya Samo", "Arammba", "Stellingwerfs", "Setaman", "Owa", "Stoney", "Southeastern Tepehuan", "Saterfriesisch", "Straits Salish", "Shumashti", "Budeh Stieng", "Samtao", "Silt'e", "Satawalese", "Siberian Tatar", "Sulka", "Suku", "Western Subanon", "Suena", "Suganga", "Suki", "Shubi", "Sukuma", "Sundanese", "Bouni", "Suri", "Tirmaga-Chai Suri", "Mwaghavul", "Susu", "Subtiaba", "Puroik", "Sumbwa", "Sumerian", "Suyá", "Sunwar", "Svan", "Ulau-Suain", "Vincentian Creole English", "Serili", "Slovakian Sign Language", "Slavomolisano", "Savosavo", "Skalvian", "Swahili (macrolanguage)", "Maore Comorian", "Congo Swahili", "Swedish", "Sere", "Swabian", "Kiswahili", "Swahili (individual language)", "Sui", "Sira", "Malawi Sena", "Swedish Sign Language", "Samosa", "Sawknah", "Shanenawa", "Suau", "Sharwa", "Saweru", "Seluwasan", "Sawila", "Suwawa", "Shekhawati", "Sowa", "Suruahá", "Sarua", "Suba", "Sicanian", "Sighu", "Shixing", "Shuhi", "Southern Kalapuya", "Selian", "Samre", "Sangir", "Sorothaptic", "Saaroa", "Sasaru", "Upper Saxon", "Saxwe Gbe", "Siang", "Central Subanen", "Classical Syriac", "Seki", "Sukur", "Sylheti", "Maya Samo", "Senaya", "Suoy", "Syriac", "Sinyar", "Kagate", "Samay", "Al-Sayyid Bedouin Sign Language", "Semelai", "Ngalum", "Semaq Beri", "Seze", "Sengele", "Silesian", "Sula", "Suabo", "Solomon Islands Sign Language", "Isu (Fako Division)", "Isubu", "Sawai", "Sakizaya", "Lower Tanana", "Tabassaran", "Lowland Tarahumara", "Tause", "Tariana", "Tapirapé", "Tagoi", "Tahitian", "Eastern Tamang", "Tala", "Tal", "Tamil", "Tangale", "Yami", "Taabwa", "Tamasheq", "Central Tarahumara", "Tay Boi", "Tatar", "Upper Tanana", "Tatuyo", "Tai", "Tamki", "Atayal", "Tocho", "Aikanã", "Takia", "Kaki Ae", "Tanimbili", "Mandara", "North Tairora", "Dharawal", "Thurawal", "Gaam", "Tiang", "Calamian Tagbanwa", "Tboli", "Tagbu", "Barro Negro Tunebo", "Tawala", "Diebroud", "Taworta", "Tumtum", "Tanguat", "Tembo (Kitembo)", "Tubar", "Tobo", "Tagbanwa", "Kapin", "Tabaru", "Ditammari", "Ticuna", "Tanacross", "Datooga", "Tafi", "Southern Tutchone", "Malinaltepec Me'phaa", "Malinaltepec Tlapanec", "Tamagario", "Turks And Caicos Creole English", "Wára", "Tchitchege", "Taman (Myanmar)", "Tanahmerah", "Tichurong", "Taungyo", "Tawr Chin", "Kaiy", "Torres Strait Creole", "Yumplatok", "T'en", "Southeastern Tarahumara", "Tecpatlán Totonac", "Toda", "Tulu", "Thado Chin", "Tagdal", "Panchpargania", "Emberá-Tadó", "Tai Nüa", "Tiranige Diga Dogon", "Talieng", "Western Tamang", "Thulung", "Tomadino", "Tajio", "Tambas", "Sur", "Taruma", "Tondano", "Teme", "Tita", "Todrah", "Doutai", "Tetun Dili", "Toro", "Tandroy-Mahafaly Malagasy", "Tadyawan", "Temiar", "Tetete", "Terik", "Tepo Krumen", "Huehuetla Tepehua", "Teressa", "Teke-Tege", "Tehuelche", "Torricelli", "Ibali Teke", "Telugu", "Timne", "Tama (Colombia)", "Teso", "Tepecano", "Temein", "Tereno", "Tengger", "Tetum", "Soo", "Teor", "Tewa (USA)", "Tennet", "Tulishi", "Tetserret", "Tofin Gbe", "Tanaina", "Tefaro", "Teribe", "Ternate", "Sagalla", "Tobilung", "Tigak", "Ciwogai", "Eastern Gorkha Tamang", "Chalikha", "Tobagonian Creole English", "Lawunuia", "Tagin", "Tajik", "Tagalog", "Tandaganon", "Sudest", "Tangoa", "Tring", "Tareng", "Nume", "Central Tagbanwa", "Tanggu", "Tingui-Boto", "Tagwana Senoufo", "Tagish", "Togoyo", "Tagalaka", "Thai", "Kuuk Thaayorre", "Thayore", "Chitwania Tharu", "Thangmi", "Northern Tarahumara", "Tai Long", "Kitharaka", "Tharaka", "Dangaura Tharu", "Aheu", "Thachanadan", "Nłeʔkepmxcín", "Thompson", "Thompson River Salish", "Kochila Tharu", "Rana Tharu", "Thakali", "Tahltan", "Tāłtān", "Thuri", "Tahaggart Tamahaq", "Tha", "Tayart Tamajeq", "Tidikelt Tamazight", "Tira", "Tifal", "Tigre", "Timugon Murut", "Tiene", "Tilung", "Tikar", "Tillamook", "Timbe", "Tindi", "Teop", "Trimuris", "Tiéfo", "Tigrinya", "Masadiit Itneg", "Tinigua", "Adasen", "Tiv", "Tiwi", "Southern Tiwa", "Tiruray", "Tai Hongjin", "Tajuasohn", "Tunjung", "Northern Tujia", "Tjungundji", "Tai Laing", "Timucua", "Tonjon", "Temacine Tamazight", "Tjupany", "Southern Tujia", "Tjurruru", "Djabwurrung", "Truká", "Buksa", "Tukudede", "Takwane", "Tukumanféd", "Tesaka Malagasy", "Tokelau", "Takelma", "Toku-No-Shima", "Tikopia", "Tee", "Tsakhur", "Takestani", "Kathoriya Tharu", "Upper Necaxa Totonac", "Mur Pano", "Teanu", "Tangko", "Takua", "Southwestern Tepehuan", "Tobelo", "Yecuatla Totonac", "Talaud", "Telefol", "Tofanma", "Klingon", "tlhIngan Hol", "Tlingit", "Talinga-Bwisi", "Taloki", "Tetela", "Tolomako", "Talondo'", "Talodi", "Filomena Mata-Coahuitlán Totonac", "Tai Loi", "Talise", "Tambotalo", "Sou Nama", "Teluti", "Tulehu", "Taliabu", "Khehek", "Talysh", "Tama (Chad)", "Avava", "Katbol", "Tumak", "Haruai", "Tremembé", "Toba-Maskoy", "Ternateño", "Tamashek", "Tutuba", "Samarokena", "Tamnim Citak", "Tai Thanh", "Taman (Indonesia)", "Temoq", "Tumleo", "Jewish Babylonian Aramaic (ca. 200-1200 CE)", "Tima", "Tasmate", "Iau", "Tembo (Motembo)", "Temuan", "Tami", "Tamanaku", "Tacana", "Western Tunebo", "Tanimuca-Retuarã", "Angosturas Tunebo", "Tobanga", "Maiani", "Tandia", "Kwamera", "Lenakel", "Tabla", "North Tanna", "Toromono", "Whitesands", "Taino", "Ménik", "Tenis", "Tontemboan", "Tay Khang", "Tangchangya", "Tonsawang", "Tanema", "Tongwe", "Ten'edn", "Toba", "Coyutla Totonac", "Toma", "Gizrra", "Tonga (Nyasa)", "Gitonga", "Tonga (Zambia)", "Tojolabal", "Toki Pona", "Tolowa", "Tombulu", "Tonga (Tonga Islands)", "Xicotepec De Juárez Totonac", "Papantla Totonac", "Toposa", "Togbo-Vara Banda", "Highland Totonac", "Tho", "Upper Taromi", "Jemez", "Tobian", "Topoiyo", "To", "Taupota", "Azoyú Me'phaa", "Azoyú Tlapanec", "Tippera", "Tarpia", "Kula", "Tok Pisin", "Tapieté", "Tupinikin", "Tlacoapa Me'phaa", "Tlacoapa Tlapanec", "Tampulma", "Tupinambá", "Tai Pao", "Pisaflores Tepehua", "Tukpa", "Tuparí", "Tlachichilco Tepehua", "Tampuan", "Tanapag", "Acatepec Me'phaa", "Acatepec Tlapanec", "Trumai", "Tinputz", "Tembé", "Lehali", "Turumsa", "Tenino", "Toaripi", "Tomoip", "Tunni", "Torona", "Western Totonac", "Touo", "Tonkawa", "Tirahi", "Terebu", "Copala Triqui", "Turi", "East Tarangan", "Trinidadian Creole English", "Lishán Didán", "Turaka", "Trió", "Toram", "Traveller Scottish", "Tregami", "Trinitario", "Tarao Naga", "Kok Borok", "San Martín Itunyoso Triqui", "Taushiro", "Chicahuaxtla Triqui", "Tunggare", "Surayt", "Turoyo", "Sediq", "Seediq", "Taroko", "Torwali", "Tringgus-Sembaan Bidayuh", "Turung", "Torá", "Tsaangi", "Tsamai", "Tswa", "Tsakonian", "Tunisian Sign Language", "Tausug", "Tsuvan", "Tsimshian", "Tshangla", "Tseku", "Ts'ün-Lao", "Türk İşaret Dili", "Turkish Sign Language", "Tswana", "Tsonga", "Northern Toussian", "Thai Sign Language", "Akei", "Taiwan Sign Language", "Tondi Songway Kiini", "Tsou", "Tsogo", "Tsishingini", "Mubami", "Tebul Sign Language", "Purepecha", "Tutelo", "Gaa", "Tektiteko", "Tauade", "Bwanabwana", "Tuotomb", "Tutong", "Upper Ta'oih", "Tobati", "Tooro", "Totoro", "Totela", "Northern Tutchone", "Towei", "Lower Ta'oih", "Tombelala", "Tawallammat Tamajaq", "Tera", "Northeastern Thai", "Muslim Tat", "Torau", "Titan", "Long Wat", "Sikaritai", "Tsum", "Wiarumus", "Tübatulabal", "Mutu", "Tuxá", "Tuyuca", "Central Tunebo", "Tunia", "Taulil", "Tupuri", "Tugutil", "Turkmen", "Tula", "Tumbuka", "Tunica", "Tucano", "Tedaga", "Turkish", "Tuscarora", "Tututni", "Turkana", "Tuxináwa", "Tugen", "Turka", "Vaghua", "Tsuvadi", "Te'un", "Batavian Portuguese Creole", "Mardijker Creole", "Tugunese", "Tulai", "Southeast Ambrym", "Tuvalu", "Tela-Masbuar", "Tavoyan", "Tidore", "Taveta", "Tutsa Naga", "Tunen", "Sedoa", "Taivoan", "Timor Pidgin", "Twana", "Western Tawbuid", "Teshenawa", "Twents", "Tewa (Indonesia)", "Northern Tiwa", "Tereweng", "Tai Dón", "Twi", "Tawara", "Tawang Monpa", "Twendi", "Tswapong", "Ere", "Tasawaq", "Southwestern Tarahumara", "Turiwára", "Termanu", "Tuwari", "Tewe", "Tawoyan", "Tombonuo", "Tokharian B", "Tsetsaut", "Totoli", "Tangut", "Thracian", "Ikpeng", "Tarjumo", "Tomini", "West Tarangan", "Toto", "Tii", "Tartessian", "Tonsea", "Citak", "Kayapó", "Tatana", "Tanosy Malagasy", "Tauya", "Kyanga", "O'du", "Teke-Tsaayi", "Tai Do", "Tai Yo", "Thu Lao", "Kombai", "Thaypan", "Tai Daeng", "Tày Sa Pa", "Tày Tac", "Kua", "Tuvinian", "Teke-Tyee", "Tiyaa", "Tày", "Tanzanian Sign Language", "Tzeltal", "Tz'utujil", "Talossan", "Central Atlas Tamazight", "Tugun", "Tzotzil", "Tabriak", "Uamué", "Kuan", "Tairuma", "Ubang", "Ubi", "Buhi'non Bikol", "Ubir", "Umbu-Ungu", "Ubykh", "Uda", "Udihe", "Muduga", "Udi", "Ujir", "Wuzlam", "Udmurt", "Uduk", "Kioko", "Ufim", "Ugaritic", "Kuku-Ugbanh", "Ughele", "Kubachi", "Ugandan Sign Language", "Ugong", "Uruguayan Sign Language", "Uhami", "Damal", "Uighur", "Uyghur", "Uisai", "Iyive", "Tanjijili", "Kaburi", "Ukuriguma", "Ukhwejo", "Kui (India)", "Muak Sa-aak", "Ukrainian Sign Language", "Ukpe-Bayobiri", "Ukwa", "Ukrainian", "Kaapor Sign Language", "Urubú-Kaapor Sign Language", "Ukue", "Kuku", "Ukwuani-Aboh-Ndoni", "Kuuk-Yak", "Fungwa", "Ulukwumi", "Ulch", "Lule", "Afra", "Usku", "Ulithian", "Meriam Mir", "Ullatan", "Ulumanda'", "Unserdeutsch", "Uma' Lung", "Ulwa", "Buli", "Umatilla", "Umbundu", "Marrucinian", "Umbindhamu", "Morrobalama", "Umbuygamu", "Ukit", "Umon", "Makyan Naga", "Umotína", "Umpila", "Umbugarla", "Pendau", "Munsee", "North Watut", "Undetermined", "Uneme", "Ngarinyin", "Uni", "Enawené-Nawé", "Unami", "Kurnai", "Mundari", "Unubahe", "Munda", "Unde Kaili", "Kulon", "Umeda", "Uripiv-Wala-Rano-Atchin", "Urarina", "Kaapor", "Urubú-Kaapor", "Urningangg", "Urdu", "Uru", "Uradhi", "Urigina", "Urhobo", "Urim", "Urak Lawoi'", "Urali", "Urapmin", "Uruangnirin", "Ura (Papua New Guinea)", "Uru-Pa-In", "Lehalurup", "Löyöp", "Urat", "Urumi", "Uruava", "Sop", "Urimo", "Orya", "Uru-Eu-Wau-Wau", "Usarufa", "Ushojo", "Usui", "Usaghade", "Uspanteco", "us-Saare", "Uya", "Otank", "Ute-Southern Paiute", "ut-Hun", "Amba (Solomon Islands)", "Etulo", "Utu", "Urum", "Ura (Vanuatu)", "U", "Fagauvea", "West Uvean", "Uri", "Lote", "Kuku-Uwanh", "Doko-Uyanga", "Uzbek", "Northern Uzbek", "Southern Uzbek", "Vaagri Booli", "Vale", "Vafsi", "Vagla", "Varhadi-Nagpuri", "Vai", "Northwestern ǃKung", "Sekele", "Vasekele", "Vehes", "Vanimo", "Valman", "Vao", "Vaiphei", "Huarijio", "Vasavi", "Vanuma", "Varli", "Wayu", "Southeast Babar", "Southwestern Bontok", "Venetian", "Veddah", "Veluws", "Vemgo-Mabas", "Venda", "Ventureño", "Veps", "Mom Jango", "Vaghri", "Flemish Sign Language", "Vlaamse Gebarentaal", "Virgin Islands Creole English", "Vidunda", "Vietnamese", "Vili", "Viemo", "Vilela", "Vinza", "Vishavan", "Viti", "Iduna", "Bajjika", "Kariyarra", "Kujarge", "Kaur", "Kulisusu", "Kamakan", "Koro Nulu", "Kodeoha", "Korlai Creole Portuguese", "Tenggarong Kutai Malay", "Kurrama", "Koro Zuba", "Valpei", "Vlaams", "Martuyhunira", "Barbaram", "Juxtlahuaca Mixtec", "Mudu Koraga", "East Masela", "Mainfränkisch", "Lungalunga", "Maraghei", "Miwa", "Ixtayutla Mixtec", "Makhuwa-Shirima", "Malgana", "Mitlatongo Mixtec", "Soyaltepec Mazatec", "Soyaltepec Mixtec", "Marenje", "Moksela", "Muluridyi", "Valley Maidu", "Makhuwa", "Tamazola Mixtec", "Ayautla Mazatec", "Mazatlán Mazatec", "Lovono", "Vano", "Neve'ei", "Vinmavis", "Vunapu", "Volapük", "Voro", "Votic", "Vera'a", "Võro", "Varisi", "Banam Bay", "Burmbar", "Moldova Sign Language", "Venezuelan Sign Language", "Vedic Sanskrit", "Llengua de signes valenciana", "Valencian Sign Language", "Vitou", "Vumbu", "Vunjo", "Vute", "Awa (China)", "Walla Walla", "Wab", "Yote", "Wasco-Wishram", "Wamesa", "Wondama", "Walser", "Wakoná", "Wa'ema", "Watubela", "Wares", "Waffa", "Wolaitta", "Wolaytta", "Wampanoag", "Wan", "Wappo", "Wapishana", "Wagiman", "Waray (Philippines)", "Washo", "Kaninuwa", "Waurá", "Waka", "Waiwai", "Marangis", "Watam", "Wayana", "Wampur", "Warao", "Wabo", "Waritai", "Wara", "Wanda", "Vwanji", "Alagwa", "Waigali", "Wakhi", "Wa", "Warlpiri", "Waddar", "Wagdi", "West Bengal Sign Language", "Warnman", "Wajarri", "Woi", "Yanomámi", "Waci Gbe", "Wandji", "Wadaginam", "Wadjiginy", "Wadikali", "Wendat", "Wadjigu", "Wadjabangayi", "Wewaw", "Wè Western", "Wedau", "Wergaia", "Weh", "Kiunum", "Weme Gbe", "Wemale", "Westphalien", "Weri", "Cameroon Pidgin", "Perai", "Rawngtu Chin", "Wejewa", "Yafi", "Zorop", "Wagaya", "Wagawaga", "Wangganguru", "Wangkangurru", "Wahgi", "Waigeo", "Wirangu", "Warrgamay", "Manusela", "Sou Upaa", "North Wahgi", "Wahau Kenyah", "Wahau Kayan", "Southern Toussian", "Wichita", "Wik-Epa", "Wik-Keyangan", "Wik Ngathan", "Wik-Me'anha", "Minidien", "Wik-Iiyanh", "Wikalkan", "Wilawila", "Wik-Mungkan", "Ho-Chunk", "Wiraféd", "Wiru", "Vitu", "Wiyot", "Waja", "Warji", "Kw'adza", "Kumbaran", "Mo", "Wakde", "Kalanadi", "Keerray-Woorroong", "Kunduvadi", "Wakawaka", "Wangkayutyuru", "Walio", "Mwali Comorian", "Wolane", "Kunbarlang", "Welaun", "Waioli", "Wailaki", "Wali (Sudan)", "Middle Welsh", "Walloon", "Wolio", "Wailapa", "Wallisian", "Wuliwuli", "Wichí Lhamtés Vejoz", "Walak", "Wali (Ghana)", "Waling", "Mawa (Nigeria)", "Wambaya", "Wamas", "Mamaindé", "Wambule", "Western Minyag", "Waima'a", "Wamin", "Maiwa (Indonesia)", "Waamwang", "Wom (Papua New Guinea)", "Wambon", "Walmajarri", "Mwani", "Womo", "Mokati", "Wantoat", "Wandarang", "Waneci", "Wanggom", "Ndzwani Comorian", "Wanukaka", "Wanggamala", "Wunumara", "Wano", "Wanap", "Usan", "Wintu", "Waanyi", "Wanyi", "Kuwema", "Tyaraity", "Wè Northern", "Wogeo", "Wolani", "Woleaian", "Gambian Wolof", "Wogamusin", "Kamang", "Longto", "Wolof", "Wom (Nigeria)", "Wongo", "Manombai", "Woria", "Hanga Hundi", "Wawonii", "Weyto", "Maco", "Waluwarra", "Warluwara", "Gudjal", "Warungu", "Wiradjuri", "Wariyangga", "Garrwa", "Warlmanpa", "Warumungu", "Warnang", "Worrorra", "Waropen", "Wardaman", "Waris", "Waru", "Waruna", "Gugu Warra", "Wae Rana", "Merwari", "Waray (Australia)", "Warembori", "Adilabad Gondi", "Wusi", "Waskia", "Owenia", "Wasa", "Wasu", "Wotapuri-Katarqalai", "Matambwe", "Watiwa", "Wathawurrung", "Berta", "Watakataui", "Mewati", "Wotu", "Wikngenchera", "Wunambal", "Wudu", "Wutunhua", "Silimo", "Wumbvu", "Bungu", "Wurrugu", "Wutung", "Wu Chinese", "Wuvulu-Aua", "Wulna", "Wauyai", "Waama", "Wakabunga", "Dorig", "Wetamut", "Warrwa", "Wawa", "Waxianghua", "Wardandi", "Wangaaybuwan-Ngiyambaa", "Woiwurrung", "Wymysorys", "Wyandot", "Wayoró", "Western Fijian", "Andalusian Arabic", "Sambe", "Kachari", "Adai", "Aequian", "Aghwan", "Kaimbé", "Ararandewára", "Máku", "Kalmyk", "Oirat", "ǀXam", "Xamtanga", "Khao", "Apalachee", "Aquitanian", "Karami", "Kamas", "Katawixi", "Kauwera", "Xavánte", "Kawaiisu", "Kayan Mahakam", "Lower Burdekin", "Bactrian", "Bindal", "Bigambal", "Bunganditj", "Kombio", "Birrpayi", "Middle Breton", "Kenaboi", "Bolgarian", "Bibbulman", "Kambera", "Kambiwá", "Batjala", "Batyala", "Cumbric", "Camunic", "Celtiberian", "Cisalpine Gaulish", "Chemakum", "Chimakum", "Classical Armenian", "Comecrudo", "Cotoname", "Chorasmian", "Carian", "Classical Tibetan", "Curonian", "Chuvantsy", "Coahuilteco", "Cayuse", "Darkinyung", "Dacian", "Dharuk", "Edomite", "Kwandu", "Kaitag", "Malayic Dayak", "Eblan", "Hdi", "ǁXegwi", "Kelo", "Kembayan", "Epi-Olmec", "Xerénte", "Kesawai", "Xetá", "Keoru-Ahia", "Faliscan", "Galatian", "Gbin", "Gudang", "Gabrielino-Fernandeño", "Goreng", "Garingbal", "Galindan", "Dharumbal", "Guwinmal", "Garza", "Unggumi", "Guwa", "Harami", "Hunnic", "Hadrami", "Khetrani", "Middle Khmer (1400 to 1850 CE)", "Xhosa", "Hernican", "Hattic", "Hurrian", "Khua", "Iberian", "Xiri", "Illyrian", "Xinca", "Xiriâna", "Kisan", "Indus Valley Language", "Xipaya", "Minjungbal", "Jaitmatang", "Kalkoti", "Northern Nago", "Kho'ini", "Mendalam Kayan", "Kereho", "Khengkha", "Kagoro", "Kenyan Sign Language", "Kajali", "Kachok", "Kaco'", "Mainstream Kenyah", "Kayan River Kayan", "Kiorr", "Kabatei", "Koroni", "Xakriabá", "Kumbewaha", "Kantosi", "Kaamba", "Kgalagadi", "Kembra", "Karore", "Uma' Lasan", "Kurtokha", "Kamula", "Loup B", "Lycian", "Lydian", "Lemnian", "Ligurian (Ancient)", "Liburnian", "Alanic", "Loup A", "Lepontic", "Lusitanian", "Cuneiform Luwian", "Elymian", "Mushungulu", "Mbonga", "Makhuwa-Marrevone", "Mbudum", "Median", "Mingrelian", "Mengaka", "Kugu-Muminh", "Majera", "Ancient Macedonian", "Malaysian Sign Language", "Manado Malay", "Manichaean Middle Persian", "Morerebi", "Kuku-Mu'inh", "Kuku-Mangk", "Meroitic", "Moroccan Sign Language", "Matbat", "Kamu", "Antankarana Malagasy", "Tankarana Malagasy", "Tsimihety Malagasy", "Maden", "Salawati", "Mayaguduna", "Mori Bawah", "Ancient North Arabian", "Kanakanabu", "Middle Mongolian", "Kuanhua", "Ngarigu", "Ngoni (Tanzania)", "Nganakarti", "Ngumbarl", "Northern Kankanay", "Anglo-Norman", "Ngoni (Mozambique)", "Kangri", "Kanashi", "Narragansett", "Nukunul", "Nyiyaparli", "Kenzi", "Mattoki", "O'chi'chi'", "Kokoda", "Soga", "Kominimung", "Xokleng", "Komo (Sudan)", "Konkomba", "Xukurú", "Kopar", "Korubo", "Kowaki", "Pirriya", "Northeastern Tasmanian", "Pyemmairrener", "Pecheneg", "Oyster Bay Tasmanian", "Liberia Kpelle", "Nuenonne", "Southeast Tasmanian", "Phrygian", "North Midlands Tasmanian", "Tyerrenoterpanner", "Pictish", "Mpalitjanh", "Kulina Pano", "Port Sorell Tasmanian", "Pumpokol", "Kapinawá", "Pochutec", "Puyo-Paekche", "Mohegan-Pequot", "Parthian", "Pisidian", "Punthamara", "Punic", "Northern Tasmanian", "Tommeginne", "Northwestern Tasmanian", "Peerapper", "Southwestern Tasmanian", "Toogee", "Puyo", "Bruny Island Tasmanian", "Karakhanid", "Qatabanian", "Krahô", "Eastern Karaboro", "Gundungurra", "Kreye", "Minang", "Krikati-Timbira", "Armazic", "Arin", "Raetic", "Aranama-Tamique", "Marriammu", "Karawa", "Sabaean", "Sambal", "Scythian", "Sidetic", "Sempan", "Shamang", "Sio", "Subi", "South Slavey", "Kasem", "Sanga (Nigeria)", "Solano", "Silopi", "Makhuwa-Saka", "Sherpa", "Sanumá", "Sudovian", "Saisiyat", "Alcozauca Mixtec", "Chazumba Mixtec", "Katcha-Kadugli-Miri", "Diuxi-Tilantongo Mixtec", "Ketengban", "Transalpine Gaulish", "Yitha Yitha", "Sinicahua Mixtec", "San Juan Teita Mixtec", "Tijaltepec Mixtec", "Magdalena Peñasco Mixtec", "Northern Tlaxiaco Mixtec", "Tokharian A", "San Miguel Piedras Mixtec", "Tumshuqese", "Early Tripuri", "Sindihui Mixtec", "Tacahua Mixtec", "Cuyamecalco Mixtec", "Thawa", "Tawandê", "Yoloxochitl Mixtec", "Alu Kurumba", "Betta Kurumba", "Umiida", "Kunigami", "Jennu Kurumba", "Ngunawal", "Nunukul", "Umbrian", "Unggaranggu", "Kuo", "Upper Umpqua", "Urartian", "Kuthant", "Khwedam", "Kxoe", "Venetic", "Kamviri", "Vandalic", "Volscian", "Vestinian", "Kwaza", "Woccon", "Wadi Wadi", "Xwela Gbe", "Kwegu", "Wajuk", "Wangkumara", "Western Xwla Gbe", "Written Oirat", "Kwerba Mamberamo", "Wotjobaluk", "Wemba Wemba", "Boro (Ghana)", "Ke'o", "Minkin", "Koropó", "Tambora", "Yaygir", "Yandjibara", "Mayi-Yapi", "Mayi-Kulan", "Yalakalore", "Mayi-Thakurti", "Yorta Yorta", "Zhang-Zhung", "Zemgalian", "Ancient Zapotec", "Yaminahua", "Yuhup", "Pass Valley Yali", "Yagua", "Pumé", "Yaka (Democratic Republic of Congo)", "Yámana", "Yazgulyam", "Yagnobi", "Banda-Yangere", "Yakama", "Yalunka", "Yamba", "Mayangna", "Yao", "Yapese", "Yaqui", "Yabarana", "Nugunu (Cameroon)", "Yambeta", "Yuwana", "Yangben", "Yawalapití", "Yauma", "Agwagwune", "Lokaa", "Yala", "Yemba", "West Yugur", "Yakha", "Yamphu", "Hasha", "Bokha", "Yukuben", "Yaben", "Yabaâna", "Yabong", "Yawiyo", "Yaweyuha", "Chesu", "Lolopo", "Yucuna", "Chepya", "Yilan Creole", "Yanda", "Eastern Yiddish", "Yangum Dey", "Yidgha", "Yoidik", "Ravula", "Yeniche", "Yimas", "Yeni", "Yevanic", "Yela", "Tarok", "Nyankpa", "Yetfa", "Yerukula", "Yapunda", "Yeyi", "Malyangapa", "Yiningayi", "Yangum Gel", "Yagomi", "Gepo", "Yagaria", "Yolŋu Sign Language", "Yugul", "Yagwoia", "Baha Buyang", "Judeo-Iraqi Arabic", "Hlepho Phowa", "Yan-nhaŋu Sign Language", "Yinggarda", "Yiddish", "Ache", "Wusa Nasu", "Western Yiddish", "Yidiny", "Yindjibarndi", "Dongshanba Lalo", "Yindjilandji", "Yimchungru Naga", "Riang Lai", "Yinchia", "Pholo", "Miqie", "North Awyu", "Yis", "Eastern Lalu", "Awu", "Northern Nisu", "Axi Yi", "Azhe", "Yakan", "Northern Yukaghir", "Khamnigan Mongol", "Yoke", "Yakaikeke", "Khlula", "Kap", "Kua-nsi", "Iyasa", "Yasa", "Yekora", "Kathu", "Kuamasi", "Yakoma", "Yaul", "Yaleba", "Yele", "Yelogu", "Angguruk Yali", "Yil", "Limi", "Langnian Buyang", "Naluo Yi", "Yalarnnga", "Aribwaung", "Nyâlayu", "Nyelâyu", "Yambes", "Southern Muji", "Muda", "Yameo", "Yamongeri", "Mili", "Moji", "Makwe", "Iamalele", "Maay", "Sunum", "Yamna", "Yangum Mon", "Yamap", "Qila Muji", "Malasar", "Mysian", "Northern Muji", "Muzi", "Aluo", "Yamben", "Yandruwandha", "Lang'e", "Yango", "Naukan Yupik", "Yangulam", "Yana", "Yong", "Yendang", "Yansi", "Yahuna", "Yoba", "Yogad", "Yonaguni", "Yokuts", "Yombe", "Yongkom", "Yoruba", "Yotti", "Yoron", "Yoy", "Phala", "Labo Phowa", "Phola", "Phupha", "Phuma", "Ani Phowa", "Alo Phola", "Phupa", "Phuza", "Yerakai", "Yareba", "Yaouré", "Nenets", "Nhengatu", "Yirrk-Mel", "Yerong", "Yaroamë", "Yarsun", "Yarawata", "Yarluyandi", "Yassic", "Samatao", "Sonaga", "Yugoslavian Sign Language", "Myanmar Sign Language", "Sani", "Nisi (China)", "Southern Lolopo", "Sirenik Yupik", "Yessan-Mayo", "Sanie", "Talu", "Tanglang", "Thopho", "Yout Wam", "Yatay", "Yucatec Maya", "Yucateco", "Yugambal", "Yuchi", "Judeo-Tripolitanian Arabic", "Yue Chinese", "Havasupai-Walapai-Yavapai", "Yug", "Yurutí", "Karkar-Yuri", "Yuki", "Yulu", "Quechan", "Bena (Nigeria)", "Yukpa", "Yuqui", "Yurok", "Yopno", "Yau (Morobe Province)", "Southern Yukaghir", "East Yugur", "Yuracare", "Yawa", "Yavitero", "Kalou", "Yinhawangka", "Western Lalu", "Yawanawa", "Wuding-Luquan Yi", "Yawuru", "Central Lalo", "Xishanba Lalo", "Wumeng Nasu", "Yawarawarga", "Mayawali", "Yagara", "Yardliyawarra", "Yinwum", "Yuyu", "Yabula Yabula", "Yir Yoront", "Yau (Sandaun Province)", "Ayizi", "E'ma Buyang", "Zokhuo", "Sierra de Juárez Zapotec", "San Juan Guelavía Zapotec", "Western Tlacolula Valley Zapotec", "Ocotlán Zapotec", "Cajonos Zapotec", "Yareni Zapotec", "Ayoquesco Zapotec", "Zaghawa", "Zangwal", "Isthmus Zapotec", "Zaramo", "Zanaki", "Zauzou", "Miahuatlán Zapotec", "Ozolotepec Zapotec", "Zapotec", "Aloápam Zapotec", "Rincón Zapotec", "Santo Domingo Albarradas Zapotec", "Tabaa Zapotec", "Zangskari", "Yatzachi Zapotec", "Mitla Zapotec", "Xadani Zapotec", "Zaysete", "Zayse-Zergulla", "Zari", "Balaibalan", "Central Berawan", "East Berawan", "Bliss", "Blissymbolics", "Blissymbols", "Batui", "Bu (Bauchi State)", "West Berawan", "Coatecas Altas Zapotec", "Las Delicias Zapotec", "Central Hongshuihe Zhuang", "Ngazidja Comorian", "Zeeuws", "Zenag", "Eastern Hongshuihe Zhuang", "Zeem", "Zenaga", "Kinga", "Guibei Zhuang", "Standard Moroccan Tamazight", "Minz Zhuang", "Guibian Zhuang", "Magori", "Chuang", "Zhuang", "Zhaba", "Dai Zhuang", "Zhire", "Kurdish Sign Language", "Nong Zhuang", "Chinese", "Zhoa", "Zia", "Zimbabwe Sign Language", "Zimakani", "Zialo", "Mesme", "Zinza", "Zigula", "Zizilivakan", "Kaimbulawa", "Kadu", "Koguryo", "Khorezmian", "Karankawa", "Kanan", "Kott", "São Paulo Kaingáng", "Zakhring", "Kitan", "Kaurna", "Krevinian", "Khazar", "Zula", "Liujiang Zhuang", "Malay (individual language)", "Lianshan Zhuang", "Liuqian Zhuang", "Zul", "Manda (Australia)", "Zimba", "Margany", "Maridan", "Mangerr", "Mfinu", "Marti Ke", "Makolkol", "Negeri Sembilan Malay", "Maridjabin", "Mandandanyi", "Matngala", "Marimanindji", "Marramaninyshi", "Mbangwe", "Molo", "Mbuun", "Mituku", "Maranunggu", "Mbesa", "Maringarr", "Muruwari", "Mbariman-Gudhinma", "Mbo (Democratic Republic of Congo)", "Bomitaba", "Mariyedi", "Mbandja", "Zan Gula", "Zande (individual language)", "Mang", "Manangkari", "Mangas", "Copainalá Zoque", "Chimalapa Zoque", "Zou", "Asunción Mixtepec Zapotec", "Tabasco Zoque", "Rayón Zoque", "Francisco León Zoque", "Lachiguiri Zapotec", "Yautepec Zapotec", "Choapan Zapotec", "Southeastern Ixtlán Zapotec", "Petapa Zapotec", "San Pedro Quiatoni Zapotec", "Guevea De Humboldt Zapotec", "Totomachapan Zapotec", "Santa María Quiegolani Zapotec", "Quiavicuzas Zapotec", "Tlacolulita Zapotec", "Lachixío Zapotec", "Mixtepec Zapotec", "Santa Inés Yatzechi Zapotec", "Amatlán Zapotec", "El Alto Zapotec", "Zoogocho Zapotec", "Santiago Xanica Zapotec", "Coatlán Zapotec", "San Vicente Coatlán Zapotec", "Yalálag Zapotec", "Chichicapan Zapotec", "Zaniza Zapotec", "San Baltazar Loxicha Zapotec", "Mazaltepec Zapotec", "Texmelucan Zapotec", "Qiubei Zhuang", "Kara (Korea)", "Mirgan", "Zerenkel", "Záparo", "Zarphatic", "Mairasi", "Sarasira", "Kaskean", "Zambian Sign Language", "Standard Malay", "Southern Rincon Zapotec", "Sukurum", "Elotepec Zapotec", "Xanaguía Zapotec", "Lapaguía-Guivini Zapotec", "San Agustín Mixtepec Zapotec", "Santa Catarina Albarradas Zapotec", "Loxicha Zapotec", "Quioquitani-Quierí Zapotec", "Tilquiapan Zapotec", "Tejalapan Zapotec", "Güilá Zapotec", "Zaachila Zapotec", "Yatee Zapotec", "Tokano", "Zulu", "Kumzari", "Zuni", "Zumaya", "Zay", "No linguistic content", "Not applicable", "Yongbei Zhuang", "Yang Zhuang", "Youjiang Zhuang", "Yongnan Zhuang", "Zyphe Chin", "Dimili", "Dimli (macrolanguage)", "Kirdki", "Kirmanjki (macrolanguage)", "Zaza", "Zazaki", "Zuojiang Zhuang"]

arr_submission_content = {
    "title": {
        "order": 1,
        "description": "Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$. \n\n NEW: Many authors in the past cycles had papers desk rejected because they did not acknowledge a resubmission, or filled the responsible NLP checklist incorrectly, or made some mistake with other metadata. In July 2025 cycle we experiment with giving the authors two extra days to edit the metadata after the submission deadline (until July 30 EoD AoE). This is in parallel with the deadline for filling the mandatory author registration form that is also due at the same time. During this time some authors may receive warnings from us about potential problems in their submissions. All fields except the main paper pdf and the author list will remain editable. After that grace period the submission metadata is final and subject to the regular desk rejection rules (see https://aclrollingreview.org/authorchecklist for a list of common issues).",
        "value": {
            "param": {
                "type": "string",
                "regex": "^.{1,250}$"
            }
        }
    },
    "authors": {
        "order": 2,
        "value": {
            "param": {
                "type": "string[]",
                "regex": "[^;,\\n]+(,[^,\\n]+)*",
                "hidden": True
            }
        }
    },
    "authorids": {
        "order": 3,
        "description": "Search for the author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.\n\n NEW IN MAY 2025: ACL adopted a policy similar to CVPR 2025. All qualified authors are expected to sign up to review, and the highly irresponsible reviewers may become ineligible from committing their paper(s) to EMNLP or resubmitting in the next cycle. The submitting authors should (a) make sure that all other authors are aware of this policy, and (b) check that everybody on their team(s) submits their (meta-)reviews on time and in accordance with the guidelines. After submission, all authors must complete the author registration form by May 21 2025 EoD AoE at the latest. More details on the policy here: https://aclrollingreview.org/incentives2025 \n\n The registration form will be in the author console immediately after paper submission: https://openreview.net/group?id=aclweb.org/ACL/ARR/2025/May/Authors",
        "value": {
            "param": {
                "type": "profile{}",
                "regex": "^~\\S+$|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})"
            }
        }
    },
    "TLDR": {
        "order": 8,
        "description": "\"Too Long; Didn't Read\": a short sentence describing your paper",
        "value": {
            "param": {
                "fieldName": "TL;DR",
                "type": "string",
                "minLength": 1,
                "optional": True
            }
        }
    },
    "abstract": {
        "order": 9,
        "description": "Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 5000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "pdf": {
        "order": 10,
        "description": "Upload a PDF file that ends with .pdf.",
        "value": {
            "param": {
                "type": "file",
                "maxSize": 50,
                "extensions": [
                    "pdf"
                ]
            }
        }
    },
    "paper_type": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Long",
                    "Short"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Long or short. See the CFP for the requirements for long and short papers.",
        "order": 11
    },
    "research_area": {
        "value": {
            "param": {
                "input": "radio",
                "enum": arr_tracks,
                "optional": False,
                "type": "string"
            }
        },
        "description": "Research Areas / Tracks. Select the most relevant research area / track for your paper. This will be used to inform the reviewer and area chair assignment.",
        "order": 12
    },
    "research_area_keywords": {
        "order": 13,
        "description": "Area-specific keywords. Please provide a comma-separated list of keywords from this page: https://aclrollingreview.org/areas",
        "value": {
            "param": {
                "type": "string",
                "regex": "^.{1,250}$"
            }
        }
    },
    "contribution_types": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "Model analysis & interpretability",
                    "NLP engineering experiment",
                    "Reproduction study",
                    "Approaches to low-resource settings",
                    "Approaches to low-compute settings (efficiency)",
                    "Publicly available software and/or pre-trained models",
                    "Data resources",
                    "Data analysis",
                    "Position papers",
                    "Surveys",
                    "Theory"
                ],
                "optional": True,
                "type": "string[]"
            }
        },
        "description": "Which of the following types of contributions does your paper make? This will inform the reviewers and meta-reviewer about what to look for in your work.",
        "order": 14
    },
    "languages_studied": {
        "value": {
            "param": {
                "optional": False,
                "type": "string[]",
                "input": "select",
                "enum": iso_639_3_languages
            }
        },
        "description": "Please list the natural languages studied in your submission, separated by commas. This form supports the languages in ISO 639-3 standard (https://iso639-3.sil.org/)",
        "order": 15
    },
    "previous_URL": {
        "value": {
            "param": {
                "regex": r'^https:\/\/openreview\.net\/forum\?id=[A-Za-z0-9_-]+$',
                "optional": True,
                "type": "string",
                "mismatchError": "must be a valid link to an OpenReview submission with the exact format: https://openreview.net/forum?id=<paper_id> (without any additional parameters, no commas, and no multiple URLs)"
            }
        },
        "description": "[COMPULSORY IF THIS IS A RESUBMISSION]: Provide the URL of your previous submission to ACL Rolling Review (this URL will look like https://openreview.net/forum?id=<some string>). Make sure to only add the paper id and not other parameters after &. Submissions that do not acknowledge prior versions reviewed at ARR can be desk rejected (see ARR CFP: https://aclrollingreview.org/cfp#resubmission-policy).",
        "order": 16
    },
    "explanation_of_revisions_PDF": {
        "value": {
            "param": {
                "type": "file",
                "maxSize": 80,
                "extensions": [
                    "pdf"
                ],
                "optional": True
            }
        },
        "description": "[COMPULSORY IF THIS IS A RESUBMISSION]: Upload a single PDF describing how you have changed your paper in response to your previous round of reviews. Note: this should NOT be a printout of your comments from the in-cycle author response period. This should be a new document that maintains anonymity and describes changes since your last submission. If any changes to the author list were made in the resubmission, do NOT include this information here. You may optionally prepend this content to the main submission pdf, to increase its visibility for reviewers (in addition to the compulsory upload of the separate file in this field). See more details in the ARR CFP: https://aclrollingreview.org/cfp#resubmission-policy",
        "order": 17
    },
    "justification_for_author_changes": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "If there were any changes to the author list since the original submission, please justify it here. Do NOT include this information in the above explanation of revisions PDF, as this will be a breach of anonymity.",
        "order": 18
    },
    "reassignment_request_area_chair": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I want a different area chair for our submission",
                    "No, I want the same area chair from our previous submission (subject to their availability).",
                    "This is not a resubmission"
                ],
                "type": "string"
            }
        },
        "description": "Do you want your submission to go to a different area chair? If you want your submission to go to the same area chair and they are unavailable this cycle, you will be assigned a new area chair.",
        "order": 19
    },
    "reassignment_request_reviewers": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I want a different set of reviewers",
                    "No, I want the same set of reviewers from our previous submission (subject to their availability)",
                    "This is not a resubmission"
                ],
                "type": "string"
            }
        },
        "description": "Do you want your submission to go to a different set of reviewers? If you want your submission to go to the same set of reviewers and at least one are unavailable this cycle, you will be assigned new reviewers in their place.",
        "order": 20
    },
    "justification_for_not_keeping_action_editor_or_reviewers": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Please specify reason for any reassignment request. Reasons may include clear lack of expertise in the area or dismissing the work without any concrete comments regarding correctness of the results or argumentation, limited perceived impact of the methods or findings, lack of clarity in exposition, or other valid criticisms. It is up to the discretion of the area chairs or editors in chief regarding whether to heed these requests.",
        "order": 21
    },
    "software": {
        "value": {
            "param": {
                "type": "file",
                "maxSize": 200,
                "extensions": [
                    "tgz",
                    "zip"
                ],
                "optional": True
            }
        },
        "description": "Each ARR submission can be accompanied by one .tgz or .zip archive containing software (max. 200MB).",
        "order": 22
    },
    "data": {
        "value": {
            "param": {
                "type": "file",
                "maxSize": 50,
                "extensions": [
                    "tgz",
                    "zip"
                ],
                "optional": True
            }
        },
        "description": "Each ARR submission can be accompanied by one .tgz or .zip archive containing data (max. 200MB). Any anonymized concurrent submissions by the same authors, referenced within the paper, can also be provided in this field.",
        "order": 23
    },
    "preprint": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "yes",
                    "no"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Would the authors like ARR to release a public anonymous pre-print of the submission?",
        "order": 24
    },
    "preprint_status": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "There is a non-anonymous preprint (URL specified in the next question).",
                    "We plan to release a non-anonymous preprint in the next two months (i.e., during the reviewing process).",
                    "We are considering releasing a non-anonymous preprint in the next two months (i.e., during the reviewing process).",
                    "There is no non-anonymous preprint and we do not intend to release one. (this option is binding)"
                ],
                "type": "string"
            }
        },
        "description": "Is there are a publicly available non-anonymous preprints of this paper, or do you plan to release one? Note, all options for this question are permitted under the updated ACL preprint policy. We are collecting this information to help inform the review process. The last option is binding, i.e. you cannot change your mind later in the cycle. \n\n NB: this category is about the possibility of deanonymization, rather than any specific publication channel such as arXiv. So e.g. withdrawn publications from other conferences also count as preprints, as long as they reveal the authors' names.",
        "order": 25
    },
    "existing_preprints": {
        "value": {
            "param": {
                "regex": ".{1,1000}",
                "optional": True,
                "type": "string"
            }
        },
        "description": "If there are any publicly available non-anonymous preprints of this paper, please list them here (provide the URLs please).",
        "order": 26
    },
    "preferred_venue": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "AACL",
                    "ACL",
                    "EACL",
                    "EMNLP",
                    "NAACL",
                    "Another venue that accepts ARR reviews"
                ],
                "type": "string"
            }
        },
        "description": "If you have a venue that you are hoping to submit this paper to, please enter it here. You must enter the designated acronym from this list: https://aclrollingreview.org/dates. Note that entering a preferred venue is not a firm commitment to submit your paper to this venue, but it will help ARR and the venue chairs in planning, so we highly recommend filling in your current intentions. Please enter only your first choice.",
        "order": 27
    },
    "visa_needs": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "yes",
                    "no"
                ],
                "type": "string",
                "optional": False
            }
        },
        "description": "If this submission is successfully reviewed, committed and accepted to your target venue specified above, will the presenting author need a visa to attend the conference? This question is only to assist the program chairs with estimating the visa needs of the prospective participants.",
        "order": 28
    },
    "country_of_origin": {
        "value": {
            "param": {
                "type": "string",
                "maxLength": 2,
                "markdown": False,
                "input": "textarea",
                "optional": True
            },
        "description": "If this submission is successfully reviewed, committed and accepted to your target venue specified above, and the presenting author would need a visa to attend, what is the country of their origin? This question is only to assist the program chairs with estimating the visa needs of the prospective participants. Please specify the country with the two-letter country code, e.g. 'CN' for China (https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes)",
        "order": 29
        }
    },
    "consent_to_share_data": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "yes",
                    "no"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "I agree for the anonymized metadata associated with my submission to be included in a publicly available dataset. This dataset WILL include scores, anonymized paper and reviewer IDs that allow grouping the reviews by paper and by reviewer, as well as acceptance decisions and other numerical and categorical metadata. This dataset WILL NOT include any textual or uniquely attributable data like names, submission titles and texts, review texts, author responses, etc. Your decision to opt-in the data does not affect the reviewing of your submission in any way.",
        "order": 30
    },
    "consent_to_share_submission_details": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "On behalf of all authors, we agree to the terms above to share our submission details."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Upon submitting this paper, authors agree to allow us to share their submission details (such as title, author names, and potentially abstract) with program committees from other conference venues for the purpose of verifying compliance with submission requirements.",
        "order": 31
    },
    "author_submission_checklist": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "yes",
                    "no"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "I confirm that this submission adheres to ARR requirements.\n\n Note: to help the authors avoid desk rejections, we prepared a list of common submission problems to check for: https://aclrollingreview.org/authorchecklist \n\n NEW: Following ICML policy, any related concurrent work should be discussed in related work and enclosed in supplementary material. See the update on submission originality and thinly sliced contributions, with desk rejection penalties: https://aclrollingreview.org/cfp#originality",
        "order": 32
    },
    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": {
        "order": 33,
        "description": "Please read and decide whether to transfer the license to your blind submission draft and its associated peer reviewing data in the current and/or previous iterations of ARR.\n*** DISCLAIMER ***\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute your draft and associated peer reviews. In particular, we may include your draft with donated review texts and scores in research datasets. Please note, to attribute authors for their draft, the author names are explicitly listed along with the draft and its associated peer reviews. Only reviews for accepted papers will be eventually made publicly available. The reviewers have to agree to the release of the textual review data associated with your submission.\n\nThis Blind Submission License Agreement (\"Agreement\") is entered into between the Association for Computational Linguistics (\"ACL\") and the Authors listed in connection with Authors’ blind submission paper listed above (referred as \"Blind Submission Content\").\nIn exchange of adequate consideration, ACL and the Authors agree as follows:\n\nSection 1: Grant of License\nAfter the peer review process is concluded and upon acceptance of the paper, Authors grant ACL a worldwide, irrevocable, and royalty-free license to use the blind submission paper version and, if applicable, the associated amendment notes and author responses to reviewers’ inquiries  (referred as \"Content\"). The foregoing license grants ACL the right to reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Content, and to sub-license the Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\nNotwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Content, and that the Authors retain their respective ownership in and to the Content.\n\nSection 2: Permission to Publish Peer Reviewers Content\nAfter the peer review process is concluded and upon acceptance of the paper, Authors have the option to grant ACL permission to publish peer reviewers content associated with the Content, which may include text, review form\nscores and metadata, charts, graphics, spreadsheets, and any other materials developed by peer reviewers in connection with the peer review process.\n\nSection 3: Attribution and Public Access License\nA. The Parties agree that for purpose of administering the public access license, ACL will be\nidentified as the licensor of the Content with the following copyright notice:\n\nCopyright © 2023 administered by the Association for Computational Linguistics (ACL) on behalf of the authors and content contributors. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\n\nB. The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\nSection 4: Effective Date\nThe grant of license pursuant to Section 1 and permission to publish peer reviewers content pursuant to Section 2 becomes effective in the event Authors’ blind submission paper has passed through this ACL Rolling Review cycle's peer review process and the cycle has ended; the end of a cycle is marked by the fact that authors received both the assigned peer review reports and the final meta-review report for this submission.\n\nSection 5: Warranty\nAuthors represent and warrant that the Content is Authors’ original work and does not infringe on the proprietary rights of others. Authors further warrant that they have\nobtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\nSection 6: Legal Relationship\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\nBy selecting 'On behalf of all authors, I agree' below, I confirm that all Authors have agreed to the above terms and that I am authorized to execute this Agreement on their behalf. Optionally, if you wish to transfer the license to the peer reviewing and blind submission data of all previous versions of this paper submitted to ARR, please select 'On behalf of all authors, I agree for all previous versions of this submission'.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "On behalf of all authors, I agree",
                    "On behalf of all authors, I do not agree",
                    "On behalf of all authors, I agree for this and all previous versions of this submission"
                ],
                "input": "radio",
                "scroll": True,
                "optional": False
            }
        }
    },
   "checklist_separator": {
        "description": "---\n\n# The Responsible Research Checklist\n\nPlease see this [page](https://aclrollingreview.org/responsibleNLPresearch/) for advice on filling it in. Please note that inappropriate or missing answers to checklist questions can be grounds for DESK REJECTION. If your answer to a given question is 'yes' or 'no', rather than 'n/a', the 'elaboration' fields MUST be filled in.",
        readers: ["everyone"],
        "order": 34
    },
    "A1_potential_risks": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss any potential ethical, societal or environmental risks of your work? \n\nThis question and those that follow are from the Responsible Research Checklist, please see this page for advice on filling it in: https://aclrollingreview.org/responsibleNLPresearch/. Please note that inappropriate or missing answers to checklist questions can be grounds for DESK REJECTION. If your answer to a given question is 'yes' or 'no', rather than 'n/a', the 'elaboration' fields MUST be filled in.",
        "order": 35
    },
    "A1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number (we recommend placing such material in the 'Ethical Considerations' section that does not count towards page limit). For no, justify why not.",
        "order": 36
    },
    "B_use_or_create_scientific_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you use or create scientific artifacts? (e.g. code, datasets, models)",
        "order": 37
    },

    "B1_cite_creators_of_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you used existing scientific artifacts (code, data, models), did you cite the original creators?",
        "order": 38
    },
    "B1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 39
    },
    "B2_discuss_the_license_for_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you are releasing any artifacts building on prior artifacts or data, did you ensure that the original license and/or the rights of the original creators allow you to do so?",
        "order": 40
    },
    "B2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 41
    },
    "B3_data_contains_personally_identifying_info": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you are releasing any artifacts that could contain personally identifiable information (unless it is necessary for the research goals), did you discuss what steps were taken to mitigate this?",
        "order": 42
    },
    "B3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 43
    },
    "B4_data_contains_offensive_content": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you are releasing any artifacts that could contain objectionable content (e.g. offensive text, deepfakes, propaganda, unless it is necessary for the research goals), did you discuss what steps were taken to mitigate this?",
        "order": 44
    },
    "B4_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 43
    },
    "B5_documentation_of_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you provide documentation of the artifacts, e.g., coverage of domains, languages, and linguistic phenomena, demographic groups represented, etc.?",
        "order": 45
    },
    "B5_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 46
    },
    "B6_statistics_for_data": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report relevant statistics like the number of examples, details of train/test/dev splits, etc. for the data that you used/created?",
        "order": 47
    },
    "B6_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 48
    },
    "C_computational_experiments": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Is the main goal of this work to present results of computational experiments?",
        "order": 49
    },
    "C1_model_size_and_budget": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report the number of parameters in the models used, the total computational budget (e.g., GPU hours), and computing infrastructure used?",
        "order": 50
    },
    "C1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 51
    },
    "C2_experimental_setup_and_hyperparameters": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss the experimental setup, e.g. hyperparameter search, best-found hyperparameter values, number and selection of in-context examples?",
        "order": 52
    },
    "C2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 53
    },
    "C3_descriptive_statistics": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report descriptive statistics about your results (e.g., error bars around results, summary statistics from sets of experiments), and is it transparent whether you are reporting the max, mean, etc. or just a single run?",
        "order": 54
    },
    "C3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 55
    },
    "C4_parameters_for_packages": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you used existing packages (e.g., for preprocessing, for normalization, or for evaluation, such as NLTK, ROUGE, LM Evaluation Harness etc.), did you report the implementation, model, and parameter settings used?",
        "order": 56
    },
    "C4_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 57
    },
    "D_human_subjects_including_annotators": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you use human annotators (e.g., crowdworkers) or research with human participants?",
        "order": 58
    },
    "D1_instructions_given_to_participants": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report the full text of instructions given to participants, including e.g., screenshots, disclaimers of any risks to participants or annotators, etc.?",
        "order": 59
    },
    "D1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 60
    },
    "D2_recruitment_and_payment": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report information about how you recruited (e.g., crowdsourcing platform, students), collected consent from, and paid the participants? If applicable, did you discuss if the payment was adequate and participation free of coercion? (except the case where all annotations were provided by the authors of the submission)",
        "order": 61
    },
    "D2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 62
    },
    "D3_data_consent": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss whether and how consent was obtained from people whose data you're using/curating? (except the case where all annotations were provided by the authors of the submission)",
        "order": 63
    },
    "D3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 64
    },
    "D4_ethics_review_board_approval": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Was the data collection protocol approved (or determined exempt) by an ethics review board in the relevant institutional framework?",
        "order": 65
    },
    "D4_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 66
    },
    "D5_annotator_population": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report the relevant demographic and geographic characteristics of the annotator population that is the source of the data? (except the case where all annotations were provided by the authors of the submission)",
        "order": 67
    },
    "D5_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number. For no, justify why not.",
        "order": 68
    },    
    "E_ai_assistants_in_research_or_writing": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you use AI assistants (e.g., ChatGPT, Copilot) in your research, coding, or writing?",
        "order": 69
    },
    "E1_information_about_use_of_ai_assistants": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you used any AI assistants for any substantive assistance in writing (beyond grammar or spellchecking), coding (beyond IDE autocomplete), or literature search, did you include information about your use? This question does NOT apply to LLMs used as research objects.",
        "order": 70
    },
    "E1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "[COMPULSORY IF YES/NO] For yes, provide a section number, or include your elaboration directly in the checklist response. For no, justify why not.",
        "order": 71
    }
}



arr_author_consent_content = {
    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": {
        "order": 1,
        "description": "Association for Computational Linguistics - Blind Submission License Agreement\n\nPlease read and decide whether to transfer the license to your blind submission draft and its associated peer reviewing data in the current and/or previous iterations of ARR.\n*** DISCLAIMER ***\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute your draft and associated peer reviews. In particular, we may include your draft with donated review texts and scores in research datasets. Please note, to attribute authors for their draft, the author names are explicitly listed along with the draft and its associated peer reviews. Only reviews for accepted papers will be made publicly available directly after acceptance. For papers that are not accepted, the donated data will be kept confidential for the two years following the submission date and then released to the public. The reviewers have to agree to the release of the textual review data associated with your submission.\n\nName of the ACL Conference: ACL Rolling Review\n\nBlind Submission Title: as stated above\n\nAuthors' names: as stated above\n\nThis Blind Submission License Agreement (“Agreement”) is entered into between the Association for Computational Linguistics (“ACL”) and the Authors listed in connection with Authors’ blind submission paper listed above (referred as “Blind Submission Content”).\n\nIn exchange of adequate consideration, ACL and the Authors agree as follows:\n\nSection 1: Grant of License\nAfter the peer review process is concluded, Authors grant ACL a worldwide, irrevocable, and royalty-free license to use the blind submission paper version and, if applicable, the associated amendment notes and author responses to reviewers’ inquiries  (referred as “Content”). The foregoing license grants ACL the right to reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Content, and to sub-license the Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\nNotwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Content, and that the Authors retain their respective ownership in and to the Content.\n\nSection 2: Permission to Publish Peer Reviewers' Content\nAfter the peer review process is concluded, Authors have the option to grant ACL permission to publish peer reviewers content associated with the Content, which may include text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials developed by peer reviewers in connection with the peer review process.\n\nSection 3: Attribution and Public Access License\nA. The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice:\n\nCopyright © 2024 administered by the Association for Computational Linguistics (ACL) on behalf of the authors and content contributors. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\n\nB. The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\nSection 4: Effective Date\nThe grant of license pursuant to Section 1 and permission to publish peer reviewers content pursuant to Section 2 becomes effective in the event Authors’ blind submission paper is accepted for publication by ACL, or upon the passing of two years from the date of submission, whichever event occurs first. If the blind submission paper is not accepted, the Content and associated peer reviewers content will remain confidential until the two years from the date of submission have passed.\n\nSection 5: Warranty\nAuthors represent and warrant that the Content is Authors’ original work and does not infringe on the proprietary rights of others. Authors further warrant that they have obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\nSection 6: Legal Relationship\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\nAgreement\n\nBy selecting 'On behalf of all authors, I agree' below, I confirm that all Authors have agreed to the above terms and that I am authorized to execute this Agreement on their behalf. Optionally, if you wish to transfer the license to the peer reviewing and blind submission data of all previous versions of this paper submitted to ARR, please select 'On behalf of all authors, I agree for all previous versions of this submission'.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "On behalf of all authors, I agree",
                    "On behalf of all authors, I do not agree",
                    "On behalf of all authors, I agree for this and all previous versions of this submission"
                ],
                "input": "radio",
                "scroll": True,
                "optional": False
            }
        }
    }
}

hide_fields = [
    "TLDR",
    "justification_for_author_changes",
    "preprint",
    "existing_preprints",
    "preferred_venue",
    "consent_to_share_data",
    "consent_to_share_submission_details",
    "existing_preprints",
    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement",
    "preprint_status",
]

hide_fields_from_public = [
    "software",
    "data",
    "previous_URL",
    "explanation_of_revisions_PDF",
    "reassignment_request_area_chair",
    "reassignment_request_reviewers",
    "justification_for_not_keeping_action_editor_or_reviewers",
    "author_submission_checklist",
    "A1_limitations_section",
    "A2_potential_risks",
    "A2_elaboration",
    "A3_abstract_and_introduction_summarize_claims",
    "A3_elaboration",
    "B_use_or_create_scientific_artifacts",
    "B1_cite_creators_of_artifacts",
    "B1_elaboration",
    "B2_discuss_the_license_for_artifacts",
    "B2_elaboration",
    "B3_artifact_use_consistent_with_intended_use",
    "B3_elaboration",
    "B4_data_contains_personally_identifying_info_or_offensive_content",
    "B4_elaboration",
    "B5_documentation_of_artifacts",
    "B5_elaboration",
    "B6_statistics_for_data",
    "B6_elaboration",
    "C_computational_experiments",
    "C1_model_size_and_budget",
    "C1_elaboration",
    "C2_experimental_setup_and_hyperparameters",
    "C2_elaboration",
    "C3_descriptive_statistics",
    "C3_elaboration",
    "C4_parameters_for_packages",
    "C4_elaboration",
    "D_human_subjects_including_annotators",
    "D1_instructions_given_to_participants",
    "D1_elaboration",
    "D2_recruitment_and_payment",
    "D2_elaboration",
    "D3_data_consent",
    "D3_elaboration",
    "D4_ethics_review_board_approval",
    "D4_elaboration",
    "D5_characteristics_of_annotators",
    "D5_elaboration",
    "E_ai_assistants_in_research_or_writing",
    "E1_information_about_use_of_ai_assistants",
    "E1_elaboration",
]

arr_official_review_content = {
    "paper_summary": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 1,
        "description": " Please make sure that you are familiar with the latest version of ARR reviewer guidelines, especially with respect to AI assistance: https://aclrollingreview.org/reviewerguidelines#-task-3-write-a-strong-review \n\n Note that the reviewer names are anonymous to the authors, but are VISIBLE to the senior researchers serving as area chairs, senior chairs and program chairs. Authors will have an opportunity to submit issue reports for problematic reviews, to be considered by area chairs (https://aclrollingreview.org/authors#step2.2). Highly problematic reviews may result in penalties, and great reviews may result in awards (https://aclrollingreview.org/incentives2025). ARR is currently experimenting with a review assistant tool, which you may optionally use to check for some common review issues (https://revas.mbzuai.ac.ae/). \n\n\n\n Describe what this paper is about. This should help the program and area chairs to understand the topic of the work and highlight any possible misunderstandings. Maximum length 20000 characters."
    },
    "summary_of_strengths": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 3,
        "description": "What are the major reasons to publish this paper at a selective *ACL venue? These could include novel and useful methodology, insightful empirical results or theoretical analysis, clear organization of related literature, or any other reason why interested readers of *ACL papers may find the paper useful. Maximum length 20000 characters."
    },
    "summary_of_weaknesses": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 4,
        "description": "What are the concerns that you have about the paper that would cause you to favor prioritizing other high-quality papers that are also under consideration for publication? These could include concerns about correctness of the results or argumentation, limited perceived impact of the methods or findings (note that impact can be significant both in broad or in narrow sub-fields), lack of clarity in exposition, or any other reason why interested readers of *ACL papers may gain less from this paper than they would from other papers under consideration. Where possible, please number your concerns so authors may respond to them individually, and mark the points where a convincing response could lead you to reconsider your assessment. Maximum length 20000 characters. \n\n If the paper is a resubmission, please discuss whether previous feedback has been adequately addressed (revision notes should be in the submission under 'explanation of revisions PDF')."
    },
    "comments_suggestions_and_typos": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 5,
        "description": "If you have any comments to the authors about how they may improve their paper, other than addressing the concerns above, please list them here.\n Maximum length 20000 characters."
    },
    "confidence": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = Positive that my evaluation is correct. I read the paper very carefully and am familiar with related work."
                    },
                    {
                        "value": 4,
                        "description": "4 = Quite sure. I tried to check the important points carefully. It's unlikely, though conceivable, that I missed something that should affect my ratings."
                    },
                    {
                        "value": 3,
                        "description": "3 =  Pretty sure, but there's a chance I missed something. Although I have a good feel for this area in general, I did not carefully check the paper's details, e.g., the math or experimental design."
                    },
                    {
                        "value": 2,
                        "description": "2 =  Willing to defend my evaluation, but it is fairly likely that I missed some details, didn't understand some central points, or can't be sure about the novelty of the work."
                    },
                    {
                        "value": 1,
                        "description": "1 = Not my area, or paper is very hard to understand. My evaluation is just an educated guess."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 6
    },
    "soundness": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5.0,
                        "description": "5 = Excellent: This study is one of the most thorough I have seen, given its type."
                    },
                    {
                        "value": 4.5,
                        "description": "4.5 "
                    },
                    {
                        "value": 4.0,
                        "description": "4 = Strong: This study provides sufficient support for all of its claims. Some extra experiments could be nice, but not essential."
                    },
                    {
                        "value": 3.5,
                        "description": "3.5 "
                    },
                    {
                        "value": 3.0,
                        "description": "3 = Acceptable: This study provides sufficient support for its main claims. Some minor points may need extra support or details."
                    },
                    {
                        "value": 2.5,
                        "description": "2.5 "
                    },
                    {
                        "value": 2.0,
                        "description": "2 = Poor: Some of the main claims are not sufficiently supported. There are major technical/methodological problems."
                    },
                    {
                        "value": 1.5,
                        "description": "1.5 "
                    },
                    {
                        "value": 1.0,
                        "description": "1 = Major Issues: This study is not yet sufficiently thorough to warrant publication or is not relevant to ACL."
                    }
                ],
                "optional": False,
                "type": "float"
            }
        },
        "order": 7,
        "description": "Given that this is a short/long paper, is it sufficiently sound and thorough? Does it clearly state scientific claims and provide adequate support for them? For experimental papers: consider the depth and/or breadth of the research questions investigated, technical soundness of experiments, methodological validity of evaluation. For position papers, surveys: consider whether the current state of the field is adequately represented and main counter-arguments acknowledged. For resource papers: consider the data collection methodology, resulting data & the difference from existing resources are described in sufficient detail."
    },
	"excitement": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5.0,
                        "description": "5 = Highly Exciting: I would recommend this paper to others and/or attend its presentation in a conference."
                    },
                    {
                        "value": 4.5,
                        "description": "4.5"
                    },
                    {
                        "value": 4.0,
                        "description": "4 = Exciting: I would mention this paper to others and/or make an effort to attend its presentation in a conference."
                    },
                    {
                        "value": 3.5,
                        "description": "3.5"
                    },
                    {
                        "value": 3.0,
                        "description": "3 = Interesting: I might mention some points of this paper to others and/or attend its presentation in a conference if there's time."
                    },
                    {
                        "value": 2.5,
                        "description": "2.5"
                    },
                    {
                        "value": 2.0,
                        "description": "2 = Potentially Interesting: this paper does not resonate with me, but it might with others in the *ACL community."
                    },
                    {
                        "value": 1.5,
                        "description": "1.5"
                    },
                    {
                        "value": 1.0,
                        "description": "1 = Not Exciting: this paper does not resonate with me, and I don't think it would with others in the *ACL community (e.g. it is in no way related to computational processing of language)."
                    }
                ],
                "optional": False,
                "type": "float"
            }
        },
        "order": 7,
        "description": "How exciting is this paper for you? Excitement is SUBJECTIVE, and does not necessarily follow what is popular in the field. We may perceive papers as transformational/innovative/surprising, e.g. because they present conceptual breakthroughs or evidence challenging common assumptions/methods/datasets/metrics. We may be excited about the possible impact of the paper on some community (not necessarily large or our own), e.g. lowering barriers, reducing costs, enabling new applications. We may be excited for papers that are relevant, inspiring, or useful for our own research. These factors may combine in different ways for different reviewers."
    },    
    "overall_assessment": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5.0,
                        "description": "5 = Consider for Award: I think this paper could be considered for an outstanding paper award at an *ACL conference (up to top 2.5% papers)."
                    },
                    {
                        "value": 4.5,
                        "description": "4.5 = Borderline Award"
                    },
                    {
                        "value": 4.0,
                        "description": "4 = Conference: I think this paper could be accepted to an *ACL conference."
                    },
                    {
                        "value": 3.5,
                        "description": "3.5 = Borderline Conference"
                    },
                    {
                        "value": 3.0,
                        "description": "3 = Findings: I think this paper could be accepted to the Findings of the ACL."
                    },
                    {
                        "value": 2.5,
                        "description": "2.5 = Borderline Findings"
                    },
                    {
                        "value": 2.0,
                        "description": "2 = Resubmit next cycle: I think this paper needs substantial revisions that can be completed by the next ARR cycle."
                    },
                    {
                        "value": 1.5,
                        "description": "1.5 = Resubmit after next cycle: I think this paper needs substantial revisions that cannot be completed by the next ARR cycle."
                    },
                    {
                        "value": 1.0,
                        "description": "1 = Do not resubmit: this paper has to be fully redone, or it is not relevant to the *ACL community (e.g. it is in no way related to computational processing of language)."
                    }
                ],
                "optional": False,
                "type": "float"
            }
        },
        "order": 9,
        "description": "If this paper was committed to an *ACL conference, do you believe it should be accepted? If you recommend conference, Findings and or even award consideration, you can still suggest minor revisions (e.g. typos, non-core missing refs, etc.).\n\n Outstanding papers should be either fascinating, controversial, surprising, impressive, or potentially field-changing. Awards will be decided based on the camera-ready version of the paper. ACL award policy: https://www.aclweb.org/adminwiki/index.php/ACL_Conference_Awards_Policy \n\n Main vs Findings papers: the main criteria for Findings are soundness and reproducibility. Conference recommendations may also consider novelty, impact and other factors."
    },
    "best_paper_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 11,
        "description": "If your overall assessment for this paper is either 'Consider for award' or 'Borderline award', please briefly describe why."
    },
    "limitations_and_societal_impact": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 12,
        "description": "Have the authors adequately discussed the limitations and potential positive and negative societal impacts of their work? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact. You are encouraged to think through whether any critical points are missing and provide these as feedback for the authors. Consider, for example, cases of exclusion of user groups, overgeneralization of findings, unfair impacts on traditionally marginalized populations, bias confirmation, under- and overexposure of languages or approaches, and dual use (see Hovy and Spruit, 2016, for examples of those). Consider who benefits from the technology if it is functioning as intended, as well as who might be harmed, and how. Consider the failure modes, and in case of failure, who might be harmed and how."
    },
    "ethical_concerns": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string",
                "default": "There are no concerns with this submission"
            }
        },
        "order": 13,
        "description": "Please review the ACL code of ethics (https://www.aclweb.org/portal/content/acl-code-ethics) and the ARR checklist submitted by the authors in the submission form. If there are ethical issues with this paper, please describe them and the extent to which they have been acknowledged or addressed by the authors. Otherwise, enter None."
    },
    "needs_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "order": 14,
        "description": "Should this paper be sent for an in-depth ethics review? Before you answer this question, please refer to https://aclrollingreview.org/ethics-flagging-guidelines/ for guidelines on what papers should and shouldn't be flagged. If your answer is yes, then ensure you have explained why in the question above, and we will try to ensure that it receives a separate ethics review."
    },
    "reproducibility": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = They could easily reproduce the results."
                    },
                    {
                        "value": 4,
                        "description": "4 = They could mostly reproduce the results, but there may be some variation because of sample variance or minor variations in their interpretation of the protocol or method."
                    },
                    {
                        "value": 3,
                        "description": "3 = They could reproduce the results with some difficulty. The settings of parameters are underspecified or subjectively determined, and/or the training/evaluation data are not widely available."
                    },
                    {
                        "value": 2,
                        "description": "2 = They would be hard pressed to reproduce the results: The contribution depends on data that are simply not available outside the author's institution or consortium and/or not enough details are provided."
                    },
                    {
                        "value": 1,
                        "description": "1 = They would not be able to reproduce the results here no matter how hard they tried."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 15,
        "description": "Is there enough information in this paper for a reader to reproduce the main results, use results presented in this paper in future work (e.g., as a baseline), or build upon this work?"
    },
    "datasets": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = Enabling: The newly released datasets should affect other people's choice of research or development projects to undertake."
                    },
                    {
                        "value": 4,
                        "description": "4 = Useful: I would recommend the new datasets to other researchers or developers for their ongoing work."
                    },
                    {
                        "value": 3,
                        "description": "3 = Potentially useful: Someone might find the new datasets useful for their work."
                    },
                    {
                        "value": 2,
                        "description": "2 = Documentary: The new datasets will be useful to study or replicate the reported research, although for other purposes they may have limited interest or limited usability. (Still a positive rating)"
                    },
                    {
                        "value": 1,
                        "description": "1 = No usable datasets submitted."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 16,
        "description": "If the authors state (in anonymous fashion) that datasets will be released, how valuable will they be to others?"
    },
    "software": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = Enabling: The newly released software should affect other people's choice of research or development projects to undertake."
                    },
                    {
                        "value": 4,
                        "description": "4 = Useful: I would recommend the new software to other researchers or developers for their ongoing work."
                    },
                    {
                        "value": 3,
                        "description": "3 = Potentially useful: Someone might find the new software useful for their work."
                    },
                    {
                        "value": 2,
                        "description": "2 = Documentary: The new software will be useful to study or replicate the reported research, although for other purposes it may have limited interest or limited usability. (Still a positive rating)"
                    },
                    {
                        "value": 1,
                        "description": "1 = No usable software released."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 17,
        "description": "If the authors state (in anonymous fashion) that their software will be available, how valuable will it be to others?"
    },
    "Knowledge_of_or_educated_guess_at_author_identity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I learned it orthogonally to the review process ",
                    "Yes, I learned it during review process (e.g. checking literature)",
                    "I can guess from the content of the submission",
                    "No, I do not have even an educated guess about author identity"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 18,
        "description": "Do you think you know the author(s) of this paper (at least one author name or affiliation)?"
    },
    "secondary_reviewer": {
        "value": {
            "param": {
            "type": "profile{}",
            "regex": "^~\\S+$|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})",
            "optional": True
            }
        },
        "description": "[OPTIONAL] If another person contributed significantly to this review, please indicate their OpenReview profile ID here. If they do not have a profile, please ask them to create one. Note that only EICs, SAEs, and AEs can see this field - other reviewers cannot. You can also use the new 'declare secondary reviewer' button, which will allow the secondary reviewer to have read-only access to author response, so that it is easier for them to check whether the review needs updating (see https://aclrollingreview.org/reviewerguidelines#secondary-reviewer).",
        "order": 26
    },
    "publication_ethics_policy_compliance": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "I did not use any generative AI tools for this review",
                    "I used a privacy-preserving tool exclusively for the use case(s) approved by PEC policy, such as language edits",
                    "I used the Revas tool to check for review issues (https://revas.mbzuai.ac.ae)"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 27,
        "description": "The reviewers (the primary and, if applicable, the secondary reviewer) certify that the review accurately reflects their assessment of the submission, and complies  with the ACL publication ethics policy (https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics#Reviewing). The reviewers have read the paper fully and drafted the content and argumentation of the review without the use of generative AI, or only in cases allowed by the policy (such as language checks). If AI was used in the allowed cases, the reviewers certify that neither the submission materials nor review content were submitted to any third-party services that could retain it."
    },
    "paper_matching_feedback": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "This work aligns well with both my expertise and interests",
                    "The match is reasonable, but not my top choice if there was bidding",
                    "This work is too far out of my technical expertise",
                    "This work is too far from my application/domain expertise or language(s)",
                    "The core goals/premises of this work aren't aligned with mine",
                    "This match does not match my current research interests",
                    "Other"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "order": 28,
        "description": "[OPTIONAL] This field is only used for improving the paper-reviewer matching at ARR. It is shown to the chairs, but not to the authors. If this wasn't a good match for you, please indicate why:"
    }
}

arr_metareview_content = {
    "metareview" : {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 1,
        "description": "Your metareview should follow the ARR metareview guidelines: https://aclrollingreview.org/acguidelines#-task-5-meta-review \n\n Describe what this paper is about. This should help SACs at publication venues understand what sessions the paper might fit in. Maximum 5000 characters. You can add  formatting using Markdown and formulas using LaTeX (see https://openreview.net/faq) "
    },
    "summary_of_reasons_to_publish": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 2,
        "description": "What are the major reasons to publish this paper at a *ACL venue? This should help SACs at publication venues understand why they might want to accept the paper. Maximum 5000 characters."
    },
    "summary_of_suggested_revisions": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 3,
        "description": "What revisions could the authors make to the research and the paper that would improve it? This should help authors understand the reviews in context, and help them plan any future resubmission. Maximum 5000 characters.\n\n For resubmissions, please consider the revisions taken in response to previous reviews and follow the guidelines: https://aclrollingreview.org/acguidelines#-preparing-a-meta-review-for-resubmissions"
    },
    "overall_assessment": {
        "description": "If this paper was committed to an *ACL conference, do you believe it should be accepted? If you recommend conference, Findings and or even award consideration, you can still suggest minor revisions (e.g. typos, non-core missing refs, etc.).\n\n Outstanding papers should be either fascinating, controversial, surprising, impressive, or potentially field-changing. Awards will be decided based on the camera-ready version of the paper. ACL award policy: https://www.aclweb.org/adminwiki/index.php/ACL_Conference_Awards_Policy \n\n Main vs Findings papers: the main criteria for Findings are soundness and reproducibility. Conference recommendations may also consider novelty, impact and other factors.",
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5.0,
                        "description": "5 = Consider for Award: I think this paper could be considered for an outstanding paper award at an *ACL conference (up to top 2.5% papers)."
                    },
                    {
                        "value": 4.5,
                        "description": "4.5 = Borderline Award"
                    },
                    {
                        "value": 4.0,
                        "description": "4 = Conference: I think this paper could be accepted to an *ACL conference."
                    },
                    {
                        "value": 3.5,
                        "description": "3.5 = Borderline Conference"
                    },
                    {
                        "value": 3.0,
                        "description": "3 = Findings: I think this paper could be accepted to the Findings of the ACL."
                    },
                    {
                        "value": 2.5,
                        "description": "2.5 = Borderline Findings"
                    },
                    {
                        "value": 2.0,
                        "description": "2 = Resubmit next cycle: I think this paper needs substantial revisions that can be completed by the next ARR cycle."
                    },
                    {
                        "value": 1.5,
                        "description": "1.5 = Resubmit after next cycle: I think this paper needs substantial revisions that cannot be completed by the next ARR cycle."
                    },
                    {
                        "value": 1.0,
                        "description": "1 = Do not resubmit: this paper has to be fully redone, or it is not relevant to the *ACL community (e.g. it is in no way related to computational processing of language)."
                    }
                ],
                "optional": False,
                "type": "float"
            }
        },
        "order": 4
    },
    "best_paper_ae_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 5,
        "description": "If your overall assessment for this paper is either 'Consider for award' or 'Borderline award', please briefly describe why."
    },
    "suggested_venues": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 6,
        "description": "If you can think of other conferences or workshops that would be a good match for this paper, please indicate them here."
    },    
    "ethical_concerns": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string",
                "default": "There are no concerns with this submission"
            }
        },
        "order": 8,
        "description": "Independent of your judgement of the quality of the work, please review the ACL code of ethics (https://www.aclweb.org/portal/content/acl-code-ethics) and list any ethical concerns related to this paper. Maximum length 2000 characters. Otherwise, enter None"
    },
    "needs_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "order": 9,
        "description": "Should this paper be sent for an in-depth ethics review? If so, why? Please refer to https://aclrollingreview.org/ethics-flagging-guidelines/ for guidelines on what papers should and shouldn't be flagged. Ideally, you will have flagged all ethical issues at the completion of AC checklist. This question should only be used as a last resort for papers that somehow were missed by both ACs and reviewers. At this stage it is too late for such papers to be reviewed by the ethics reviewers in this review cycle, and we are currently developing a process for handling such papers."
    },
    "author_identity_guess": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = From a violation of the anonymity-window or other double-blind-submission rules, I know/can guess at least one author's name."
                    },
                    {
                        "value": 4,
                        "description": "4 = From an allowed pre-existing preprint or workshop paper, I know/can guess at least one author's name."
                    },
                    {
                        "value": 3,
                        "description": "3 = From the contents of the submission itself, I know/can guess at least one author's name."
                    },
                    {
                        "value": 2,
                        "description": "2 = From social media/a talk/other informal communication, I know/can guess at least one author's name."
                    },
                    {
                        "value": 1,
                        "description": "1 = I do not have even an educated guess about author identity."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 10,
        "description": "Do you know the author identity or have an educated guess?"
    },
    "great_reviews": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 11,
        "description": "Please list the ids of any reviewers who went beyond expectations in terms of providing informative and constructive reviews and discussion, and merit a 'great reviewer' award. For example: jAxb, zZac."
    },
    "poor_reviews": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 12,
        "description": "Please list the ids of any reviewers whose reviews, in your opinion, were so problematic that it makes you question this reviewer's future roles in ARR. For example: jAxb, zZac."
    },
    "reviews_to_remove": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 13,
        "description": "Please list the ids of any reviewers whose reviews had such major issues that the review should be removed from the forum. For example: 'jAxb, zZac'."
    },
    "explanation": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 14,
        "description": "If you find that some reviews were not of sufficiently high quality, please explain why."
    },
   "reported_issues": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "No",
                    "Yes, and I took them into account in my meta-review",
                    "Yes, but I found the author complaints insufficiently justified"
                ],
                "optional": False,
                "type": "string[]"
            }
        },
        "description": "Did the authors report any issues with the reviews? If there are any such reports, they can be seen as replies to the reviews. Please search for 'Review Issue Report' on the forum page.",
        "order": 15
    },
    "note_to_authors": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 16,
        "description": "If the authors submitted a review issue report, and you would like to respond to that, please use the 'Note to authors' field."
    },
    "note_to_chairs": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 17,
        "description": "If you are uncertain about some aspect of your assessment, or have confidential comments on some aspects of the process for this paper, please use this field. It will be shown to the chairs, but not the authors or reviewers."
    },
    "publication_ethics_policy_compliance": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "I did not use any generative AI tools for this review",
                    "I used a privacy-preserving tool exclusively for the use case(s) approved by PEC policy, such as language edits"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 18,
        "description": "I certify that this meta-review complies with the ACL publication ethics policy (https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics#Reviewing). I have read all relevant materials and drafted the content and argumentation of the meta-review by myself. Any policy-compliant uses of generative AI tools (such as language checks to assist a non-native speaker) were only done with a privacy-preserving tool. Neither the submission materials nor review content were submitted to any services that could retain it."
    }        
}    

arr_ethics_review_content = {
    "recommendation": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 1,
        "description": "Recommendation."
    },
    "issues": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "1.1 Contribute to society and to human well-being, acknowledging that all people are stakeholders in computing",
                    "1.2 Avoid harm",
                    "1.3 Be honest and trustworthy",
                    "1.4 Be fair and take action not to discriminate",
                    "1.5 Respect the work required to produce new ideas, inventions, creative works, and computing artifacts",
                    "1.6 Respect privacy",
                    "1.7 Honor confidentiality",
                    "2.1 Strive to achieve high quality in both the processes and products of professional work",
                    "2.2 Maintain high standards of professional competence, conduct, and ethical practice",
                    "2.3 Know and respect existing rules pertaining to professional work",
                    "2.4 Accept and provide appropriate professional review",
                    "2.5 Give comprehensive and thorough evaluations of computer systems and their impacts, including analysis of possible risks",
                    "2.6 Perform work only in areas of competence",
                    "2.7 Foster public awareness and understanding of computing, related technologies, and their consequences",
                    "2.8 Access computing and communication resources only when authorized or when compelled by the public good",
                    "2.9 Design and implement systems that are robustly and usably secure",
                    "3.1 Ensure that the public good is the central concern during all professional computing work",
                    "3.2 Articulate, encourage acceptance of, and evaluate fulfillment of social responsibilities by members of the organization or group",
                    "3.3 Manage personnel and resources to enhance the quality of working life",
                    "3.4 Articulate, apply, and support policies and processes that reflect the principles of the Code",
                    "3.5 Create opportunities for members of the organization or group to grow as professionals",
                    "3.6 Use care when modifying or retiring systems",
                    "3.7 Recognize and take special care of systems that become integrated into the infrastructure of society",
                    "4.1 Uphold, promote, and respect the principles of the Code",
                    "4.2 Treat violations of the Code as inconsistent with membership in the ACL",
                    "None"
                ],
                "optional": False,
                "type": "string[]"
            }
        },
        "description": "Please check all relevant aspects of the ACL code of ethics which apply to the paper (either through omission or violation)",
        "order": 2
    },
    "explanation": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 3,
        "description": "Detailed explanation of your selection (max. 10000 characters)."
    }
}



arr_reviewer_ac_recognition_task_forum = {
    "title": "Requesting a Letter of Recognition",
    "instructions": "Please add a letter of recognition request to this forum if you want one for this month."
}

arr_reviewer_ac_recognition_task = {
    "request_a_letter_of_recognition":{
        "order": 1,
        "description": "If you want to receive a letter of recognition for your reviewing activities at ARR, please select 'Yes' below",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes, please send me a letter of recognition for my service as a reviewer / AE", "No, I do not need a letter of recognition for my service as a reviewer / AE"],
                "input": "radio",
                "optional": False,
            }
        }
    }
}

arr_max_load_task_forum = {
    "title": "Unavailability and Maximum Load Request for Volunteer Service",
    "instructions": "Please complete this form to indicate your (un)availability for reviewing performed as volunteer ARR service. If you wish to change your maximum load, please delete your previous request using the trash can icon, refresh the page and submit a new request. Please note that this form only applies to *volunteer* service, and is overridden by applicable author service requirements for authors submitting in a given cycle."
}

arr_max_load_task = {
    "maximum_load_this_cycle": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [0, 4, 5, 6, 7, 8],
                "optional": False,
                "type": "integer",
            }
        },
        "description": "Enter your maximum reviewing load for papers in this cycle. This refers only to the specific role mentioned at the top of this page. A load of '0' indicates you are unable to review new submissions. \n\n This form is only for preferences expressed for **volunteer** service roles. If you are an author in a given cycle, you are required to contribute to the review process if asked, and preferences expressed in this form will be overridden for that cycle according to the information in the author registration form. If you believe you should be exempt you must provide a suitable reason in the author registration form. For details of suitable reasons for exemption see: https://aclrollingreview.org/exemptions2025",
        "order": 1,
    },
    "maximum_load_this_cycle_for_resubmissions": {
        "value": {
            "param": {
                "input": "radio",
                "enum": ["Yes", "No"],
                "optional": False,
                "type": "string",
            }
        },
        "description": "Are you able to review resubmissions of papers you previously reviewed? (even if you answered '0' to the previous question)",
        "order": 2,
    },
    "next_available_month": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ],
                "optional": True,
                "type": "string",
            }
        },
        "description": "If you are going to be unavailable for an extended period of time, please indicate the next month that you will be available.",
        "order": 4,
    },
    "next_available_year": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [datetime.today().year + i for i in range(5)],
                "optional": True,
                "type": "integer",
            }
        },
        "description": "If you are going to be unavailable for an extended period of time, please fill out the next year, in combination with the previously filled out month, that you will be available.",
        "order": 5,
    }
}

arr_reviewer_max_load_task = deepcopy(arr_max_load_task)

arr_reviewer_max_load_task["meta_data_donation"] = {
    "value": {
        "param": {
            "input": "radio",
            "enum": [
                "Yes, I consent to donating anonymous metadata of my review for research.",
                "No, I do not consent to donating anonymous metadata of my review for research."
            ],
            "type": "string",
        }
    },
    "description": "Do you agree for the anonymized metadata associated with your reviews produced in this cycle to be included in a publicly available dataset? This dataset WILL include scores, anonymized paper and reviewer IDs that allow grouping the reviews by paper and by reviewer, as well as meta-review decisions and other numerical and categorical metadata. This dataset WILL NOT include any textual or uniquely attributable data like names, submission titles and texts, review texts, author responses, etc.",
    "order": 3
}

arr_ac_max_load_task = deepcopy(arr_max_load_task)
arr_ac_max_load_task["maximum_load_this_cycle"] = {
        "value": {
            "param": {
                "input": "radio",
                "enum": [0, 6, 7, 8, 9, 10, 11, 12],
                "optional": False,
                "type": "integer",
            }
        },
        "description": "Enter your maximum reviewing load for papers in this cycle. This refers only to the specific role mentioned at the top of this page. A load of '0' indicates you are unable to review new submissions.",
        "order": 1,
    }
arr_ethics_max_load_task = deepcopy(arr_max_load_task)
arr_ethics_max_load_task["maximum_load_this_cycle"] = {
        "value": {
            "param": {
                "input": "radio",
                "enum": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                "optional": False,
                "type": "integer",
            }
        },
        "description": "Enter your maximum reviewing load for papers in this cycle. This refers only to the specific role mentioned at the top of this page. A load of '0' indicates you are unable to review new submissions.",
        "order": 1,
    }

arr_sac_max_load_task = deepcopy(arr_max_load_task)
del arr_sac_max_load_task["maximum_load_this_cycle_for_resubmissions"]
del arr_sac_max_load_task["maximum_load_this_cycle"]
arr_sac_max_load_task['availability_this_cycle'] = {
    "value": {
        "param": {
        "input": "radio",
        "enum": [
            "I confirm that I will serve as SAC in this cycle, with the review load shared equally with other SACs (computed per track in conference-associated cycles).",
            "I will NOT be able to serve as SAC in this cycle"
        ],
        "optional": False,
        "type": "string"
        }
    },
    "order": 1,
    "description": "Please confirm your availability to be an SAC with the options below:"
}

arr_reviewer_emergency_load_task_forum = {
    "title": "Emergency Reviewing Form",
    "instructions": "Use the form below to opt in as an emergency reviewer. Your new maximum load will be made immediately available to the editors.\n\nTo edit your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating your adjusted availability\n\nTo withdraw your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating \"No\" for the \"Emergency Reviewing Agreement\"\n\nThe emergency review due is at the start day and time of the Author response period. This is a hard deadline. You can find the start date and time on https://aclrollingreview.org/dates"
}

arr_reviewer_emergency_load_task = {
    "emergency_reviewing_agreement": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "By selecting Yes, you agree to being an emergency reviewer for this cycle.",
        "order": 1
    },
    "emergency_load": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [0, 1, 2, 3, 4],
                "optional": False,
                "type": "integer",
            }
        },
        "description": "Enter your emergency reviewing load. This will be added to your originally submitted load.",
        "order": 2
    },
    "research_area": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": arr_tracks,
                "optional": True,
                "type": "string[]"
            }
        },
        "description": "Research Areas / Tracks. Select the most relevant research areas / tracks for your expertise",
        "order": 3
    }
}

arr_ac_emergency_load_task_forum = {
    "title": "Emergency Reviewing Form",
    "instructions": "Use the form below to opt in as an emergency area chair. Your new maximum load will be made immediately available to the senior area chairs.\n\nTo edit your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating your adjusted availability.\n\nTo withdraw your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating \"No\" for the \"Emergency Metareviewing Agreement\"",
}

arr_ac_emergency_load_task = {
    "emergency_reviewing_agreement": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "By selecting Yes, you agree to being an emergency reviewer for this cycle.",
        "order": 1
    },
    "emergency_load": {
        "value": {
            "param": {
                "optional": True,
                "type": "integer"
            }
        },
        "description": "Enter your emergency reviewing load. This will be added to your originally submitted load.",
        "order": 2
    },
    "research_area": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": arr_tracks,
                "optional": True,
                "type": "string[]"
            }
        },
        "description": "Research Areas / Tracks. Select the most relevant research areas / tracks for your expertise",
        "order": 3
    }
}


arr_content_license_task_forum = {
    "title": "Association for Computational Linguistics - Peer Reviewer Content License Agreement",
    "instructions": "If you have not reviewed for the previous ARR cycle, please ignore this task. If you have reviewed, please read and decide whether to transfer the license to your reviewing data for this iteration of ARR.\n\n***DISCLAIMER***\n\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute the text of your review. In particular, we may include your review text and scores in research datasets without revealing the OpenReview identifier that produced the review. Keep in mind that as with any text, your identity might be approximated using author profiling techniques. Only reviews for accepted papers will be eventually made publicly available. The authors of the papers will have to agree to the release of the textual review data associated with their papers.\n\nName of the ACL Conference: previous ARR cycle\n\n**Introduction**\nThis Peer Reviewer Content License Agreement (“Agreement”) is entered into between the Association for Computational Linguistics (“ACL”) and the Peer Reviewer listed above in connection with content developed and contributed by Peer Reviewer during the peer review process (referred as “Peer Review Content”). In exchange of adequate consideration, ACL and the Peer Reviewer agree as follows:\n\n**Section 1: Grant of License**\nPeer Reviewer grants ACL a worldwide, irrevocable, and royalty-free license to use the Peer Review Content developed and prepared by Peer Reviewer in connection with the peer review process for the ACL Conference listed above, including but not limited to text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials according to the following terms: A. For Peer Review Content associated with papers accepted for publication, and subject to the Authors permission, ACL may reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Peer Review Content, and to sub-license the Peer Review Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B. For Peer Review Content associated with papers not accepted for publication, ACL may use the Peer Review Content for internal research, program analysis, and record- keeping purposes. Notwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Peer Review Content, and that Peer Review retains respective ownership in and to the Peer Review Content.\n\n**Section 2: Attribution and Public Access License**\nA.The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice: Copyright © 2022 administered by the Association for Computational Linguistics (ACL) on behalf of ACL content contributors: ______________ (list names of peer reviewers who wish to be attributed), and other contributors who wish to remain anonymous. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B.In the event Peer Reviewer intends to modify the attribution displayed in connection with the copyright notice above, ACL will use reasonable efforts to modify the copyright notice after receipt of Peer Reviewer’s written request. Notwithstanding the foregoing, Peer Reviewer acknowledges and agrees that any modification in connection with attribution will not be retroactively applied. C.The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\n**Section 3: Warranty**\nPeer Reviewer represents and warrants that the Content is Peer Reviewer’s original work and does not infringe on the proprietary rights of others. Peer Reviewer further warrants that he or she has obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\n**Section 4: Legal Relationship**\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\n"
}

arr_content_license_task = {
    "attribution": {
        "order": 1,
        "description": "Unless the peer reviewer elects to be attributed according to Section 2, the peer reviewer’s name will not be identified in connection with publication of the Peer Review Content. If you wish to be attributed, please check the box below. ATTENTION: this will allow you to get credit for your reviews, but it will also DEANONYMIZE your reviews. Please select after careful consideration.",
         "value": {
            "param": {
                "type": "string",
                "enum": ["Yes, I wish to be attributed."],
                "input": "radio",
                "optional": True
            }
        }
    },
    "agreement": {
      "description": "By selecting 'I agree' below you confirm that you agree to this license agreement.",
      "order": 2,
      "value": {
            "param": {
                "type": "string",
                "enum": [
                    "I agree",
                    "I agree for this cycle and all future cycles until I explicitly revoke my decision",
                    "I do not agree"
                ],
                "input": "radio",
                "optional": False
            }
        }
    }
}

arr_metareview_license_task_forum = {
    "title": "Association for Computational Linguistics - Meta-reviewer Content License Agreement",
    "instructions": "If you have not meta-reviewed for this cycle, please ignore this task. If you have meta-reviewed, please read and decide whether to transfer the license to your meta-reviewing data for this iteration of ARR.\n\n*** DISCLAIMER ***\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute the text of your review. In particular, we may include your review text and scores in research datasets without revealing the OpenReview identifier that produced the review. Keep in mind that as with any text, your identity might be approximated using author profiling techniques. Only reviews for accepted papers will be eventually made publicly available. The authors of the papers will have to agree to the release of the textual review data associated with their papers.\n\nThis Meta-reviewer Content License Agreement (“Agreement”) is entered into between the Association for Computational Linguistics (“ACL”) and the Meta-reviewer listed above in connection with content developed and contributed by meta-reviewer during the peer review process (referred as “Meta-review Content”). In exchange of adequate consideration, ACL and the Meta-reviewer agree as follows:\n\nSection 1: Grant Of License\nMeta-reviewer grants ACL a worldwide, irrevocable, and royalty-free license to use the Meta-review Content developed and prepared by meta-reviewer in connection with the peer review process for the ACL Conference listed above, including but not limited to text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials according to the following terms: A. For Meta-review Content associated with papers accepted for publication, and subject to the Authors permission, ACL may reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Meta-review Content, and to sub-license the Meta-review Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B. For Meta-review Content associated with papers not accepted for publication, ACL may use the Meta-review Content for internal research, program analysis, and record- keeping purposes. Notwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Meta-review Content, and that Meta-reviewer retains respective ownership in and to the Meta-review Content.\n\nSection 2 Attribution and Public Access License\nA.The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice: Copyright © 2022 administered by the Association for Computational Linguistics (ACL) on behalf of ACL content contributors: ______________ (name of meta-reviewer who wishes to be attributed), and other contributors who wish to remain anonymous. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B.In the event Meta-reviewer intends to modify the attribution displayed in connection with the copyright notice above, ACL will use reasonable efforts to modify the copyright notice after receipt of Meta-reviewer’s written request. Notwithstanding the foregoing, Meta-reviewer acknowledges and agrees that any modification in connection with attribution will not be retroactively applied. C.The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\nSection 3 Warranty\nMeta-reviewer represents and warrants that the Content is Meta-reviewer’s original work and does not infringe on the proprietary rights of others. Meta-reviewer further warrants that he or she has obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\nSection 4 Legal Relationship\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other."
}

arr_metareview_license_task = {
    "attribution": {
        "order": 1,
        "description": "Unless the meta-reviewer elects to be attributed according to Section 2, the meta-reviewer’s name will not be identified in connection with publication of the Meta-review Content. If you wish to be attributed, please check the box below. ATTENTION: this will allow you to get credit for your reviews, but it will also DEANONYMIZE your reviews. Please select after careful consideration.",
         "value": {
            "param": {
                "type": "string",
                "enum": ["Yes, I wish to be attributed."],
                "input": "radio",
                "optional": True
            }
        }
    },
    "agreement": {
      "description": "By selecting 'I agree' below you confirm that you agree to this license agreement.",
      "order": 2,
      "value": {
            "param": {
                "type": "string",
                "enum": [
                    "I agree",
                    "I do not agree"
                ],
                "input": "radio",
                "optional": False
            }
        }
    }
}

arr_registration_task_forum = {
    "title": "Registration for Volunteer Service at ARR",
    "instructions": "Please check below points and verify that you provided the required pieces of information in your OpenReview profile. \nYou can view and edit your profile at https://openreview.net/profile\n\n You can curate the list of your past work indicative of your expertise by going to this cycle's console, clicking on the tasks tab and clicking \"Expertise Selection\"",
}

arr_registration_task = {
    "domains": {
        "order": 1,
        "description": "I confirm that I have specified the history of domains I am and previously was affiliated with.",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "emails": {
        "order": 2,
        "description": "I confirm that I have specified all (professional) email addresses I use and used beforehand.",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "DBLP": {
        "order": 3,
        "description": "I confirm that I specified the URL to my DBLP profile (if existent).",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "semantic_scholar": {
        "order": 4,
        "description": "I confirm that I specified the URL to my Semantic Scholar profile (if existent).",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "research_area": {
        "order": 5,
        "description": "Research Areas / Tracks. Select all relevant research areas / tracks that are the best fit for your expertise. These will be used to inform the reviewer and area chair assignment",
        "value": {
            "param": {
                "type": "string[]",
                "enum": arr_tracks,
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "languages_studied": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Please list the languages that fall under your expertise, separated by commas.",
        "order": 6
    },
}

arr_desk_reject_verification = {
    "verification": {
        "order": 1,
        "description": "Indicate whether or not a decision to desk reject this paper has been made or not",
        "value": {
            "param": {
                "type": "string",
                "enum": ["I have checked the potential violation(s) and have decided to either desk reject this submission or decided that no further action is required."],
                "input": "checkbox",
                "optional": False
            }
        }
    }
}

arr_ae_checklist = {
    "appropriateness": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "This and the following questions help us to identify possible violations for which the paper may be desk rejected without review. \n\n Is the paper appropriate for *CL? ARR is NOT a general machine learning venue: submissions should make a clear contribution to computational processing of natural language.",
        "order": 1
    },
    "appropriateness_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper makes a contribution to computational processing of natural language.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper is not relevant for *CL, please explain your reasoning to help the chairs consider the case.",
        "order": 2
    },
    "formatting": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper properly formatted according to the ACL guidelines? (https://acl-org.github.io/ACLPUB/formatting.html)",
        "order": 3
    },
    "formatting_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper is properly formatted.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper is not appropriately formatted (e.g. some text is too small to be legible when printed on A4 paper), please describe the violation to help the chairs consider the case.",
        "order": 4
    },
    "length": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have the proper length? Short papers: 4 content pages maximum; Long papers: 8 content pages maximum. Sections on ethical considerations and limitations do not count towards page limit.",
        "order": 5
    },
    "length_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper is within the page limits.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper is violating the page limit rules (e.g. appendix contains materials critical to understanding the main paper), please describe the violation to help the chairs consider the case.",
        "order": 6
    },
    "anonymity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper properly anonymized?",
        "order": 7
    },
    "anonymity_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper is properly anonymized.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper discloses the author identity somehow (e.g. self-citations, links to non-anonymous repositories), please describe the violation to help the chairs consider the case.",
        "order": 8
    },
    "limitations": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have a section entitled \"Limitations\"?",
        "order": 9
    },
    "limitations_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper has the 'Limitations' section.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If this paper is missing the required 'Limitations' section, please indicate if you noticed a description of limitations elsewhere.",
        "order": 10
    },
    "overall_level": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the submission seem to be a good-faith submission that merits full review?",
        "order": 11
    },
    "overall_level_justification": {
        "value": {
            "param": {
                "regex": ".{1,250}",
                "optional": False,
                "default": "N/A - this seems like a good-faith submission worthy of full review.",
                "type": "string"
            }
        },
        "description": "ARR is receiving many low-quality submissions -- some possibly generated -- that do not merit full review and put a strain on our volunteer reviewer resources. If you notice a submission that is clearly not in good faith, please indicate that the chairs should consider desk rejection, and provide your rationale.  Hallucinated citations are one of the possible indicators.",
        "order": 12
    },
    "responsible_checklist": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Have the authors completed the responsible NLP research checklist in good faith?",
        "order": 13
    },
    "potential_violation_justification": {
        "value": {
            "param": {
                "regex": ".{1,250}",
                "optional": False,
                "default": "N/A - the authors filled in the responsible NLP checklist in good faith.",
                "type": "string"
            }
        },
        "description": "If the authors provided incorrect, incomplete or misleading information in this checklist, please give a brief explanation of the issue. Bad-faith responses can be grounds for desk rejection. If the authors did provide a reasonable response, but you disagree with it scientifically, this should be considered in the review process.",
        "order": 14
    },
    "need_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Should this paper be sent for an in-depth ethics review? We have a small ethics committee that can specially review very challenging papers when it comes to ethical issues. If this seems to be such a paper, then please explain why below, and we will try to ensure that it receives a separate review. Please refer to https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 15
    },
    "ethics_review_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper does not need an ethics review.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "Please provide a meaningful justification for why this paper needs an ethics review. Note that lack of ethical considerations section, limitations section, copyright details etc. should be directly communicated to the authors in your reviews, and often do not need a full ethics review. When in doubt, please flag. For more guidelines on ethics review flagging, see https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 16
    },
    "number_of_assignments": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "This and the following questions aim to ensure that the submission is adequately handled, if it is accepted for review. \n\n Does the submission have 3 reviewers?",
        "order": 17
    },
    "diversity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Are the reviewers diverse with respect to seniority, geographies and institutions? If not, answer 'no' and please modify the assignments",
        "order": 18
    },
    "resubmission": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "This paper is a not a resubmission"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "description": "If the paper is a resubmission, does the link to the previous submission work?",
        "order": 19
    },
    "resubmission_reassignments": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "This paper is a not a resubmission"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "description": "If this is a resubmission, has the authors' request regarding keeping or changing reviewers been respected? If not, answer 'No' and please modify the assignments",
        "order": 20
    },
    "resubmission_notes": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "This paper is a not a resubmission"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "description": "If this is a resubmission, is it accompanied by revision notes listing the changes made? (field: 'explanation of revisions PDF'). It should contain a good-faith attempt to incorporate reasonable feedback from the past cycle, or explain why it should be disregarded.",
        "order": 21
    },
    "other_issues": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Please let us know if you have any other serious concerns about this submission that should be considered by the chairs, e.g. possible salami slicing concerns (https://aclrollingreview.org/cfp#originality). Markdown formatting and latex formulas can be used.",
        "order": 22
    }
}



arr_reviewer_checklist = {
    "appropriateness": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper appropriate for *CL? ARR is NOT a general machine learning venue: submissions should make a clear contribution to computational processing of natural language.",
        "order": 1
    },
    "appropriateness_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper makes a contribution to computational processing of natural language.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper is not relevant for *CL, please explain your reasoning to help the chairs consider the case.",
        "order": 2
    },
    "formatting": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper properly formatted according to the ACL guidelines? (https://acl-org.github.io/ACLPUB/formatting.html)",
        "order": 3
    },
    "formatting_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper is properly formatted.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper is not appropriately formatted (e.g. some text is too small to be legible when printed on A4 paper), please describe the violation to help the chairs consider the case.",
        "order": 4
    },
    "length": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have the proper length? Short papers: 4 content pages maximum; Long papers: 8 content pages maximum. Sections on ethical considerations and limitations do not count towards page limit.",
        "order": 5
    },
    "length_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper is within the page limits.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper is violating the page limit rules (e.g. appendix contains materials critical to understanding the main paper), please describe the violation to help the chairs consider the case.",
        "order": 6
    },
    "anonymity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper properly anonymized?",
        "order": 7
    },
    "anonymity_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper is properly anonymized.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If you believe this paper discloses the author identity somehow (e.g. self-citations, links to non-anonymous repositories), please describe the violation to help the chairs consider the case.",
        "order": 8
    },
    "limitations": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have a section entitled \"Limitations\"?",
        "order": 9
    },
    "limitations_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper has the 'Limitations' section.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "If this paper is missing the required 'Limitations' section, please indicate if you noticed a description of limitations elsewhere.",
        "order": 10
    },
    "overall_level": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the submission seem to be a good-faith submission that merits full review?",
        "order": 11
    },
    "overall_level_justification": {
        "value": {
            "param": {
                "regex": ".{1,250}",
                "optional": False,
                "default": "N/A - this seems like a good-faith submission worthy of full review.",
                "type": "string"
            }
        },
        "description": "ARR is receiving many low-quality submissions -- some possibly generated -- that do not merit full review and put a strain on our volunteer reviewer resources. If you notice a submission that is clearly not in good faith, please indicate that the chairs should consider desk rejection, and provide your rationale.  Hallucinated citations are one of the possible indicators.",
        "order": 12
    },
    "responsible_checklist": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Have the authors completed the responsible NLP research checklist in good faith?",
        "order": 13
    },
    "potential_violation_justification": {
        "value": {
            "param": {
                "regex": ".{1,250}",
                "optional": False,
                "default": "N/A - the authors filled in the responsible NLP checklist appropriately.",
                "type": "string"
            }
        },
        "description": "If the authors provided incorrect, incomplete or misleading information in this checklist, please give a brief explanation of the issue. Bad-faith responses can be grounds for desk rejection. If the authors did provide a reasonable response, but you disagree with it scientifically, this should be considered in the review process.",
        "order": 14
    },
    "need_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Should this paper be sent for an in-depth ethics review? We have a small ethics committee that can specially review very challenging papers when it comes to ethical issues. If this seems to be such a paper, then please explain why below, and we will try to ensure that it receives a separate review. Please refer to https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 15
    },
    "ethics_review_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A - this paper does not need an ethics review.",
                "optional": False,
                "type": "string"
            }
        },
        "description": "Please provide a meaningful justification for why this paper needs an ethics review. Note that lack of ethical considerations section, limitations section, copyright details etc. should be directly communicated to the authors in your reviews, and often do not need a full ethics review. When in doubt, please flag. For more guidelines on ethics review flagging, see https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 16
    },
    "other_issues": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Please let us know if you have any other serious concerns about this submission that should be considered by the chairs, e.g. possible salami slicing concerns (https://aclrollingreview.org/cfp#originality). Markdown formatting and latex formulas can be used.",
        "order": 17
    }
}


arr_review_rating_content = {
    "I1_not_specific": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review is not specific enough."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: missing references are not specified.",
        "order": 1
    },
    "I2_reviewer_heuristics": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review exhibits one or more of the reviewer heuristics discussed in the ARR reviewer guidelines: https://aclrollingreview.org/reviewertutorial"
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Examples: 'not SOTA', 'not novel', 'not suprising', 'too simple'. Note that such criticisms *may* be legitimate, if the reviewer explains their reasoning and backs it up with arguments/evidence/references. This flag should only be used to report cases where the reviewer has not done due diligence.",
        "order": 2
    },
    "I3_score_mismatch": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review score(s) do not match the text of the review."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "'Overall assessment' score is a combination of several factors. Two of them are reflected in the 'soundness' and 'reproducibility' scores, which assess the technical merit of the submission. If they are low, this should be backed up by the text of the review. The 'excitement' score is subjective and may not be justified in text (e.g. different researchers have different ideas of what is exciting and presentation-worthy).",
        "order": 3
    },
    "I4_unprofessional_tone": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The tone of the review does not conform to professional conduct standards."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Examples: rude reviews, sexist/racist/ageist etc. insinuations.",
        "order": 4
    },
    "I5_expertise": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review does not evince expertise."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Examples: reviews that are not based on a deep understanding of the submission, or the core methodology used in this research area. This rubric can also be used for reviews suspected of being auto-generated.",
        "order": 5
    },
    "I6_type_mismatch": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review does not match the type of paper."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: a short paper expected to provide more experiments than is necessary to support the stated claim.",
        "order": 6
    },
    "I7_contribution_mismatch": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review does not match the type of contribution."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Examples: experimental results expected from a paper relying on a different methodology.",
        "order": 7
    },
    "I8_missing_review": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review is missing or is uninformative."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: one-liner reviews with generic criticisms.",
        "order": 8
    },
    "I9_late_review": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review was late."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: the review came too late to be addressed in the author response.",
        "order": 9
    },
    "I10_unreasonable_requests": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The reviewer requests experiments that are not needed to demonstrate the stated claim."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: requests for comparisons with the latest 'closed' models when it is not relevant for the research question.",
        "order": 10
    },
    "I11_non_response": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review does not acknowledge critical evidence in the author response."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "The reviewers are volunteers, and are not required to respond to all author comments. Many do not respond in the forum, but do edit their reviews after seeing the author response. You should only use this rubric when there is a critical misunderstanding or unnoticed evidence, which would significantly impact key claims made in the review.",
        "order": 11
    },
    "I12_revisions_unacknowledged": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The review does not acknowledge the revisions"
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "[For revised submissions only:] the review does not acknowledge the revisions documented in revision notes, without sufficient justification.",
        "order": 12
    },
    "I13_other": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "Some other technical violation of the peer review process."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Please explain your issue in sufficient detail below.",
        "order": 13
    },
    "justification": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "maxLength": 2000,
                "type": "string"
            }
        },
        "order": 14,
        "description": "Describe the issue(s) with this review, clearly and concisely, with supporting evidence. You can use markdown. Please start the description for each type of issue with a new paragraph that starts with the review issue code. For example: `I2. The reviewer states [...]. We believe that this corresponds to review issue type I2, because [...]`.\n\nIn case of reviewers not changing their scores based on the discussion, it is not in your interest to try to present a one-sided view of a reasonable scientific disagreement. Please include the link to the specific comment."
    }
}

arr_metareview_rating_content = {
    "MI1_not_specific": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review is not specific enough."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: the metareview requests revisions but is not specific enough about what should be changed.",
        "order": 1
    },
    "MI2_technical_problem": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review has a technical issue"
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: meta-review for the wrong paper was submitted by mistake.",
        "order": 2
    },
    "MI3_guidelines_violation": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review has a serious procedural violation of AC guidelines."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: the meta-review is not based on a deep understanding of the submission, or the core methodology used in this research area. This rubric can also be used for meta-reviews suspected of being auto-generated.",
        "order": 3
    },
    "MI4_unprofessional_tone": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The tone of the meta-review does not conform to professional conduct standards."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Examples: rude meta-reviews, sexist/racist/ageist etc. insinuations.",
        "order": 4
    },
    "MI5_author_response": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review does not acknowledge a key aspect of author response."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: the meta-review hinges on a key weakness that the authors provided a detailed response to (within the recommended discussion length), but neither reviewer or meta-reviewer said why the response was unsatisfactory.",
        "order": 5
    },
    "MI6_review_issue_ignored": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review fails to take into account a serious review issue."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Example: the authors reported a serious issue with the review(s), but the meta-reviewer ignored the report (note that this is different from disagreeing with the authors about that issue).",
        "order": 6
    },
    "MI7_score_mismatch": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review score does not match the text."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Examples: the score assigned with the metareview should be higher (or lower), given the revisions requested.",
        "order": 7
    },
    "MI8_revisions_unacknowledged": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "The meta-review does not acknowledge the revisions."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "[For revised submissions only:] the meta-review does not acknowledge the revisions documented in revision notes, without sufficient justification.",
        "order": 8
    },
    "MI9_other": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "Some other technical violation of the meta review process."
                ],
                "optional": True,
                "deletable": True,
                "type": "string"
            }
        },
        "description": "Please explain your issue in sufficient detail below.",
        "order": 9
    },
    "metareview_rating_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "input": "textarea",
                "markdown": True,
                "maxLength": 2000,
                "type": "string"
            }
        },
        "order": 10,
        "description": "Describe the issue(s) with this meta-review, clearly and concisely, with supporting evidence. You can use markdown. Please start the description for each type of issue with a new paragraph that starts with the review issue code. For example: `MI2. The meta-reviewer states [...]. We believe that this corresponds to review issue type MI2, because [...]`.\n\nThis form should only be used for reporting serious procedural issues with meta-reviews. It is not in your interest to try to present the senior area chairs with a one-sided view of a reasonable scientific disagreement."
    }
}

arr_submitted_author_forum = {
    'title': 'Submitted Author Profile Form',
    'instructions': 'This form is required for all authors. Failure to complete it will lead to desk rejection. If any of your co-authors are unable to complete the form (e.g., they are unable to access it), please provide their OpenReview IDs in the first question below. If you believe you should be exempt, please read this blog post before claiming an exemption: https://aclrollingreview.org/exemptions2025 ',
}

arr_submitted_author_content = {
    "coauthor_issues": {
        "value": {
            "param": {
                "type": "profile[]",
                "regex": "^~\\S+$|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})",
                "optional": True,
            }
        },
        "description": "If any of your co-authors are unable to complete this form, please provide their Openreview IDs in this question. Search for the author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.",
        "order": 2
    },
    "confirm_you_are_willing_to_serve_as_a_reviewer_or_AC": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "I will serve as a reviewer or area chair (AC) in this cycle if ARR considers me qualified.",
                    "I will serve as a reviewer or area chair (AC) in this cycle if ARR considers me qualified, but I would prefer to serve as an AC.",
                    "I will serve as a reviewer in this cycle if ARR considers me qualified, but I do not wish to be an AC.",
                    "I am already serving in this ARR cycle as one of: senior area chair, ethics reviewer, ethics chair, editor in chief, technical team, support team, or editorial staff, which I will specify in the next question.",
                    "No, I cannot serve because I am unqualified (we will check this and if you are qualified you will be required to review).",
                    "No, I cannot serve because I am on parental leave.",
                    "No, I cannot serve because I am on family medical leave.",
                    "No, I cannot serve because I have a medical emergency.",
                    "No, I cannot serve because of another form of emergency beyond my control.",
                    "No, I cannot serve because I am an AC / SAC / PC / General Chair / Local Chair for a related venue.",
                    "No, I cannot serve because I am editor-in-chief of a major related journal.",
                    "No, I cannot serve for another reason (this choice is very rare)."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "ARR requires all authors of submissions in a given cycle to contribute to the review process in that cycle if asked (see: https://aclrollingreview.org/incentives2026). Serving as either a reviewer or an AC is sufficient to satisfy this requirement. If you are unable to serve please select the most appropriate option that starts with 'No'. **Note that for the last three options you must provide sufficient justification in the next question or your paper will be desk rejected.** If you are already a reviewer or AC in ARR, please select one of the first three options to confirm you are willing to serve in this cycle. \n\n We clarify that the service expectations for the submitting authors authors are different from the regular volunteer service. If you are a submitting author in this cycle, your answers in this form override any previously indicated unavailability or service load preferences as an ARR volunteer reviewer or chair for this cycle.",
        "order": 3
    },
    "details_of_reason_for_being_unable_to_serve_or_ARR_role": {
        "value": {
            "param": {
                "optional": True,
                "type": "string",
                "input": "textarea"
            }
        },
        "description": "If you chose 'No, I cannot serve ... which I will specify in the next question' above, please provide details here, e.g., the name of the conference you are a PC for. If you are already serving in this ARR cycle in a role other than reviewer or AC, please specify your role. Otherwise, please leave this blank. If you believe you are not qualified, do *not* write that here. **Without [a suitable explanation](https://aclrollingreview.org/exemptions2025), the request will be denied.**",
        "order": 4
    },
    "serving_as_a_regular_or_emergency_reviewer_or_AC": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I am willing to serve as an emergency reviewer or AC.",
                    "No, I am not willing to serve as an emergency reviewer or AC."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Some reviewers and ACs will be needed to quickly review (in 1-2 days) papers that are missing reviews at the end of the review period. Please indicate if you are willing to serve in this way.",
        "order": 5
    },
    "indicate_emergency_reviewer_load": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "N/A, in the previous question I indicated I do not wish to be an emergency reviewer or AC.",
                    "1",
                    "2",
                    "3"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Please indicate how many papers you would be willing to do emergency reviews for if asked.",
        "order": 6
    },
    "confirm_you_are_qualified_to_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I meet the ARR requirements to be a reviewer.",
                    "No, I do not meet the ARR requirements to be a reviewer."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "The ARR requirements for reviewers are: (a) at least two papers in main ACL events or Findings, plus (b) at least one more paper in the ACL Anthology or a major AI venue. Venues considered 'main ACL' are: ACL, CL, CoLing, CoNLL, EACL, EMNLP, HLT, IJCNLP / AACL, LREC, NAACL, TACL, *SEM. Major AI venues we consider are: AAAI, CVPR, ECCV, FAccT, ICCV, ICLR, ICML, IJCAI, JAIR, JMLR, NeurIPS, TMLR, TPAMI. Note, we will check that your response matches data online. Having your self-reported status helps us identify issues with available data.",
        "order": 7
    },
    "are_you_a_student": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I am a Bachelors student, or an earlier education stage.",
                    "Yes, I am a Masters student.",
                    "Yes, I am a Doctoral student.",
                    "No, I am not a student."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "We collect this information because sometimes it is unclear from OpenReview profiles.",
        "order": 8
    },
    "what_is_your_highest_level_of_completed_education": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Bachelors or earlier",
                    "Masters",
                    "Doctorate"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "We collect this information because sometimes it is unclear from OpenReview profiles.",
        "order": 9
    },
    "confirm_your_profile_has_past_domains": {
        "description": "I confirm that I have specified in my OpenReview profile the full history of domains I am now and previously was affiliated with.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes"
                ],
                "input": "checkbox",
                "optional": False
            }
        },
        "order": 11
    },
    "confirm_your_profile_has_all_email_addresses": {
        "description": "I confirm that I have specified in my OpenReview profile all (professional) email addresses I now use and have used before.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes"
                ],
                "input": "checkbox",
                "optional": False
            }
        },
        "order": 12
    },
    "meta_data_donation": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, If selected as a reviewer, I consent to donating anonymous metadata of my review for research.",
                    "No, I do not consent to donating anonymous metadata of my review for research."
                ],
                "type": "string"
            }
        },
        "description": "If selected as reviewer, do you agree for the anonymized metadata associated with your reviews produced in this cycle to be included in a publicly available dataset? This dataset WILL include scores, anonymized paper and reviewer IDs that allow grouping the reviews by paper and by reviewer, as well as meta-review decisions and other numerical and categorical metadata. This dataset WILL NOT include any textual or uniquely attributable data like names, submission titles and texts, review texts, author responses, etc.",
        "order": 13
    },
    "indicate_your_research_areas": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": arr_tracks,
                "optional": False,
                "type": "string[]"
            }
        },
        "description": "If you are selected as a reviewer, we will need to know the research areas / tracks you are qualified to review for. Please select the most relevant research areas / tracks for your expertise",
        "order": 14
    },
    "indicate_your_languages": {
        "value": {
            "param": {
                "optional": True,
                "type": "string[]",
                "input": "select",
                "enum": iso_639_3_languages
            }
        },
        "description": "If you have expertise in any natural languages apart from English, and could help to review resources or applications for those languages, please specify them here. This form supports the languages in ISO 639-3 standard (https://iso639-3.sil.org/)",
        "order": 15
    },
    "confirm_your_openreview_profile_contains_a_DBLP_link": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, my OpenReview profile contains a link to a DBLP profile with just my papers.",
                    "No, the DBLP profile for my name contains other peoples' publications.",
                    "No, I have no DBLP listed publications."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "If there is a valid DBLP profile for you, your OpenReview profile must contain a link to it. If the profile is invalid, you must either import your papers to OpenReview or provide a valid ACL Anthology profile link.",
        "order": 16
    },
    "provide_your_DBLP_URL": {
        "description": "If there is a valid DBLP profile for you, please provide it here. If the profile is invalid, e.g., because it has other people's papers in it, please leave this blank.",
        "value": {
            "param": {
                "optional": True,
                "type": "string"
            }
        },
        "order": 17
    },
    "confirm_your_openreview_profile_contains_a_semantic_scholar_link": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, my OpenReview profile contains a link to a Semantic Scholar profile with just my papers.",
                    "No, the Semantic Scholar profile for my name contains other peoples' publications.",
                    "No, I have no Semantic Scholar listed publications."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "If there is a valid Semantic Scholar profile for you, your OpenReview profile must contain a link to it. If the profile is invalid, you must either import your papers to OpenReview or provide a valid ACL Anthology profile link.",
        "order": 18
    },
    "provide_your_semantic_scholar_URL": {
        "description": "If there is a valid Semantic Scholar profile for you, please provide it here. If the profile is invalid, e.g., because it has other people's papers in it, please leave this blank.",
        "value": {
            "param": {
                "optional": True,
                "type": "string"
            }
        },
        "order": 19
    },
    "provide_your_ACL_anthology_URL": {
        "description": "If there is a valid ACL Anthology profile for you, please provide it here. If the profile is invalid, e.g., because it has a other people's papers in it, please leave this blank.",
        "value": {
            "param": {
                "optional": True,
                "type": "string"
            }
        },
        "order": 20
    },
    "provide_your_ORCID": {
        "description": "If you have any publicly available publications (including preprints), please confirm that your OpenReview profile contains a valid ORCID ID.",
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, my OpenReview profile contains a valid ORCID ID.",
                    "N/A: I do not have any publications or preprints."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 21,
    },
    "attribution": {
        "description": "Please read and decide whether to transfer the license to your reviewing data for this iteration of ARR if you are selected as a reviewer.\n\n***DISCLAIMER***\n\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute the text of your review. In particular, we may include your review text and scores in research datasets without revealing the OpenReview identifier that produced the review. Keep in mind that as with any text, your identity might be approximated using author profiling techniques. Only reviews for accepted papers will be eventually made publicly available. The authors of the papers will have to agree to the release of the textual review data associated with their papers.\n\nName of the ACL Conference: previous ARR cycle\n\n**Introduction**\nThis Peer Reviewer Content License Agreement (\u201cAgreement\u201d) is entered into between the Association for Computational Linguistics (\u201cACL\u201d) and the Peer Reviewer listed above in connection with content developed and contributed by Peer Reviewer during the peer review process (referred as \u201cPeer Review Content\u201d). In exchange of adequate consideration, ACL and the Peer Reviewer agree as follows:\n\n**Section 1: Grant of License**\nPeer Reviewer grants ACL a worldwide, irrevocable, and royalty-free license to use the Peer Review Content developed and prepared by Peer Reviewer in connection with the peer review process for the ACL Conference listed above, including but not limited to text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials according to the following terms: A. For Peer Review Content associated with papers accepted for publication, and subject to the Authors permission, ACL may reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Peer Review Content, and to sub-license the Peer Review Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B. For Peer Review Content associated with papers not accepted for publication, ACL may use the Peer Review Content for internal research, program analysis, and record- keeping purposes. Notwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Peer Review Content, and that Peer Review retains respective ownership in and to the Peer Review Content.\n\n**Section 2: Attribution and Public Access License**\nA.The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice: Copyright \u00a9 2022 administered by the Association for Computational Linguistics (ACL) on behalf of ACL content contributors: ______________ (list names of peer reviewers who wish to be attributed), and other contributors who wish to remain anonymous. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B.In the event Peer Reviewer intends to modify the attribution displayed in connection with the copyright notice above, ACL will use reasonable efforts to modify the copyright notice after receipt of Peer Reviewer\u2019s written request. Notwithstanding the foregoing, Peer Reviewer acknowledges and agrees that any modification in connection with attribution will not be retroactively applied. C.The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\n**Section 3: Warranty**\nPeer Reviewer represents and warrants that the Content is Peer Reviewer\u2019s original work and does not infringe on the proprietary rights of others. Peer Reviewer further warrants that he or she has obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\n**Section 4: Legal Relationship**\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\nUnless the peer reviewer elects to be attributed according to Section 2, the peer reviewer\u2019s name will not be identified in connection with publication of the Peer Review Content. If you wish to be attributed, please check the box below. ATTENTION: this will allow you to get credit for your reviews, but it will also DEANONYMIZE your reviews. Please select after careful consideration.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes, I wish to be attributed.",
                    "No, I do not wish to be attributed."
                ],
                "input": "radio",
                "optional": True
            }
        },
        "order": 22
    },
    "agreement": {
        "description": "By selecting 'I agree' below you confirm that you agree to this license agreement if you are selected to review.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "I agree",
                    "I agree for this cycle and all future cycles until I explicitly revoke my decision",
                    "I do not agree"
                ],
                "input": "radio",
                "optional": False
            }
        },
        "order": 23
    }
}

arr_withdrawal_content = {
    "comment": {
        "order": 3,
        "description": "Any comments? (optional)",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 200000,
                "input": "textarea",
                "optional": True,
                "deletable": True,
                "markdown": True
            }
        }
    },
    "confirm_need_to_withdraw": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "I confirm that I need to withdraw my submission, for which I have not yet received a meta-review."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "I confirm that I actually need to withdraw this submission (e.g. because I plan to resubmit it to another venue before the end of this cycle).\n\n We ask you to confirm this, because many authors request a withdrawal AFTER the release of meta-reviews. This is NOT needed, because the paper is NO LONGER UNDER REVIEW and can be resubmitted anywhere without withdrawal from ARR.",
        "order": 1
    },
    "withdrawal_confirmation": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "I confirm that I am aware of and accept the implications of withdrawing this submission from ARR. In particular, the submission will not be fully reviewed and ready for commitment in this cycle, and any earlier reviewed versions will also be ineligible for commitment. I will also not be able to resubmit it to ARR without restoring this submission, and if I have received even one review for it -- it would count as a resubmission, it would need to be disclosed and accompanied with an explanation of revisions. See https://aclrollingreview.org/cfp#withdrawal and https://aclrollingreview.org/cfp#resubmissions",
        "order": 2
    }
}

arr_delay_notification_content = {
    "notification": {
        "order": 1,
        "description": "Please specify the exact date and time (with timezone) when your review will be submitted. You may also optionally provide a brief explanation. Note that if your paper was assigned more than 1 week before reviews are due, the delayed review or meta-review will make you ineligible for 'great reviewer/chair' recognition and a chance to get free conference registration: https://aclrollingreview.org/incentives2025",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 2000,
                "markdown": False,
                "input": "textarea",
                "optional": False
            }
        }
    }
}

arr_emergency_declaration_content = {
    "declaration": {
        "order": 1,
        "description": "I certify that I have a personal emergency of the following kind that will make it impossible for me to complete my (meta)-review for this paper, and hereby request that the (S)AC find a replacement for me ASAP:",
        "value": {
            "param": {
                "type": "string",
                "input": "radio",
                "enum": [
                    "Medical",
                    "Family",
                    "Other"
                ]
            }
        }
        },
        "explanation": {
        "order": 2,
        "description": "Provide any additional information about your emergency",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 200000,
                "markdown": True,
                "input": "textarea",
                "optional": True,
                "deletable": True
            }
        }
    }
}

arr_great_or_irresponsible_reviewer_content = {
    "rating": {
        "order": 1,
        "description": "This button allows to indicate which reviewers did a great job or were highly irresponsible. See this post on the new peer review incentives at ACL venues:  https://aclrollingreview.org/incentives2025 \n\n Great review: the reviewer went above expectations, e.g. in a highly rigorous review, in investing the effort to champion the paper, in thoughtful engagement with authors, in an active discussion with other reviewers, in patient and constructive feedback, in heroic emergency reviews performed quickly and with high quality. \n\n Completely unacceptable review: the review is so deeply problematic that it makes you question this reviewer's future roles in ARR. This rubric should be used not for the more common cases of guidelines violations, but in extreme cases (e.g. clear violations of policy on AI assistance, extremely terse or rude reviews). This recommendation may be informed by the review issue reports from the authors, or something you noticed yourself. Note that the authors tend to only flag negative reviews, but positive reviews may also be problematic, e.g. when the paper is clearly deeply flawed but the reviewer recommends acceptance.",
        "value": {
            "param": {
                "type": "string",
                "input": "radio",
                "enum": [
                    "0: This review merits a 'great reviewer' award",
                    "1: This review is unacceptable in quality"
                ]
            }
        }
    },
    "justification": {
        "order": 2,
        "description": "Please add a short justification for your recommendation (1-3 sentences)",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 1000,
                "markdown": True,
                "input": "textarea",
                "optional": True
            }
        }
    }
}

arr_great_or_irresponsible_ac_content = {
    "rating": {
        "order": 1,
        "description": "This button allows to indicate which ACs did a great job or were highly irresponsible. See this post on the new peer review incentives at ACL venues:  https://aclrollingreview.org/incentives2025 \n\n Great meta-review: the AC went above expectations, e.g. in a highly rigorous meta-review, in extra effort to engage the reviewers or verify the claims of the submission, in ensuring that the process timeline was observed despite high volume of emergency reassignments. \n\n Completely unacceptable meta-review: the meta-review is so deeply problematic that it makes you question this AC's future roles in ARR. This rubric should be used not for the more common cases of guidelines violations, but in extreme cases (e.g. clear violations of policy on AI assistance, extremely terse or rude meta-reviews). This recommendation may be informed by the meta-review issue reports from the authors, or something you noticed yourself. Note that the authors tend to only flag negative meta-reviews, but positive reviews may also be problematic, e.g. when the paper is clearly deeply flawed but the AC recommends acceptance.",
        "value": {
            "param": {
                "type": "string",
                "input": "radio",
                "enum": [
                    "0: This meta-review merits a 'great area chair' award",
                    "1: This meta-review is unacceptable in quality"
                ]
            }
        }
    },
    "justification": {
        "order": 2,
        "description": "Please add a short justification for your recommendation (1-3 sentences)",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 1000,
                "markdown": True,
                "input": "textarea",
                "optional": True
            }
        }
    }
}