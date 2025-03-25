from pypdf import PdfReader

reader = PdfReader("backend/assets/irs_templates/Schedule_D_Fillable_2024.pdf")
fields = reader.get_fields()

for name, field in fields.items():
    print(f"{name}")
