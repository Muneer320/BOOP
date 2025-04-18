from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from PyPDF2 import PdfReader, PdfWriter
from svglib.svglib import svg2rlg
import os
import re
import time
import stat


def append_page(book_name, image_path):
    pdf_filename = f"{book_name}.pdf"

    page_width, page_height = A4

    if os.path.exists(pdf_filename):
        # print(f"'{pdf_filename}' exists. Appending the image.")
        existing_pdf = PdfReader(pdf_filename)
        output = PdfWriter()

        for page_num in range(len(existing_pdf.pages)):
            output.add_page(existing_pdf.pages[page_num])

        packet = canvas.Canvas("temp_page.pdf", pagesize=A4)
        packet.drawImage(image_path, 0, 0, width=page_width,
                         height=page_height)
        packet.save()

        new_page = PdfReader("temp_page.pdf")
        output.add_page(new_page.pages[0])

        with open(pdf_filename, "wb") as output_stream:
            output.write(output_stream)

        os.remove("temp_page.pdf")

    else:
        print(f"Creating '{pdf_filename}' and adding the image.")
        c = canvas.Canvas(pdf_filename, pagesize=A4)
        c.drawImage(image_path, 0, 0, width=page_width, height=page_height)
        c.showPage()
        c.save()

    print(f"{image_path} successfully added.")





