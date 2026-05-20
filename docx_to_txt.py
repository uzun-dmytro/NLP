from docx import Document
from pathlib import Path

docx_path = Path("samchuk-ulas-oleksiyovych-volyn.docx")
txt_path = Path("Uzun_file_1.txt")

doc = Document(docx_path)

paragraphs = []
for paragraph in doc.paragraphs:
    text = paragraph.text.strip()
    if text:
        paragraphs.append(text)

result = "\n\n".join(paragraphs)

txt_path.write_text(result, encoding="utf-8")

print(f"{len(result)}")