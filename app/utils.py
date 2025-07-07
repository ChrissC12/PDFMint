# app/utils.py

def parse_page_ranges(range_string, max_pages):
    """
    Parses a string like "1, 3, 5-8, 10" into a set of page indices (0-based).
    Validates against the maximum number of pages.
    """
    pages_to_extract = set()
    parts = range_string.replace(" ", "").split(',')
    for part in parts:
        if not part: continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end or start < 1 or end > max_pages: raise ValueError
                pages_to_extract.update(range(start - 1, end))
            except (ValueError, TypeError): raise ValueError(f"Invalid range '{part}'.")
        else:
            try:
                page_num = int(part)
                if page_num < 1 or page_num > max_pages: raise ValueError
                pages_to_extract.add(page_num - 1)
            except (ValueError, TypeError): raise ValueError(f"Invalid page number '{part}'.")
    return sorted(list(pages_to_extract))