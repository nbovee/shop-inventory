import uuid
from treepoem import generate_barcode
from PIL import Image
from io import BytesIO


def barcode_page_generation(rows=14, cols=11, dry_run=False):
    # TODO improve efficiency, perhaps SVG methods could help?
    dpi = 600
    page_width = int(8.5 * dpi)
    page_height = int(11.0 * dpi)
    # designed for Avery Presta 94503
    barcode_size = int(0.3 * dpi)
    barcode_spacing_x = int(0.72 * dpi)
    barcode_spacing_y = int(0.69 * dpi)

    barcode_rows = int(rows)
    barcode_cols = int(cols)

    barcode_offset_x = int(0.53 * dpi)
    barcode_offset_y = int(0.91 * dpi)

    if dry_run:
        # Return dummy PDF bytes for testing
        return b"%PDF-1.4\n%EOF\n"

    sheet_img = Image.new("1", (page_width, page_height), 1)

    for row in range(0, barcode_rows):
        for col in range(0, barcode_cols):
            id = uuid.uuid4()
            # 22px size is 1px target border, 20x20 data
            encoded = generate_barcode(
                barcode_type="qrcode",
                data=f"{id.hex}",
                options={"version": "3"},
                scale=1,
            )
            # scale 7.5 could be correct for this dpi but it takes int
            barcode_img = encoded.convert("1").resize((barcode_size, barcode_size))
            sheet_img.paste(
                barcode_img,
                (
                    barcode_offset_x + col * barcode_spacing_x,
                    barcode_offset_y + row * barcode_spacing_y,
                ),
            )

    bytes = BytesIO()
    sheet_img.save(bytes, "PDF", resolution=dpi)
    return bytes.getvalue()
