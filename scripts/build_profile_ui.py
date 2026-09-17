"""Build small, self-contained SVG links for GitHub's sanitized README.

Requires fonttools and Montserrat-Medium.ttf / Montserrat-SemiBold.ttf.
Usage: python scripts/build_profile_ui.py --font-dir C:/Windows/Fonts
All lettering is outlined so visitors do not need the fonts installed.
"""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--font-dir', type=Path, required=True)
args = parser.parse_args()
fonts = {weight: TTFont(args.font_dir / f'Montserrat-{weight}.ttf')
         for weight in ['Medium', 'SemiBold']}
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'navigation'
OUT.mkdir(parents=True, exist_ok=True)
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
report = []


def add(parent, tag, **attrs):
    return ET.SubElement(parent, f'{{{NS}}}{tag}', {k: str(v) for k, v in attrs.items()})


def text(parent, value, x, y, size, color, weight='SemiBold'):
    font = fonts[weight]
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font['head'].unitsPerEm
    group = add(parent, 'g', fill=color, **{'aria-label': value})
    bounds = BoundsPen(glyphs)
    for char in value:
        glyph = glyphs[cmap[ord(char)]]
        matrix = (scale, 0, 0, -scale, x, y)
        pen = SVGPathPen(glyphs)
        glyph.draw(TransformPen(pen, matrix))
        glyph.draw(TransformPen(bounds, matrix))
        if pen.getCommands():
            add(group, 'path', d=pen.getCommands())
        x += font['hmtx'].metrics[cmap[ord(char)]][0] * scale
    return bounds.bounds


