"""Build-time warm-up: convert a tiny generated PDF twice (text layer and
forced OCR) so Marker downloads its CPU models and font into the image."""
import time

from weasyprint import HTML

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

HTML(
    string="<h1>Marker warm-up</h1><p>Hello <b>world</b>, x = 2 + 2.</p>"
    "<table border=1><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
).write_pdf("/tmp/warmup.pdf")



def run():
    models = create_model_dict()
    for config in ({"mode": "fast"}, {"mode": "fast", "force_ocr": True}):
        converter = PdfConverter(artifact_dict=models, config=config)
        text, _, _ = text_from_rendered(converter("/tmp/warmup.pdf"))
        print(config, "->", text.strip().replace("\n", " ")[:200], flush=True)


# Model downloads can hit transient network errors; retry a few times.
for attempt in range(1, 6):
    try:
        run()
        break
    except Exception as exc:  # noqa: BLE001
        if attempt == 5:
            raise
        print(f"warm-up attempt {attempt} failed: {exc!r}; retrying", flush=True)
        time.sleep(5 * attempt)
