#!/usr/bin/env python3
"""
Pure-Python PDF generator for the English C1 Roadmap.
Uses only Python stdlib (struct, zlib) — no external dependencies.
Produces a properly formatted A4 PDF with multiple pages.
"""

import zlib
import struct
from datetime import datetime

# ─── PDF low-level helpers ────────────────────────────────────────────────────

class PDFWriter:
    def __init__(self):
        self.objects = []      # list of (obj_id, content_bytes)
        self.obj_id = 0
        self.pages = []
        self.fonts = {}
        self.font_objs = {}

    def new_id(self):
        self.obj_id += 1
        return self.obj_id

    def add_object(self, content: str) -> int:
        oid = self.new_id()
        self.objects.append((oid, content.encode('latin-1', errors='replace')))
        return oid

    def add_object_raw(self, content: bytes) -> int:
        oid = self.new_id()
        self.objects.append((oid, content))
        return oid

    def build(self) -> bytes:
        buf = bytearray()
        buf += b'%PDF-1.4\n'
        buf += b'%\xe2\xe3\xcf\xd3\n'  # binary comment

        offsets = {}
        for oid, content in self.objects:
            offsets[oid] = len(buf)
            buf += f'{oid} 0 obj\n'.encode()
            buf += content
            if not content.endswith(b'\n'):
                buf += b'\n'
            buf += b'endobj\n'

        xref_offset = len(buf)
        buf += b'xref\n'
        buf += f'0 {self.obj_id + 1}\n'.encode()
        buf += b'0000000000 65535 f \n'
        for i in range(1, self.obj_id + 1):
            if i in offsets:
                buf += f'{offsets[i]:010d} 00000 n \n'.encode()
            else:
                buf += b'0000000000 65535 f \n'

        buf += b'trailer\n'
        buf += f'<< /Size {self.obj_id + 1} /Root 1 0 R /Info 2 0 R >>\n'.encode()
        buf += b'startxref\n'
        buf += f'{xref_offset}\n'.encode()
        buf += b'%%EOF\n'
        return bytes(buf)


# ─── Color helpers ────────────────────────────────────────────────────────────

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


def rgb_str(h):
    r, g, b = hex_to_rgb(h)
    return f'{r:.4f} {g:.4f} {b:.4f}'


# ─── Page content builder ─────────────────────────────────────────────────────

# A4: 595 x 842 pts  (1pt = 1/72 inch)
PW, PH = 595, 842
MARGIN = 36
CW = PW - 2 * MARGIN  # content width = 523

COLORS = {
    'bg':      '#0d0d14',
    'card':    '#16161f',
    'border':  '#242435',
    'text':    '#e8e8f0',
    'muted':   '#7878a0',
    'accent':  '#6c63ff',
    'accent2': '#ff6584',
    'accent3': '#43e97b',
    'accent4': '#f7971e',
    'accent5': '#38f9d7',
    'white':   '#ffffff',
    'ph1':     '#6c63ff',
    'ph2':     '#f7971e',
    'ph3':     '#43e97b',
    'ph4':     '#ff6584',
    'ph5':     '#38f9d7',
}

def c(name): return hex_to_rgb(COLORS[name])
def cs(name): return rgb_str(COLORS[name])

class PageBuilder:
    """Builds PDF page content stream."""

    def __init__(self, width=PW, height=PH):
        self.w = width
        self.h = height
        self.ops = []
        self.y = height - MARGIN  # current y (top-down)

    def _y(self, y): return y  # PDF coords are bottom-up; we handle externally

    def op(self, s): self.ops.append(s)

    def fill_page(self, color_hex):
        r, g, b = hex_to_rgb(color_hex)
        self.op(f'{r:.4f} {g:.4f} {b:.4f} rg')
        self.op(f'0 0 {self.w} {self.h} re f')

    def rect_filled(self, x, y, w, h, color_hex):
        r, g, b = hex_to_rgb(color_hex)
        self.op(f'{r:.4f} {g:.4f} {b:.4f} rg')
        self.op(f'{x:.2f} {y:.2f} {w:.2f} {h:.2f} re f')

    def rect_stroke(self, x, y, w, h, color_hex, lw=0.5):
        r, g, b = hex_to_rgb(color_hex)
        self.op(f'{lw:.2f} w')
        self.op(f'{r:.4f} {g:.4f} {b:.4f} RG')
        self.op(f'{x:.2f} {y:.2f} {w:.2f} {h:.2f} re S')

    def rect_filled_stroke(self, x, y, w, h, fill_hex, stroke_hex, lw=0.5):
        fr, fg, fb = hex_to_rgb(fill_hex)
        sr, sg, sb = hex_to_rgb(stroke_hex)
        self.op(f'{lw:.2f} w')
        self.op(f'{fr:.4f} {fg:.4f} {fb:.4f} rg')
        self.op(f'{sr:.4f} {sg:.4f} {sb:.4f} RG')
        self.op(f'{x:.2f} {y:.2f} {w:.2f} {h:.2f} re B')

    def line_h(self, x, y, length, color_hex, lw=0.5):
        r, g, b = hex_to_rgb(color_hex)
        self.op(f'{lw:.2f} w')
        self.op(f'{r:.4f} {g:.4f} {b:.4f} RG')
        self.op(f'{x:.2f} {y:.2f} m {x+length:.2f} {y:.2f} l S')

    def line_v(self, x, y, height, color_hex, lw=1.5):
        r, g, b = hex_to_rgb(color_hex)
        self.op(f'{lw:.2f} w')
        self.op(f'{r:.4f} {g:.4f} {b:.4f} RG')
        self.op(f'{x:.2f} {y:.2f} m {x:.2f} {y+height:.2f} l S')

    def circle_filled(self, cx, cy, r, color_hex):
        k = 0.5523
        ops_c = hex_to_rgb(color_hex)
        self.op(f'{ops_c[0]:.4f} {ops_c[1]:.4f} {ops_c[2]:.4f} rg')
        self.op(f'{cx-r:.2f} {cy:.2f} m')
        self.op(f'{cx-r:.2f} {cy+k*r:.2f} {cx-k*r:.2f} {cy+r:.2f} {cx:.2f} {cy+r:.2f} c')
        self.op(f'{cx+k*r:.2f} {cy+r:.2f} {cx+r:.2f} {cy+k*r:.2f} {cx+r:.2f} {cy:.2f} c')
        self.op(f'{cx+r:.2f} {cy-k*r:.2f} {cx+k*r:.2f} {cy-r:.2f} {cx:.2f} {cy-r:.2f} c')
        self.op(f'{cx-k*r:.2f} {cy-r:.2f} {cx-r:.2f} {cy-k*r:.2f} {cx-r:.2f} {cy:.2f} c f')

    def set_font(self, name, size):
        self.op(f'/{name} {size} Tf')

    def set_text_color(self, color_hex):
        r, g, b = hex_to_rgb(color_hex)
        self.op(f'{r:.4f} {g:.4f} {b:.4f} rg')

    def text(self, x, y, s, font='F1', size=9, color='#e8e8f0'):
        if not s:
            return
        r, g, b = hex_to_rgb(color)
        safe = s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        # Replace common unicode
        safe = safe.replace('→', '->').replace('✕', 'x').replace('●', '*')
        safe = safe.replace('▸', '>').replace('–', '-').replace('—', '--')
        safe = safe.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        safe = safe.replace('…', '...').replace('≥', '>=').replace('×', 'x')
        safe = safe.encode('latin-1', errors='replace').decode('latin-1')
        self.op(f'BT /{font} {size} Tf {r:.4f} {g:.4f} {b:.4f} rg {x:.2f} {y:.2f} Td ({safe}) Tj ET')

    def text_wrapped(self, x, y, text_str, max_width, font='F1', size=9,
                     color='#e8e8f0', line_height=None, char_width_factor=0.55):
        """Wrap text and return final y position after last line."""
        if line_height is None:
            line_height = size * 1.4
        words = str(text_str).split()
        lines = []
        line = ''
        char_w = size * char_width_factor
        max_chars = int(max_width / char_w)
        for word in words:
            test = (line + ' ' + word).strip()
            if len(test) <= max_chars:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        cur_y = y
        for ln in lines:
            self.text(x, cur_y, ln, font, size, color)
            cur_y -= line_height
        return cur_y

    def build(self):
        return '\n'.join(self.ops)



