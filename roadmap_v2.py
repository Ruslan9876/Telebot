#!/usr/bin/env python3
"""
English A2-B1 → C1 Roadmap PDF Generator — v2
Pure Python stdlib only. 36 weeks / 5 phases / 33 topics / 5 capstones.
A4 (595×842 pts), dark premium design.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PDF WRITER
# ═══════════════════════════════════════════════════════════════════════════════

class PDFWriter:
    def __init__(self):
        self._objs = {}

    def put(self, oid: int, content: str):
        self._objs[oid] = content.encode('latin-1', errors='replace')

    def put_stream(self, oid: int, data: bytes):
        hdr = f'<< /Length {len(data)} >>\nstream\n'.encode()
        self._objs[oid] = hdr + data + b'\nendstream'

    def build(self) -> bytes:
        buf = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offsets = {}
        max_id = max(self._objs)
        for oid in range(1, max_id + 1):
            if oid not in self._objs:
                continue
            offsets[oid] = len(buf)
            buf += f'{oid} 0 obj\n'.encode()
            buf += self._objs[oid]
            if not self._objs[oid].endswith(b'\n'):
                buf += b'\n'
            buf += b'endobj\n'
        xs = len(buf)
        buf += b'xref\n'
        buf += f'0 {max_id + 1}\n'.encode()
        buf += b'0000000000 65535 f \n'
        for i in range(1, max_id + 1):
            if i in offsets:
                buf += f'{offsets[i]:010d} 00000 n \n'.encode()
            else:
                buf += b'0000000000 65535 f \n'
        buf += (f'trailer\n<< /Size {max_id+1} /Root 1 0 R /Info 2 0 R >>\n'
                f'startxref\n{xs}\n%%EOF\n').encode()
        return bytes(buf)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE STREAM BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

PW, PH = 595, 842
M  = 32
CW = PW - 2 * M   # 531

def _hx(c):
    c = c.lstrip('#')
    return (int(c[0:2],16)/255, int(c[2:4],16)/255, int(c[4:6],16)/255)

def _rgb(c):
    r,g,b = _hx(c)
    return f'{r:.4f} {g:.4f} {b:.4f}'

def _esc(s):
    for a,b in [('→','->'),('✕','x'),('●','*'),('▸','>'),('–','-'),('—','--'),
                ('"','"'),('"','"'),(''', "'"),(''', "'"),('…','...'),
                ('≥','>='),('≤','<='),('×','x'),('\n',' '),('·','*')]:
        s = s.replace(a, b)
    return s.encode('latin-1', errors='replace').decode('latin-1') \
             .replace('\\','\\\\').replace('(','\\(').replace(')','\\)')

class S:
    """PDF content stream builder."""
    def __init__(self): self.o = []
    def _(self, x): self.o.append(x)

    def bg(self, c):
        self._(f'{_rgb(c)} rg 0 0 {PW} {PH} re f')

    def rf(self, x, y, w, h, fc=None, sc=None, lw=0.5):
        """rect: filled, stroked, or both."""
        if fc: self._(f'{_rgb(fc)} rg')
        if sc: self._(f'{lw:.2f} w {_rgb(sc)} RG')
        cmd = 'B' if (fc and sc) else ('f' if fc else 'S')
        self._(f'{x:.1f} {y:.1f} {w:.1f} {h:.1f} re {cmd}')

    def ln(self, x1,y1,x2,y2, c, lw=0.5):
        self._(f'{lw:.2f} w {_rgb(c)} RG {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S')

    def vbar(self, x, y, h, c, lw=2.5):
        self.ln(x, y, x, y+h, c, lw)

    def t(self, x, y, s, f='F1', sz=9, c='#e8e8f0'):
        if not s: return
        e = _esc(str(s))
        r,g,b = _hx(c)
        self._(f'BT /{f} {sz} Tf {r:.4f} {g:.4f} {b:.4f} rg '
               f'{x:.1f} {y:.1f} Td ({e}) Tj ET')

    def tw(self, x, y, s, mw, f='F1', sz=9, c='#e8e8f0', lh=None, maxlines=99):
        """Word-wrap text; returns y after last line."""
        if lh is None: lh = sz * 1.35
        cw = sz * 0.52
        lim = max(1, int(mw / cw))
        words = str(s).split()
        lines, cur = [], ''
        for w in words:
            test = (cur+' '+w).strip()
            if len(test) <= lim: cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        cy = y
        for ln in lines[:maxlines]:
            self.t(x, cy, ln, f, sz, c)
            cy -= lh
        return cy

    def build(self) -> bytes:
        return '\n'.join(self.o).encode('latin-1', errors='replace')



# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

BG    = '#09090f'
CARD  = '#13131c'
CARD2 = '#0f0f18'
BDR   = '#1e1e30'
BDR2  = '#2a2a42'
TXT   = '#ddddf0'
MUT   = '#6868a0'
MUT2  = '#9090b8'
WHT   = '#ffffff'

PC = ['#7c6fff', '#ff8c42', '#36d986', '#ff5577', '#00d4c8']
# phase accent colors: violet, amber, emerald, rose, cyan

PH_DATA = [
    # (num, weeks_range, dur_wk, n_topics, code, name_ru, accent_idx)
    (1, '1–5',   5,  5, 'BRIDGE',    'Разгон',      0),
    (2, '6–14',  9,  8, 'VOLUME',    'Объём',       1),
    (3, '15–25', 11, 9, 'PRECISION', 'Точность',    2),
    (4, '26–33', 8,  7, 'FLIGHT',    'Полёт',       3),
    (5, '34–36', 3,  4, 'IDENTITY',  'Идентичность',4),
]


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

PHASES = [
  {
    'n':1,'wr':'1–5','dw':5,'nt':5,'code':'BRIDGE','col':PC[0],
    'name':'Разгон',
    'desc': (
      'Переключаешь режим: с "изучаю язык" на "живу на языке". '
      'Claude выступает объясняющим партнёром — говоришь вслух любые фразы, '
      'он моментально исправляет и объясняет паттерн, не правило.'
    ),
    'skip': [
      'IELTS Vocabulary lists — экзаменационный регистр убивает разговорную беглость на старте',
      'Грамматика: Passive Voice, Subjunctive — сложность не нужна до уверенного B2',
      'Anki с картинками-переводами — на A2-B1 переводной режим тормозит, нужны контекстные предложения',
      'Подкасты без транскрипта — иллюзия понимания; до 70% comprehension только с текстом',
    ],
    'topics': [
      ('Н 1–2', 'Диагностика и обнуление установок',
       'LangCorrect.com: пишешь 10 предложений о себе — получаешь правки от носителей. '
       'Claude: 15-минутный разговор без остановок — Claude фиксирует топ-5 системных ошибок. '
       'Цель: честная карта стартового уровня.',
       '2 нед.', False),
      ('Н 1–5', 'Ежедневное говорение 10 мин',
       'Claude ежедневно: случайная тема из банка (погода→мнение→история). '
       'Правило: сначала говори 5 мин — потом разбор ошибок. '
       'Otter.ai записывает; сравниваешь темп нед 1 vs нед 5.',
       '5 нед.', True),
      ('Н 2–3', 'Грамматика: Present Perfect vs Past Simple',
       'Murphy "English Grammar in Use" (синяя): Units 7–14. '
       'Anki-колода 120 карточек — только контекстные предложения. '
       'Закрытие: 30 предложений вслух без запинки.',
       '2 нед.', False),
      ('Н 3–5', 'Словарь: 1500–2500 активных слов',
       'Oxford 3000 Word List — следующий блок от твоего уровня. '
       'Anki c Forvo-аудио: слово→пример→вслух. '
       'Тест: каждое новое слово — в предложении вслух за 3 сек.',
       '3 нед.', False),
      ('Н 4–5', 'Фонетика: stress и connected speech',
       'Speechling.com: тренажёр с мгновенным аудио-фидбэком от носителей. '
       'Rachel\'s English (YouTube) — "Reductions" плейлист: gonna/wanna/kinda. '
       'Shadowing: 1 абзац TED × 5 повторений вслух.',
       '2 нед.', False),
    ],
    'cap_name': 'Старт-спринт: 5 минут без остановки',
    'cap': [
      '5-минутный звонок на Tandem с носителем: расскажи о своей работе/учёбе — без заготовок',
      'Claude: запиши себя на 5 мин → загрузи транскрипт → получи список топ-7 ошибок с паттерном',
      'Speechling: пройди 20 фраз из набора "Daily Conversations" — оценка >= 3.5/5',
      'Критерий: собеседник понял тебя без переспросов, разговор продолжился',
    ],
  },
  {
    'n':2,'wr':'6–14','dw':9,'nt':8,'code':'VOLUME','col':PC[1],
    'name':'Объём',
    'desc': (
      'Строишь плотный B2-фундамент: грамматика + лексика + слушание одновременно. '
      'Claude становится тренером беглости — ежедневные 15-минутные диалоги '
      'с расширением тематики и принудительным использованием новых слов.'
    ),
    'skip': [
      'Advanced Grammar in Use (красная) — рано; синяя до автоматизма сначала',
      'Идиомы из списков "100 popular idioms" — без контекста оседают мёртвым грузом',
      'Изучение произношения по IPA таблицам — на этом этапе только аудио-shadowing',
      'Параллельный учебник или курс — один источник грамматики, иначе конфликт систем',
      'Speak-to-score приложения (Elsa, Speechify) — геймификация подменяет реальную речь',
    ],
    'topics': [
      ('Н 6–8', 'Грамматика B2: модальные, conditionals, пассив',
       'Murphy синяя: Units 25–55 (модальные + Conditionals 1-3 + Passive). '
       'Anki 200 карточек. Claude: каждый день — диалог с намеренным использованием '
       'изучаемой структуры. Закрытие: 0 ошибок в 20 предложениях.',
       '3 нед.', False),
      ('Н 6–10', 'Аудирование: транскрипт-метод',
       'BBC 6 Minute English — 4 эпизода/нед: слушай → транскрипт → слушай без текста. '
       'Цель к нед.10: 75% понимания без текста. '
       'Youglish: каждое новое слово — слушай в 5 контекстах.',
       '5 нед.', True),
      ('Н 8–10', 'Словарь 2500–3500: тематические кластеры',
       'Oxford 5000 по кластерам: Career, Society, Environment, Technology. '
       'Anki: front=контекст с пропуском, back=слово+пример. '
       'Норма: 15 новых слов/день × 5 дней.',
       '3 нед.', False),
      ('Н 10–12', 'Phrasal verbs: топ-80',
       'Phrasal Verb Organiser (Headway Publishers): тематические группы. '
       'Anki: только в предложении, никогда изолированно. '
       'Claude roleplay: мини-история, где каждое предложение содержит phrasal verb.',
       '3 нед.', False),
      ('Н 10–13', 'Разговор 20 мин/день — расширение тем',
       'iTalki Community Tutor: 2 сессии/нед × 30 мин. '
       'Claude: ежедневно — новая тема из списка (наука, деньги, политика, культура). '
       'Запись каждой сессии в Otter.ai → еженедельный разбор.',
       '4 нед.', True),
      ('Н 11–13', 'Чтение: адаптированные → оригинальные',
       'Penguin Readers Level 4 → Level 6 (одна книга). '
       'Затем: первые 50 страниц "The Alchemist" (Coelho) в оригинале. '
       'Правило 50: если >50 незнакомых слов/страницу — текст слишком сложный.',
       '3 нед.', False),
      ('Н 12–14', 'Reported speech + Cleft sentences',
       'Murphy синяя: Units 46–50. '
       'Cleft: "What I need is…", "It was John who…" — 30 Anki-карточек. '
       'Claude: перескажи новость BBC в reported speech — 5 предложений.',
       '3 нед.', False),
      ('Н 13–14', 'Коллокации: Oxford 3000 core',
       'Oxford Collocations Dictionary Online: 200 высокочастотных пар '
       '(make a decision, take a risk, heavy rain). '
       'Anki: front=глагол+существительное с пропуском. '
       'Норма: 10 новых коллокаций/день.',
       '2 нед.', False),
    ],
    'cap_name': 'B2-спринт: структурированный разговор 15 минут',
    'cap': [
      'iTalki certified teacher: 30-минутная сессия — тема предложена учителем, без подготовки',
      'Claude аудит: транскрипт → % правильных структур, топ-10 ошибок, сравнение с фазой 1',
      'Anki статистика: >= 2500 карточек "mature" (8+ дней без ошибки)',
      'Критерий: учитель не объяснял тебе слова — ты объяснял ему своё мнение',
    ],
  },
  {
    'n':3,'wr':'15–25','dw':11,'nt':9,'code':'PRECISION','col':PC[2],
    'name':'Точность',
    'desc': (
      'Выходишь из зоны комфорта: точность произношения, реальные условия, '
      'системные ошибки под микроскопом. '
      'Claude переходит в роль строгого аудитора — ведёт персональный error log, '
      'строит недельные паттерны ошибок, назначает хирургические drill-сессии.'
    ),
    'skip': [
      'Новые грамматические темы — грамматика закрыта. Сейчас только применение и исправление',
      'IELTS Writing Task 2 essays — письменный академический стиль ломает устную интонацию',
      'Расширение словаря ради числа — 3500 слов достаточно; сейчас нужна глубина использования',
      'Параллельный язык (испанский "для разнообразия") — конкурирует за ресурс фокуса',
    ],
    'topics': [
      ('Н 15–17', 'Произношение: акцент и интонация',
       'Speechling Premium: 30 мин/день — запись → оценка носителя в течение 24 ч. '
       'Forvo: каждое слово из error log — слушай + повторяй 10 раз. '
       'Выбор диалекта (RP или General American) — зафиксируй и не меняй.',
       '3 нед.', False),
      ('Н 15–25', 'Error Log — персональный журнал ошибок',
       'Notion-таблица: дата / ошибка / правильный вариант / тип (грамм./лекс./фонет.) / контекст. '
       'После каждого разговора — минимум 3 записи. '
       'Claude еженедельно: анализирует лог → топ-3 системных паттерна → drill на каждый.',
       '11 нед.', True),
      ('Н 17–20', 'Сериалы и подкасты без субтитров',
       '"The Crown" или "Fleabag" (Netflix): 20 мин/день — mirroring technique: '
       'пауза → повтори последнюю фразу вслух интонационно точно. '
       '"Hardcore History" (Carlin) или "99% Invisible" — без транскрипта, только контекст.',
       '4 нед.', False),
      ('Н 18–21', 'Словарь 3500–5000: Academic Word List',
       'Coxhead AWL (570 слов) полностью — Anki с академическими примерами. '
       'The Economist: 2 статьи/нед → 10 новых слов → Anki на следующий день. '
       'Тест: объясни слово без перевода, только через английский пример.',
       '4 нед.', False),
      ('Н 19–22', 'iTalki certified teacher × 8 сессий',
       'Еженедельно: 45-минутная сессия — тема предложена учителем. '
       'Учитель делает error correction в реальном времени (не потом). '
       'Каждую сессию записываешь → Claude разбирает топ-5 ошибок из записи.',
       '4 нед.', True),
      ('Н 21–23', 'Inversion и расширенные структуры C1',
       'Murphy Advanced (красная): Units 1–20 — inversion, emphasis, nominalisation. '
       '"Never have I…", "Not only did he…", "It is worth noting that…". '
       'Цель: 3 из этих структур в одном разговоре органично.',
       '3 нед.', False),
      ('Н 22–24', 'Fluency drill: скорость без остановок',
       'RandomWordGenerator.com: случайная тема → говори 3 мин без пауз. '
       'Claude фиксирует только: паузы >2 сек и слова-паразиты (um/like/you know). '
       'Целевая скорость: ≥ 115 слов/мин.',
       '3 нед.', False),
      ('Н 23–25', 'Регистры: formal vs informal vs spoken',
       'Oxford Living Dictionaries: одно слово — 3 контекста разных регистров. '
       'Claude roleplay: одна тема в трёх форматах — job interview / pub chat / academic panel. '
       'Anki с пометкой formal/informal/neutral.',
       '3 нед.', False),
      ('Н 24–25', 'Оригинальная книга: 100 страниц без словаря',
       '"Sapiens" (Harari) или "The Great Gatsby" — 15 стр/день. '
       'Правило: незнакомое слово — выводи из контекста, не ищи. '
       'Только если слово встретилось 3+ раза — добавляй в Anki.',
       '2 нед.', False),
    ],
    'cap_name': 'Публичный монолог: YouTube 5 минут',
    'cap': [
      'Запись видео: 5 мин на тему по твоему выбору — без сценария, только 3 тезиса. Публикуй (unlisted)',
      'Claude транскрипция → error rate, паузы/мин, слова-паразиты. Цель: ≤ 4 ошибки/мин',
      'Speechling: оценка произношения фрагмента 60 сек >= 4.0/5',
      'Критерий: незнакомый носитель понимает тебя без усилий — accent не мешает',
    ],
  },
  {
    'n':4,'wr':'26–33','dw':8,'nt':7,'code':'FLIGHT','col':PC[3],
    'name':'Полёт',
    'desc': (
      'Спонтанная речь на любую тему — без подготовки, без пауз на перевод. '
      'Claude симулирует носителя-эксперта: задаёт неудобные вопросы, '
      'перебивает, требует аргументации — готовит к непредсказуемому живому общению.'
    ),
    'skip': [
      'Новые карточки базовой лексики в Anki — база закрыта; сейчас только C1-фразеология и идиомы',
      'Adverb/adjective lists наизусть — без контекстного использования это мёртвый груз',
      'Онлайн-курсы уровня B2 (Coursera, etc.) — ты выше; формальные курсы замедляют',
    ],
    'topics': [
      ('Н 26–28', 'Идиомы и C1-фразеология: топ-150',
       'Oxford Dictionary of Idioms — тематические кластеры (time, business, emotions). '
       'Anki: front=ситуация, back=идиома+пример. '
       'Claude: разговор, где 5 идиом используются органично, не списком.',
       '3 нед.', False),
      ('Н 26–33', 'AI-дебаты: 25 мин/день',
       'Claude: спорная тема ежедневно — ты защищаешь позицию 7 мин → '
       'Claude контраргументирует → ты отвечаешь. '
       'Темы не повторяются. Claude оценивает: coherence, vocabulary range, fluency.',
       '8 нед.', True),
      ('Н 28–30', 'Нативный контент: подкасты без опоры',
       '"How I Built This" (Guy Raz), "Radiolab", "Freakonomics Radio". '
       '30 мин/день без транскрипта. После — 3-минутный пересказ Claude. '
       'Цель: ≥ 90% понимание без вспомогательных материалов.',
       '3 нед.', False),
      ('Н 29–31', 'Метафоры, юмор, культурный код',
       '"The Office US" и "Arrested Development" — British/American irony разница. '
       'KnowYourMeme.com: 20 актуальных мемов 2024–2026. '
       'Claude roleplay: small talk с юмором — носитель шутит, ты подхватываешь.',
       '3 нед.', False),
      ('Н 30–32', 'Длинные разговоры 45+ мин с носителями',
       'Preply: еженедельно 1 сессия × 60 мин — тема предложена репетитором, не тобой. '
       'Конверсационный клуб (Meetup.com или Discord "English Speaking"): 1×/нед. '
       'Правило: не готовиться к теме заранее.',
       '3 нед.', False),
      ('Н 31–33', 'Нон-фикшн в оригинале: 200 страниц',
       '"Thinking, Fast and Slow" (Kahneman) или "Educated" (Westover). '
       '25 стр/день без словаря. '
       'Claude: обсуди главу как с образованным носителем — аргументируй, не пересказывай.',
       '3 нед.', False),
      ('Н 32–33', 'Mock C1 speaking: симуляция экзамена',
       'Cambridge C1 Advanced Speaking Test format: Parts 1–4. '
       'Claude проводит полный 15-минутный mock: long turn → collaborative task → discussion. '
       'Оценка по Cambridge Assessment Speaking Grid (fluency/lexis/grammar/discourse).',
       '2 нед.', False),
    ],
    'cap_name': 'Незнакомая тема, живой носитель — 20 минут',
    'cap': [
      'iTalki certified teacher: тема выбрана учителем из 5 вариантов (ты не знаешь заранее) — 20 мин',
      'Claude: сравнение метрик с фазой 3 — error rate delta, скорость, лексическое разнообразие (TTR)',
      'Пересказ статьи The Economist (800 слов) за 3 мин вслух — своими словами, без текста',
      'Критерий: учитель оценил твой уровень как C1 без подсказки с твоей стороны',
    ],
  },
  {
    'n':5,'wr':'34–36','dw':3,'nt':4,'code':'IDENTITY','col':PC[4],
    'name':'Идентичность',
    'desc': (
      'Новый материал не нужен — нужна система. '
      'Claude становится зеркалом: еженедельный progress audit, '
      'отслеживание деградации навыков, финальная калибровка перед живым C1-разговором.'
    ),
    'skip': [
      'Новые темы и учебники — фаза закрытия, не расширения; новый материал дробит фокус',
      'Переход на другой диалект — RP или GA выбраны в фазе 3; смешение хуже, чем один чистый',
      'Откладывание финального разговора — капстоун не переносится, это финальное доказательство',
    ],
    'topics': [
      ('Н 34–35', 'Daily stack: 35 минут навсегда',
       '10 мин Anki (поддержание 5000+ слов) + 15 мин нативный контент + '
       '10 мин разговор с Claude. '
       'Habit tracker: Streaks (iOS) или Habitica. '
       'Система должна выдержать 5 лет — проверяешь, что стек реалистичен.',
       '2 нед.', False),
      ('Н 34–36', 'Еженедельный Claude progress audit',
       'Каждое воскресенье: 10-мин сессия по 5 метрикам — '
       'скорость речи / error rate / лексическое разнообразие (TTR) / паузы / переспросы. '
       'Claude строит недельный граф. Деградация метрики → немедленный drill-день.',
       '3 нед.', True),
      ('Н 35–36', 'Финальный error log: хирургический разбор',
       'Полный аудит Notion error log за 36 недель. '
       'Топ-5 паттернов ошибок по частоте. '
       'Claude строит персональные micro-drills: 3 дня × 15 мин на каждый паттерн.',
       '2 нед.', False),
      ('Н 36', 'День X: финальный разговор',
       'iTalki: новый носитель, которого ты не видел. '
       'Он выбирает тему разговора сам. 30 минут. Без тезисов. Без записи. '
       'Это не экзамен — это факт: ты говоришь на уровне C1.',
       '1 нед.', False),
    ],
    'cap_name': '30 минут. Незнакомый носитель. Его тема. Без подготовки.',
    'cap': [
      'Сессия iTalki: носитель выбирает тему — ты говоришь 30 мин уверенно, без пауз на перевод',
      'После: попроси носителя оценить уровень в одной фразе. "Advanced / C1" — финальный критерий',
      'Claude итоговый отчёт: кривая прогресса всех 5 метрик от нед.1 до нед.36',
      'Публикуешь Claude-summary разговора: в соцсетях или дневнике — реальная ставка закрыта',
    ],
  },
]



# ═══════════════════════════════════════════════════════════════════════════════
# RENDER: COVER
# ═══════════════════════════════════════════════════════════════════════════════

def render_cover(st: S):
    st.bg(BG)
    y = PH - M

    # ── decorative vertical accent bars ──
    for i, col in enumerate(PC):
        st.rf(PW - M - 6 - i*10, M, 4, PH - 2*M, col)

    # ── category bar ──
    st.rf(M, y-18, 300, 18, CARD2, PC[0], 0.6)
    st.t(M+8, y-13, 'АНГЛИЙСКИЙ ЯЗЫК  ·  2026  ·  ROADMAP  ·  V2.0', 'F2', 7.5, PC[0])
    y -= 28

    # ── main title ──
    st.t(M, y-6,  'Топ 1%',       'F2', 40, WHT)
    y -= 46
    st.t(M, y-6,  'Носитель',     'F2', 40, '#b0abff')
    y -= 46
    st.t(M, y-6,  'уровня C1',    'F2', 40, PC[0])
    y -= 52

    # ── subtitle ──
    sub = '36 недель · 5 фаз · 33 темы · без воды — инструменты 2026: Claude, Anki, iTalki, Speechling'
    st.tw(M, y, sub, CW - 60, 'F1', 9.5, MUT2)
    y -= 22

    # ── 4 stats ──
    sw = (CW - 18) // 4
    stats = [('36', 'недель', PC[0]), ('5', 'фаз', PC[1]),
             ('33', 'темы',   PC[2]), ('5', 'капстонов', PC[3])]
    for i, (num, lbl, col) in enumerate(stats):
        bx = M + i*(sw+6)
        st.rf(bx, y-62, sw, 62, CARD, BDR2, 0.5)
        st.rf(bx, y-62, sw, 3, col)                     # bottom accent
        num_x = bx + sw//2 - len(num)*10
        st.t(num_x, y-26, num, 'F2', 26, col)
        lbl_x = bx + sw//2 - len(lbl)*3
        st.t(lbl_x, y-42, lbl, 'F1', 7.5, MUT)
    y -= 72

    # ── divider ──
    st.ln(M, y, M+CW, y, BDR2)
    y -= 14

    # ── nav title ──
    st.t(M, y, '▸  Навигация по фазам', 'F2', 8, MUT)
    y -= 14

    # ── phase nav cards ──
    nw = (CW - 20) // 5
    nh = 88
    for i, (n, wr, dw, nt, code, name, _) in enumerate(PH_DATA):
        col = PC[i]
        nx = M + i*(nw+5)
        st.rf(nx, y-nh, nw, nh, CARD, col, 0.7)
        # top accent strip
        st.rf(nx, y, nw, 3, col)
        st.t(nx + nw//2 - 9, y-16, str(n), 'F2', 20, col)
        st.t(nx+4, y-33, 'НЕД '+wr, 'F1', 7, MUT)
        st.t(nx+4, y-45, name,      'F2', 9, WHT)
        st.t(nx+4, y-57, dw_str(dw), 'F1', 7.5, MUT)
        st.t(nx+4, y-69, str(nt)+' тем', 'F1', 7, col)
        st.t(nx+4, y-80, code,      'F2', 6.5, col)
    y -= nh + 12

    # ── divider ──
    st.ln(M, y, M+CW, y, BDR2)
    y -= 14

    # ── final goal box ──
    gh = 58
    st.rf(M, y-gh, CW, gh, CARD2, PC[0], 0.8)
    st.vbar(M+2, y-gh+3, gh-6, PC[0], 3)
    st.t(M+12, y-12, '▸  Финальная цель', 'F2', 8, PC[0])
    st.t(M+12, y-26, '30-минутный разговор с незнакомым носителем без подготовки', 'F2', 11.5, WHT)
    st.t(M+12, y-40, 'по теме, которую собеседник выбирает сам — уверенно, без пауз на перевод', 'F1', 9, '#a8a3ff')
    st.t(M+12, y-52, 'Стартовый уровень: A2–B1  ·  Длительность: 36 недель  ·  Инструмент: Claude + Anki + iTalki + Speechling', 'F1', 7.5, MUT)

def dw_str(n): return f'{n} нед.'



# ═══════════════════════════════════════════════════════════════════════════════
# RENDER: PHILOSOPHY
# ═══════════════════════════════════════════════════════════════════════════════

def render_philosophy(st: S):
    st.bg(BG)
    y = PH - M

    # header
    st.rf(M, y-16, 28, 16, CARD2, PC[0], 0.5)
    st.t(M+5, y-11, '02', 'F2', 8, PC[0])
    st.t(M+36, y-11, 'Философия / Манифест', 'F2', 14, WHT)
    y -= 26

    # manifesto
    mh = 72
    st.rf(M, y-mh, CW, mh, CARD2, PC[0], 0.5)
    st.vbar(M+2, y-mh+4, mh-8, PC[0], 3)
    st.t(M+12, y-11, 'ПАРАДОКС:', 'F2', 9, PC[0])
    manifest_lines = [
        'На уровне A2–B1 ты уже умеешь говорить — но не делаешь этого достаточно.',
        'Проблема не в грамматике и не в словарном запасе.',
        'Проблема в том, что ты всё ещё переводишь с русского — вместо того чтобы думать на английском.',
        'Эта программа не учит язык — она переключает режим мышления.',
        'Сначала объём живой речи, потом точность. Сначала смелость, потом шлифовка.',
        'Через 36 недель ты не "выучишь" С1 — ты будешь на нём жить.',
    ]
    my = y - 23
    for line in manifest_lines:
        st.t(M+12, my, line, 'F1', 8.5, '#c8c8e0')
        my -= 11
    y -= mh + 10

    # 6 principles — 2×3 grid
    principles = [
        (PC[0], '01', 'Глубина одного навыка — до уверенности',
         'Один инструмент до автоматизма — потом следующий. Anki-колода '
         'закрыта только когда не думаешь о ней в разговоре.'),
        (PC[1], '02', 'Осознанный пропуск — часть дизайна',
         'Каждая фаза имеет список "не трогай сейчас". Пропускать сложную '
         'грамматику на B1 — дисциплина. Преждевременная сложность создаёт страх.'),
        (PC[2], '03', 'Топ 1% — это привычки, не сложность',
         '36 нед × 7 дней × 25 мин = ~105 часов активной практики. '
         'Носитель C1 отличается не знанием редких слов, а ежедневным ритмом.'),
        (PC[3], '04', 'Реальная ставка обязательна',
         'Каждый капстоун — живой собеседник или реальная аудитория. '
         'iTalki, Tandem, YouTube. Тренировочный полигон без ставки не засчитывается.'),
        (PC[4], '05', 'Не объясняешь — значит не знаешь',
         'Если не можешь объяснить зачем используешь этот инструмент '
         'и что он меняет — выброси. Anki, shadowing, Claude — всё требует обоснования.'),
        ('#a8a3ff', '06', 'Claude: партнёр по объёму, не замена носителю',
         'Claude — 24/7 терпеливый аудитор без осуждения. Роль меняется: '
         'объясняющий партнёр → тренер беглости → строгий аудитор → симулятор носителя.'),
    ]
    pw2 = (CW - 6) // 2
    ph2 = 62
    px, py = M, y
    for i, (col, num, title, body) in enumerate(principles):
        fill = '#0e0e1d' if i==5 else CARD
        stroke = '#3a3a70' if i==5 else BDR
        st.rf(px, py-ph2, pw2, ph2, fill, stroke, 0.5)
        st.rf(px, py, pw2, 2, col)                  # top accent
        st.t(px+8, py-15, num, 'F2', 16, '#1a1a2e')
        st.t(px+8, py-28, title, 'F2', 8.5, WHT if i<5 else '#c8c3ff')
        st.tw(px+8, py-40, body, pw2-14, 'F1', 7.5, MUT, 10)
        if i % 2 == 0:
            px = M + pw2 + 6
        else:
            px = M
            py -= ph2 + 5
    y = py - 8

    # phase table
    st.t(M, y, '▸  Обзор всех фаз', 'F2', 8, MUT)
    y -= 12
    st.rf(M, y-14, CW, 14, '#12121e')
    hx_list = [M+4, M+22, M+95, M+360, M+415, M+465]
    for hdr, hxx in zip(['#','Фаза','Фокус','Недели','Длит.','Тем'], hx_list):
        st.t(hxx, y-10, hdr, 'F2', 7, '#505080')
    y -= 14

    table_rows = [
        (PC[0],'1','Разгон',     'Диагностика + базовая беглость + connected speech', '1–5',   '5 нед.', '5'),
        (PC[1],'2','Объём',      'B2-грамматика + лексика + аудирование + разговор',  '6–14',  '9 нед.', '8'),
        (PC[2],'3','Точность',   'Произношение + error log + C1-структуры + регистры','15–25', '11 нед.','9'),
        (PC[3],'4','Полёт',      'Спонтанная речь + идиомы + нон-фикшн + дебаты',     '26–33', '8 нед.', '7'),
        (PC[4],'5','Идентичность','Система поддержания + финальный живой разговор',   '34–36', '3 нед.', '4'),
    ]
    for col, n, name, focus, wk, dr, tc in table_rows:
        st.ln(M, y, M+CW, y, '#181828', 0.3)
        st.t(hx_list[0], y-10, n,    'F2', 9, col)
        st.t(hx_list[1], y-10, name, 'F2', 9, WHT)
        st.t(hx_list[2], y-10, focus,'F1', 7.5, MUT2)
        st.t(hx_list[3], y-10, wk,   'F1', 8,   MUT)
        st.t(hx_list[4], y-10, dr,   'F2', 8.5, col)
        st.t(hx_list[5], y-10, tc,   'F2', 9,   WHT)
        y -= 16



# ═══════════════════════════════════════════════════════════════════════════════
# RENDER: PHASE PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_phase(st: S, ph: dict):
    col = ph['col']
    st.bg(BG)
    y = PH - M

    # ── phase header strip ──
    st.rf(M, y-18, CW, 18, '#0c0c18', col, 0.7)
    badge = f"ФАЗА {ph['n']}  ·  НЕД {ph['wr']}  ·  {ph['code']}"
    st.t(M+8, y-13, badge, 'F2', 8.5, col)
    # right stats
    stats_x = PW - M - 108
    st.t(stats_x, y-6,  f"Нед: {ph['wr']}", 'F2', 8, col)
    st.t(stats_x, y-14, f"Дли: {ph['dw']} нед.", 'F2', 8, col)
    y -= 24

    # ── phase title ──
    st.t(M, y-5, ph['name'], 'F2', 22, col)
    y -= 30

    # ── description ──
    y = st.tw(M, y, ph['desc'], CW-110, 'F1', 9, MUT2, 12, 3)
    y -= 8

    # ── skip box ──
    skip_lines = ph['skip']
    sk_h = 14 + len(skip_lines)*12 + 4
    st.rf(M, y-sk_h, CW, sk_h, '#110808', '#3a1010', 0.5)
    st.t(M+8, y-10, '✕  ПРОПУСКАЙ НА ЭТОЙ ФАЗЕ:', 'F2', 8, PC[3])
    sy = y - 22
    for sk in skip_lines:
        st.tw(M+8, sy, '✕  '+sk, CW-16, 'F1', 7.5, '#c8a0a0', 10, 2)
        sy -= 12
    y -= sk_h + 7

    # ── topics grid ──
    topics = ph['topics']
    ncols = 3 if len(topics) >= 6 else 2
    tw_w = (CW - (ncols-1)*5) // ncols
    avail = y - 68
    nrows = (len(topics) + ncols-1) // ncols
    th = max(60, min(85, avail // nrows - 4))

    for i, (wk, name, body, dur, par) in enumerate(topics):
        ci = i % ncols
        ri = i // ncols
        bx = M + ci*(tw_w+5)
        by = y - ri*(th+4)
        # card
        st.rf(bx, by-th, tw_w, th, CARD, BDR, 0.4)
        st.vbar(bx+2, by-th+3, th-6, col, 2)
        # week label
        st.t(bx+9, by-10, wk, 'F2', 7, MUT)
        # name
        nm = (name[:40]+'..') if len(name) > 42 else name
        st.t(bx+9, by-21, nm, 'F2', 9, WHT)
        # parallel tag
        if par:
            tag_x = bx+9 + len(nm)*4.9
            st.rf(tag_x, by-23, 30, 10, '#061e1a', '#00d4c8', 0.5)
            st.t(tag_x+2, by-20, 'PAR', 'F2', 5.5, '#00d4c8')
        # body
        st.tw(bx+9, by-33, body, tw_w-16, 'F1', 7, '#9090b8', 9,
              max(2, int((th-45)/9)))
        # duration
        st.t(bx+9, by-th+8, dur, 'F2', 7.5, col)

    y -= nrows*(th+4) + 4

    # ── capstone ──
    cap_lines = ph['cap']
    ch = max(56, 18 + len(cap_lines)*14 + 6)
    if y - ch < 12: ch = y - 12
    st.rf(M, y-ch, CW, ch, '#0c100c', col, 1.0)
    st.vbar(M+2, y-ch+3, ch-6, col, 3)
    st.t(M+12, y-12, f"→  КАПСТОУН ФАЗЫ {ph['n']}:", 'F2', 8, col)
    st.t(M+12, y-24, ph['cap_name'], 'F2', 10, WHT)
    cy = y - 38
    for item in cap_lines:
        st.tw(M+12, cy, item, CW-20, 'F1', 8, '#d0d0e8', 11, 2)
        cy -= 14



# ═══════════════════════════════════════════════════════════════════════════════
# RENDER: FINISH PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def render_finish(st: S):
    st.bg(BG)
    y = PH - M

    # header
    st.rf(M, y-16, 28, 16, '#1a0812', '#3d1030', 0.5)
    st.t(M+5, y-11, '07', 'F2', 8, PC[3])
    st.t(M+36, y-11, 'Финиш / Самопроверка', 'F2', 14, WHT)
    y -= 26

    # question
    st.t(M, y-5,  'Ты в топ-1%,', 'F2', 22, WHT)
    y -= 28
    st.t(M, y-5,  'когда —',       'F2', 22, PC[0])
    y -= 22
    st.t(M, y, 'Поведенческие маркеры, а не сертификаты. Замечаешь в разговоре — не в тесте.', 'F1', 9.5, MUT)
    y -= 20

    # 6 markers — 2×3 grid
    markers = [
        (PC[0], '// БЕГЛОСТЬ',
         'Думаешь на английском, не переводишь',
         'Внутренний монолог переключился на английский в моменты концентрации. '
         'При чтении значение появляется сразу — без промежуточного русского слова.'),
        (PC[1], '// ТОЧНОСТЬ',
         'Слышишь ошибки у других — и у себя в старых записях',
         'Слушая запись месячной давности — слышишь то, что раньше казалось нормальным. '
         'Error log пустеет — системные паттерны устранены.'),
        (PC[2], '// ВКУС',
         'Выбираешь слово по нюансу, не первое попавшееся',
         'Между big/large/vast/enormous — выбираешь осознанно. '
         'Чувствуешь, когда "however" звучит тяжело, а "but" — живее.'),
        (PC[3], '// СТОЙКОСТЬ',
         'Незнакомая тема не вызывает паники, а включает inference',
         '"I\'m not sure about the exact term, but what I mean is..." — '
         'это C1-ответ, а не провал. Строишь из того, что есть.'),
        (PC[4], '// СИСТЕМА',
         '35 минут в день не ощущаются как учёба — это просто жизнь',
         'Подкаст во время еды, статья вместо ленты, Claude пока ждёшь. '
         'Язык встроен в поток — не интенсивность, а устойчивость.'),
        ('#a8a3ff', '// AI-ИНСТРУМЕНТ',
         'Используешь Claude как зеркало, не как переводчик',
         'Давно не просишь "переведи". Просишь: "оцени убедительность", '
         '"найди 3 слова точнее", "где потерял темп". AI — инструмент самооценки.'),
    ]
    mw = (CW - 6) // 2
    mh = 76
    mx0, my0 = M, y
    for i, (col, lbl, title, body) in enumerate(markers):
        ci = i % 2
        ri = i // 2
        bx = M + ci*(mw+6)
        by = my0 - ri*(mh+5)
        fill = '#0d0d1e' if i==5 else CARD
        stroke = '#3a3a70' if i==5 else BDR
        st.rf(bx, by-mh, mw, mh, fill, stroke, 0.5)
        st.rf(bx, by, mw, 3, col)              # top accent
        st.t(bx+9, by-13, lbl,   'F2', 7.5, col)
        st.t(bx+9, by-25, title, 'F2', 9.5, WHT)
        st.tw(bx+9, by-38, body, mw-16, 'F1', 7.5, MUT, 10, 3)
    y -= 3*(mh+5) + 12

    # closing line
    cl_h = 56
    st.rf(M, y-cl_h, CW, cl_h, CARD2, PC[0], 0.8)
    ctr = M + CW//2
    st.t(ctr-200, y-14, 'Язык учат годами —', 'F2', 14, WHT)
    st.t(ctr-240, y-31, 'носителями становятся за 36 недель привычек.', 'F2', 12, PC[0])
    st.t(ctr-235, y-46, 'Не знание делает разницу — делает разницу то, что ты делаешь каждый день.', 'F1', 9, MUT)

    # footer
    y -= cl_h + 12
    st.ln(M, y, M+CW, y, BDR, 0.4)
    st.t(M,         y-9, 'АНГЛИЙСКИЙ ЯЗЫК  ·  ROADMAP  ·  2026  ·  V2.0', 'F2', 7, '#404060')
    st.t(PW-M-220,  y-9, 'A2-B1 → C1  ·  36 нед.  ·  5 фаз  ·  33 темы  ·  5 капстонов', 'F1', 7, '#404060')



# ═══════════════════════════════════════════════════════════════════════════════
# ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════

def build_pdf() -> bytes:
    w = PDFWriter()

    # Fixed object map:
    #  1 = Catalog   2 = Info    3 = Pages (dict)
    #  4 = Font F1   5 = Font F2
    #  then pairs: (stream, page) × N pages

    w.put(1, '<< /Type /Catalog /Pages 3 0 R >>')
    w.put(2, '<< /Title (Top 1% Nositel C1 — English Roadmap 2026) /Author (Kiro) >>')
    # obj 3 reserved for Pages dict — filled after we know all page IDs
    w.put(4, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica '
             '/Encoding /WinAnsiEncoding >>')
    w.put(5, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold '
             '/Encoding /WinAnsiEncoding >>')

    FR = '<< /F1 4 0 R /F2 5 0 R >>'
    next_id = [6]   # mutable counter

    def add_page(fn, *args) -> int:
        st = S()
        fn(st, *args)
        sid = next_id[0]; next_id[0] += 1
        w.put_stream(sid, st.build())
        pid = next_id[0]; next_id[0] += 1
        w.put(pid,
              f'<< /Type /Page /Parent 3 0 R '
              f'/MediaBox [0 0 {PW} {PH}] '
              f'/Contents {sid} 0 R '
              f'/Resources << /Font {FR} >> >>')
        return pid

    kids = []
    kids.append(add_page(lambda s: render_cover(s)))
    kids.append(add_page(lambda s: render_philosophy(s)))
    for ph in PHASES:
        kids.append(add_page(lambda s, p=ph: render_phase(s, p)))
    kids.append(add_page(lambda s: render_finish(s)))

    kids_str = ' '.join(f'{k} 0 R' for k in kids)
    w.put(3, f'<< /Type /Pages /Kids [{kids_str}] /Count {len(kids)} >>')

    return w.build()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import re, sys
    print('Building English A2→C1 Roadmap PDF v2...')

    data = build_pdf()
    out = '/projects/sandbox/english_roadmap_v2.pdf'
    with open(out, 'wb') as f:
        f.write(data)

    # ── verification ──
    pages   = len(re.findall(rb'/Type /Page ', data))
    xref_ok = b'xref\n0 ' in data
    eof_ok  = data.endswith(b'%%EOF\n')
    obj3    = re.search(rb'3 0 obj\n(.*?)\nendobj', data, re.DOTALL)
    o3_pages = obj3 and b'/Type /Pages' in obj3.group(1)
    fonts   = set(re.findall(rb'/BaseFont /(\S+)', data))
    streams = data.count(b'stream\n')

    print(f'  File:    {len(data):,} bytes → {out}')
    print(f'  Pages:   {pages}  (expect 8)   {"OK" if pages==8 else "FAIL"}')
    print(f'  xref:    {"OK" if xref_ok else "FAIL"}')
    print(f'  EOF:     {"OK" if eof_ok  else "FAIL"}')
    print(f'  obj3=Pages: {"OK" if o3_pages else "FAIL"}')
    print(f'  Fonts:   {[f.decode() for f in fonts]}')
    print(f'  Streams: {streams}')

    # numeric check
    total_wk  = sum(d[2] for d in PH_DATA)
    total_top = sum(d[3] for d in PH_DATA)
    caps      = len(PHASES)
    print(f'\n  Numeric logic:')
    print(f'  Total weeks:  {total_wk}  (expect 36)  {"OK" if total_wk==36 else "FAIL"}')
    print(f'  Total topics: {total_top} (expect 33)  {"OK" if total_top==33 else "FAIL"}')
    print(f'  Capstones:    {caps}     (expect 5)   {"OK" if caps==5 else "FAIL"}')
    # week coverage
    prev = 0
    ok = True
    for n, wr, dw, *_ in PH_DATA:
        s, e = map(int, wr.split('–'))
        if s != prev+1: ok = False
        if e-s+1 != dw: ok = False
        prev = e
    print(f'  Week coverage 1–{prev}: {"OK" if ok and prev==36 else "FAIL"}')
    print(f'  Distribution: {[d[2] for d in PH_DATA]} (non-linear: {"OK" if PH_DATA[0][2]<PH_DATA[1][2] and PH_DATA[-1][2]<PH_DATA[-2][2] else "check"})')

    if pages==8 and xref_ok and eof_ok and o3_pages and total_wk==36:
        print('\n  ALL CHECKS PASSED')
    else:
        print('\n  SOME CHECKS FAILED')
        sys.exit(1)