def append_puzzle_page(pdf_file, svg_directory, background_image=None):
    temp_pdf = "temp.pdf"

    if os.path.exists(pdf_file):
        print(f"Reading existing PDF: {pdf_file}")
        with open(pdf_file, "rb") as f:
            existing_pdf = PdfReader(f)
            pdf_writer = PdfWriter()
            for page_num, page in enumerate(existing_pdf.pages, start=1):
                print(f"Adding existing page {page_num}")
                pdf_writer.add_page(page)
            with open(temp_pdf, "wb") as f_temp:
                pdf_writer.write(f_temp)
        print(f"Existing PDF pages saved to {temp_pdf}")

    new_pdf = "new_pages.pdf"
    new_solutions_pdf = "new_solutions.pdf"
    c = canvas.Canvas(new_pdf, pagesize=A4)
    c_solutions = canvas.Canvas(new_solutions_pdf, pagesize=A4)
    width, height = A4
    top_margin = 100
    bottom_margin = 100

    # Add "SOLUTIONS" cover page
    if background_image:
        c_solutions.drawImage(background_image, 0, 0,
                              width=width, height=height)
    solutions_cover = os.path.join(svg_directory, "S.svg")
    if os.path.exists(solutions_cover):
        cover_drawing = svg2rlg(solutions_cover)
        cover_width = cover_drawing.width
        cover_height = cover_drawing.height
        scale_cover_width = width / cover_width
        scale_cover_height = height / cover_height
        scale_cover = min(scale_cover_width, scale_cover_height)

        cover_drawing.scale(scale_cover, scale_cover)
        renderPDF.draw(cover_drawing, c_solutions, 0, 0)
        c_solutions.showPage()
        print(f"Added SOLUTIONS cover page: {solutions_cover}")
    else:
        c_solutions.setFont("Helvetica-Bold", 48)
        solutions_text = "SOLUTIONS"
        c_solutions.drawString(
            (width - c_solutions.stringWidth(solutions_text)) / 2, height / 2, solutions_text)
        c_solutions.showPage()

    def extract_order_number(filename):
        match = re.match(r"(\d+)", filename)
        return int(match.group(1)) if match else float('inf')

    solutions_per_line = 2
    max_lines_per_page = 3
    # Starting position for the first line of solutions
    y_position = height - top_margin - 150
    solution_page_num = 0
    for page_num, svg_filename in enumerate(sorted(os.listdir(svg_directory), key=extract_order_number), start=1):
        if svg_filename.endswith("S.svg"):
            continue

        svg_filepath = os.path.join(svg_directory, svg_filename)
        drawing = svg2rlg(svg_filepath)

        if background_image:
            c.drawImage(background_image, 0, 0, width=width, height=height)

        drawing_width = drawing.width
        drawing_height = drawing.height
        scale_width = width / drawing_width
        scale_height = height / drawing_height
        scale = min(scale_width, scale_height)

        drawing.scale(scale, scale)
        renderPDF.draw(drawing, c, (width - drawing_width * scale) /
                       2, (height - drawing_height * scale) / 2)

        print(f"Adding new page: {svg_filename}")
        c.showPage()

        # Add solution page
        solution_filename = svg_filename.replace(".svg", "S.svg")
        solution_filepath = os.path.join(svg_directory, solution_filename)
        if os.path.exists(solution_filepath):
            solution_drawing = svg2rlg(solution_filepath)

            if solution_page_num == 0 and background_image:
                c_solutions.drawImage(
                    background_image, 0, 0, width=width, height=height)

            if solution_drawing:
                solution_width = solution_drawing.width
                solution_height = solution_drawing.height
                # Two solutions per line
                scale_solution_width = (width / 2 - 50) / solution_width
                scale_solution_height = (height - top_margin - bottom_margin) / (
                    max_lines_per_page + 1) / solution_height  # Adjust for multiple lines per page
                scale_solution = min(scale_solution_width,
                                     scale_solution_height) * 1.2

                if solution_height * scale_solution + y_position < bottom_margin:
                    c_solutions.showPage()
                    if background_image:
                        c_solutions.drawImage(
                            background_image, 0, 0, width=width, height=height)
                    y_position = height - top_margin - 150

                x_position = (width / 2 - solution_width * scale_solution) / 2 + (solution_page_num %
                                                                                  # Adjust x-position for two solutions per line
                                                                                  solutions_per_line) * (width / 2)

                # Manually scale and position the drawing
                c_solutions.saveState()
                c_solutions.translate(x_position, y_position)
                c_solutions.scale(scale_solution, scale_solution)
                renderPDF.draw(solution_drawing, c_solutions, 0, 0)
                c_solutions.restoreState()

                # Add the name below each solution
                c_solutions.setFont("Helvetica", 12)
                solution_name = os.path.basename(solution_filepath).split(".")[
                    1].replace("S", "")
                text_width = c_solutions.stringWidth(
                    solution_name, "Helvetica", 12)
                c_solutions.drawString(
                    x_position + (solution_width * scale_solution - text_width) / 2, y_position - 20, solution_name)

                if solution_page_num % solutions_per_line == (solutions_per_line - 1):
                    y_position -= (solution_height * scale_solution + 50)
                    if solution_page_num % (solutions_per_line * max_lines_per_page) == (solutions_per_line * max_lines_per_page - 1):
                        c_solutions.showPage()
                        if background_image:
                            c_solutions.drawImage(
                                background_image, 0, 0, width=width, height=height)
                        y_position = height - top_margin - 150

                solution_page_num += 1

                print(f"Adding solution: {solution_filename}")

    c.save()
    c_solutions.save()

    # Merge puzzle and solution PDFs into the main PDF
    if os.path.exists(pdf_file):
        print(f"Merging existing and new pages into {pdf_file}")
        with open(temp_pdf, "rb") as f_existing, open(new_pdf, "rb") as f_new, open(new_solutions_pdf, "rb") as f_solutions:
            existing_pdf = PdfReader(f_existing)
            new_pdf_content = PdfReader(f_new)
            solutions_pdf_content = PdfReader(f_solutions)
            pdf_writer = PdfWriter()

            with open(pdf_file, "wb") as f_final:
                for page_num, page in enumerate(existing_pdf.pages, start=1):
                    print(f"Adding existing page: {page_num}")
                    pdf_writer.add_page(page)
                for page_num, page in enumerate(new_pdf_content.pages, start=1):
                    print(f"Adding new page: {page_num}")
                    pdf_writer.add_page(page)
                for page_num, page in enumerate(solutions_pdf_content.pages, start=1):
                    print(f"Adding new solution: {page_num}")
                    pdf_writer.add_page(page)
                pdf_writer.write(f_final)

        print(f"Final PDF saved as {pdf_file}")

        f_existing.close()
        f_new.close()
        f_solutions.close()

        time.sleep(1)

        def force_delete(file_path):
            try:
                os.remove(file_path)
                print(f"Successfully deleted {file_path}")
            except PermissionError:
                print(f"PermissionError: Changing permissions for {file_path}")
                os.chmod(file_path, stat.S_IWUSR)
                os.remove(file_path)
                print(f"Successfully deleted {
                      file_path} after changing permissions")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        force_delete(temp_pdf)
        force_delete(new_pdf)
        force_delete(new_solutions_pdf)