# ─── Content definitions ──────────────────────────────────────────────────────

PHASES = [
    {
        'num': '1', 'weeks': '1-6', 'dur': '6 нед.', 'topics_count': 6,
        'color': '#6c63ff', 'code': 'FOUNDATION',
        'name': 'Фундамент',
        'desc': 'Строишь мышление на английском. AI-собеседник: объясняющий партнёр -- говоришь вслух, он исправляет, объясняет, повторяет.',
        'skip': [
            'Present Perfect vs Past Simple -- разграничение убивает скорость на старте; добавишь в фазе 2',
            'Учебники IELTS/TOEFL -- экзаменационный формат ломает естественную речь на A1',
            'Перевод сложных текстов -- закрепляет русскоязычное мышление',
            'Таблицы всех неправильных глаголов -- сначала паттерн, потом исключения',
        ],
        'topics': [
            ('НЕД 1-2', 'Фонетика и алфавит произношения',
             'IPA (44 звука RP): Forvo, Cambridge Dictionary -- слушай и повторяй. Minimal pairs: ship/sheep, bit/beat. Youglish по каждому звуку.',
             '2 нед.', False),
            ('НЕД 1-6', 'Ежедневное говорение 5 мин/день',
             '5 минут с AI ежедневно. Тема -- твой день. Говори сначала, исправляй потом. Запись голоса в Otter.ai.',
             '6 нед.', True),
            ('НЕД 2-3', 'Present Simple + Present Continuous',
             'Anki 150 карточек -- контекстные предложения, не переводы слов. British Council Grammar Guide. Цель: 50 предложений вслух без запинки.',
             '2 нед.', False),
            ('НЕД 3-4', 'Топ-500 слов -- ядерный словарный запас',
             'Oxford 3000 Word List -- первые 500. Anki с аудио Forvo. Слово активно только после 3 использований вслух.',
             '2 нед.', False),
            ('НЕД 4-5', 'Past Simple -- регулярные и топ-30 нерегулярных',
             'Топ-30 неправильных глаголов (go/went, see/saw). Anki + аудио. AI: расскажи вчерашний день только на Past Simple.',
             '2 нед.', False),
            ('НЕД 5-6', 'Базовые вопросы и диалоговые паттерны',
             'Wh-вопросы + Yes/No. Shadowing: BBC Learning English Short Talks. 10 сценариев: знакомство, покупка, заказ еды. AI roleplay.',
             '2 нед.', False),
        ],
        'capstone_title': '«Моя жизнь за 3 минуты» -- первый живой разговор',
        'capstone': [
            '5-минутный звонок на Tandem/HelloTalk: расскажи о себе без заготовок',
            'AI-разбор: запись 3 мин -> транскрипция -> Claude выдаёт топ-5 ошибок',
            'Называешь 10 предметов вокруг и описываешь их за 1 минуту без пауз',
            'Критерий: собеседник понял, продолжил разговор, не просил повторить дважды',
        ],
    },
    {
        'num': '2', 'weeks': '7-20', 'dur': '14 нед.', 'topics_count': 10,
        'color': '#f7971e', 'code': 'VOLUME',
        'name': 'Объём',
        'desc': 'Массовое поглощение -- грамматика, лексика, слушание. AI: тренер беглости -- 10-минутные сессии, отслеживание прогресса словарного запаса.',
        'skip': [
            'Subjunctive Mood -- редкая структура, не нужна до B2',
            'Идиомы и сленг из TikTok -- без грамматической базы звучат неуместно',
            'Академическое письмо -- для экзамена, не для разговора',
            'Параллельный учебник -- один источник до конца (English Grammar in Use)',
            'Нативные подкасты без транскрипции -- создают иллюзию понимания',
        ],
        'topics': [
            ('НЕД 7-9', 'Ядро грамматики: времена глагола',
             'Murphy "English Grammar in Use" B1: Units 1-20. Все времена + Perfect. Anki 200 карточек. AI ежедневно -- намеренно используй все времена.',
             '3 нед.', False),
            ('НЕД 7-10', 'Слушание -- транскрипт-метод',
             'BBC 6 Minute English -- 3 эпизода/нед: слушай -> читай транскрипт -> слушай без текста. Цель к нед.10: 70% без транскрипта.',
             '4 нед.', True),
            ('НЕД 9-11', 'Словарный запас 500->1500 слов',
             'Oxford 3000: следующие 1000 слов тематическими кластерами (еда, работа, эмоции). Anki с аудио. Слово активно после 3 использований.',
             '3 нед.', False),
            ('НЕД 11-13', 'Модальные глаголы и conditionals (0,1,2)',
             'Murphy Units 25-35. Conditionals Type 0,1,2. AI roleplay: "Что сделаешь, если..." -- только с conditionals.',
             '3 нед.', False),
            ('НЕД 11-14', 'Разговорная практика 15 мин/день',
             'Tandem/HelloTalk: 2 сессии/нед. AI ежедневно -- случайная тема. Запись + анализ скорости (слов/мин).',
             '4 нед.', True),
            ('НЕД 13-15', 'Предлоги и фразовые глаголы (топ-50)',
             'Prepositions of time/place/movement. Топ-50 phrasal verbs: pick up, turn off, give up. AI: мини-истории с изучаемым глаголом.',
             '3 нед.', False),
            ('НЕД 15-17', 'Чтение на уровне A2-B1',
             'Penguin Readers L2-3: одна книга за 2 недели (Forrest Gump Adapted). Контекстный вывод значений. BBC News Simple English.',
             '3 нед.', False),
            ('НЕД 17-19', 'Произношение: интонация и связная речь',
             "Rachel's English: connected speech, linking, reduction. Shadowing: TED-Ed (3-4 мин) -- 5 раз каждое. AI: оценка натуральности.",
             '3 нед.', False),
            ('НЕД 18-20', 'Пассивный залог + reported speech',
             'Murphy Units 40-50. Passive во всех временах. Reported speech: say/tell/ask + backshift. AI: перескажи новость BBC.',
             '3 нед.', True),
            ('НЕД 19-20', 'Лексика 1500->2500 слов',
             'Oxford 3000 финальный блок. Oxford Collocations Dictionary: 100 ключевых пар (make a decision, take a risk). Anki + AI-диалоги.',
             '2 нед.', False),
        ],
        'capstone_title': '«10 минут без остановки» -- структурированный разговор на B1',
        'capstone': [
            'Звонок в Tandem/Preply (30 мин) на свободную тему -- без заготовок',
            'AI-аудит: транскрипция -> статистика (% правильных времён, топ-10 ошибок, слов/мин)',
            'Адаптированная книга вслух 5 минут на запись -- без пауз (skip or guess)',
            'Критерий: скорость >= 90 слов/мин, собеседник не переспрашивает > 1 раза за 5 мин',
        ],
    },
    {
        'num': '3', 'weeks': '21-36', 'dur': '16 нед.', 'topics_count': 9,
        'color': '#43e97b', 'code': 'PRECISION',
        'name': 'Строгость',
        'desc': 'Точность произношения, реальные условия, исправление системных ошибок. AI: строгий аудитор -- отмечает каждую неточность, строит персональный error log.',
        'skip': [
            'Новые темы из Murphy -- грамматика закрыта в фазе 2; только применение',
            'Advanced IELTS writing tasks -- ломает естественную устную интонацию',
            'Расширение редкими словами -- 2500 слов достаточно для B2; нужна глубина',
            'Просмотр сериалов "для фона" -- пассивное аудирование без задачи не даёт прогресса',
        ],
        'topics': [
            ('НЕД 21-23', 'Произношение: акцент и редукция',
             "Rachel's English + нативные TED Talks (Brené Brown). Выбери один диалект (RP или GA) и не меняй. AI: запись 1 мин -> разбор проблемных звуков.",
             '3 нед.', False),
            ('НЕД 21-36', 'Error Log -- персональный дневник ошибок',
             'Notion-таблица: дата, ошибка, правильный вариант, контекст. После каждой AI-сессии -- 3 записи. Раз в 2 недели -- AI анализирует топ-3 паттерна.',
             '16 нед.', True),
            ('НЕД 23-26', 'Нативный слух: сериалы с заданием',
             '"Friends" или "The Crown" -- не для фона. 15 мин -> пауза -> повтори фразу вслух (mirroring). 10 новых выражений в Anki. Цель: 85% без субтитров.',
             '4 нед.', False),
            ('НЕД 25-28', 'Сложные грамматические структуры',
             'Cleft sentences, inversion (Never have I...), Conditional Type 3, mixed. Murphy Advanced Units 1-30. Цель: понимать и использовать 2-3 в разговоре.',
             '4 нед.', False),
            ('НЕД 27-30', 'Лексика 2500->4000 слов',
             'Oxford 5000 + Academic Word List (570 слов). Vocabulary.com для контекста. Тест: 10 новых слов в одном AI-разговоре без подсказки.',
             '4 нед.', True),
            ('НЕД 29-32', 'Регулярные встречи с носителями',
             '4 сессии на iTalki с certified teacher. Тема -- всегда новая, предложена учителем. Error correction в реальном времени. Запись каждой сессии.',
             '4 нед.', False),
            ('НЕД 31-33', 'Коллокации и регистры речи',
             'Oxford Collocations: 500 пар. Formal vs Informal -- Oxford Living Dictionaries. AI roleplay: одна тема в двух регистрах (интервью vs друг).',
             '3 нед.', False),
            ('НЕД 33-35', 'Чтение оригинальных текстов',
             'Первая неадаптированная книга: "The Alchemist" или Sherlock Holmes. Правило 50 (50+ непонятных слов/стр = слишком сложно). 20 стр/день.',
             '3 нед.', False),
            ('НЕД 35-36', 'Fluency drill -- скорость без качества',
             '2 минуты без остановки на случайную тему (RandomWordGenerator.com). AI фиксирует паузы и слова-паразиты. Цель: >= 110 слов/мин.',
             '2 нед.', False),
        ],
        'capstone_title': '«Запись для реальной аудитории» -- YouTube-монолог 5 минут',
        'capstone': [
            'Запись видео 5 минут без сценария, только 3 тезиса. Опубликуй на YouTube (хоть unlisted)',
            'AI-аудит транскрипции: error rate, паузы, грамматические ошибки на минуту. Цель: <= 3 ошибок/мин',
            'iTalki-сессия: учитель смотрит видео и даёт письменный feedback с оценкой B2/C1 готовности',
            'Критерий: незнакомый носитель понимает без усилий, accent не мешает коммуникации',
        ],
    },
    {
        'num': '4', 'weeks': '37-48', 'dur': '12 нед.', 'topics_count': 8,
        'color': '#ff6584', 'code': 'FLIGHT',
        'name': 'Полёт',
        'desc': 'Спонтанная речь, широкий словарный запас, C1-регистры. AI: симулятор носителя -- задаёт неудобные темы, перебивает, переводит разговор.',
        'skip': [
            'Новые карточки Anki базовой лексики -- база закрыта; только C1-фразеология',
            'Graded readers (адаптированные книги) -- замедляют восприятие нативной скорости',
            'Переспрашивать собеседника каждые 2 минуты -- тренируй inference из контекста',
            'Фокус на одном акценте -- C1 понимает British, American, Australian, Indian',
        ],
        'topics': [
            ('НЕД 37-39', 'Идиомы и разговорные выражения C1',
             'Oxford Dictionary of Idioms. Топ-200 идиом по темам (business, emotions, time). Anki + аудио. AI: разговор с 5 идиомами органично.',
             '3 нед.', False),
            ('НЕД 37-48', 'Ежедневные AI-дебаты 20 мин',
             'AI задаёт спорную тему. Ты защищаешь позицию 5 мин -> AI контраргументирует -> ты отвечаешь. Нет повторяющихся тем. 12 недель.',
             '12 нед.', True),
            ('НЕД 39-42', 'Лексика 4000->6000 слов',
             'Oxford 5000 финальный блок + C1 Word List. The Economist/Atlantic: 2 статьи/нед, 10 слов. Тест: объясни слово без перевода.',
             '4 нед.', False),
            ('НЕД 40-43', 'Нативный контент без субтитров',
             '"How I Built This", "Lex Fridman Podcast". 30 мин/день. После 15 мин -- пересказ AI вслух. Цель: >= 90% понимание без вспомогательных.',
             '4 нед.', True),
            ('НЕД 42-45', 'Длинные разговоры с носителями (30+ мин)',
             'Еженедельно: 45 мин на Preply -- тема предложена собеседником, не готовиться заранее. AI-анализ после: паузы, темы-блоки.',
             '4 нед.', False),
            ('НЕД 44-46', 'Метафоры, юмор и культурный код',
             'The Office, Friends. British irony vs American sarcasm. KnowYourMeme. AI roleplay: small talk с юмором. Понимать шутку и уместно реагировать.',
             '3 нед.', False),
            ('НЕД 45-47', 'Оригинальная литература и нон-фикшн',
             '"Sapiens" или "Thinking, Fast and Slow" -- оригинал. 25 стр/день без словаря. The Guardian, Wired. AI: обсуди как с образованным носителем.',
             '3 нед.', False),
            ('НЕД 47-48', 'Симуляция финального разговора',
             'AI проводит mock-интервью: 30 минут, 3 смены темы без предупреждения. Оценивает когезию, скорость, TTR. Цель: оценка C1.',
             '2 нед.', False),
        ],
        'capstone_title': '«Незнакомая тема, живой носитель» -- 20 минут без подготовки',
        'capstone': [
            'Сессия iTalki: носитель выбирает тему из 5 (ты не знаешь). 20 минут непрерывного разговора',
            'AI-аудит: error rate, паузы, TTR -- сравнение с капстоуном фазы 3 (дельта роста)',
            'Пересказываешь статью The Economist (800 слов) за 3 мин вслух своими словами',
            'Критерий: собеседник оценивает уровень как "advanced" без подсказки с твоей стороны',
        ],
    },
    {
        'num': '5', 'weeks': '49-52', 'dur': '4 нед.', 'topics_count': 5,
        'color': '#38f9d7', 'code': 'HABITS',
        'name': 'Привычки',
        'desc': 'Новый материал не нужен -- нужна система. AI: личный компас качества -- еженедельный прогресс-репорт, отслеживание деградации.',
        'skip': [
            'Новые темы и учебники -- фаза закрытия, не расширения',
            'Переход на другой диалект -- смешение акцентов хуже, чем один чистый',
            'Откладывание финального живого разговора -- капстоун не переносится',
        ],
        'topics': [
            ('НЕД 49-50', 'Система поддержания C1 -- daily stack',
             'Устойчивый стек: 10 мин Anki + 15 мин нативный контент + 10 мин AI. Итого: 35 мин/день. Habit tracker в Notion или Streaks.',
             '2 нед.', False),
            ('НЕД 49-52', 'Еженедельный AI progress-report',
             'Каждое воскресенье: 10 мин AI по 5 метрикам -- скорость, error rate, TTR, паузы, переспросы. Граф прогресса. Если деградация -- немедленный drill.',
             '4 нед.', True),
            ('НЕД 50-51', 'Финальный error-log разбор',
             'Полный аудит error log за 52 недели. 5 ошибок-лидеров. AI строит micro-drills на каждую. 3 дня финальной проработки каждой.',
             '2 нед.', False),
            ('НЕД 51-52', 'Карта своего английского -- рефлексия',
             'Документируешь: топ-5 инструментов, что было лишним, самый эффективный навык. AI помогает структурировать. Публикуй -- это реальная ставка.',
             '2 нед.', False),
            ('НЕД 52', 'День финального разговора',
             'iTalki: новый носитель, он выбирает тему. 30 минут. Никаких тезисов. Это и есть цель -- живой разговор как факт, не диплом.',
             '1 нед.', False),
        ],
        'capstone_title': '«30 минут. Незнакомый носитель. Его тема. Без подготовки.»',
        'capstone': [
            'Сессия iTalki с новым носителем: он выбирает тему, ты разговариваешь 30 минут',
            'Попроси носителя оценить уровень в 1 предложении. "Advanced / C1" -- финальный критерий',
            'AI финальный отчёт: кривая прогресса всех 5 метрик от фазы 1 до фазы 5',
            'Публикуешь запись или AI-summary -- в соцсетях, дневнике. Реальная ставка закрыта.',
        ],
    },
]

