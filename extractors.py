"""
extractors.py — извлечение текста из документов.

Поддерживаемые форматы:
- PDF  (через библиотеку pdfplumber)
- DOCX (через библиотеку python-docx)
- TXT  (обычный текст в кодировке UTF-8)

Каждая функция принимает file-like объект (например, BytesIO)
и возвращает строку с извлечённым текстом.
Если файл пуст или повреждён — бросает ValueError.
"""

import docx
import pdfplumber


def extract_text_from_pdf(file) -> str:
    """
    Извлекает текст из PDF-файла постранично.

    Args:
        file: Файл в виде байтового потока (BytesIO).

    Returns:
        Строка со всем текстом из PDF.

    Raises:
        ValueError: Если PDF не содержит текста или повреждён.
    """
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            # extract_text() может вернуть None для пустых страниц
            text += page.extract_text() or ""

    if not text.strip():
        raise ValueError("PDF-файл не содержит текста или повреждён")

    return text


def extract_text_from_docx(file) -> str:
    """
    Извлекает текст из DOCX-файла, объединяя все параграфы.

    Args:
        file: Файл в виде байтового потока (BytesIO).

    Returns:
        Строка с текстом, параграфы разделены переносом строки.

    Raises:
        ValueError: Если DOCX не содержит текста или повреждён.
    """
    document = docx.Document(file)
    # Собираем текст из каждого параграфа через перенос строки
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    if not text.strip():
        raise ValueError("DOCX-файл не содержит текста или повреждён")

    return text


def extract_text_from_txt(file) -> str:
    """
    Читает текст из TXT-файла в кодировке UTF-8.

    Args:
        file: Файл в виде байтового потока (BytesIO).

    Returns:
        Строка с содержимым файла.

    Raises:
        ValueError: Если файл пуст или повреждён.
    """
    text = file.read().decode("utf-8")

    if not text.strip():
        raise ValueError("TXT-файл пуст или повреждён")

    return text
