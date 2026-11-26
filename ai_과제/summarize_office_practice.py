import csv
import io
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
source = ROOT / 'office_practice_clean.csv'
original_bytes = source.read_bytes()
records = list(csv.DictReader(io.StringIO(original_bytes.decode('utf-8'), newline='')))
types = ['문서작성', '비품신청', '시스템문의', '자료요청', '비용정산', '일정조율', '계정문의']
departments = ['경영지원팀', '총무팀', 'IT지원팀', '재무팀', '기획팀', '미분류']
statuses = ['접수', '진행중', '완료', '보류', '미분류']
counts = Counter(row['업무유형'] for row in records)
cross = Counter((row['담당부서'], row['처리상태']) for row in records)
assert set(counts) == set(types)
assert {r['담당부서'] for r in records} == set(departments)
assert {r['처리상태'] for r in records} == set(statuses)
total = len(records)
type_rows = [[name, counts[name]] for name in types] + [['전체 합계', total]]
cross_rows = [[dept] + [cross[dept, status] for status in statuses]
              + [sum(cross[dept, status] for status in statuses)] for dept in departments]
status_totals = [sum(cross[dept, status] for dept in departments) for status in statuses]
cross_rows.append(['전체 합계'] + status_totals + [total])
assert sum(counts.values()) == sum(status_totals) == sum(row[-1] for row in cross_rows[:-1]) == total

for filename, header, rows in [
    ('office_practice_type_counts.csv', ['업무유형', '건수'], type_rows),
    ('office_practice_department_status.csv', ['담당부서'] + statuses + ['전체 합계'], cross_rows),
]:
    with (ROOT / filename).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(header)
        writer.writerows(rows)
    with (ROOT / filename).open(encoding='utf-8-sig', newline='') as f:
        assert list(csv.reader(f)) == [[str(v) for v in row] for row in [header] + rows]

# Draw the charts directly with Pillow because matplotlib is unavailable.
image = Image.new('RGB', (1600, 1260), '#f5f7fb')
draw = ImageDraw.Draw(image)
regular = 'C:/Windows/Fonts/malgun.ttf'
bold = 'C:/Windows/Fonts/malgunbd.ttf'
font = ImageFont.truetype(regular, 25)
small = ImageFont.truetype(regular, 22)
heading = ImageFont.truetype(bold, 34)
title = ImageFont.truetype(bold, 44)
ink = '#1d293d'
muted = '#56657a'
colors = ['#2563eb', '#0f766e', '#7c3aed', '#b45309', '#64748b']
draw.text((60, 35), '업무 접수 집계', font=title, fill=ink)
draw.text((60, 100), f'정리 데이터 기준 · 전체 {total}건 · 단위: 건', font=font, fill=muted)
draw.rounded_rectangle((40, 160, 1560, 680), radius=18, fill='white')
draw.rounded_rectangle((40, 710, 1560, 1220), radius=18, fill='white')
draw.text((70, 180), '업무유형별 건수', font=heading, fill=ink)

left, right = 290, 1400
top_y, gap, bar_h = 265, 51, 31
scale_max = max(counts.values()) + 1
for tick in range(scale_max + 1):
    x = left + (right - left) * tick / scale_max
    draw.line((x, top_y - 10, x, top_y + gap * 6 + bar_h + 10), fill='#e4e9f1', width=1)
    draw.text((x, 640), str(tick), font=small, fill=muted, anchor='mt')
for i, name in enumerate(types):
    y = top_y + i * gap
    value = counts[name]
    end = left + (right - left) * value / scale_max
    draw.text((260, y + bar_h / 2), name, font=font, fill=ink, anchor='rm')
    draw.rectangle((left, y, end, y + bar_h), fill='#2563eb')
    draw.text((end + 15, y + bar_h / 2), str(value), font=font, fill=ink, anchor='lm')

draw.text((70, 730), '담당부서별 처리상태', font=heading, fill=ink)
draw.text((1510, 743), '막대 오른쪽: 부서 합계', font=small, fill=muted, anchor='rt')
for i, status in enumerate(statuses):
    x = 290 + i * 205
    draw.rectangle((x, 795, x + 23, 818), fill=colors[i])
    draw.text((x + 34, 806), status, font=small, fill=ink, anchor='lm')
top_y, gap, bar_h = 865, 48, 32
dept_max = max(row[-1] for row in cross_rows[:-1]) + 1
for tick in range(dept_max + 1):
    x = left + (right - left) * tick / dept_max
    draw.line((x, top_y - 10, x, top_y + gap * 5 + bar_h + 10), fill='#e4e9f1', width=1)
    draw.text((x, 1165), str(tick), font=small, fill=muted, anchor='mt')
for i, dept in enumerate(departments):
    y = top_y + i * gap
    draw.text((260, y + bar_h / 2), dept, font=font, fill=ink, anchor='rm')
    running = 0
    for j, status in enumerate(statuses):
        value = cross[dept, status]
        if value:
            start = left + (right - left) * running / dept_max
            end = left + (right - left) * (running + value) / dept_max
            draw.rectangle((start, y, end, y + bar_h), fill=colors[j])
            draw.text(((start + end) / 2, y + bar_h / 2 - 1), str(value), font=small,
                      fill='white', anchor='mm')
        running += value
    end = left + (right - left) * running / dept_max
    draw.text((end + 15, y + bar_h / 2), str(running), font=font, fill=ink, anchor='lm')
image_path = ROOT / 'office_practice_summary.png'
image.save(image_path)
with Image.open(image_path) as saved:
    saved.verify()
assert source.read_bytes() == original_bytes
print(json.dumps({'total': total, 'type_counts': type_rows,
                  'cross_header': ['담당부서'] + statuses + ['전체 합계'],
                  'cross_rows': cross_rows, 'source_unchanged': True}, ensure_ascii=True))
