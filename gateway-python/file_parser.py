import csv
import io
from typing import Any

from docx import Document
from openpyxl import load_workbook


def _clean_cell(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _split_delimited_line(line: str) -> list[str]:
    text = line.strip()
    if not text:
        return []
    if "\t" in text:
        return [_clean_cell(c) for c in text.split("\t")]
    if "," in text:
        return [_clean_cell(c) for c in next(csv.reader([text]))]
    if ";" in text:
        return [_clean_cell(c) for c in text.split(";")]
    return [_clean_cell(c) for c in text.split()]


def _parse_csv_or_txt(content: bytes) -> list[list[str]]:
    decoded = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            decoded = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if decoded is None:
        raise ValueError("No se pudo decodificar el archivo de texto/CSV.")

    rows: list[list[str]] = []
    for line in decoded.splitlines():
        parsed = _split_delimited_line(line)
        if parsed and any(cell != "" for cell in parsed):
            rows.append(parsed)

    if not rows:
        raise ValueError("El archivo CSV/TXT está vacío o no contiene filas válidas.")
    return rows


def _parse_xlsx_bytes(content: bytes) -> list[list[str]]:
    wb = load_workbook(filename=io.BytesIO(content), data_only=True)
    ws = wb.active
    rows: list[list[str]] = []

    for row in ws.iter_rows(values_only=True):
        cells = [_clean_cell(cell) for cell in row]
        if any(cell != "" for cell in cells):
            rows.append(cells)

    if not rows:
        raise ValueError("El archivo Excel no contiene datos legibles.")
    return rows


def _parse_docx_bytes(content: bytes) -> list[list[str]]:
    doc = Document(io.BytesIO(content))
    rows: list[list[str]] = []

    # 1. Priorizar tabla en el documento Word si existe
    if doc.tables:
        table = doc.tables[0]
        for row in table.rows:
            cells = [_clean_cell(cell.text) for cell in row.cells]
            if any(cell != "" for cell in cells):
                rows.append(cells)
        if rows:
            return rows

    # 2. Si no hay tabla, leer párrafos no vacíos como filas
    for para in doc.paragraphs:
        parsed = _split_delimited_line(para.text)
        if parsed and any(cell != "" for cell in parsed):
            rows.append(parsed)

    if not rows:
        raise ValueError("El archivo .docx no contiene tablas ni líneas de datos legibles.")
    return rows


def _normalize_row_lengths(raw_rows: list[list[str]]) -> list[list[str]]:
    max_cols = max(len(r) for r in raw_rows)
    normalized: list[list[str]] = []
    for r in raw_rows:
        padded = r + [""] * (max_cols - len(r))
        normalized.append(padded)
    return normalized


def parse_uploaded_file(
    filename: str,
    content: bytes,
    has_header: bool = True,
    has_id: bool = True,
) -> dict[str, Any]:
    if not filename:
        raise ValueError("Nombre de archivo no proporcionado.")
    if not content:
        raise ValueError("El archivo está vacío.")

    lower_name = filename.lower().strip()

    if lower_name.endswith((".csv", ".txt", ".data")):
        raw_rows = _parse_csv_or_txt(content)
    elif lower_name.endswith(".xlsx"):
        raw_rows = _parse_xlsx_bytes(content)
    elif lower_name.endswith(".docx"):
        raw_rows = _parse_docx_bytes(content)
    else:
        raise ValueError(
            f"Formato no soportado para '{filename}'. Usa .csv, .txt, .data, .xlsx o .docx."
        )

    grid = _normalize_row_lengths(raw_rows)
    num_cols = len(grid[0])

    if has_header:
        header_row = grid[0]
        data_rows = grid[1:]
    else:
        header_row = [f"Var_{i + 1}" for i in range(num_cols)]
        data_rows = grid

    if not data_rows:
        raise ValueError("No hay filas de datos después de procesar el encabezado.")

    if has_id and num_cols >= 2:
        headers = header_row[1:] if has_header else [f"Var_{i}" for i in range(1, num_cols)]
        labels = [
            row[0] if row[0] != "" else f"Obs_{idx + 1}"
            for idx, row in enumerate(data_rows)
        ]
        matrix = [row[1:] for row in data_rows]
    else:
        headers = [
            h if h != "" else f"Var_{i + 1}"
            for i, h in enumerate(header_row)
        ]
        labels = [f"Obs_{idx + 1}" for idx in range(len(data_rows))]
        matrix = data_rows

    return {
        "headers": headers,
        "labels": labels,
        "matrix": matrix,
    }