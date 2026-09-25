"""Field-block regressions for the supplied label and reusable ZPL behavior."""
from pathlib import Path
import unittest
from PIL import ImageChops
from zplconvert import convert_zpl_to_image
from zplconvert.parser import parse_zpl
from zplconvert.elements.field_block import FieldBlockElement
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class FieldBlockTests(unittest.TestCase):
    def test_supplied_label_centers_track_labelary(self):
        actual = convert_zpl_to_image((ROOT / 'comparisons/field-block.zpl').read_text())
        with Image.open(ROOT / 'comparisons/field-block-labelary.png') as reference:
            boxes = [(34, 40, 777, 135)]
            for y in (190, 290, 380, 470, 560, 650):
                boxes.extend([(34, y-5, 298, y+65), (304, y-5, 777, y+65)])
            for box in boxes:
                with self.subTest(box=box):
                    bounds = [image.crop(box).convert('L').point(lambda p: 255 if p < 128 else 0).getbbox()
                              for image in (reference, actual)]
                    self.assertTrue(all(bounds))
                    centers = [(b[0]+b[2])/2 for b in bounds]
                    # Different bundled glyphs, but field centers must align.
                    self.assertLessEqual(abs(centers[0]-centers[1]), 5)

    def test_field_separator_resets_block(self):
        label = parse_zpl('^XA^FO20,20^A0N,30^FB300,1,0,C^FDHeading^FS^FO20,100^FDPlain^FS^XZ')
        self.assertIsInstance(label.elements[0], FieldBlockElement)
        self.assertNotIsInstance(label.elements[1], FieldBlockElement)
        actual = label.render().crop((0,100,400,160))
        expected = convert_zpl_to_image('^XA^FO20,100^A0N,30^FDPlain^FS^XZ').crop((0,100,400,160))
        self.assertIsNone(ImageChops.difference(actual, expected).getbbox())

    def test_left_center_right_move_text_inside_same_block(self):
        bounds = []
        for alignment in 'LCR':
            image = convert_zpl_to_image(f'^XA^FO20,20^A0N,30^FB300,1,0,{alignment}^FDTEST^FS^XZ')
            bounds.append(ImageChops.invert(image.convert('L')).getbbox())
        self.assertLess(bounds[0][0], bounds[1][0])
        self.assertLess(bounds[1][0], bounds[2][0])
        self.assertLessEqual(bounds[2][2], 320)
        self.assertEqual(len({b[2]-b[0] for b in bounds}), 1)

    def test_break_spacing_indent_and_last_line_overprint(self):
        label = parse_zpl(r'^XA^FO20,20^A0N,30^FB300,2,7,L,25^FDOne\&Two\&Three^FS^XZ')
        runs = label.elements[0].layout()
        self.assertEqual([r[0] for r in runs], ['One', 'Two', 'Three'])
        self.assertEqual([r[1] for r in runs], [0, 25, 25])
        self.assertEqual([r[2] for r in runs], [0, 37, 37])

    def test_wraps_words_and_splits_long_words(self):
        label = parse_zpl('^XA^A0N,30^FB100,10^FDONE TWO THREE ABCDEFGHIJKLMNOP^FS^XZ')
        runs = label.elements[0].layout()
        self.assertGreater(len(runs), 2)
        self.assertIn('ONE', [run[0] for run in runs])
        self.assertTrue(any(run[0].endswith('-') for run in runs))

    def test_zero_width_suppresses_text(self):
        image = convert_zpl_to_image('^XA^A0N,30^FB0^FDHidden^FS^XZ')
        self.assertIsNone(ImageChops.invert(image).getbbox())


if __name__ == '__main__':
    unittest.main()