def append_solutions_page(pdf_file, svg_directory, background_image=None):
    """
    Append solution pages to the existing PDF file with enhancements.
    """
    temp_pdf = "temp_solutions.pdf"
    if os.path.exists(pdf_file):
        with open(pdf_file, "rb") as f:
            existing_pdf = PdfReader(f)
            pdf_writer = PdfWriter()
            for page in existing_pdf.pages:
                pdf_writer.add_page(page)
            with open(temp_pdf, "wb") as f_temp:
                pdf_writer.write(f_temp)

    new_pdf = "solution_pages.pdf"
    c = canvas.Canvas(new_pdf, pagesize=A4)
    width, height = A4
    margin = 50
    usable_width = width - 2 * margin
    max_svg_height = 250  # Increased SVG size for better visibility

    def parse_solution_file(filename):
        match = re.match(r"^\d+\.\s*(\d+)(N|H|BN|BH)(\d+)(S?)\.svg$", filename)
        if match:
            topic, mode, puzzle_number, solution_flag = match.groups()
            return {
                "topic": int(topic),
                "mode": mode,
                "puzzle_number": int(puzzle_number),
                "is_solution": solution_flag == "S"
            }
        return None

    solution_files = [f for f in os.listdir(
        svg_directory) if f.endswith("S.svg")]
    grouped_solutions = {}

    for solution_file in solution_files:
        details = parse_solution_file(solution_file)
        if details:
            topic = details["topic"]
            mode = details["mode"]
            if topic not in grouped_solutions:
                grouped_solutions[topic] = {
                    "N": [], "H": [], "BN": [], "BH": []}
            grouped_solutions[topic][mode].append(solution_file)

    is_first_page = True

    for topic, modes in sorted(grouped_solutions.items()):
        if is_first_page:
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(width / 2, height / 2, "SOLUTIONS")
            is_first_page = False
            c.showPage()

        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 50, f"Topic: {topic}")

        y_offset = height - 100

        for mode_name, mode_files in [("Normal", "N"), ("Hard", "H"), ("Bonus I", "BN"), ("Bonus II", "BH")]:
            if mode_files not in modes or not modes[mode_files]:
                continue

            for i, solution_file in enumerate(sorted(modes[mode_files]), start=1):
                svg_filepath = os.path.join(svg_directory, solution_file)
                drawing = svg2rlg(svg_filepath)

                # Scale SVG to fit better
                drawing_width, drawing_height = drawing.width, drawing.height
                scale = min((usable_width / 2) / drawing_width,
                            max_svg_height / drawing_height)
                drawing.scale(scale, scale)

                # Position SVG side-by-side
                x_position = margin if i % 2 != 0 else margin + usable_width / 2
                renderPDF.draw(drawing, c, x_position,
                               y_offset - drawing_height * scale)

                # Add file name below SVG
                c.setFont("Helvetica", 10)
                file_name = os.path.basename(solution_file)
                c.drawCentredString(x_position + (usable_width / 4),
                                    y_offset - drawing_height * scale - 10, file_name)

                if i % 2 == 0:  # Move down after two per row
                    y_offset -= max_svg_height + 40

                # Page overflow
                if y_offset - max_svg_height < margin:
                    if background_image:
                        c.drawImage(background_image, 0, 0,
                                    width=width, height=height)
                    c.showPage()
                    y_offset = height - 100
                    c.setFont("Helvetica-Bold", 20)
                    c.drawCentredString(
                        width / 2, height - 50, f"Topic: {topic}")

            y_offset -= 40

    c.save()

    # Merge PDFs
    if os.path.exists(pdf_file):
        with open(temp_pdf, "rb") as f_existing, open(new_pdf, "rb") as f_new:
            existing_pdf = PdfReader(f_existing)
            new_pdf_content = PdfReader(f_new)
            pdf_writer = PdfWriter()
            with open(pdf_file, "wb") as f_final:
                for page in existing_pdf.pages:
                    pdf_writer.add_page(page)
                for page in new_pdf_content.pages:
                    pdf_writer.add_page(page)
                pdf_writer.write(f_final)
        os.remove(temp_pdf)
        os.remove(new_pdf)


def main():
    image_path = input("Enter the image path: ")
    append_page("Where's Word-o", image_path)


if __name__ == '__main__':
    # main()
    # append_solutions_page("Test.pdf", "generated_puzzles", "Assets/Background.png")
    append_puzzle_page(
        "Test.pdf", 
        "generated_puzzles", 
        "Assets/pageBackground.png"
    )
