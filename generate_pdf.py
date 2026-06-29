#!/usr/bin/env python3
"""
Pure-Python PDF generator — English C1 Roadmap 2026
No external dependencies. Fixed xref table, correct object IDs.
"""

# ─── PDF Writer ───────────────────────────────────────────────────────────────

class PDFWriter:
    """Minimal but correct PDF 1.4 writer."""

    def __init__(self):
        self._objs = {}   # id -> bytes
        self._next = 1

    def reserve(self):
        oid = self._next
        self._next += 1
        return oid

    def put(self, oid: int, content: str):
        self._objs[oid] = content.encode('latin-1', errors='replace')

    def put_stream(self, oid: int, data: bytes):
        header = f'<< /Length {len(data)} >>\nstream\n'.encode()
        self._objs[oid] = header + data + b'\nendstream'

    def build(self) -> bytes:
        buf = bytearray()
        buf += b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        offsets = {}
        max_id = max(self._objs.keys())
        for oid in range(1, max_id + 1):
            if oid not in self._objs:
                continue
            offsets[oid] = len(buf)
            buf += f'{oid} 0 obj\n'.encode()
            buf += self._objs[oid]
            if not self._objs[oid].endswith(b'\n'):
                buf += b'\n'
            buf += b'endobj\n'
        xref_start = len(buf)
        buf += b'xref\n'
        buf += f'0 {max_id + 1}\n'.encode()
        buf += b'0000000000 65535 f \n'
        for i in range(1, max_id + 1):
            if i in offsets:
                buf += f'{offsets[i]:010d} 00000 n \n'.encode()
            else:
                buf += b'0000000000 65535 f \n'
        buf += b'trailer\n'
        buf += f'<< /Size {max_id + 1} /Root 1 0 R /Info 2 0 R >>\n'.encode()
        buf += b'startxref\n'
        buf += f'{xref_start}\n'.encode()
        buf += b'%%EOF\n'
        return bytes(buf)


# ─── Page stream builder ──────────────────────────────────────────────────────

PW, PH = 595, 842   # A4 points
M  = 36             # margin
CW = PW - 2 * M    # content width = 523

def hx(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i+2], 16) / 255 for i in (0, 2, 4))

def rgb(c):
    r, g, b = hx(c)
    return f'{r:.4f} {g:.4f} {b:.4f}'

class Stream:
    def __init__(self):
        self._ops = []

    def op(self, s):
        self._ops.append(s)

    # ── Shapes ──────────────────────────────────────────────────────────────

    def bg(self, color):
        self.op(f'{rgb(color)} rg 0 0 {PW} {PH} re f')

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=0.5):
        if fill:
            self.op(f'{rgb(fill)} rg')
        if stroke:
            self.op(f'{lw:.2f} w {rgb(stroke)} RG')
        if fill and stroke:
            self.op(f'{x:.1f} {y:.1f} {w:.1f} {h:.1f} re B')
        elif fill:
            self.op(f'{x:.1f} {y:.1f} {w:.1f} {h:.1f} re f')
        elif stroke:
            self.op(f'{x:.1f} {y:.1f} {w:.1f} {h:.1f} re S')

    def line(self, x1, y1, x2, y2, color, lw=0.5):
        self.op(f'{lw:.2f} w {rgb(color)} RG {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S')

    def vbar(self, x, y, h, color, lw=2):
        self.line(x, y, x, y + h, color, lw)

    # ── Text ────────────────────────────────────────────────────────────────

    def txt(self, x, y, s, font='F1', size=9, color='#e8e8f0'):
        if not s:
            return
        s = str(s)
        for old, new in [
            ('→','->'),('✕','x'),('●','*'),('▸','>'),('–','-'),('—','--'),
            ('"','"'),('"','"'),('\u2019',"'"),(''',"'"),(''',"'"),
            ('…','...'),('≥','>='),('×','x'),('\n',' ')
        ]:
            s = s.replace(old, new)
        s = s.encode('latin-1', errors='replace').decode('latin-1')
        s = s.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
        r, g, b = hx(color)
        self.op(f'BT /{font} {size} Tf {r:.4f} {g:.4f} {b:.4f} rg '
                f'{x:.1f} {y:.1f} Td ({s}) Tj ET')

    def txt_wrap(self, x, y, s, max_w, font='F1', size=9,
                 color='#e8e8f0', leading=None):
        """Wrap text, return y after last line."""
        if leading is None:
            leading = size * 1.35
        cw = size * 0.52
        limit = max(1, int(max_w / cw))
        words = str(s).split()
        lines, cur = [], ''
        for w in words:
            test = (cur + ' ' + w).strip()
            if len(test) <= limit:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        cy = y
        for ln in lines:
            self.txt(x, cy, ln, font, size, color)
            cy -= leading
        return cy

    def build(self) -> bytes:
        return '\n'.join(self._ops).encode('latin-1', errors='replace')


# ─── Phase colors & data ──────────────────────────────────────────────────────

