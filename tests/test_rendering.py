"""Offline regression checks against independently rendered Labelary PNGs."""
from pathlib import Path
import os
import tempfile
import unittest
from PIL import Image, ImageChops
from zplconvert import convert_zpl_to_image
from zplconvert.elements.graphic import ImageElement

ROOT = Path(__file__).resolve().parents[1]


class LabelaryRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images = {}
        for name, source in [('sample', 'zpl_data.txt'), ('shipping', 'compare_zpl.txt'),
                             ('brand', 'comparisons/brand-template.zpl')]:
            cls.images[name] = (Image.open(ROOT / 'comparisons' / f'{name}-labelary.png').convert('RGB'),
                                convert_zpl_to_image((ROOT / source).read_text(), optimize=True))

    def assert_region(self, name, box):
        reference, actual = self.images[name]
        self.assertIsNone(ImageChops.difference(reference.crop(box), actual.crop(box)).getbbox())

    def test_reversed_logo(self):
        self.assert_region('sample', (0, 0, 200, 200))

    def test_brand_qr_matches_labelary(self):
        self.assert_region('brand', (30, 400, 180, 560))

    def test_omitted_font_width_matches_explicit_proportional_width(self):
        for height in (30, 40, 70, 80):
            for preceding in ('', '^A0N,20,8^FDPrevious^FS'):
                prefix = '^XA' + preceding + '^FO30,100'
                implicit = convert_zpl_to_image(prefix + f'^A0N,{height}^FDTest 123^FS^XZ')
                explicit = convert_zpl_to_image(prefix + f'^A0N,{height},{height}^FDTest 123^FS^XZ')
                self.assertIsNone(ImageChops.difference(implicit, explicit).getbbox())

    def test_qr_prefix_and_literal_whitespace(self):
        from zplconvert.elements.qrcode import QRCodeElement
        self.assertEqual(QRCodeElement(0, 0, 'MA,  hello,world').payload, '  hello,world')
        self.assertEqual(QRCodeElement(0, 0, '   {$qr$}').payload, ' {$qr$}')

    def test_qr_does_not_change_following_barcode_or_text(self):
        from zplconvert.parser import parse_zpl
        from zplconvert.elements.barcode import BarcodeElement
        from zplconvert.elements.text import TextElement
        label = parse_zpl('^XA^BY3^BQ,2,5^FDMA,hello^FS^FO200,100^FDText^FS^FO0,600^BCN,50,N^FD123^FS^XZ')
        self.assertIsInstance(label.elements[1], TextElement)
        self.assertIsInstance(label.elements[2], BarcodeElement)
        self.assertEqual(label.elements[2].module_width, 3)

    def test_code128_default_subset_b(self):
        self.assert_region('sample', (100, 550, 750, 820))

    def test_compressed_graphic(self):
        self.assert_region('shipping', (0, 0, 202, 202))

    def test_gs1_code128(self):
        self.assert_region('shipping', (75, 870, 745, 1035))

    def test_automatic_code128_odd_digit_run(self):
        self.assert_region('shipping', (12, 1120, 450, 1180))

    def test_datamatrix_uses_exact_modules_and_baseline(self):
        self.assert_region('shipping', (25, 640, 115, 730))
        self.assert_region('shipping', (700, 1120, 790, 1210))

    def test_canvas_clips_fields(self):
        image = convert_zpl_to_image('^XA^PW900^LL1300^FO0,1200^GB200,200,200^FS^XZ')
        self.assertEqual(image.size, (812, 1218))

    def test_graphic_repeat_counts_apply_to_next_nibble(self):
        graphic = ImageElement(0, 0, 16, 4, 'HF,!:')
        self.assertEqual(graphic.ascii_to_hex(graphic.image_data), 'FF00\nFFFF\nFFFF')

    def test_optimization_preserves_pixels(self):
        source = (ROOT / 'zpl_data.txt').read_text()
        self.assertIsNone(ImageChops.difference(convert_zpl_to_image(source), convert_zpl_to_image(source, optimize=True)).getbbox())

    def test_web_endpoint_uses_same_renderer(self):
        from examples.web_server import app
        source = (ROOT / 'comparisons/brand-template.zpl').read_text()
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            try:
                os.chdir(directory)
                with app.test_client() as client:
                    response = client.post('/convert', json={'zpl': source})
                    self.assertEqual(response.status_code, 200)
                    with Image.open('output.png') as actual:
                        self.assertIsNone(ImageChops.difference(actual, self.images['brand'][1]).getbbox())
                    with client.get('/output.png') as served:
                        self.assertEqual(served.status_code, 200)
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
