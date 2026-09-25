"""Offline regression checks for local rendering behavior."""
from pathlib import Path
import os
import tempfile
import unittest
from PIL import Image, ImageChops
from zplconvert import convert_zpl_to_image
from zplconvert.elements.graphic import ImageElement

ROOT = Path(__file__).resolve().parents[1]


class RenderingTests(unittest.TestCase):
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
        source = '^XA^FO30,40^A0N,30^FDWeb render^FS^FO30,100^BQN,2,5^FDMA,hello^FS^XZ'
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            try:
                os.chdir(directory)
                with app.test_client() as client:
                    response = client.post('/convert', json={'zpl': source})
                    self.assertEqual(response.status_code, 200)
                    with Image.open('output.png') as actual:
                        self.assertIsNone(ImageChops.difference(actual, convert_zpl_to_image(source, optimize=True)).getbbox())
                    with client.get('/output.png') as served:
                        self.assertEqual(served.status_code, 200)
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
