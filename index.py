from fpdf import FPDF
import json
import os
from PyPDF2 import PdfReader, PdfWriter


class PDF(FPDF):
    def __init__(self, pdf_file, background_image=None):
        super().__init__()
        self.pdf_file = pdf_file if pdf_file.endswith(".pdf") else f"{pdf_file}.pdf"
        self.background_image = background_image

    def add_page(self, *args, **kwargs):
        super().add_page(*args, **kwargs)
        if self.background_image:
            self.image(self.background_image, x=0, y=0, w=self.w, h=self.h)

    def save_and_append(self):
        if os.path.exists(self.pdf_file):
            new_pdf_path = f"{os.path.splitext(self.pdf_file)[0]}_temp.pdf"
            self.output(new_pdf_path, "F")

            reader = PdfReader(self.pdf_file)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            new_reader = PdfReader(new_pdf_path)
            for page in new_reader.pages:
                writer.add_page(page)

            with open(self.pdf_file, "wb") as f:
                writer.write(f)

            os.remove(new_pdf_path)
        else:
            self.output(self.pdf_file, "F")


def create_title_page(pdf_file, words_json, background_image=None):
    pdf = PDF(pdf_file, background_image)
    pdf.add_page()

    book_title = os.path.splitext(os.path.basename(pdf_file))[0]
    pdf.set_font("Arial", "B", 32)
    pdf.cell(200, 20, txt=book_title, ln=True, align="C")
    pdf.ln(10)

    if not os.path.exists(words_json):
        print(f"Error: File '{words_json}' does not exist.")
        return

    with open(words_json, 'r') as f:
        data = json.load(f)

    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 10, txt="Table of Contents", ln=True, align="C")
    pdf.ln(10)

    for topic, modes in data.items():
        pdf.set_font("Arial", "BU", 14)
        pdf.cell(200, 10, txt=topic, ln=True, align="L")

        for mode, puzzles in modes.items():
            puzzle_count = sum(len(p) for p in puzzles.values()) if mode == "Bonus" else len(puzzles)
            if puzzle_count < 1:
                continue
            pdf.cell(10)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(20, 8, txt=f"{mode}:", ln=False)
            pdf.set_font("Arial", "", 12)

            if mode == "Bonus":
                for i in range(puzzle_count):
                    x_pos = pdf.get_x() + 12 * i
                    y_pos = pdf.get_y() + 5
                    pdf.text(x_pos, y_pos, "O")
                pdf.ln(5)

                pdf.cell(25)
                pdf.set_font("Arial", "", 7)
                for i in range(puzzle_count):
                    pdf.cell(12, 6, txt=str(i + 1), align="C")
                pdf.set_font("Arial", "", 12)
                pdf.ln(10)

            else:
                for i in range(len(puzzles)):
                    x_pos = pdf.get_x() + 12 * i
                    y_pos = pdf.get_y() + 5
                    pdf.text(x_pos, y_pos, "O")
                pdf.ln(5)

                pdf.cell(25)
                pdf.set_font("Arial", "", 7)
                for i in range(len(puzzles)):
                    pdf.cell(12, 6, txt=str(i + 1), align="C")
                pdf.set_font("Arial", "", 12)
                pdf.ln(10)

        pdf.ln(5)

    pdf.save_and_append()


def main():
    create_title_page(
        pdf_file="Where's Word-o",
        words_json="Words/words.json",
        background_image="Assets/Background.png"
    )


if __name__ == '__main__':
    main()