MARKERS = [
    ('#6c63ff', '// БЕГЛОСТЬ',
     'Думаешь на английском, не переводишь',
     'Внутренний монолог переключился на английский в моменты концентрации. При чтении значение появляется сразу -- без промежуточного русского слова.'),
    ('#f7971e', '// ТОЧНОСТЬ',
     'Слышишь ошибки у других (и у себя в записях)',
     'Когда носитель говорит неправильно -- замечаешь. Слушая запись месячной давности -- слышишь то, что казалось нормальным.'),
    ('#43e97b', '// ВКУС',
     'Выбираешь слово по нюансу, а не первое попавшееся',
     'Между big/large/vast/enormous -- выбираешь осознанно. Чувствуешь, когда "however" тяжело, а "but" -- живее.'),
    ('#ff6584', '// СТРЕССОУСТОЙЧИВОСТЬ',
     'Незнакомая тема включает inference, а не панику',
     '"I\'m not sure about the exact term, but what I mean is..." -- это C1-ответ, а не провал. Строишь из того, что есть.'),
    ('#38f9d7', '// СИСТЕМА',
     '35 минут в день не ощущаются как учёба',
     'Подкаст во время еды, статья вместо ленты, AI пока ждёшь. Язык встроен в поток -- не интенсивность, а устойчивость.'),
    ('#a8a3ff', '// AI-ИНСТРУМЕНТ',
     'Используешь AI как зеркало, а не переводчик',
     'Ты давно не просишь "переведи". Просишь: "оцени убедительность", "найди 3 точнее", "где потерял темп". AI -- инструмент самооценки.'),
]



