from pypdf import PdfReader

reader = PdfReader("backend/assets/irs_templates/Form_8949_Fillable_2024.pdf")
fields = reader.get_fields()

for name, field in fields.items():
    print(f"{name}")
