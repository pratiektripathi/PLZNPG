"""Compare local rendering with saved or freshly fetched Labelary references.

Run: python -B tools/compare_labelary.py [--refresh]
--refresh sends the listed sample ZPL files to the Labelary API.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request
from PIL import Image, ImageChops, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zplconvert import convert_zpl_to_image

CASES = {'sample': 'zpl_data.txt', 'shipping': 'compare_zpl.txt',
         'brand': 'comparisons/brand-template.zpl',
         'field-block': 'comparisons/field-block.zpl'}
REGIONS = {
    'field-block': {'bottom_border': (30, 717, 780, 720)},
    'brand': {'qr': (30, 400, 180, 560), 'separator': (50, 130, 750, 133)},
    'sample': {'logo': (0, 0, 200, 200), 'code128': (100, 550, 750, 820)},
    'shipping': {'graphic': (0, 0, 202, 202), 'datamatrix': (25, 640, 115, 730),
                 'gs1_128': (75, 870, 745, 1035), 'automatic_code128': (12, 1120, 450, 1180)},
}


def metrics(reference, actual):
    if reference.size != actual.size:
        return {'exact': False, 'size': list(actual.size), 'expected_size': list(reference.size)}
    diff = ImageChops.difference(reference.convert('RGB'), actual.convert('RGB'))
    channels = diff.split()
    mask = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    changed = reference.width * reference.height - mask.histogram()[0]
    return {'exact': changed == 0, 'different_pixels': changed,
            'different_percent': round(changed / (reference.width * reference.height) * 100, 4),
            'mean_absolute_error': round(sum(ImageStat.Stat(diff).mean) / 3, 4)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    out = ROOT / 'comparisons'
    out.mkdir(exist_ok=True)
    report = {}
    for name, source in CASES.items():
        payload = (ROOT / source).read_bytes()
        reference_path = out / f'{name}-labelary.png'
        if args.refresh:
            req = urllib.request.Request('https://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/',
                data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'image/png'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
            reference_path.write_bytes(data)
            time.sleep(0.4)
        reference = Image.open(reference_path).convert('RGB')
        actual = convert_zpl_to_image(payload.decode('utf-8'), optimize=True)
        actual.save(out / f'{name}-after.png')
        result = {'source': source, 'zpl_sha256': hashlib.sha256(payload).hexdigest(),
                  'after': metrics(reference, actual),
                  'regions': {key: metrics(reference.crop(box), actual.crop(box)) for key, box in REGIONS[name].items()}}
        before = out / f'{name}-before.png'
        if before.exists():
            result['before'] = metrics(reference, Image.open(before))
        report[name] = result
        diff = ImageChops.difference(reference, actual)
        diff.save(out / f'{name}-diff.png')
        panel = Image.new('RGB', (reference.width * 3, reference.height + 30), 'white')
        d = ImageDraw.Draw(panel)
        for index, (title, im) in enumerate([('Labelary', reference), ('Local app', actual), ('Difference (black = equal)', diff)]):
            d.text((index*reference.width+10, 8), title, fill='black')
            panel.paste(im, (index*reference.width, 30))
        panel.save(out / f'{name}-comparison.png')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