PC = ['#6c63ff','#f7971e','#43e97b','#ff6584','#38f9d7']
PH_NAMES  = ['Fundament','Ob\'yom','Strogost','Polet','Privychki']
PH_WEEKS  = ['1-6','7-20','21-36','37-48','49-52']
PH_DUR    = ['6 ned.','14 ned.','16 ned.','12 ned.','4 ned.']
PH_TOPICS = [6,10,9,8,5]
PH_CODE   = ['FOUNDATION','VOLUME','PRECISION','FLIGHT','HABITS']

PHASES = [
  { 'n':'1','col':'#6c63ff','weeks':'1-6','dur':'6 ned.','ntop':6,'code':'FOUNDATION',
    'name':'Fundament',
    'desc':'Stroish myshlenie na angliyskom. AI -- ob\'yasnyayuschiy partner: govori vslukh, on ispravlyayet.',
    'skip':[
      'Present Perfect vs Past Simple -- slozhno na starte, dobavish v faze 2',
      'Uchebniki IELTS/TOEFL -- ekzamenatsionnyy format lomayet estestvennuyu rech na A1',
      'Perevod slozhnyh tekstov -- zakreplyayet russkoeyazychnoye myshlenie',
      'Tablitsy vseh nepr. glagolov -- snachala pattern, potom isklyucheniya',
    ],
    'topics':[
      ('N 1-2','IPA Fonetika','44 zvuka British RP: Forvo, Cambridge Dict. Minimal pairs: ship/sheep. Youglish po kazhdomu zvuku.','2 ned.',False),
      ('N 1-6','Ezhednevnoye govorenie 5 min','5 min s AI kazhdyy den. Tema -- tvoy den. Govori snachala, ispravlyay potom. Zapis v Otter.ai.','6 ned.',True),
      ('N 2-3','Present Simple + Continuous','Anki 150 kartochek -- kontekstnye predlozheniya. British Council Grammar. Tsel: 50 predlozheniy bez zapinki.','2 ned.',False),
      ('N 3-4','Top-500 slov -- yadro','Oxford 3000 -- pervye 500. Anki + audio Forvo. Slovo aktivno posle 3 ispolzovaniy vslukh.','2 ned.',False),
      ('N 4-5','Past Simple -- top-30 glagolov','go/went, see/saw, make/made. Anki + audio. AI: rasskazhi vcherashney den -- tolko Past Simple.','2 ned.',False),
      ('N 5-6','Voprosy i dialogovye patterny','Wh-voprosy + Yes/No. BBC Learning English Short Talks shadowing. 10 stsenariyev. AI roleplay.','2 ned.',False),
    ],
    'cap_title':'[Kapston 1] "Moya zhizn za 3 minuty" -- pervyy zhivoy razgovor',
    'cap':[
      '-> 5-min zvonok na Tandem/HelloTalk: rasskazhi o sebe bez zagotovok',
      '-> AI-razbor: zapis 3 min -> transkriptsiya -> top-5 oshibok',
      '-> Nazyvaesh 10 predmetov i opisyvaesh za 1 minutu bez paus',
      '-> Kriteriy: sobesednik ponyal i prodolzhil razgovor',
    ],
  },
  { 'n':'2','col':'#f7971e','weeks':'7-20','dur':'14 ned.','ntop':10,'code':'VOLUME',
    'name':'Ob\'yom',
    'desc':'Massovoe pogloschenie: grammatika, leksika, slushanie. AI -- trener beglosty, 10-minutnye sessii.',
    'skip':[
      'Subjunctive Mood -- redkaya struktura, ne nuzhna do B2',
      'Idiomy i sleng iz TikTok -- bez grammatiki zvuchat neusmestno',
      'Akademicheskoe pismo -- dlya ekzamena, ne dlya razgovora',
      'Parallelnyy uchebnik -- odin istochnik do kontsa (English Grammar in Use)',
      'Nativnye podkasty bez transkriptsii -- sozdayut illyuziyu ponimaniya',
    ],
    'topics':[
      ('N 7-9','Vremena glagola -- yadro','Murphy "English Grammar in Use" B1: Units 1-20. Vse vremena + Perfect. Anki 200 kart. AI: naumerenno ispolzuy vse vremena.','3 ned.',False),
      ('N 7-10','Slushanie -- transkript-metod','BBC 6 Minute English -- 3 epizoda/ned: slushay -> chitay transkript -> slushay bez teksta. Tsel: 70% bez transkripta.','4 ned.',True),
      ('N 9-11','Slovar 500->1500 slov','Oxford 3000: sleduyuschie 1000 slov tematich. klasterami. Anki + audio. Slovo aktivno posle 3 ispolzovaniy.','3 ned.',False),
      ('N 11-13','Modalnyye glagoly + Conditionals 0,1,2','Murphy Units 25-35. Anki deck na kazhdyy tip. AI roleplay: "Chto sdelayesh, yesli..." tolko s conditionals.','3 ned.',False),
      ('N 11-14','Razgovornaya praktika 15 min/den','Tandem 2x/ned. AI ezhednevno -- sluchaynaya tema. Zapis + analiz skorosti (slov/min).','4 ned.',True),
      ('N 13-15','Predlogi + Frazovye glagoly top-50','Prepositions of time/place/movement. pick up, turn off, give up. AI: mini-istoriya s kazdym glagolom.','3 ned.',False),
      ('N 15-17','Chtenie A2-B1','Penguin Readers L2-3: 1 kniga/2 ned (Forrest Gump Adapted). Kontekstnyy vyvod znacheniy. BBC News Simple.','3 ned.',False),
      ('N 17-19','Intonatsiya i svyaznaya rech',"Rachel's English: connected speech, linking, reduction. TED-Ed shadowing (5 raz). AI: otsenka naturalnosti.",'3 ned.',False),
      ('N 18-20','Passivnyy zalog + reported speech','Murphy Units 40-50. AI: pereskazi novost BBC tolko v reported speech.','3 ned.',True),
      ('N 19-20','Slovar 1500->2500','Oxford 3000 finalnyy blok + 100 kollokatsiy (make a decision, take a risk). Anki + AI-dialogi.','2 ned.',False),
    ],
    'cap_title':'[Kapston 2] "10 minut bez ostanovki" -- razgovor na B1',
    'cap':[
      '-> Zvonok Tandem/Preply 30 min na svobodnuyu temu bez zagotovok',
      '-> AI-audit: transkriptsiya -> % pravilnyh vremen, top-10 oshibok, slov/min',
      '-> Adaptirovannaya kniga vslukh 5 min na zapis -- bez paus (skip or guess)',
      '-> Kriteriy: skorost >= 90 slov/min, sobesednik ne peresprashivayet > 1r/5min',
    ],
  },
  { 'n':'3','col':'#43e97b','weeks':'21-36','dur':'16 ned.','ntop':9,'code':'PRECISION',
    'name':'Strogost',
    'desc':'Tochnost, proiznosheniye, realnyye usloviya. AI -- strogiy auditor: otmechayet kazhdyy lyap, stroyt error log.',
    'skip':[
      'Novyye temy iz Murphy -- grammatika zakryta v faze 2, tolko primeneniye',
      'Advanced IELTS writing -- lomayet estestvennuyu ustnuyu intonatsiyu',
      'Rasshireniye redkimi slovami -- 2500 slov dostatochno dlya B2, nuzhna glubina',
      'Serialy "dlya fona" -- passivnoye audirovaniye bez zadachi ne dayet progressa',
    ],
    'topics':[
      ('N 21-23','Aktsent i reduktsiya',"Rachel's English + TED Talks (Brene Brown). Vyberi odin dialekt (RP ili GA). AI: zapis 1 min -> razbor zvukov.",'3 ned.',False),
      ('N 21-36','Error Log -- dnevnik oshibok','Notion-tablitsa: data, oshibka, pravilno, kontekst. 3 zapisi posle kazhdoy AI-sessii. Raz v 2 ned: AI analizirует top-3 pattern.','16 ned.',True),
      ('N 23-26','Nativnyy slukh: serialy s zadaniyem','"Friends" ili "The Crown" -- ne dlya fona. 15 min -> pauza -> povtori frazu vslukh. 10 novykh vyrazheniy v Anki/den.','4 ned.',False),
      ('N 25-28','Slozhnyye grammatich. struktury','Cleft sentences, inversion (Never have I...), Conditional 3, mixed. Murphy Advanced Units 1-30.','4 ned.',False),
      ('N 27-30','Slovar 2500->4000','Oxford 5000 + Academic Word List (570 slov). Vocabulary.com. Test: 10 novykh slov v AI-razgovore bez podskazki.','4 ned.',True),
      ('N 29-32','Vstrechi s nositelyami','4 sessii iTalki s certified teacher. Tema -- vsegda novaya, predlozhena uchitelem. Error correction v realnom vremeni.','4 ned.',False),
      ('N 31-33','Kollokatsii i registry rechi','Oxford Collocations: 500 par. Formal vs Informal. AI roleplay: odna tema v dvukh registrakh (intervyu vs drug).','3 ned.',False),
      ('N 33-35','Originalnyye teksty -- pervaya kniga',"'The Alchemist' ili Sherlock Holmes. Pravilo 50. Kontekstnyy vyvod znacheniy. 20 str/den.",'3 ned.',False),
      ('N 35-36','Fluency drill -- skorost bez kachestva','2 min bez ostanovki (RandomWordGenerator.com). AI: tolko pauzy i slova-parazity. Tsel: >= 110 slov/min.','2 ned.',False),
    ],
    'cap_title':'[Kapston 3] "Zapis dlya YouTube" -- monolog 5 minut',
    'cap':[
      '-> Video 5 min bez stsenariya, tolko 3 tezisa. Opublikuy na YouTube',
      '-> AI-audit: error rate, pauzy, oshibki na minutu. Tsel: <= 3 oshibok/min',
      '-> iTalki-sessiya: uchitel smotrit video, dayet otsenku B2/C1 gotovnosti',
      '-> Kriteriy: nositel ponimayet bez usiliy, aktsent ne meshayet kommunikatsii',
    ],
  },
  { 'n':'4','col':'#ff6584','weeks':'37-48','dur':'12 ned.','ntop':8,'code':'FLIGHT',
    'name':'Polet',
    'desc':'Spontannaya rech, shirokiy slovar, C1-registry. AI -- simulator nositelya: neudob. temy, perebivaet, menyaet temu.',
    'skip':[
      'Novyye kartochki Anki bazovoy leksiki -- baza zakryta, tolko C1-frazeologiya',
      'Graded readers (adaptirovannye) -- zamedlyayut vospriyatiye nativnoy skorosti',
      'Peresprashivat sobesednika kazhdye 2 min -- treniruy inference iz konteksta',
      'Fokus na odnom aktse -- C1 ponimayet British, American, Australian, Indian',
    ],
    'topics':[
      ('N 37-39','Idiomy i razgovornye vyrazheniya C1','Oxford Dict of Idioms. Top-200 idiom po temam (business, emotions, time). AI: razgovor s 5 idiomami organichno.','3 ned.',False),
      ('N 37-48','Ezhednevnye AI-debaty 20 min','AI zadayet spornuyu temu. Ty zashchischaesh pozitsiyu 5 min -> AI kontrargumentiruyet -> ty otvechaesh. 12 nedel.','12 ned.',True),
      ('N 39-42','Slovar 4000->6000 slov','Oxford 5000 + C1 Word List. The Economist/Atlantic: 2 stati/ned, 10 slov. Test: ob\'yasni slovo bez perevoda.','4 ned.',False),
      ('N 40-43','Nativnyy kontent bez subtitrov','"How I Built This", "Lex Fridman Podcast". 30 min/den. Posle 15 min -- pereskaz AI. Tsel: >= 90% bez pomoschi.','4 ned.',True),
      ('N 42-45','Dlinnye razgovory 30+ min','Ezhenedelno: 45 min na Preply, tema predlozhena sobesednikom. Ne gotovitsya zaranee. AI-analiz posle.','4 ned.',False),
      ('N 44-46','Metafory, yumor, kulturnyy kod','The Office, Friends. British irony vs American sarcasm. KnowYourMeme. AI: small talk s yumorom.','3 ned.',False),
      ('N 45-47','Originalnaya literatura i non-fiction','"Sapiens" ili "Thinking Fast and Slow" -- original. 25 str/den bez slovarya. AI: obsudi kak s obrazovannym nositelem.','3 ned.',False),
      ('N 47-48','Simulyatsiya finalnogo razgovora','AI mock-intervyu: 30 min, 3 smeny temy. Otsenka kogezii, skorosti, TTR. Tsel: otsenka C1.','2 ned.',False),
    ],
    'cap_title':'[Kapston 4] "Neznakomaya tema, zhivoy nositel" -- 20 min bez podgotovki',
    'cap':[
      '-> Sessiya iTalki: nositel vybirayet temu iz 5. 20 min nepreryvnogo razgovora',
      '-> AI-audit: error rate, pauzy, TTR -- sravneniye s kapston-3 (delta rosta)',
      '-> Pereskaz stati The Economist (800 slov) za 3 min vslukh svoimi slovami',
      '-> Kriteriy: sobesednik otseniva uroven kak "advanced" bez podskazki',
    ],
  },
  { 'n':'5','col':'#38f9d7','weeks':'49-52','dur':'4 ned.','ntop':5,'code':'HABITS',
    'name':'Privychki',
    'desc':'Novyy material ne nuzhen -- nuzhna sistema. AI -- lichnyy kompas kachestva: ezhenedelnyy progress-report.',
    'skip':[
      'Novyye temy i uchebniki -- faza zakrytiya, ne rasshireniya',
      'Perekhod na drugoy dialekt -- smesheniye aktsentov khuzhe, chem odin chistyy',
      'Otkladyvaniye finalnogo razgovora -- kapston ne perenositsya',
    ],
    'topics':[
      ('N 49-50','Systema C1 -- daily stack','10 min Anki + 15 min nativnyy kontent + 10 min AI. Itogo 35 min/den. Habit tracker v Notion ili Streaks app.','2 ned.',False),
      ('N 49-52','Ezhenedelnyy AI progress-report','Kazhdoye voskresenye: 10 min po 5 metrikam -- skorost, error rate, TTR, pauzy, peresprasy. Graf progressa.','4 ned.',True),
      ('N 50-51','Finalnyy error-log razbor','Polnyy audit loga za 52 nedeli. Top-5 povtoryayuschkhsya oshibok. AI micro-drills. 3 dnya na kazhdyy pattern.','2 ned.',False),
      ('N 51-52','Karta svoyego angliyskogo','Top-5 instrumentov, chto bylo lishnim, samyy effektivnyy navyk. AI pomogaet strukturirovat. Publikuy.','2 ned.',False),
      ('N 52','Den finalnogo razgovora','iTalki: novyy nositel, on vybirayet temu. 30 minut. Nikakih tezisov. Zhivoy razgovor kak fakt, ne diplom.','1 ned.',False),
    ],
    'cap_title':'[Kapston 5 -- FINALNYY] "30 minut. Neznakomyy nositel. Ego tema. Bez podgotovki."',
    'cap':[
      '-> Sessiya iTalki: nositel vybirayet temu, ty govopish 30 minut svobodno',
      '-> Popros nositelya otsenit tvoy uroven v 1 predlozhenii -- "C1" = kriteriy',
      '-> AI finalnyy otchet: krivaya progressa vsekh 5 metrik za 52 nedeli',
      '-> Publikuesh zapis ili AI-sammari -- v sotsssetyakh, dnevnike. Stavka zakryta.',
    ],
  },
]


