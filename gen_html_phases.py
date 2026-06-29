#!/usr/bin/env python3
"""Generate phase + finish HTML sections from roadmap_v2 data, append to HTML."""
import sys
sys.path.insert(0, '/projects/sandbox')
from roadmap_v2 import PHASES, PC

# map phase color hex -> css var
COLVAR = {PC[0]:'--p1', PC[1]:'--p2', PC[2]:'--p3', PC[3]:'--p4', PC[4]:'--p5'}
# rgba helpers
RGBA = {
  PC[0]:'124,111,255', PC[1]:'255,140,66', PC[2]:'54,217,134',
  PC[3]:'255,85,119', PC[4]:'0,212,200',
}

def esc(s):
    return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

out = []

for ph in PHASES:
    col = ph['col']; cv = COLVAR[col]; rgba = RGBA[col]
    out.append(f'\n<!-- ════ PHASE {ph["n"]} ════ -->')
    out.append('<div class="page">')
    # header
    out.append(
      f'  <div class="ph-head" style="background:rgba({rgba},.06);border:1px solid rgba({rgba},.35)">\n'
      f'    <div class="ph-badge" style="color:var({cv})">ФАЗА {ph["n"]} &nbsp;·&nbsp; НЕД {ph["wr"]} &nbsp;·&nbsp; {ph["code"]}</div>\n'
      f'    <div class="ph-mini" style="color:var({cv})">Нед: {ph["wr"]}<br>Длит.: {ph["dw"]} нед.<br>Тем: {ph["nt"]}</div>\n'
      f'  </div>'
    )
    out.append(f'  <div class="ph-title" style="color:var({cv})">{esc(ph["name"])}</div>')
    out.append(f'  <div class="ph-desc">{esc(ph["desc"])}</div>')

    # skip box
    out.append('  <div class="skip-box">')
    out.append('    <div class="skip-title">✕ Пропускай на этой фазе</div>')
    for sk in ph['skip']:
        out.append(f'    <div class="skip-item">{esc(sk)}</div>')
    out.append('  </div>')

    # topics
    ncols = 3 if len(ph['topics']) >= 6 else 2
    out.append(f'  <div class="topics c{ncols}">')
    for wk, name, body, dur, par in ph['topics']:
        partag = '<span class="par-tag">ПАРАЛЛЕЛЬНО</span>' if par else ''
        out.append(
          f'    <div class="topic" style="border-left-color:{col}">\n'
          f'      <div class="tw">{esc(wk)}</div>\n'
          f'      <div class="tn">{esc(name)}{partag}</div>\n'
          f'      <div class="tb">{esc(body)}</div>\n'
          f'      <div class="td" style="color:{col}">{esc(dur)}</div>\n'
          f'    </div>'
        )
    out.append('  </div>')

    # capstone
    out.append(
      f'  <div class="capstone" style="background:rgba({rgba},.07);border-color:rgba({rgba},.4);border-left-color:{col}">\n'
      f'    <div class="ch" style="color:var({cv})">→ Капстоун фазы {ph["n"]}</div>\n'
      f'    <div class="ct">{esc(ph["cap_name"])}</div>\n'
      f'    <ul>'
    )
    for item in ph['cap']:
        out.append(f'      <li>{esc(item)}</li>')
    out.append('    </ul>\n  </div>')
    out.append('</div>')

# ════ FINISH PAGE ════
markers = [
    ('--p1','// БЕГЛОСТЬ','Думаешь на английском, не переводишь',
     'Внутренний монолог переключился на английский в моменты концентрации. При чтении значение появляется сразу — без промежуточного русского слова.'),
    ('--p2','// ТОЧНОСТЬ','Слышишь ошибки у других — и у себя в старых записях',
     'Слушая запись месячной давности — слышишь то, что раньше казалось нормальным. Error log пустеет — системные паттерны устранены.'),
    ('--p3','// ВКУС','Выбираешь слово по нюансу, не первое попавшееся',
     'Между big/large/vast/enormous — выбираешь осознанно. Чувствуешь, когда «however» звучит тяжело, а «but» — живее.'),
    ('--p4','// СТОЙКОСТЬ','Незнакомая тема включает inference, не панику',
     '«I\'m not sure about the exact term, but what I mean is...» — это C1-ответ, а не провал. Строишь из того, что есть.'),
    ('--p5','// СИСТЕМА','35 минут в день не ощущаются как учёба',
     'Подкаст во время еды, статья вместо ленты, Claude пока ждёшь. Язык встроен в поток — не интенсивность, а устойчивость.'),
    ('ai','// AI-ИНСТРУМЕНТ','Используешь Claude как зеркало, не переводчик',
     'Давно не просишь «переведи». Просишь: «оцени убедительность», «найди 3 слова точнее», «где потерял темп». AI — инструмент самооценки.'),
]

out.append('\n<!-- ════ FINISH ════ -->')
out.append('<div class="page">')
out.append('  <div class="sec-head"><span class="sec-tag" style="color:var(--p4);border-color:var(--p4)">07</span>'
           '<span class="sec-title">Финиш / Самопроверка</span></div>')
out.append('  <div class="finish-q">Ты в топ-1%, <span>когда —</span></div>')
out.append('  <div class="finish-sub">Поведенческие маркеры, а не сертификаты. Замечаешь в разговоре — не в тесте.</div>')
out.append('  <div class="markers">')
for cv, lbl, title, body in markers:
    klass = ' marker-ai' if cv == 'ai' else ''
    topcol = '#a8a3ff' if cv == 'ai' else f'var({cv})'
    lblcol = '#a8a3ff' if cv == 'ai' else f'var({cv})'
    out.append(
      f'    <div class="marker{klass}"><div class="mtop" style="background:{topcol}"></div>\n'
      f'      <div class="mlbl" style="color:{lblcol}">{lbl}</div>\n'
      f'      <div class="mtitle">{esc(title)}</div>\n'
      f'      <div class="mbody">{esc(body)}</div>\n'
      f'    </div>'
    )
out.append('  </div>')
out.append(
  '  <div class="closing">\n'
  '    <div class="c1">Язык учат годами —</div>\n'
  '    <div class="c2">носителями становятся за 36 недель привычек.</div>\n'
  '    <div class="c3">Не знание делает разницу — делает разницу то, что ты делаешь каждый день.</div>\n'
  '  </div>'
)
out.append(
  '  <div class="footer">\n'
  '    <span>АНГЛИЙСКИЙ ЯЗЫК · ROADMAP · 2026 · V2.0</span>\n'
  '    <span>A2-B1 → C1 · 36 нед. · 5 фаз · 33 темы · 5 капстонов</span>\n'
  '  </div>\n'
  '</div>'
)

out.append('\n</body>\n</html>')

with open('/projects/sandbox/english_roadmap_v2.html', 'a', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')

print('Phases + finish appended:', len(out), 'lines')
