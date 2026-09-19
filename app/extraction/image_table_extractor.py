import logging
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
from app.storage.storage_service import storage_service

logger = logging.getLogger(__name__)


class ImageTableExtractor:
    """Extracts embedded images and structured tables from PDF pages using PyMuPDF."""

    def extract_images_from_page(self, page: fitz.Page, doc_id: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract embedded images from PyMuPDF Page.
        Saves files using StorageService and returns image metadata.
        """
        images = []
        if page is None or not hasattr(page, "get_images"):
            return images

        try:
            image_list = page.get_images(full=True)
            for idx, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = page.parent.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image.get("ext", "png")
                    original_name = f"doc_{doc_id}_p{page_num}_img{idx+1}.{image_ext}"

                    storage_key = storage_service.save_file(image_bytes, original_name)
                    images.append({
                        "storage_key": storage_key,
                        "page_number": page_num,
                        "width": base_image.get("width"),
                        "height": base_image.get("height"),
                        "xref": xref
                    })
                except Exception as ex:
                    logger.warning(f"Could not extract image xref {xref} on page {page_num}: {ex}")
        except Exception as e:
            logger.warning(f"Error extracting images on page {page_num}: {e}")

        return images

    def extract_tables_from_page(self, page: fitz.Page, page_num: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract structured tables using PyMuPDF find_tables().
        Returns (tables_list, warnings_list).
        """
        tables = []
        warnings = []
        if page is None or not hasattr(page, "find_tables"):
            return tables, warnings

        try:
            tabs = page.find_tables()
            if tabs and hasattr(tabs, "tables"):
                for idx, tab in enumerate(tabs.tables):
                    grid = tab.extract()
                    if grid and len(grid) > 0:
                        headers = [str(cell) if cell is not None else "" for cell in grid[0]]
                        rows = [[str(cell) if cell is not None else "" for cell in row] for row in grid[1:]]
                        tables.append({
                            "table_index": idx + 1,
                            "page_number": page_num,
                            "headers": headers,
                            "rows": rows
                        })
        except Exception as e:
            logger.warning(f"Table parsing failed on page {page_num}: {e}")
            warnings.append({
                "warning_type": "TABLE_EXTRACTION_UNCERTAIN",
                "message": f"Table extraction structure uncertain on page {page_num}: {str(e)}",
                "severity": "medium",
                "page_number": page_num
            })

        return tables, warnings


image_table_extractor = ImageTableExtractor()
