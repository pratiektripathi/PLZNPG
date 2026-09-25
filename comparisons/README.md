# Labelary comparison results

Both supplied labels were rendered with the live Labelary API and the local app
at 812 × 1218 pixels. Reference PNGs and original local outputs are preserved.
The app remains offline; only the explicit comparison refresh calls Labelary.

| Label | Different pixels before | Different pixels after |
| --- | ---: | ---: |
| zpl_data.txt | 129,279 (13.0715%) | 47,199 (4.7723%) |
| compare_zpl.txt | 66,851 (6.7593%) | 47,081 (4.7604%) |

These percentages include white background and do not imply equivalent visual
quality or an exact whole-label match. All differing RGB pixels count, including
antialiasing differences. The full labels are **not yet pixel-exact**.

Independently checked regions now have zero differing pixels: the reversed logo,
compressed graphic, default Code 128 bars, GS1-128 bars, automatic Code 128 bars,
and both Data Matrix symbols. The remaining differences are text rendering,
including barcode captions. Bundled substitute fonts do not reproduce Labelary's
font outlines and rasterization exactly.

- [Sample: reference / app / difference](sample-comparison.png)
- [Shipping: reference / app / difference](shipping-comparison.png)
- [Machine-readable report](report.json)

`*-labelary.png` are reference images; `*-before.png` are untouched initial app
outputs; `*-after.png` are updated app outputs. Difference PNGs are black where
pixels agree. `report.json` includes source hashes so input changes can be detected.

Run `python -B tools/compare_labelary.py` from the project root to reproduce.
Run `python -B -m unittest discover -s tests -v` for the offline regression suite.

## Brand template supplied in the follow-up

[Labelary / updated app / difference](brand-comparison.png).
The exact input is [brand-template.zpl](brand-template.zpl), with all placeholders
retained. The logo placeholder is not ZPL graphics and produces no logo in either
renderer. QR and separator regions match exactly. Font width defaults were fixed:
`^A0N,70` now has the same proportions as `^A0N,70,70`.

The whole-label difference is 54,967 pixels (5.5577%), versus 54,879 (5.5488%)
before. Mean absolute channel error improved from 12.3912 to 11.5157. The changed
pixel count alone is misleading here: the old text was severely compressed and
mostly blank; the corrected text occupies the intended area but substitute font
outlines and spacing still differ. No exact whole-label claim is made.

The QR region has **zero differing pixels**. Use `^FDMA,{$qr$}` in a production
QR template instead of the ambiguous three-space prefix. This is a recommended
input correction; the supplied test input has not been changed.

## Field-block label

[Labelary / updated app / difference](field-block-comparison.png).
Input: [field-block.zpl](field-block.zpl). Added local `^FB` layout and reset at
`^FS`. In all 13 supplied fields, the rendered text centers are within 5 pixels
of the reference centers; bundled font outlines still differ. The field widths
and origins are used exactly as provided, without adjusting the table geometry.

Different pixels decreased from 91,289 (9.2303%) to 54,490 (5.5095%). Mean absolute
channel error decreased from 19.8181 to 10.3912. The app remains fully local.
The regression suite now includes centering against this reference, left/center/
right alignment, field reset, line breaks, spacing, indentation, word wrapping,
and last-line overflow. Whole-label pixel equality is not claimed.