# ─── Page renderers ────────────────────────────────────────────────────────────

def render_cover(p: PageBuilder):
    p.fill_page('#0d0d14')

    # Decorative gradient circles (approximated as filled circles with low opacity)
    # Top-left glow
    for radius in [120, 90, 60, 30]:
        alpha = 0.03 + (120 - radius) * 0.001
        p.rect_filled(MARGIN - 40, PH - MARGIN - 40,
                      radius * 2, radius * 2, '#0d0d14')

    y = PH - MARGIN

    # Category bar
    p.rect_filled_stroke(MARGIN, y - 18, 260, 16, '#11111e', '#2a2a55', 0.5)
    p.text(MARGIN + 8, y - 12, 'АНГЛИЙСКИЙ ЯЗЫК  *  2026  *  ROADMAP  *  V1.0',
           'F2', 7, '#6c63ff')
    y -= 28

    # Title
    p.text(MARGIN, y - 18, 'Top 1%', 'F2', 36, '#ffffff')
    y -= 42
    p.text(MARGIN, y - 18, 'Nositel', 'F2', 36, '#a8a3ff')
    y -= 42
    p.text(MARGIN, y - 18, 'urovnya C1', 'F2', 36, '#6c63ff')
    y -= 50

    # Subtitle
    p.text(MARGIN, y, '12 mesyacev * 52 nedeli * 5 faz * 38 tem * bez vody -- aktualno dlya 2026',
           'F1', 9.5, '#7878a0')
    y -= 22

    # ─ Stats row ─
    stat_w = (CW - 18) // 4
    stats = [('52', 'Недели', '#6c63ff'), ('5', 'Фаз', '#f7971e'),
             ('38', 'Тем', '#43e97b'), ('5', 'Капстонов', '#ff6584')]
    sx = MARGIN
    for num, label, col in stats:
        bh = 60
        p.rect_filled_stroke(sx, y - bh, stat_w, bh, '#16161f', '#242435', 0.5)
        p.text(sx + stat_w//2 - len(num)*11, y - 22, num, 'F2', 26, col)
        p.text(sx + stat_w//2 - len(label)*3, y - 38, label, 'F1', 7.5, '#7878a0')
        sx += stat_w + 6
    y -= 72

    # Divider
    p.line_h(MARGIN, y, CW, '#242435', 0.5)
    y -= 14

    # Nav title
    p.text(MARGIN, y, '> Навигация по фазам', 'F2', 8, '#7878a0')
    y -= 16

    # Phase nav cards
    phase_colors = ['#6c63ff', '#f7971e', '#43e97b', '#ff6584', '#38f9d7']
    phase_names = ['Фундамент', 'Объём', 'Строгость', 'Полёт', 'Привычки']
    phase_weeks = ['НЕД 1-6', 'НЕД 7-20', 'НЕД 21-36', 'НЕД 37-48', 'НЕД 49-52']
    phase_durs = ['6 нед.', '14 нед.', '16 нед.', '12 нед.', '4 нед.']
    phase_topics = ['6 тем', '10 тем', '9 тем', '8 тем', '5 тем']

    nav_w = (CW - 24) // 5
    nav_h = 80
    nx = MARGIN
    for i in range(5):
        col = phase_colors[i]
        p.rect_filled_stroke(nx, y - nav_h, nav_w, nav_h, '#16161f', col, 0.8)
        p.text(nx + nav_w//2 - 7, y - 18, str(i+1), 'F2', 20, col)
        pw_label = phase_weeks[i]
        p.text(nx + 4, y - 33, pw_label, 'F1', 6.5, '#7878a0')
        p.text(nx + 4, y - 44, phase_names[i], 'F2', 8.5, '#e8e8f0')
        p.text(nx + 4, y - 55, phase_durs[i], 'F1', 7, '#7878a0')
        p.text(nx + 4, y - 65, phase_topics[i], 'F1', 7, col)
        nx += nav_w + 6
    y -= nav_h + 12

    # Divider
    p.line_h(MARGIN, y, CW, '#242435', 0.5)
    y -= 14

    # Final goal box
    box_h = 50
    p.rect_filled_stroke(MARGIN, y - box_h, CW, box_h, '#0f0f1a', '#2a2a55', 0.8)
    p.line_v(MARGIN + 2, y - box_h + 3, box_h - 6, '#6c63ff', 2.5)
    p.text(MARGIN + 12, y - 12, '> Финальная цель', 'F2', 8, '#6c63ff')
    p.text(MARGIN + 12, y - 24,
           '30-минутный незаписанный разговор с носителем без подготовки',
           'F2', 10.5, '#ffffff')
    p.text(MARGIN + 12, y - 37,
           'по теме, которую собеседник выбирает сам -- уверенно, без пауз на перевод',
           'F1', 9, '#a8a3ff')


def render_philosophy(p: PageBuilder):
    p.fill_page('#0d0d14')
    y = PH - MARGIN

    # Header
    p.rect_filled_stroke(MARGIN, y - 14, 30, 14, '#11111e', '#2a2a55', 0.5)
    p.text(MARGIN + 5, y - 10, '02', 'F2', 8, '#6c63ff')
    p.text(MARGIN + 38, y - 10, 'Filosofiya / Manifest', 'F2', 14, '#ffffff')
    y -= 26

    # Manifesto box
    mbox_h = 62
    p.rect_filled_stroke(MARGIN, y - mbox_h, CW, mbox_h, '#0f0f1a', '#2a2a55', 0.5)
    p.line_v(MARGIN + 2, y - mbox_h + 4, mbox_h - 8, '#6c63ff', 2.5)
    p.text(MARGIN + 12, y - 10, 'PARADOKS PROGRAMMY:', 'F2', 8.5, '#6c63ff')
    manifesto_lines = [
        'Ty ne izuchaesh angliiskii -- ty perestaesh perevodyt s russkogo. Pervyi mesyats',
        'kazhetsia medlennym, potomu chto ty stroish myshlenie na drugom yazyke.',
        'Govori s pervogo dnya -- koryavo, netochno, vslukh. AI-sobesednik prinimaet',
        'lyuboi uroven i razbiraet kazhdyu oshibku. Snachala ob\'em -- potom tochnost.',
        'Cherez 52 nedeli ty ne "vyuchish" yazyk -- ty na nem zhivesh.',
    ]
    my = y - 22
    for line in manifesto_lines:
        p.text(MARGIN + 12, my, line, 'F1', 8.5, '#c8c8e0')
        my -= 11
    y -= mbox_h + 10

    # Principles grid (2 cols x 3 rows)
    principles = [
        ('#ffffff', '01 Глубина одного навыка -- до уверенности',
         'Один инструмент до автоматизма, прежде чем следующий. Anki-колода по Present',
         'Simple закрыта только когда не думаешь о ней в разговоре.'),
        ('#ffffff', '02 Осознанный пропуск -- часть плана',
         'Каждая фаза имеет список "не трогай сейчас". Пропускать сложную грамматику',
         'на A1 -- не лень, а дисциплина. Преждевременная сложность создаёт страх.'),
        ('#ffffff', '03 Топ 1% -- это привычки, а не сложность',
         '52 недели x 7 дней x 20 минут = ~121 час активной практики.',
         'Носитель C1 отличается не редкими словами, а ежедневными привычками.'),
        ('#ffffff', '04 Реальная ставка обязательна',
         'Каждый капстоун -- живой собеседник или реальная аудитория. Tandem, iTalki,',
         'запись для YouTube. Тренировочный полигон без ставки не засчитывается.'),
        ('#ffffff', '05 Не используешь -- не знаешь',
         'Если не можешь объяснить, зачем делаешь это и что меняет в твоей речи --',
         'выброси инструмент. Anki, Grammarly, shadowing -- всё требует объяснения.'),
        ('#a8a3ff', '06 AI-собеседник: партнёр по объёму, не костыль',
         'ChatGPT/Claude -- 24/7 носитель без осуждения. Роль меняется по фазам:',
         'партнёр -> тренер -> аудитор. Живое общение он не заменяет -- готовит к нему.'),
    ]

    pcol_w = (CW - 6) // 2
    ph = 60
    px, py = MARGIN, y
    for i, (col, title, l1, l2) in enumerate(principles):
        fill = '#11111a' if i < 5 else '#0f0f1e'
        stroke = '#242435' if i < 5 else '#3a3a77'
        p.rect_filled_stroke(px, py - ph, pcol_w, ph, fill, stroke, 0.5)
        big_num = title[:2]
        p.text(px + 6, py - 12, big_num, 'F2', 18, '#1e1e30')
        p.text(px + 6, py - 26, title[3:], 'F2', 8, col)
        p.text(px + 6, py - 38, l1, 'F1', 7.5, '#7878a0')
        p.text(px + 6, py - 49, l2, 'F1', 7.5, '#7878a0')
        if i % 2 == 0:
            px = MARGIN + pcol_w + 6
        else:
            px = MARGIN
            py -= ph + 5

    y = py - 8

    # Phase overview table
    p.text(MARGIN, y, '> Obzor faz', 'F2', 8, '#7878a0')
    y -= 12

    headers = ['#', 'Фаза', 'Фокус', 'Недели', 'Длит.', 'Тем']
    col_widths = [18, 65, 265, 55, 45, 30]
    # Header row
    p.rect_filled(MARGIN, y - 14, CW, 14, '#16161f')
    hx = MARGIN + 4
    for h, cw in zip(headers, col_widths):
        p.text(hx, y - 10, h.upper(), 'F2', 7, '#5858a0')
        hx += cw

    phase_rows = [
        ('#6c63ff', '1', 'Фундамент', 'Базовые конструкции + ежедневное говорение с AI', '1-6', '6 нед.', '6'),
        ('#f7971e', '2', 'Объём', 'Грамматика, лексика, слушание -- массовое поглощение', '7-20', '14 нед.', '10'),
        ('#43e97b', '3', 'Строгость', 'Точность, произношение, реальные условия', '21-36', '16 нед.', '9'),
        ('#ff6584', '4', 'Полёт', 'Спонтанная речь, широкий словарь, C1-регистры', '37-48', '12 нед.', '8'),
        ('#38f9d7', '5', 'Привычки', 'Система поддержания C1 + финальная демонстрация', '49-52', '4 нед.', '5'),
    ]
    y -= 14
    for col, num, name, focus, weeks, dur, tc in phase_rows:
        p.line_h(MARGIN, y, CW, '#1e1e2e', 0.3)
        rx = MARGIN + 4
        p.circle_filled(rx + 4, y - 6, 3, col)
        rx += 12
        p.text(rx - 12, y - 10, num, 'F2', 9, col)
        rx = MARGIN + 4 + col_widths[0]
        p.text(rx, y - 10, name, 'F2', 9, '#e8e8f0')
        rx += col_widths[1]
        p.text(rx, y - 10, focus, 'F1', 8, '#7878a0')
        rx += col_widths[2]
        p.text(rx, y - 10, weeks, 'F2', 8.5, '#7878a0')
        rx += col_widths[3]
        p.text(rx, y - 10, dur, 'F2', 9, col)
        rx += col_widths[4]
        p.text(rx, y - 10, tc, 'F2', 9, '#ffffff')
        y -= 16



def render_phase(p: PageBuilder, phase: dict):
    p.fill_page('#0d0d14')
    col = phase['color']
    y = PH - MARGIN

    # Phase badge
    p.rect_filled_stroke(MARGIN, y - 14, CW, 14, '#0f0f1a', col, 0.8)
    badge_text = f"FAZA {phase['num']}  *  NED {phase['weeks']}  *  {phase['code']}"
    p.text(MARGIN + 8, y - 10, badge_text, 'F2', 8, col)
    y -= 20

    # Phase title
    p.text(MARGIN, y - 5, phase['name'], 'F2', 22, col)
    y -= 30

    # Description
    desc_words = phase['desc'].split()
    desc_line = ''
    desc_lines = []
    for w in desc_words:
        test = (desc_line + ' ' + w).strip()
        if len(test) < 100:
            desc_line = test
        else:
            desc_lines.append(desc_line)
            desc_line = w
    if desc_line:
        desc_lines.append(desc_line)
    for dl in desc_lines[:2]:
        p.text(MARGIN, y, dl, 'F1', 8.5, '#9090b8')
        y -= 11
    y -= 4

    # Mini stats
    p.text(PW - MARGIN - 120, PH - MARGIN - 12, f"Ned: {phase['weeks']}", 'F2', 8.5, col)
    p.text(PW - MARGIN - 120, PH - MARGIN - 23, f"Dur: {phase['dur']}", 'F2', 8.5, col)
    p.text(PW - MARGIN - 120, PH - MARGIN - 34, f"Tem: {phase['topics_count']}", 'F2', 8.5, col)

    # Skip box
    skip_h = 14 + len(phase['skip']) * 12 + 4
    p.rect_filled_stroke(MARGIN, y - skip_h, CW, skip_h, '#120a0a', '#3d1a1a', 0.6)
    p.text(MARGIN + 8, y - 10, 'x  PROPUSKAY NA ETOI FAZE', 'F2', 8, '#ff6584')
    sy = y - 21
    for sk in phase['skip']:
        p.text(MARGIN + 8, sy, f'x  {sk[:110]}', 'F1', 7.5, '#c8a0a0')
        if len(sk) > 110:
            p.text(MARGIN + 16, sy - 9, sk[110:], 'F1', 7.5, '#c8a0a0')
            sy -= 9
        sy -= 12
    y -= skip_h + 8

    # Topics
    topics = phase['topics']
    ncols = 3 if len(topics) >= 6 else 2
    tcol_w = (CW - (ncols - 1) * 5) // ncols
    # Calculate rows needed
    n_rows = (len(topics) + ncols - 1) // ncols
    topic_h = min(80, max(60, (y - 80) // n_rows))  # dynamic height

    tx, ty = MARGIN, y
    for i, (weeks, name, body, dur, parallel) in enumerate(topics):
        col_idx = i % ncols
        row_idx = i // ncols
        bx = MARGIN + col_idx * (tcol_w + 5)
        by = ty - row_idx * (topic_h + 4)

        p.rect_filled_stroke(bx, by - topic_h, tcol_w, topic_h, '#16161f', '#242435', 0.5)
        p.line_v(bx + 2, by - topic_h + 3, topic_h - 6, col, 2)

        p.text(bx + 8, by - 10, weeks, 'F2', 7.5, '#5858a0')

        # Name (possibly wrap)
        name_display = name if len(name) < 45 else name[:44] + '...'
        if parallel:
            p.text(bx + 8, by - 21, name_display, 'F2', 8.5, '#ffffff')
            p.text(bx + 8 + len(name_display) * 4.8, by - 21, ' // PAR', 'F2', 6.5, '#38f9d7')
        else:
            p.text(bx + 8, by - 21, name_display, 'F2', 8.5, '#ffffff')

        # Body text (2 lines max)
        body_words = body.split()
        bl = ''
        blines = []
        for w in body_words:
            test = (bl + ' ' + w).strip()
            char_limit = int(tcol_w / 4.5)
            if len(test) < char_limit:
                bl = test
            else:
                blines.append(bl)
                bl = w
        if bl:
            blines.append(bl)
        max_blines = max(2, int((topic_h - 40) / 9))
        by_text = by - 32
        for bl in blines[:max_blines]:
            p.text(bx + 8, by_text, bl, 'F1', 7, '#9090b8')
            by_text -= 9

        p.text(bx + 8, by - topic_h + 7, dur, 'F2', 7.5, col)

    y -= n_rows * (topic_h + 4) + 4

    # Capstone box
    cap_h = max(58, 18 + len(phase['capstone']) * 13 + 5)
    if y - cap_h < 20:
        cap_h = y - 22
    cap_h = max(cap_h, 55)

    p.rect_filled_stroke(MARGIN, y - cap_h, CW, cap_h, '#0f0f1a', col, 1.0)
    p.line_v(MARGIN + 2, y - cap_h + 3, cap_h - 6, col, 3)
    p.text(MARGIN + 10, y - 10, f'-> KAPSTON FAZY {phase["num"]}', 'F2', 8, col)
    p.text(MARGIN + 10, y - 22, phase['capstone_title'][:90], 'F2', 9.5, '#ffffff')
    cy = y - 35
    for item in phase['capstone'][:4]:
        p.text(MARGIN + 10, cy, f'-> {item[:95]}', 'F1', 7.5, '#c8c8e0')
        cy -= 12


def render_finish(p: PageBuilder):
    p.fill_page('#0d0d14')
    y = PH - MARGIN

    # Header tag
    p.rect_filled_stroke(MARGIN, y - 14, 30, 14, '#1a0a0f', '#3d1a2a', 0.5)
    p.text(MARGIN + 5, y - 10, '05', 'F2', 8, '#ff6584')
    p.text(MARGIN + 38, y - 10, 'Final / Samoproverka', 'F2', 14, '#ffffff')
    y -= 28

    # Question
    p.text(MARGIN, y - 5, 'Ty v top-1%,', 'F2', 20, '#ffffff')
    y -= 25
    p.text(MARGIN, y - 5, 'kogda --', 'F2', 20, '#6c63ff')
    y -= 20
    p.text(MARGIN, y, 'Povedencheskie markery, a ne sertifikaty. Ty ikh zamechaesh v razgovore -- ne v teste.',
           'F1', 9, '#7878a0')
    y -= 18

    # Markers grid (2 cols x 3 rows)
    mcol_w = (CW - 6) // 2
    mh = 72

    for i, (col, label, title, body) in enumerate(MARKERS):
        col_idx = i % 2
        row_idx = i // 2
        mx = MARGIN + col_idx * (mcol_w + 6)
        my = y - row_idx * (mh + 5)
        fill = '#12121e' if i < 5 else '#0e0e1e'
        stroke = '#242435' if i < 5 else '#3a3a77'
        p.rect_filled_stroke(mx, my - mh, mcol_w, mh, fill, stroke, 0.5)
        p.rect_filled(mx, my, mcol_w, 2, col)  # top accent line

        p.text(mx + 8, my - 12, label, 'F2', 7.5, col)
        p.text(mx + 8, my - 24, title, 'F2', 9.5, '#ffffff')

        # Body wrap
        bwords = body.split()
        bl = ''
        blines = []
        for w in bwords:
            test = (bl + ' ' + w).strip()
            if len(test) < int(mcol_w / 4.3):
                bl = test
            else:
                blines.append(bl)
                bl = w
        if bl:
            blines.append(bl)
        by_m = my - 38
        for bln in blines[:3]:
            p.text(mx + 8, by_m, bln, 'F1', 7.5, '#7878a0')
            by_m -= 10

    y -= 3 * (mh + 5) + 10

    # Closing line
    closing_h = 50
    p.rect_filled_stroke(MARGIN, y - closing_h, CW, closing_h,
                         '#0f0f1a', '#3a3a77', 0.8)
    p.text(MARGIN + CW//2 - 190, y - 16,
           'Yazyk uchyat godami --', 'F2', 13, '#ffffff')
    p.text(MARGIN + CW//2 - 130, y - 31,
           'nositelyami stanovyatsya za 52 nedeli privychek.', 'F2', 11, '#6c63ff')
    p.text(MARGIN + CW//2 - 170, y - 44,
           'Ne znanie delaet raznitsu -- delaet raznitsu to, chto ty delaesh kazhdyi den.', 'F1', 9, '#7878a0')

    # Footer
    y -= closing_h + 12
    p.line_h(MARGIN, y, CW, '#242435', 0.5)
    y -= 10
    p.text(MARGIN, y, 'ANGLIISKII YAZYK * ROADMAP * 2026 * V1.0', 'F2', 7, '#5858a0')
    p.text(PW - MARGIN - 160, y, 'A1 -> C1 * 52 ned. * 5 faz * 38 tem * 5 kaostonov', 'F1', 7, '#5858a0')


# ─── PDF assembly ─────────────────────────────────────────────────────────────

def build_pdf() -> bytes:
    pdf = PDFWriter()

    # Font objects (standard PDF fonts -- no embedding needed)
    # F1 = Helvetica, F2 = Helvetica-Bold
    font1_id = pdf.add_object('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    font2_id = pdf.add_object('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')

    font_res = f'<< /F1 {font1_id} 0 R /F2 {font2_id} 0 R >>'

    page_ids = []
    pages_parent_id = pdf.new_id()  # reserve id for pages dict

    def make_page(builder: PageBuilder) -> int:
        content_str = builder.build()
        content_bytes = content_str.encode('latin-1', errors='replace')
        stream_id = pdf.add_object_raw(
            f'<< /Length {len(content_bytes)} >>\nstream\n'.encode() +
            content_bytes +
            b'\nendstream'
        )
        page_id = pdf.add_object(
            f'<< /Type /Page /Parent {pages_parent_id} 0 R '
            f'/MediaBox [0 0 {PW} {PH}] '
            f'/Contents {stream_id} 0 R '
            f'/Resources << /Font {font_res} >> >>'
        )
        return page_id

    # Build pages
    builders = []

    # Cover
    cover = PageBuilder()
    render_cover(cover)
    builders.append(cover)

    # Philosophy
    phil = PageBuilder()
    render_philosophy(phil)
    builders.append(phil)

    # Phases 1-5
    for phase in PHASES:
        pp = PageBuilder()
        render_phase(pp, phase)
        builders.append(pp)

    # Finish
    finish = PageBuilder()
    render_finish(finish)
    builders.append(finish)

    for b in builders:
        page_ids.append(make_page(b))

    # Pages dictionary (uses the pre-reserved ID)
    kids = ' '.join(f'{pid} 0 R' for pid in page_ids)
    pages_content = f'<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>'
    pdf.objects.append((pages_parent_id, pages_content.encode('latin-1')))

    # Catalog
    catalog_id = pdf.add_object(f'<< /Type /Catalog /Pages {pages_parent_id} 0 R >>')

    # Info
    info_id = pdf.add_object(
        f'<< /Title (Top 1% Nositel C1 -- English Roadmap 2026) '
        f'/Author (Kiro AI) '
        f'/Subject (English Language Learning Roadmap A1 to C1) '
        f'/Keywords (English C1 Roadmap 2026) >>'
    )

    # Fix catalog to be obj 1
    # We need catalog at id 1 and info at id 2
    # Let's reorder: swap catalog to position 1
    # Actually let's just rebuild with catalog first
    pdf2 = PDFWriter()
    pdf2.obj_id = 0

    catalog_id2 = pdf2.add_object(f'<< /Type /Catalog /Pages 3 0 R >>')  # id=1
    info_id2 = pdf2.add_object(
        f'<< /Title (Top 1% Nositel C1 -- English Roadmap 2026) '
        f'/Author (Kiro AI) >>'
    )  # id=2
    pages_id2 = pdf2.new_id()  # id=3 reserved

    # Font objects
    f1_id = pdf2.add_object('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    f2_id = pdf2.add_object('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
    font_res2 = f'<< /F1 {f1_id} 0 R /F2 {f2_id} 0 R >>'

    page_ids2 = []

    def make_page2(builder: PageBuilder) -> int:
        content_str = builder.build()
        content_bytes = content_str.encode('latin-1', errors='replace')
        stream_id = pdf2.add_object_raw(
            f'<< /Length {len(content_bytes)} >>\nstream\n'.encode() +
            content_bytes +
            b'\nendstream'
        )
        page_id = pdf2.add_object(
            f'<< /Type /Page /Parent {pages_id2} 0 R '
            f'/MediaBox [0 0 {PW} {PH}] '
            f'/Contents {stream_id} 0 R '
            f'/Resources << /Font {font_res2} >> >>'
        )
        return page_id

    for b in builders:
        page_ids2.append(make_page2(b))

    kids2 = ' '.join(f'{pid} 0 R' for pid in page_ids2)
    pdf2.objects.append((pages_id2, f'<< /Type /Pages /Kids [{kids2}] /Count {len(page_ids2)} >>'.encode()))

    return pdf2.build()


if __name__ == '__main__':
    print('Generating PDF...')
    data = build_pdf()
    out_path = '/projects/sandbox/english_roadmap_c1.pdf'
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f'Done! Written {len(data):,} bytes to {out_path}')
    print(f'Pages: 8 (cover + philosophy + 5 phases + finish)')