def icon(parent, kind, x, y, color):
    group = add(parent, 'g', transform=f'translate({x} {y})')
    if kind == 'apps':
        for a, b in [(1, 1), (13, 1), (1, 13), (13, 13)]:
            add(group, 'rect', x=a, y=b, width=9, height=9, rx=2, fill=color)
    elif kind == 'youtube':
        add(group, 'rect', x=0, y=3, width=26, height=18, rx=5, fill='#ff0000')
        add(group, 'path', d='M10 7.5V16.5L18 12Z', fill='#fff')
    elif kind == 'course':
        add(group, 'path', d='M2 4Q7 2 12 5Q17 2 22 4V20Q17 18 12 21Q7 18 2 20ZM12 5V21',
            fill='none', stroke=color, **{'stroke-width': 1.8, 'stroke-linejoin': 'round'})
    elif kind == 'linkedin':
        add(group, 'rect', x=1, y=1, width=22, height=22, rx=4, fill='#0a66c2')
        text(group, 'in', 4.1, 18.3, 15, '#fff')
    elif kind == 'contact':
        add(group, 'rect', x=1, y=4, width=22, height=16, rx=3, fill='none', stroke=color, **{'stroke-width': 1.6})
        add(group, 'path', d='M2 6L12 13L22 6', fill='none', stroke=color, **{'stroke-width': 1.6, 'stroke-linejoin': 'round'})
    elif kind == 'support':
        add(group, 'path', d='M3 7H17V16A4 4 0 0 1 13 20H7A4 4 0 0 1 3 16ZM17 8H19A4 4 0 0 1 19 16H17M2 23H21M7 1V4M12 1V4',
            fill='none', stroke=color, **{'stroke-width': 1.7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'})


def button(name, label, width, theme='light', small=False):
    dark = theme == 'dark'
    height = 48 if small else 62
    primary = name == 'apps'
    ink = '#ffffff' if primary else ('#e8f0f7' if dark else '#294f6e')
    fill = '#3772a3' if primary else ('#1a2734' if dark else '#f6f9fc')
    stroke = '#3772a3' if primary else ('#3b5062' if dark else '#d5e1eb')
    svg = ET.Element(f'{{{NS}}}svg', {'width': str(width), 'height': str(height),
                                    'viewBox': f'0 0 {width} {height}', 'role': 'img', 'aria-label': label})
    add(svg, 'title').text = label
    # Soft fixed shadows are inside the image canvas; no clipped filter effects.
    if not small:
        add(svg, 'rect', x=2, y=6, width=width-4, height=height-10, rx=12,
            fill='#000' if dark else '#234d70', opacity='.22' if dark else '.07')
    add(svg, 'rect', x=2, y=2, width=width-4, height=height-10, rx=11 if not small else 9,
        fill=fill, stroke=stroke, **{'stroke-width': 3 if primary else 1})
    if not small:
        add(svg, 'path', d=f'M15 4H{width-15}', stroke='#fff', opacity='.2' if primary else '.09')
    center = (height-6)/2
    icon_x = 14 if small else 18
    icon(svg, name, icon_x, center-12, ink if primary else ('#93c4eb' if dark else '#3772a3'))
    size = 14 if small else (15.5 if primary else 15)
    bounds = text(svg, label, 45 if small else 54, center+5.3, size, ink)
    limit = width-12 if small else width-34
    assert bounds[2] <= limit and bounds[1] > 4 and bounds[3] < height-6, (name, bounds, limit)
    if not small:
        add(svg, 'path', d=f'M{width-29} {center}H{width-17}M{width-22} {center-5}L{width-17} {center}L{width-22} {center+5}',
            fill='none', stroke=ink, **{'stroke-width': 1.7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'})
    filename = f'{name}.svg' if primary else f'{name}-{theme}.svg'
    file = OUT / filename
    ET.ElementTree(svg).write(file, encoding='utf-8', xml_declaration=True)
    report.append({'file': filename, 'canvas': [width, height], 'label_bounds': bounds, 'bytes': file.stat().st_size})


def project_card(name, title, description, category, theme):
    dark = theme == 'dark'
    width, height = 400, 146
    foreground = '#edf3f9' if dark else '#202a36'
    muted = '#b1c2d2' if dark else '#586b7c'
    blue = '#93c4eb' if dark else '#3772a3'
    svg = ET.Element(f'{{{NS}}}svg', {'width': str(width), 'height': str(height),
                                    'viewBox': f'0 0 {width} {height}', 'role': 'img', 'aria-label': title})
    add(svg, 'title').text = f'{title}. {description} Open the source code.'
    add(svg, 'rect', x=2, y=5, width=width-4, height=height-9, rx=14,
        fill='#000' if dark else '#234d70', opacity='.18' if dark else '.04')
    add(svg, 'rect', x=2, y=2, width=width-4, height=height-10, rx=13,
        fill='#16212c' if dark else '#fbfcfe', stroke='#344b5d' if dark else '#d5e1eb', **{'stroke-width': 1})
    bounds = []
    bounds.append(text(svg, category, 22, 28, 12, blue))
    bounds.append(text(svg, title, 22, 62, 21, foreground))
    bounds.append(text(svg, description, 22, 86, 16, muted, 'Medium'))
    bounds.append(text(svg, 'Open project', 22, 119, 14.5, blue))
    add(svg, 'path', d='M123 114H138M133 109L138 114L133 119', fill='none', stroke=blue,
        **{'stroke-width': 1.6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'})
    ornament = add(svg, 'g', transform='translate(348 15)', stroke=blue, fill='none', **{'stroke-width': 1.6, 'stroke-linejoin': 'round'})
    if name == 'sales':
        add(ornament, 'rect', x=0, y=0, width=27, height=25, rx=5)
        add(ornament, 'path', d='M6 19V13M13 19V7M20 19V10', **{'stroke-width': 3, 'stroke-linecap': 'round'})
    else:
        add(ornament, 'path', d='M14 0L17.5 10.5L28 14L17.5 17.5L14 28L10.5 17.5L0 14L10.5 10.5ZM27 0V6M24 3H30')
    assert all(b[0]>=20 and b[2]<width-20 and b[1]>8 and b[3]<height-10 for b in bounds), (name,bounds)
    filename = f'project-{name}-{theme}.svg'
    file = OUT / filename
    ET.ElementTree(svg).write(file, encoding='utf-8', xml_declaration=True)
    report.append({'file': filename, 'canvas': [width,height], 'bytes': file.stat().st_size})


button('apps', 'Explore apps & add-ins', 312)
for theme in ['light', 'dark']:
    button('youtube', 'Watch tutorials', 214, theme)
    button('course', 'Excel automation course', 284, theme)
    button('linkedin', 'LinkedIn', 148, theme, small=True)
    button('contact', 'Get in touch', 156, theme, small=True)
    button('support', 'Support', 142, theme, small=True)
    project_card('sales', 'Sales dashboard', 'Turn Excel data into an interactive app.', 'PYTHON / STREAMLIT', theme)
    project_card('office-ai', 'AI for office tasks', 'Automate reports, files and emails.', 'PYTHON / CHATGPT', theme)

print(json.dumps(report, indent=2))
