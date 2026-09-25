# ZPL to PNG

Local Flask application and Python renderer for ZPL labels. The default canvas is
812 × 1218 pixels (4 × 6 inches at 203 DPI).

## Run

```powershell
python -m pip install -r requirements.txt
python examples/web_server.py
```

Open http://localhost:5000. The app renders locally; label content is not sent to
Labelary during normal conversion.

## Labelary comparison

```powershell
python -B tools/compare_labelary.py
python -B -m unittest discover -s tests -v
```

The comparison uses saved reference PNGs. To regenerate them, explicitly run
`python -B tools/compare_labelary.py --refresh`; this sends `zpl_data.txt` and
`compare_zpl.txt` to the [Labelary API](https://labelary.com/service.html).
The API settings are 8 dpmm, 4 × 6 inches, label index 0. Compare decoded pixel
values, not PNG file bytes (compression and metadata can differ).

See [comparison report](comparisons/README.md), [pixel metrics](comparisons/report.json),
[sample comparison](comparisons/sample-comparison.png), and
[shipping comparison](comparisons/shipping-comparison.png).

## Current limits

This is a partial ZPL implementation, not a pixel-exact Labelary replacement.
The bundled Roboto Condensed and Liberation Mono fonts approximate printer fonts
0 and A; glyph outlines, font metrics, hinting, and barcode captions still differ.
Field blocks (`^FB`) support alignment, word wrapping, explicit `\&` line breaks,
line spacing, hanging indentation, and last-line overprinting. Rotated blocks,
soft hyphens, and exact printer font metrics need further validation.
International encodings and several printer commands are not fully implemented.
Code 128 supports default subset B, explicit subset
invocations, and automatic numeric runs; Data Matrix currently supports square
ECC 200 with the `_1` FNC1 escape. Other barcode options need separate validation.

The canvas dimensions are controlled by the conversion call; out-of-bounds fields
are clipped. `^PW` and `^LL` do not expand the requested media dimensions.

## Brand template comparison

The supplied brand template is saved as `comparisons/brand-template.zpl` and is
included in the comparison script. QR model 2 rendering now uses qrcodegen;
`^A0N,h` now derives an omitted width from the requested height.
See [brand comparison](comparisons/brand-comparison.png).

For production templates, use `^BQN,2,5,M^FDMA,{$qr$}^FS` and substitute your
actual payload. `MA,` is the normal QR configuration prefix. The supplied three
spaces are retained in the saved fixture: Labelary consumes two prefix characters
and encodes the remaining leading space along with `{$qr$}`. The local renderer
reproduces that behavior. Replace `{$logo$}` with valid ZPL graphics before rendering.
QR automatic input, numeric/alphanumeric/manual bytes, magnification, and explicit
mask selection are supported. Model 1 and Kanji/mixed manual modes are not.
The tested Labelary service chooses masks automatically even when explicitly set;
the local renderer honors explicit masks, so those QR patterns can differ.
