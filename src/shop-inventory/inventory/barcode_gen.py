import uuid
import qrcode
from PIL import Image
from io import BytesIO
from PyPDF2 import PdfMerger
import logging
from tqdm import tqdm


def barcode_page_generation(rows: int = 14, cols: int = 11, pages: int = 1) -> bytes:
    logger = logging.getLogger(__name__)
    logger.info(
        f"Starting barcode generation: {pages} pages, {rows}x{cols} barcodes per page"
    )

    # Constants
    dpi = 600
    page_width = int(8.5 * dpi)
    page_height = int(11.0 * dpi)
    # designed for Avery Presta 94503
    barcode_size = int(0.3 * dpi)
    barcode_spacing_x = int(0.72 * dpi)
    barcode_spacing_y = int(0.69 * dpi)
    barcode_offset_x = int(0.53 * dpi)
    barcode_offset_y = int(0.91 * dpi)

    # Create QR code generator with fixed settings
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        border=0,
    )

    # Create PDF merger for multiple pages
    merger = PdfMerger()

    # Reuse BytesIO object for pages
    page_bytes = BytesIO()

    # Calculate total number of barcodes
    total_barcodes = rows * cols * pages

    # Create progress bar
    with tqdm(total=total_barcodes, desc="Generating barcodes") as pbar:
        for page in range(pages):
            logger.info(f"Generating page {page + 1} of {pages}")
            sheet_img = Image.new("1", (page_width, page_height), 1)

            for row in range(rows):
                for col in range(cols):
                    id = uuid.uuid4()
                    qr.clear()
                    qr.add_data(id.hex)
                    qr.make(fit=True)
                    barcode_img = qr.make_image(fill_color="black", back_color="white")
                    barcode_img = barcode_img.resize((barcode_size, barcode_size))

                    sheet_img.paste(
                        barcode_img,
                        (
                            barcode_offset_x + col * barcode_spacing_x,
                            barcode_offset_y + row * barcode_spacing_y,
                        ),
                    )
                    pbar.update(1)

            # Clear and reuse BytesIO for each page
            page_bytes.truncate(0)
            page_bytes.seek(0)
            sheet_img.save(page_bytes, "PDF", resolution=dpi)
            page_bytes.seek(0)
            merger.append(page_bytes)

    logger.info("Merging pages and finalizing PDF")
    # Get final merged PDF
    final_bytes = BytesIO()
    merger.write(final_bytes)
    merger.close()

    final_bytes.seek(0)
    return final_bytes.getvalue()