# ─── Page renderers ───────────────────────────────────────────────────────────

def render_cover(s: Stream):
    s.bg('#0d0d14')
    y = PH - M

    # Category bar
    s.rect(M, y-16, 280, 16, '#11111e', '#2a2a55', 0.5)
    s.txt(M+6, y-11, 'ANGLIISKIY YAZYK  *  2026  *  ROADMAP  *  V1.0', 'F2', 7, '#6c63ff')
    y -= 26

    # Main title
    for line, col in [('Top 1%','#ffffff'),("Nositel",'#a8a3ff'),('urovnya C1','#6c63ff')]:
        s.txt(M, y-4, line, 'F2', 34, col)
        y -= 40

    # Subtitle
    s.txt(M, y, '12 mesyacev * 52 nedeli * 5 faz * 38 tem * bez vody -- aktualno dlya 2026', 'F1', 9, '#7878a0')
    y -= 18

    # 4 stats
    sw = (CW - 18) // 4
    for i, (num, lbl, col) in enumerate([('52','Nedeli','#6c63ff'),('5','Faz','#f7971e'),
                                          ('38','Tem','#43e97b'),('5','Kaostonov','#ff6584')]):
        bx = M + i*(sw+6)
        s.rect(bx, y-56, sw, 56, '#16161f', '#242435', 0.5)
        s.txt(bx + sw//2 - len(num)*9, y-22, num, 'F2', 24, col)
        s.txt(bx + sw//2 - len(lbl)*3, y-37, lbl, 'F1', 7.5, '#7878a0')
    y -= 66

    # Divider
    s.line(M, y, M+CW, y, '#242435')
    y -= 14

    # Phase nav title
    s.txt(M, y, '> Navigatsiya po fazam', 'F2', 8, '#7878a0')
    y -= 14

    # Phase nav cards
    nw = (CW - 24) // 5
    for i in range(5):
        nx = M + i*(nw+6)
        s.rect(nx, y-76, nw, 76, '#16161f', PC[i], 0.8)
        s.txt(nx+nw//2-8, y-16, str(i+1), 'F2', 18, PC[i])
        s.txt(nx+4, y-31, 'NED '+PH_WEEKS[i], 'F1', 6.5, '#7878a0')
        s.txt(nx+4, y-42, PH_NAMES[i], 'F2', 8.5, '#e8e8f0')
        s.txt(nx+4, y-53, PH_DUR[i], 'F1', 7, '#7878a0')
        s.txt(nx+4, y-63, str(PH_TOPICS[i])+' tem', 'F1', 7, PC[i])
    y -= 86

    # Divider
    s.line(M, y, M+CW, y, '#242435')
    y -= 14

    # Final goal
    s.rect(M, y-54, CW, 54, '#0f0f1a', '#2a2a55', 0.8)
    s.vbar(M+2, y-51, 47, '#6c63ff', 2.5)
    s.txt(M+10, y-11, '> Finalnaya tsel', 'F2', 8, '#6c63ff')
    s.txt(M+10, y-24, '30-minutnyy razgovor s nositelem bez podgotovki', 'F2', 11, '#ffffff')
    s.txt(M+10, y-37, 'po teme, kotoruyu sobesednik vybirayet sam -- uverenno, bez paus na perevod', 'F1', 9, '#a8a3ff')


def render_philosophy(s: Stream):
    s.bg('#0d0d14')
    y = PH - M

    # Header
    s.rect(M, y-14, 28, 14, '#11111e', '#2a2a55', 0.5)
    s.txt(M+4, y-10, '02', 'F2', 8, '#6c63ff')
    s.txt(M+36, y-10, 'Filosofiya / Manifest', 'F2', 13, '#ffffff')
    y -= 24

    # Manifesto
    mh = 68
    s.rect(M, y-mh, CW, mh, '#0f0f1a', '#2a2a55', 0.5)
    s.vbar(M+2, y-mh+4, mh-8, '#6c63ff', 2.5)
    s.txt(M+10, y-10, 'PARADOKS:', 'F2', 8.5, '#6c63ff')
    manifest = [
        'Ty ne izuchaesh angliiskiy -- ty perestaesh perevodyt s russkogo.',
        'Pervyy mesyats kazhetsya medlennym: ty stroish myshlenie na drugom yazyke.',
        'Govori s pervogo dnya -- koryavo, netochno, vslukh. AI prinimaet lyuboy uroven',
        'i razbirает kazhdуyu oshibku. Snachala ob\'em -- potom tochnost.',
        'Cherez 52 nedeli ty ne "vyuchish" yazyk -- ty na nem zhivyosh.',
    ]
    my = y - 22
    for line in manifest:
        s.txt(M+10, my, line, 'F1', 8.5, '#c8c8e0')
        my -= 11
    y -= mh + 8

    # Principles 2x3 grid
    principles = [
        ('01','Glubina do uverennosti','Odin instrument do avtomatizma, prezhde chem sleduyuschiy. Anki-koloda zakryta kogda ne dumaesh o ney v razgovore.'),
        ('02','Osoznanny propusk -- chast plana','Kazhdaya faza imeet spisok "ne trogay seychas". Propuskat grammatiku na A1 -- disciplina, ne len.'),
        ('03','Top 1% -- eto privychki','52 ned x 7 dn x 20 min = ~121 chas aktivnoy praktiki. Nositel C1 otlichaetsya ezhednevnymi privychkami.'),
        ('04','Realnaya stavka obyazatelna','Kazhdyy kapston -- zhivoy sobesednik ili realnaya auditoriya. Trenirovochnyy polygon bez stavki ne zachityvaetsya.'),
        ('05','Ne ispolzuesh -- ne znaesh','Esli ne mozhesh ob\'yasnit zachem -- vybrosì instrument. Anki, shadowing -- vsyo trebuet ob\'yasneniya.'),
        ('06 AI','AI -- partner, ne kostyl','ChatGPT/Claude -- 24/7 nositel bez osuzhdeniya. Rol menyaetsya: partner -> trener -> auditor. Zhivoye obshcheniye on ne zamenyayet.'),
    ]
    pw2 = (CW - 6) // 2
    ph2 = 58
    px, py = M, y
    for i, (num, title, body) in enumerate(principles):
        fill = '#0f0f1e' if i==5 else '#11111a'
        stroke = '#3a3a77' if i==5 else '#242435'
        s.rect(px, py-ph2, pw2, ph2, fill, stroke, 0.5)
        s.txt(px+6, py-14, num, 'F2', 16, '#1e1e30')
        s.txt(px+6, py-27, title, 'F2', 8, '#a8a3ff' if i==5 else '#ffffff')
        s.txt_wrap(px+6, py-39, body, pw2-12, 'F1', 7.5, '#7878a0', 10)
        if i%2==0:
            px = M + pw2 + 6
        else:
            px = M
            py -= ph2 + 5
    y = py - 8

    # Phase table
    s.txt(M, y, '> Obzor faz', 'F2', 8, '#7878a0')
    y -= 12
    s.rect(M, y-14, CW, 14, '#16161f')
    cols_x = [M+4, M+22, M+90, M+355, M+410, M+460]
    for hdr, cx in zip(['#','Faza','Fokus','Ned.','Dlyt.','Tem'], cols_x):
        s.txt(cx, y-10, hdr.upper(), 'F2', 7, '#5858a0')
    y -= 14
    rows = [
        ('#6c63ff','1','Fundament','Bazovye konstruktsii + ezhednevnoe govorenie s AI','1-6','6 n.','6'),
        ('#f7971e','2','Ob\'yom','Grammatika, leksika, slushanie -- massovoe pogloschenie','7-20','14 n.','10'),
        ('#43e97b','3','Strogost','Tochnost, proiznosh., realnyye usloviya + error log','21-36','16 n.','9'),
        ('#ff6584','4','Polet','Spontannaya rech, shirokiy slovar, C1-registry','37-48','12 n.','8'),
        ('#38f9d7','5','Privychki','Sistema podderzhania C1 + finalnaya demonstratsiya','49-52','4 n.','5'),
    ]
    for col, n, name, focus, wk, dr, tc in rows:
        s.line(M, y, M+CW, y, '#1e1e2e', 0.3)
        s.txt(cols_x[0], y-10, n, 'F2', 9, col)
        s.txt(cols_x[1], y-10, name, 'F2', 8.5, '#e8e8f0')
        s.txt(cols_x[2], y-10, focus, 'F1', 7.5, '#7878a0')
        s.txt(cols_x[3], y-10, wk, 'F1', 8, '#7878a0')
        s.txt(cols_x[4], y-10, dr, 'F2', 8.5, col)
        s.txt(cols_x[5], y-10, tc, 'F2', 9, '#ffffff')
        y -= 16


def render_phase(s: Stream, ph: dict):
    s.bg('#0d0d14')
    col = ph['col']
    y = PH - M

    # Badge
    s.rect(M, y-15, CW, 15, '#0f0f1a', col, 0.6)
    s.txt(M+6, y-11, f"FAZA {ph['n']}  *  NED {ph['weeks']}  *  {ph['code']}", 'F2', 8, col)
    y -= 21

    # Title + mini stats (right)
    s.txt(M, y-4, ph['name'], 'F2', 20, col)
    sx = PW - M - 110
    s.txt(sx, y-5, f"Ned: {ph['weeks']}", 'F2', 8, col)
    s.txt(sx, y-15, f"Dur: {ph['dur']}", 'F2', 8, col)
    s.txt(sx, y-25, f"Tem: {ph['ntop']}", 'F2', 8, col)
    y -= 26

    # Desc
    y = s.txt_wrap(M, y, ph['desc'], CW-120, 'F1', 8.5, '#9090b8', 11)
    y -= 6

    # Skip box
    skip_h = 14 + len(ph['skip']) * 11 + 4
    s.rect(M, y-skip_h, CW, skip_h, '#120a0a', '#3d1a1a', 0.5)
    s.txt(M+6, y-10, 'x  PROPUSKAY NA ETOY FAZE:', 'F2', 8, '#ff6584')
    sy = y - 21
    for sk in ph['skip']:
        s.txt_wrap(M+8, sy, 'x  '+sk, CW-16, 'F1', 7.5, '#c8a0a0', 10)
        sy -= 11
    y -= skip_h + 6

    # Topics grid
    topics = ph['topics']
    ncols = 3 if len(topics) >= 7 else 2
    tw = (CW - (ncols-1)*5) // ncols
    avail_h = y - 70  # leave room for capstone
    nrows = (len(topics) + ncols - 1) // ncols
    th = max(58, min(80, avail_h // nrows - 4))

    for i, (wk, name, body, dur, par) in enumerate(topics):
        ci = i % ncols
        ri = i // ncols
        bx = M + ci*(tw+5)
        by = y - ri*(th+4)
        s.rect(bx, by-th, tw, th, '#16161f', '#242435', 0.5)
        s.vbar(bx+2, by-th+3, th-6, col, 2)
        s.txt(bx+8, by-10, wk, 'F2', 7, '#5858a0')
        nm = (name[:38]+'..') if len(name)>40 else name
        s.txt(bx+8, by-20, nm, 'F2', 8.5, '#ffffff')
        if par:
            s.txt(bx+8+len(nm)*5, by-20, ' [PAR]', 'F2', 6.5, '#38f9d7')
        body_lines = int((th-42)/9)
        s.txt_wrap(bx+8, by-31, body, tw-14, 'F1', 7, '#9090b8', 9)
        s.txt(bx+8, by-th+7, dur, 'F2', 7.5, col)

    y -= nrows*(th+4) + 4

    # Capstone
    ch = max(52, 16 + len(ph['cap'])*13 + 6)
    if y - ch < 14:
        ch = y - 14
    s.rect(M, y-ch, CW, ch, '#0f0f1a', col, 1.0)
    s.vbar(M+2, y-ch+3, ch-6, col, 3)
    s.txt(M+10, y-11, ph['cap_title'], 'F2', 9, '#ffffff')
    cy = y - 26
    for item in ph['cap']:
        s.txt_wrap(M+10, cy, item, CW-18, 'F1', 8, '#c8c8e0', 11)
        cy -= 13


def render_finish(s: Stream):
    s.bg('#0d0d14')
    y = PH - M

    # Header
    s.rect(M, y-14, 28, 14, '#1a0a0f', '#3d1a2a', 0.5)
    s.txt(M+4, y-10, '05', 'F2', 8, '#ff6584')
    s.txt(M+36, y-10, 'Final / Samoproverka', 'F2', 13, '#ffffff')
    y -= 26

    s.txt(M, y-4,  'Ty v top-1%,', 'F2', 20, '#ffffff')
    y -= 24
    s.txt(M, y-4,  'kogda --', 'F2', 20, '#6c63ff')
    y -= 20
    s.txt(M, y, 'Povedencheskie markery, a ne sertifikaty. Zamechaesh v razgovore, ne v teste.', 'F1', 9, '#7878a0')
    y -= 18

    markers = [
        ('#6c63ff','// BEGOST','Dumayesh na angliyskom, ne perevodish',
         'Vnutrenniy monolog perelyuchaetsya na angliiskiy. Pri chtenii znacheniye poyavlyaetsya srazu.'),
        ('#f7971e','// TOCHNOST','Slyshish oshibki u drugikh (i u sebya v zapisyakh)',
         'Kogda nositel govori nepr. -- zamechaesh. Zapis mesyachnoy davnosti -- slyshish chto kazalos normalnym.'),
        ('#43e97b','// VKUS','Vybiraesh slovo po nyuansu, ne pervoe popavsheyesya',
         'Mezhdu big/large/vast/enormous -- vybiraesh osoznanno. Chuvstvuesh kogda "however" tyazhelo.'),
        ('#ff6584','// STRESS','Neznakomaya tema vklyuchayet inference, ne paniku',
         '"I am not sure about the term, but what I mean is..." -- eto C1-otvet, ne proval.'),
        ('#38f9d7','// SISTEMA','35 minut v den ne oschuschayutsya kak uchyoba',
         'Podkast vo vremya edy, statya vmesto lenty. Yazyk vstroen v potok -- ne intensivnost, a ustoychivost.'),
        ('#a8a3ff','// AI-TOOL','Ispolzuesh AI kak zerkalo, a ne perevodchik',
         'Davno ne prosish "perevedi". Prosish "otsenyi ubeditelnost", "naydyi 3 tochnee". AI -- instrument samootsenki.'),
    ]
    mw = (CW-6)//2
    mh = 70
    mx0, my0 = M, y
    for i, (col, lbl, title, body) in enumerate(markers):
        ci = i % 2
        ri = i // 2
        bx = M + ci*(mw+6)
        by = my0 - ri*(mh+5)
        fill = '#0e0e1e' if i==5 else '#12121e'
        stroke = '#3a3a77' if i==5 else '#242435'
        s.rect(bx, by-mh, mw, mh, fill, stroke, 0.5)
        s.rect(bx, by, mw, 2, col)   # top accent
        s.txt(bx+8, by-12, lbl, 'F2', 7.5, col)
        s.txt(bx+8, by-24, title, 'F2', 9, '#ffffff')
        s.txt_wrap(bx+8, by-37, body, mw-14, 'F1', 7.5, '#7878a0', 10)
    y -= 3*(mh+5) + 10

    # Closing
    ch = 52
    s.rect(M, y-ch, CW, ch, '#0f0f1a', '#3a3a77', 0.8)
    s.txt(M+CW//2-185, y-14, 'Yazyk uchyat godami --', 'F2', 13, '#ffffff')
    s.txt(M+CW//2-215, y-30, 'nositеlyami stanovyatsya za 52 nedeli privychek.', 'F2', 11, '#6c63ff')
    s.txt(M+CW//2-215, y-44, 'Ne znanie delaet raznitsu -- to, chto ty delaesh kazhdyy den.', 'F1', 9, '#7878a0')

    # Footer
    y -= ch + 12
    s.line(M, y, M+CW, y, '#242435', 0.5)
    s.txt(M, y-9, 'ANGLIISKIY YAZYK * ROADMAP * 2026 * V1.0', 'F2', 7, '#5858a0')
    s.txt(PW-M-200, y-9, 'A1->C1 * 52 ned. * 5 faz * 38 tem * 5 kaostonov', 'F1', 7, '#5858a0')



# ─── Main assembly ────────────────────────────────────────────────────────────

def build_pdf() -> bytes:
    w = PDFWriter()

    # Object 1: Catalog (points to pages obj = 3)
    w.put(1, '<< /Type /Catalog /Pages 3 0 R >>')
    # Object 2: Info
    w.put(2, '<< /Title (Top 1% Nositel C1 -- English Roadmap 2026) /Author (Kiro) >>')
    # Object 3: Pages dict (filled in later, after we know kids)
    pages_id = 3
    # Object 4: Font F1 Helvetica
    w.put(4, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    # Object 5: Font F2 Helvetica-Bold
    w.put(5, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')

    font_res = '<< /F1 4 0 R /F2 5 0 R >>'
    next_id = 6

    def add_page(renderer_fn, *args) -> int:
        nonlocal next_id
        st = Stream()
        renderer_fn(st, *args)
        data = st.build()
        stream_id = next_id
        w.put_stream(stream_id, data)
        next_id += 1
        page_id = next_id
        w.put(page_id,
              f'<< /Type /Page /Parent {pages_id} 0 R '
              f'/MediaBox [0 0 {PW} {PH}] '
              f'/Contents {stream_id} 0 R '
              f'/Resources << /Font {font_res} >> >>')
        next_id += 1
        return page_id

    kids = []
    kids.append(add_page(lambda s: render_cover(s)))
    kids.append(add_page(lambda s: render_philosophy(s)))
    for ph in PHASES:
        kids.append(add_page(lambda s, p=ph: render_phase(s, p)))
    kids.append(add_page(lambda s: render_finish(s)))

    # Now fill object 3 (Pages)
    kids_str = ' '.join(f'{k} 0 R' for k in kids)
    w.put(pages_id, f'<< /Type /Pages /Kids [{kids_str}] /Count {len(kids)} >>')

    return w.build()


if __name__ == '__main__':
    print('Generating PDF...')
    data = build_pdf()
    out = '/projects/sandbox/english_roadmap_c1.pdf'
    with open(out, 'wb') as f:
        f.write(data)
    print(f'Written {len(data):,} bytes -> {out}')

    # Verify
    import re
    pages = len(re.findall(rb'/Type /Page ', data))
    has_xref = b'xref\n0 ' in data
    has_eof  = data.endswith(b'%%EOF\n')
    obj3_type = re.search(rb'3 0 obj\n(.*?)\nendobj', data, re.DOTALL)
    obj3_is_pages = obj3_type and b'/Type /Pages' in obj3_type.group(1)
    fonts_found = set(re.findall(rb'/BaseFont /(\w+)', data))
    print(f'Pages: {pages} (expect 8) -- {"OK" if pages==8 else "FAIL"}')
    print(f'xref correct: {has_xref} -- {"OK" if has_xref else "FAIL"}')
    print(f'EOF marker: {has_eof} -- {"OK" if has_eof else "FAIL"}')
    print(f'obj 3 is /Pages: {obj3_is_pages} -- {"OK" if obj3_is_pages else "FAIL"}')
    print(f'Fonts: {fonts_found}')
