"""
CampusConnect - Minor Project Report Generator (.docx)
 Vivekananda Institute of Professional Studies - Technical Campus (VIPS-TC)
 Guru Gobind Singh Indraprastha University (GGSIPU), Delhi
 Master of Computer Applications (MCA 1-B)
 Student: Isha Dagar (09617704426)
 Mentor: Dr. Cosmena
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

PRIMARY_HEX = "700124"
PRIMARY_RGB = RGBColor(112, 1, 36)
TEXT_DARK = RGBColor(30, 41, 59)
TEXT_MUTED = RGBColor(100, 116, 139)
BORDER_GRAY = "E2E8F0"
BG_LIGHT = "FBF0F3"
WHITE = RGBColor(255, 255, 255)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def add_styled_paragraph(doc, text="", style='Normal', space_before=0, space_after=6, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = doc.add_paragraph(text, style=style)
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    return p


def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = PRIMARY_RGB
    return p


def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = PRIMARY_RGB
    return p


def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = TEXT_DARK
    return p


def add_body_p(doc, text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
        r_pre.font.color.rgb = TEXT_DARK
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.color.rgb = TEXT_DARK
    return p


def add_bullet_point(doc, title, desc):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    r_t = p.add_run(title + ": ")
    r_t.font.name = 'Calibri'
    r_t.font.size = Pt(11)
    r_t.font.bold = True
    r_t.font.color.rgb = TEXT_DARK
    r_d = p.add_run(desc)
    r_d.font.name = 'Calibri'
    r_d.font.size = Pt(11)
    r_d.font.color.rgb = TEXT_DARK
    return p


def build_table(doc, headers, data, col_widths=None):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table, color="CCCCCC")

    # Header Row
    hdr_row = table.rows[0]
    tblHeader = OxmlElement('w:tblHeader')
    hdr_row._tr.get_or_add_trPr().append(tblHeader)

    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        set_cell_background(cell, PRIMARY_HEX)
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        run = p.add_run(h)
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = WHITE

    # Data Rows
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        bg_col = BG_LIGHT if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            if bg_col != "FFFFFF":
                set_cell_background(cell, bg_col)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            run = p.add_run(str(val))
            run.font.name = 'Calibri'
            run.font.size = Pt(9.5)
            run.font.color.rgb = TEXT_DARK

    if col_widths:
        for r in table.rows:
            for i, w in enumerate(col_widths):
                r.cells[i].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return table


def generate_minor_project_report(output_filename="CampusConnect_Minor_Project_Report.docx"):
    doc = Document()

    # Set 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.different_first_page_header_footer = True

        header = section.header
        p_hdr = header.paragraphs[0]
        p_hdr.text = "CampusConnect: An Academic Progress and Communication Portal | Minor Project Report"
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.runs[0].font.name = "Calibri"
        p_hdr.runs[0].font.size = Pt(8.5)
        p_hdr.runs[0].font.color.rgb = TEXT_MUTED

        footer = section.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.text = "VIPS-TC | Vivekananda School of Information Technology | GGSIPU"
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ftr.runs[0].font.name = "Calibri"
        p_ftr.runs[0].font.size = Pt(8.5)
        p_ftr.runs[0].font.color.rgb = TEXT_MUTED

    # =========================================================================
    # 1. TITLE PAGE / COVER PAGE
    # =========================================================================
    p = add_styled_paragraph(doc, "VIVEKANANDA INSTITUTE OF PROFESSIONAL STUDIES - TC", space_before=12, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.bold = True
    p.runs[0].font.size = Pt(14)
    p.runs[0].font.color.rgb = PRIMARY_RGB

    p = add_styled_paragraph(doc, "VIVEKANANDA SCHOOL OF INFORMATION TECHNOLOGY\n(Affiliated to Guru Gobind Singh Indraprastha University, Delhi)", space_before=0, space_after=28, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.size = Pt(11)
    p.runs[0].font.color.rgb = TEXT_MUTED

    p = add_styled_paragraph(doc, "CAMPUSCONNECT", space_before=18, space_after=6, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.bold = True
    p.runs[0].font.size = Pt(26)
    p.runs[0].font.color.rgb = PRIMARY_RGB

    p = add_styled_paragraph(doc, "An Academic Progress and Communication Portal", space_before=0, space_after=32, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.bold = True
    p.runs[0].font.size = Pt(14)
    p.runs[0].font.color.rgb = TEXT_DARK

    p = add_styled_paragraph(doc, "A MINOR PROJECT REPORT\nSubmitted in partial fulfillment of the requirements for the award of the degree of", space_before=12, space_after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.size = Pt(11)
    p.runs[0].font.color.rgb = TEXT_MUTED

    p = add_styled_paragraph(doc, "MASTER OF COMPUTER APPLICATIONS (MCA)", space_before=0, space_after=36, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.bold = True
    p.runs[0].font.size = Pt(13)
    p.runs[0].font.color.rgb = PRIMARY_RGB

    # Submission info table (no borders)
    sub_table = doc.add_table(rows=1, cols=2)
    sub_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sub_table.rows[0].cells[0].width = Inches(3.2)
    sub_table.rows[0].cells[1].width = Inches(3.2)

    c1 = sub_table.rows[0].cells[0].paragraphs[0]
    c1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r1 = c1.add_run("Submitted By:\n")
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = PRIMARY_RGB
    r2 = c1.add_run("Isha Dagar\nEnrollment No.: 09617704426\nClass: MCA 1 (B)")
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = TEXT_DARK

    c2 = sub_table.rows[0].cells[1].paragraphs[0]
    c2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r3 = c2.add_run("Under the Guidance of:\n")
    r3.font.bold = True
    r3.font.size = Pt(11)
    r3.font.color.rgb = PRIMARY_RGB
    r4 = c2.add_run("Dr. Cosmena\nFaculty Mentor, VSIT\nVIPS-TC, Delhi")
    r4.font.size = Pt(10.5)
    r4.font.color.rgb = TEXT_DARK

    doc.add_paragraph().paragraph_format.space_before = Pt(28)
    p = add_styled_paragraph(doc, "Academic Year: 2026-2027\nNew Delhi, India", space_before=16, space_after=0, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.runs[0].font.size = Pt(10.5)
    p.runs[0].font.color.rgb = TEXT_MUTED

    doc.add_page_break()

    # =========================================================================
    # 2. CERTIFICATE OF ORIGINALITY & APPROVAL
    # =========================================================================
    add_heading_1(doc, "CERTIFICATE OF APPROVAL")
    add_body_p(doc, "This is to certify that the Minor Project Report entitled “CAMPUSCONNECT: An Academic Progress and Communication Portal”, submitted by Isha Dagar (Enrollment No.: 09617704426), a student of Master of Computer Applications (MCA 1-B) at Vivekananda School of Information Technology, Vivekananda Institute of Professional Studies - TC (VIPS-TC), affiliated to Guru Gobind Singh Indraprastha University, Delhi, is a bonafide record of project work carried out under my supervision and guidance.")
    add_body_p(doc, "The project report reflects sound technical implementation, adherence to modern software engineering principles, and a complete functional web-based solution for centralized academic task management, progress tracking, and secure Telegram messaging automation.")
    add_body_p(doc, "To the best of my knowledge, the matter embodied in this report has not been submitted to any other university or institute for the award of any degree or diploma.")

    doc.add_paragraph().paragraph_format.space_before = Pt(36)
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.rows[0].cells[0].width = Inches(3.2)
    sig_table.rows[0].cells[1].width = Inches(3.2)

    sc1 = sig_table.rows[0].cells[0].paragraphs[0]
    sc1.add_run("________________________\nDr. Cosmena\nProject Guide / Mentor\nVSIT, VIPS-TC, Delhi").font.size = Pt(10.5)

    sc2 = sig_table.rows[0].cells[1].paragraphs[0]
    sc2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    sc2.add_run("________________________\nHead of Department\nMCA Programme\nVSIT, VIPS-TC, Delhi").font.size = Pt(10.5)

    doc.add_page_break()

    # =========================================================================
    # 3. STUDENT DECLARATION
    # =========================================================================
    add_heading_1(doc, "CANDIDATE'S DECLARATION")
    add_body_p(doc, "I, Isha Dagar, a student of Master of Computer Applications, MCA 1 (B), Enrollment No.: 09617704426, hereby declare that the minor project report entitled “CAMPUSCONNECT: An Academic Progress and Communication Portal”, submitted to Vivekananda Institute of Professional Studies-TC (VIPS-TC), affiliated to Guru Gobind Singh Indraprastha University, Delhi, is an authentic record of my original work carried out under the supervision and guidance of Dr. Cosmena.")
    add_body_p(doc, "I have adhered to all academic integrity norms. Any literature, data, technology documentation, or reference material utilized in the course of designing and developing this portal has been duly acknowledged.")
    add_body_p(doc, "I further declare that this report has not previously formed the basis for the award of any degree, diploma, associateship, fellowship, or similar title in this or any other university or educational institution.")

    doc.add_paragraph().paragraph_format.space_before = Pt(36)
    dp = add_styled_paragraph(doc, "Isha Dagar\nEnrollment No.: 09617704426\nClass: MCA 1 (B)\nVivekananda School of Information Technology\nVivekananda Institute of Professional Studies - TC\nPlace: New Delhi", space_before=12, space_after=0)
    dp.runs[0].font.size = Pt(10.5)

    doc.add_page_break()

    # =========================================================================
    # 4. ACKNOWLEDGEMENT
    # =========================================================================
    add_heading_1(doc, "ACKNOWLEDGEMENT")
    add_body_p(doc, "I express my profound gratitude and sincere appreciation to my project mentor, Dr. Cosmena, for her invaluable guidance, patient encouragement, constructive critiques, and technical insights throughout the design, implementation, and evaluation of CampusConnect.")
    add_body_p(doc, "I extend my sincere thanks to the Vivekananda School of Information Technology (VSIT) and the leadership of Vivekananda Institute of Professional Studies - TC (VIPS-TC) for providing the academic infrastructure, laboratories, and supportive environment required to conduct this minor project.")
    add_body_p(doc, "I am also indebted to the faculty members and fellow student peers of MCA Section B, whose real-world feedback on academic deadline bottlenecks, scattered WhatsApp groups, and lost assignment circulars shaped the foundational requirements and user-centric architecture of this portal.")
    add_body_p(doc, "Finally, I wish to express my deepest appreciation to my family and friends for their unwavering encouragement, patience, and support throughout the duration of this work.")

    doc.add_paragraph().paragraph_format.space_before = Pt(24)
    add_styled_paragraph(doc, "Isha Dagar\nMCA 1 (B), VIPS-TC", space_before=8, space_after=0)

    doc.add_page_break()

    # =========================================================================
    # 5. ABSTRACT & INDEX TERMS
    # =========================================================================
    add_heading_1(doc, "ABSTRACT")
    add_body_p(doc, "Colleges and universities operate within an intensive semester schedule characterized by continuous coursework, practical laboratory sessions, major and minor projects, viva examinations, and administrative circulars. In traditional institutional workflows, academic communication is severely fragmented across disparate channels, including informal WhatsApp messaging groups, multi-recipient email threads, disparate learning platforms, and physical notice boards. This fragmentation introduces major academic bottlenecks: students frequently overlook critical submission deadlines or lose track of updated assignment specifications, while faculty members endure laborious manual tracking across multiple spreadsheets to identify pending, submitted, overdue, and reviewed student submissions.")
    add_body_p(doc, "This project presents CAMPUSCONNECT, a comprehensive, unified, role-based academic progress and communication web portal engineered specifically for higher education institutions. Developed using Python, Flask, SQLAlchemy, MySQL, and modern semantic HTML5/CSS3/JavaScript, CampusConnect establishes a single, consolidated academic workspace organized under strict role-based access control (Administrator, Faculty, Student).")
    add_body_p(doc, "Key architectural highlights include: (1) structured academic task management supporting assignments, projects, and practical files with granular course/section mapping, strict 12 MB file-validation, and deadline enforcement; (2) real-time course-wise academic progress tracking matrices computing live submission completion rates, overdue status, and faculty review indices; (3) a targeted departmental notice board supporting both batch-wide announcements and direct student-specific private notices; and (4) an automated Telegram Bot API notification engine featuring a dual-mode integration (production webhook delivery with secret-token authentication and local development long-polling synchronization) alongside 10-minute expiring single-use linking tokens.")
    add_body_p(doc, "The platform was evaluated through exhaustive automated unit, integration, and benchmark test suites spanning 15 Functional Requirements (FR1-FR15), 6 Performance Benchmarks (BM1-BM6), 8 Security Controls (SEC1-SEC8), and 10 Standard Test Cases (TC1-TC10), achieving a 100% test pass rate, sub-50ms dashboard query response times, zero Unicode emoji pollution in the academic UI, and complete data isolation between courses.")

    add_body_p(doc, "Academic Management Systems, Student Progress Tracking, Assignment Lifecycle, Relational Database Design, Telegram Bot API, Role-Based Access Control, Flask Web Framework, Academic Notice Board.", bold_prefix="Index Terms — ")

    doc.add_page_break()

    # =========================================================================
    # 6. TABLE OF CONTENTS
    # =========================================================================
    add_heading_1(doc, "TABLE OF CONTENTS")

    toc_items = [
        ("Certificate of Approval", "ii"),
        ("Candidate's Declaration", "iii"),
        ("Acknowledgement", "iv"),
        ("Abstract", "v"),
        ("List of Figures and Tables", "vii"),
        ("Chapter 1: Introduction and Project Overview", "1"),
        ("    1.1 Background and Institutional Context", "1"),
        ("    1.2 Problem Statement", "2"),
        ("    1.3 Proposed System and Core Ideology", "3"),
        ("    1.4 Project Objectives", "4"),
        ("    1.5 Project Scope and Boundary Conditions", "5"),
        ("Chapter 2: Literature Review and Feasibility Study", "7"),
        ("    2.1 Survey of Existing Communication Approaches", "7"),
        ("    2.2 Comparative Study of Related Platforms", "8"),
        ("    2.3 Technical, Operational and Economic Feasibility", "9"),
        ("Chapter 3: System Requirements Specification (SRS)", "11"),
        ("    3.1 Functional Requirements (FR1 - FR15)", "11"),
        ("    3.2 Non-Functional Requirements (NFR1 - NFR7)", "14"),
        ("    3.3 Security, Privacy and Access Control (SEC1 - SEC8)", "15"),
        ("    3.4 Hardware and Software Operating Environment", "17"),
        ("Chapter 4: System Architecture and Relational Design", "18"),
        ("    4.1 Three-Tier Architectural Framework", "18"),
        ("    4.2 Data Flow Modeling (DFD Levels 0, 1, 2)", "19"),
        ("    4.3 Entity-Relationship (ER) Architecture", "21"),
        ("    4.4 Comprehensive Relational Data Dictionary", "22"),
        ("    4.5 Task and Submission State Transition Lifecycle", "25"),
        ("    4.6 Dual-Mode Telegram Messaging Architecture", "26"),
        ("Chapter 5: Modular Implementation and Execution Details", "28"),
        ("    5.1 Module 1: Authentication and Session Security", "28"),
        ("    5.2 Module 2: Course Mapping and Academic Task CRUD", "29"),
        ("    5.3 Module 3: Submission Processing and Faculty Review", "30"),
        ("    5.4 Module 4: Departmental Notices and 1-on-1 Student Messaging", "32"),
        ("    5.5 Module 5: Real-Time Academic Progress Indicators", "33"),
        ("    5.6 Module 6: Telegram Bot Engine and Long-Polling Sync", "34"),
        ("    5.7 Module 7: Administrative Governance and Provisioning", "35"),
        ("Chapter 6: System Verification, Testing and Benchmark Results", "36"),
        ("    6.1 Verification Methodology and Test Levels (TL1 - TL6)", "36"),
        ("    6.2 Test Case Specifications and Execution Matrix (TC1 - TC10)", "37"),
        ("    6.3 Benchmark Verification Results (BM1 - BM6)", "39"),
        ("    6.4 Negative Constraints and Professional UI Compliance", "40"),
        ("Chapter 7: Deployment, Publishing and Operations Guide", "41"),
        ("    7.1 Local Development and Virtual Environment Setup", "41"),
        ("    7.2 Production Cloud Deployment (Gunicorn, Render, MySQL)", "42"),
        ("    7.3 Telegram Bot Setup, Webhook Registration and Operations", "44"),
        ("Chapter 8: Conclusion and Future Roadmap", "45"),
        ("    8.1 Summary of Completed Achievements", "45"),
        ("    8.2 Practical Limitations", "46"),
        ("    8.3 Planned Future Enhancements", "46"),
        ("References and Technical Bibliography", "48"),
    ]

    for title, page in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        r_t = p.add_run(title)
        r_t.font.name = 'Calibri'
        r_t.font.size = Pt(10)
        r_t.font.color.rgb = TEXT_DARK
        if not title.startswith("    "):
            r_t.font.bold = True
        # Dot leader simulation
        dots_count = max(2, 65 - len(title))
        r_d = p.add_run(" " + "." * dots_count + " ")
        r_d.font.color.rgb = TEXT_MUTED
        r_p = p.add_run(page)
        r_p.font.name = 'Calibri'
        r_p.font.size = Pt(10)
        r_p.font.bold = True
        r_p.font.color.rgb = PRIMARY_RGB

    doc.add_page_break()

    # =========================================================================
    # 7. LIST OF TABLES & FIGURES
    # =========================================================================
    add_heading_1(doc, "LIST OF TABLES AND FIGURES")

    add_heading_2(doc, "List of Tables")
    tables_list = [
        ("Table 1.1", "Guiding Principles of CampusConnect", "4"),
        ("Table 2.1", "Comparison of Existing Communication Channels vs. CampusConnect", "8"),
        ("Table 3.1", "Functional Requirements Specification (FR1 to FR15)", "12"),
        ("Table 3.2", "Non-Functional Requirements Specification (NFR1 to NFR7)", "14"),
        ("Table 3.3", "Security and Privacy Controls (SEC1 to SEC8)", "16"),
        ("Table 3.4", "Minimum Hardware and Software Configuration", "17"),
        ("Table 4.1", "Data Dictionary: USERS Table", "22"),
        ("Table 4.2", "Data Dictionary: COURSES Table", "23"),
        ("Table 4.3", "Data Dictionary: ENROLMENTS Table", "23"),
        ("Table 4.4", "Data Dictionary: TASKS Table", "23"),
        ("Table 4.5", "Data Dictionary: SUBMISSIONS Table", "24"),
        ("Table 4.6", "Data Dictionary: NOTICES Table", "24"),
        ("Table 4.7", "Data Dictionary: TELEGRAM_LINKS Table", "25"),
        ("Table 4.8", "Data Dictionary: TELEGRAM_CODES Table", "25"),
        ("Table 4.9", "Task and Submission State Transition Matrix", "26"),
        ("Table 6.1", "Sample Test Cases Execution and Verification Matrix (TC1 to TC10)", "37"),
        ("Table 6.2", "Benchmark Evaluation and Performance Results (BM1 to BM6)", "39"),
    ]
    for num, desc, pnum in tables_list:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r1 = p.add_run(f"{num}: {desc}")
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_DARK
        dots = max(2, 62 - len(desc))
        r2 = p.add_run(" " + "." * dots + " ")
        r2.font.color.rgb = TEXT_MUTED
        r3 = p.add_run(pnum)
        r3.font.size = Pt(10)
        r3.font.bold = True
        r3.font.color.rgb = PRIMARY_RGB

    add_heading_2(doc, "List of Figures")
    figures_list = [
        ("Figure 4.1", "Three-Tier Conceptual Architecture of CampusConnect", "18"),
        ("Figure 4.2", "Level 0 Context Data Flow Diagram", "19"),
        ("Figure 4.3", "Level 1 System Data Flow Diagram", "20"),
        ("Figure 4.4", "Level 2 Task and Submission Data Flow Diagram", "21"),
        ("Figure 4.5", "Entity-Relationship (ER) Relational Schema Diagram", "22"),
        ("Figure 4.6", "Dual-Mode Telegram Bot Integration Architecture (Webhook & Polling)", "27"),
    ]
    for num, desc, pnum in figures_list:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r1 = p.add_run(f"{num}: {desc}")
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_DARK
        dots = max(2, 62 - len(desc))
        r2 = p.add_run(" " + "." * dots + " ")
        r2.font.color.rgb = TEXT_MUTED
        r3 = p.add_run(pnum)
        r3.font.size = Pt(10)
        r3.font.bold = True
        r3.font.color.rgb = PRIMARY_RGB

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 1: INTRODUCTION AND PROJECT OVERVIEW
    # =========================================================================
    add_heading_1(doc, "CHAPTER 1: INTRODUCTION AND PROJECT OVERVIEW")

    add_heading_2(doc, "1.1 Background and Institutional Context")
    add_body_p(doc, "Higher educational institutions such as Vivekananda Institute of Professional Studies - Technical Campus (VIPS-TC) manage a continuous flow of rigorous academic coursework throughout every semester. In professional postgraduate programmes such as Master of Computer Applications (MCA), students must simultaneously manage theoretical assignments, software engineering mini-projects, practical laboratory files, presentations, and examination schedules across multiple specialized subjects (e.g., Advanced Java Programming, Web Technologies, Software Engineering).")
    add_body_p(doc, "Conventionally, these academic interactions are conducted through ad-hoc, uncoordinated communication channels. Faculty members announce task requirements during lectures or distribute PDF circulars through messaging platforms such as WhatsApp or multi-recipient email threads. As the academic semester accelerates, these informal mechanisms break down under the sheer volume of daily messages, leading to critical informational loss, overlooked deadlines, and heightened academic stress for students.")

    add_heading_2(doc, "1.2 Problem Statement")
    add_body_p(doc, "The absence of a centralized, dedicated academic portal results in multiple acute institutional deficiencies:")
    add_bullet_point(doc, "Information Scatter and Deadlines Loss", "Assignment briefs, practical problem sets, and submission deadlines get buried under casual conversations in informal WhatsApp groups, resulting in missed deadlines and frequent student disorientation.")
    add_bullet_point(doc, "Laborious Faculty Progress Monitoring", "Faculty members are forced to maintain individual spreadsheets or manual registers to verify which students have submitted their practical records or project reports. Identifying overdue or defaulting students requires hours of manual cross-referencing.")
    add_bullet_point(doc, "Absence of Structured Feedback Channels", "When submissions are received via disparate emails or file folders, returning timely qualitative feedback or requesting resubmissions becomes disorganized, depriving students of clear learning correction.")
    add_bullet_point(doc, "Ineffective Notice Circulation", "Departmental circulars, laboratory reschedule notices, and individual academic directives are often broadcast indiscriminately, creating alert fatigue or failing to reach the exact target students.")

    add_heading_2(doc, "1.3 Proposed System and Core Ideology")
    add_body_p(doc, "CAMPUSCONNECT resolves these systemic problems by delivering a unified, web-based academic progress and communication workspace designed specifically for faculty and students. The portal organizes every academic interaction under strict role-based access control, ensuring faculty manage only their assigned courses while students interact exclusively with the courses they are enrolled in.")
    add_body_p(doc, "The ideology of CampusConnect is anchored upon seven core guiding principles:")

    principles_data = [
        ("P1", "One Academic Workspace", "Assignments, projects, practicals, deadlines and notices are organized within one centralized portal."),
        ("P2", "Role-Based Access Control", "Faculty manage assigned courses; students view and submit work linked strictly to enrolled courses."),
        ("P3", "Clear Progress Status", "Faculty can instantly identify pending, submitted, reviewed and overdue work through course-wise matrices."),
        ("P4", "Student Visibility", "Students monitor upcoming deadlines, submission status, grades, and written feedback in their dashboard."),
        ("P5", "Timely Automated Communication", "Telegram notifications deliver opt-in alerts for new coursework, deadline reminders, and notices."),
        ("P6", "Practical Implementation", "Engineered using stable, industry-standard web technologies: Python, Flask, SQLAlchemy, and MySQL."),
        ("P7", "Privacy and Accountability", "Access is guarded by hashed credentials, session authentication, and server-side authorization boundaries."),
    ]
    build_table(doc, ["#", "Principle", "Operational Description"], principles_data, [0.6, 2.0, 3.8])

    add_heading_2(doc, "1.4 Project Objectives")
    add_body_p(doc, "The project was developed to accomplish the following specific academic and technical objectives:")
    add_body_p(doc, "1. To design and deploy a role-specific dashboard ecosystem providing Administrators, Faculty, and Students with tailored operational interfaces.", bold_prefix="Primary Objective A: ")
    add_body_p(doc, "2. To provide faculty with complete CRUD lifecycle control over coursework (assignments, projects, practicals) with precise deadline management and course mapping.", bold_prefix="Primary Objective B: ")
    add_body_p(doc, "3. To implement a secure file upload mechanism validating file extensions and enforcing a 12 MB size ceiling to prevent server-side denial-of-service.", bold_prefix="Primary Objective C: ")
    add_body_p(doc, "4. To calculate real-time academic progress indicators (total assigned, submitted, reviewed, pending, overdue, and percentage submission rates).", bold_prefix="Primary Objective D: ")
    add_body_p(doc, "5. To implement dual-mode Telegram Bot API integration delivering instant notifications for coursework publication, review feedback, and notices.", bold_prefix="Primary Objective E: ")
    add_body_p(doc, "6. To enable targeted communication supporting both course-wide announcements and direct, private 1-on-1 messages between faculty and individual students.", bold_prefix="Secondary Objective F: ")

    add_heading_2(doc, "1.5 Project Scope and Boundary Conditions")
    add_body_p(doc, "The operational boundaries of CampusConnect are explicitly delineated below:")
    add_bullet_point(doc, "In-Scope Capabilities", "User account authentication, role-based dashboards, course mapping, task authoring, submission uploads, faculty review with status toggling, departmental notices, direct student messaging, progress tracking matrices, single-use Telegram linking, and administrative management.")
    add_bullet_point(doc, "Out-of-Scope Elements", "CampusConnect does not attempt to replace the official University ERP/LMS (e.g., GGSIPU Examination Portal), does not perform automated grading of source code or essays, does not provide native mobile apps, and strictly forbids sending unsolicited messages to unlinked Telegram accounts.")
    add_bullet_point(doc, "Planned Enhancements", "Automated scheduled deadline reminders (E1), exportable tabular progress reports (E2), calendar-style visual timeline views (E3), and advanced graphical completion analytics (E4).")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 2: LITERATURE REVIEW AND FEASIBILITY STUDY
    # =========================================================================
    add_heading_1(doc, "CHAPTER 2: LITERATURE REVIEW AND FEASIBILITY STUDY")

    add_heading_2(doc, "2.1 Survey of Existing Communication Approaches")
    add_body_p(doc, "An analysis of contemporary academic workflows reveals that academic communication in higher education institutions typically oscillates between two extremes: heavyweight, complex Enterprise Resource Planning (ERP) / Learning Management Systems (LMS) and unorganized social messaging applications.")
    add_body_p(doc, "Commercial LMS platforms such as Moodle and Blackboard provide comprehensive pedagogical tooling but suffer from steep learning curves, cluttered navigation, heavy server resource requirements, and high maintenance overhead. Consequently, for routine semester tasks like tracking practical file submissions or sharing urgent laboratory notices, faculty frequently abandon the formal LMS in favor of instant messaging platforms like WhatsApp or Telegram groups.")
    add_body_p(doc, "However, informal instant messaging groups introduce significant pedagogical liabilities: critical academic circulars are interspersed with casual banter, student submissions sent via chat clutter phone storage without systematic logging, privacy is compromised as personal mobile numbers are exposed to entire batches, and faculty have no automated mechanism to compute completion rates or isolate overdue work.")

    add_heading_2(doc, "2.2 Comparative Study of Related Platforms")
    add_body_p(doc, "Table 2.1 presents a structured comparative analysis contrasting CampusConnect with existing institutional approaches across seven vital academic parameters.")

    comp_data = [
        ("Platform", "Targeted Notices", "Task Status Tracking", "Direct Student Msg", "File Submissions", "Telegram Alerts", "Setup Simplicity"),
        ("WhatsApp Groups", "Broadcast only (noisy)", "None (Manual)", "Unorganized chat", "Clutters phone storage", "None (Manual)", "High"),
        ("Google Classroom", "Course stream only", "Basic submission view", "Private comments only", "Google Drive quota", "None", "Moderate"),
        ("Moodle / Canvas", "Forums & Announcements", "Complex gradebook", "Internal messaging", "Server storage", "Requires plugins", "Low (Complex)"),
        ("CampusConnect", "Targeted + Direct 1-on-1", "Real-Time KPI Matrix", "Private Direct Notice", "Secure 12MB Local/Cloud", "Native Bot API", "High (Streamlined)"),
    ]
    build_table(doc, comp_data[0], comp_data[1:], [1.2, 1.1, 1.1, 1.0, 1.0, 0.9, 0.9])

    add_heading_2(doc, "2.3 Technical, Operational and Economic Feasibility")
    add_bullet_point(doc, "Technical Feasibility", "The system leverages Python 3, Flask, SQLAlchemy ORM, and MySQL. Flask is lightweight, highly modular, and well-suited for microservice and monolithic web applications. Python-dotenv and Werkzeug provide robust security primitives. The Telegram Bot API requires only standard HTTPS REST interactions. Thus, technical feasibility is fully established.")
    add_bullet_point(doc, "Operational Feasibility", "CampusConnect features an intuitive, minimalist user interface built using modern typography (DM Sans and Manrope) with a dignified institutional maroon palette (#700124) and zero emojis. The navigation mimics standard web patterns, requiring zero prior training for faculty or students.")
    add_bullet_point(doc, "Economic Feasibility", "The entire software stack comprises open-source technologies (Python, Flask, SQLite/MySQL, Gunicorn). Cloud hosting can be provisioned on free or low-cost tiers (Render, Railway, PythonAnywhere) without software licensing expenditures.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 3: SYSTEM REQUIREMENTS SPECIFICATION (SRS)
    # =========================================================================
    add_heading_1(doc, "CHAPTER 3: SYSTEM REQUIREMENTS SPECIFICATION (SRS)")

    add_heading_2(doc, "3.1 Functional Requirements (FR1 - FR15)")
    add_body_p(doc, "Table 3.1 details the complete catalog of Functional Requirements extracted from Section VII-A of the approved academic synopsis and implemented in CampusConnect.")

    fr_data = [
        ("FR1", "User Authentication", "The system shall authenticate faculty, student, and administrator users using email and hashed passwords."),
        ("FR2", "Role-Specific Dashboards", "The system shall render tailored dashboards based on the user's role (Admin, Faculty, Student)."),
        ("FR3", "Task Lifecycle Management", "The system shall permit faculty to create, edit, publish, and delete assignments, projects, and practical tasks."),
        ("FR4", "Course & Section Targeting", "The system shall allow faculty to assign coursework to specific courses, semesters, and sections."),
        ("FR5", "Deadline & Instructions", "The system shall allow faculty to set task descriptions, issue dates, and hard submission deadlines."),
        ("FR6", "Enrolment-Based Visibility", "The system shall ensure students view academic tasks relevant exclusively to their enrolled courses."),
        ("FR7", "Submission File Uploads", "The system shall permit students to upload submission files up to 12 MB in permitted formats."),
        ("FR8", "Submission Timestamping", "The system shall record exact submission timestamps and assign an initial status of 'Submitted'."),
        ("FR9", "Faculty Review & Feedback", "The system shall allow faculty to review student submissions, provide written feedback, and update status."),
        ("FR10", "Departmental Notices", "The system shall allow authorized users to publish notices targeted to all students, specific courses, or individual students."),
        ("FR11", "Progress Status Matrices", "The system shall display pending, submitted, reviewed, and overdue work counts in real-time dashboards."),
        ("FR12", "Telegram Account Linking", "The system shall allow users to securely link a Telegram account via a 10-minute single-use token."),
        ("FR13", "Automated Telegram Alerts", "The system shall dispatch instant Telegram alerts for new tasks, reviewed work, notices, and reminders."),
        ("FR14", "Data Isolation & RBAC", "The system shall enforce server-side access control preventing unauthorized cross-course data access."),
        ("FR15", "Responsive Web Design", "The system shall render a fully responsive UI accessible seamlessly on desktop, tablet, and mobile browsers."),
    ]
    build_table(doc, ["Req ID", "Requirement Name", "Technical Specification"], fr_data, [0.8, 1.8, 4.0])

    add_heading_2(doc, "3.2 Non-Functional Requirements (NFR1 - NFR7)")
    add_body_p(doc, "The non-functional characteristics governing system quality are summarized in Table 3.2.")

    nfr_data = [
        ("NFR1", "Security", "Passwords stored as PBKDF2:SHA-256 hashes; protected endpoints require session auth and role validation."),
        ("NFR2", "Privacy", "Students access only their own submissions; private messages visible only to the specified recipient student."),
        ("NFR3", "Usability", "Zero emoji pollution in UI; clean typography; clear status badges; 5-second auto-dismiss flash alerts."),
        ("NFR4", "Performance", "Dashboard and query response times strictly under 500 ms for normal institutional concurrency."),
        ("NFR5", "Reliability", "Relational foreign-key cascading; atomic database commits; atomic file saving with sanitized unique names."),
        ("NFR6", "Maintainability", "Modular architecture with clear separation of models, authorization decorators, routes, and views."),
        ("NFR7", "Compatibility", "Compliant with modern web standards across Chrome, Firefox, Safari, Edge, and mobile WebKit browsers."),
    ]
    build_table(doc, ["NFR ID", "Category", "Quality Benchmark"], nfr_data, [0.8, 1.4, 4.4])

    add_heading_2(doc, "3.3 Security, Privacy and Access Control (SEC1 - SEC8)")
    add_body_p(doc, "Security in CampusConnect is implemented strictly on the server side in compliance with Section VIII-E of the project synopsis:")

    sec_data = [
        ("SEC1", "Password Hashing", "generate_password_hash() with scrypt/pbkdf2:sha256; plain text passwords never stored or logged."),
        ("SEC2", "Server-Side RBAC", "@roles('faculty', 'admin') custom decorators enforce role permissions before executing view handlers."),
        ("SEC3", "Student Enrolment Check", "Submissions and task views verify student enrolment record in database; returns 403 Forbidden on violation."),
        ("SEC4", "Faculty Ownership Check", "Faculty can view/edit only tasks and submissions belonging to courses where faculty_id matches current_user."),
        ("SEC5", "File Upload Validation", "Extension whitelist (.pdf, .docx, .zip, etc.); secure_filename() sanitization; 12 MB size ceiling."),
        ("SEC6", "Environment Isolation", "Database credentials, secret keys, and Telegram tokens stored in .env and loaded via python-dotenv."),
        ("SEC7", "Expiring Linking Tokens", "Telegram linking codes generated using secrets.token_urlsafe(12) with 10-minute expiry and single-use flag."),
        ("SEC8", "Notification Privacy", "Telegram messages contain only course titles and deadlines; sensitive grades or personal IDs are excluded."),
    ]
    build_table(doc, ["Sec ID", "Security Principle", "Implementation Technique"], sec_data, [0.8, 1.8, 4.0])

    add_heading_2(doc, "3.4 Hardware and Software Operating Environment")
    add_bullet_point(doc, "Server Specifications", "Intel Core i5 or AMD Ryzen processor, 8 GB RAM, 20 GB available storage, Linux / Windows OS.")
    add_bullet_point(doc, "Runtime Environment", "Python 3.12, Flask 3.1.1, Flask-SQLAlchemy 3.1.1, Flask-Login 0.6.3, Gunicorn 23.0.0.")
    add_bullet_point(doc, "Database Server", "MySQL 8.0+ or SQLite 3 (for lightweight development / automated testing).")
    add_bullet_point(doc, "External APIs", "Telegram Bot API (HTTPS REST endpoints via requests 2.32.4).")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 4: SYSTEM ARCHITECTURE AND RELATIONAL DESIGN
    # =========================================================================
    add_heading_1(doc, "CHAPTER 4: SYSTEM ARCHITECTURE AND RELATIONAL DESIGN")

    add_heading_2(doc, "4.1 Three-Tier Architectural Framework")
    add_body_p(doc, "CampusConnect follows a classic Three-Tier Model-View-Controller (MVC) architectural pattern:")
    add_bullet_point(doc, "Presentation Tier (Views)", "Jinja2 templates rendered on the server, styled with an academic CSS design system (DM Sans, Manrope, #700124 primary maroon, zero emojis) and responsive client-side JavaScript for file validation and flash message transitions.")
    add_bullet_point(doc, "Application Tier (Controller)", "Flask application layer incorporating routing, authentication handlers (Flask-Login), custom RBAC decorators (@roles), task progress aggregators, and the Telegram dispatching subsystem.")
    add_bullet_point(doc, "Data Persistence Tier (Models)", "Relational database schema managed through SQLAlchemy ORM, supporting both SQLite for self-contained testing and MySQL for production deployments.")

    add_heading_2(doc, "4.2 Data Flow Modeling (DFD Levels 0, 1, 2)")
    add_body_p(doc, "The functional data flow across CampusConnect is modeled across three structural abstraction levels:")
    add_body_p(doc, "At the highest level of abstraction, the Level 0 Context Diagram depicts the primary external entities (Student, Faculty, Administrator, Telegram API) interacting with the central CampusConnect system boundary. Students supply registration details, credentials, and coursework files, receiving personalized dashboards, task details, and notices. Faculty supply course definitions, task specifications, reviews, and circulars, receiving submission files and aggregate progress matrices. The Telegram API receives notification payloads and transmits bot command updates.", bold_prefix="Level 0 Context Diagram: ")
    add_body_p(doc, "The Level 1 System DFD decomposes the system into six core processes: Process 1.0 (Authentication & Session Management), Process 2.0 (Course & Enrolment Mapping), Process 3.0 (Task Authoring & Lifecycle), Process 4.0 (Submission Upload & Review), Process 5.0 (Notice Publication & Targeted Delivery), and Process 6.0 (Telegram Notification & Verification). Data stores include D1 (Users), D2 (Courses), D3 (Enrolments), D4 (Tasks), D5 (Submissions), D6 (Notices), and D7 (Telegram Links).", bold_prefix="Level 1 DFD: ")
    add_body_p(doc, "Level 2 diagrams further detail the critical Task & Submission Subsystem, detailing how uploaded files are validated for size and MIME extension, stored on disk with randomized unique prefixes, and recorded in D5 with foreign key associations.", bold_prefix="Level 2 Detailed DFD: ")

    add_heading_2(doc, "4.3 Entity-Relationship (ER) Architecture")
    add_body_p(doc, "The entity relationship architecture establishes strong relational integrity with foreign keys and cascading delete rules across eight core entities: USERS, COURSES, ENROLMENTS, TASKS, SUBMISSIONS, NOTICES, TELEGRAM_LINKS, and TELEGRAM_CODES. Key cardinality relationships include:")
    add_bullet_point(doc, "User to Courses (1:N)", "A faculty User can instruct multiple Courses; each Course is assigned to at most one faculty member.")
    add_bullet_point(doc, "User to Enrolments (1:N) & Course to Enrolments (1:N)", "Students and Courses are linked via the ENROLMENTS junction entity, with a unique constraint on (student_id, course_id).")
    add_bullet_point(doc, "Course to Tasks (1:N)", "A Course contains multiple academic Tasks; deleting a Course cascades to delete all associated Tasks.")
    add_bullet_point(doc, "Task to Submissions (1:N) & Student to Submissions (1:N)", "Each student can submit at most one active record per task, enforced by a unique constraint on (task_id, student_id).")
    add_bullet_point(doc, "User to Telegram Link (1:1)", "Each User can link at most one active Telegram chat ID.")

    add_heading_2(doc, "4.4 Comprehensive Relational Data Dictionary")
    add_body_p(doc, "The physical schema specifications implemented in MySQL/SQLite are detailed in Tables 4.1 through 4.8.")

    # Table 4.1 USERS
    add_heading_3(doc, "Table 4.1: USERS Table Schema")
    users_dict = [
        ("user_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique identifier for user"),
        ("full_name", "VARCHAR(150)", "NOT NULL", "Full legal academic name of user"),
        ("email", "VARCHAR(180)", "UNIQUE, NOT NULL", "Institutional login email address"),
        ("password_hash", "VARCHAR(255)", "NOT NULL", "PBKDF2 / Scrypt hashed password"),
        ("role", "VARCHAR(20)", "NOT NULL, DEFAULT 'student'", "User role: 'admin', 'faculty', 'student'"),
        ("department", "VARCHAR(120)", "NOT NULL, DEFAULT ''", "Academic department (e.g., Computer Applications)"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], users_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.2 COURSES
    add_heading_3(doc, "Table 4.2: COURSES Table Schema")
    courses_dict = [
        ("course_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique course identifier"),
        ("course_name", "VARCHAR(150)", "NOT NULL", "Title of course (e.g. Advanced Java Programming)"),
        ("course_code", "VARCHAR(50)", "NOT NULL", "Official course code (e.g. MCA-101)"),
        ("semester", "VARCHAR(20)", "NOT NULL, DEFAULT ''", "Semester designation (e.g. '1', '2')"),
        ("section", "VARCHAR(20)", "NOT NULL, DEFAULT ''", "Section designation (e.g. 'B')"),
        ("academic_year", "VARCHAR(20)", "NOT NULL, DEFAULT ''", "Academic calendar year (e.g. 2026-2027)"),
        ("faculty_id", "INT", "FK -> users.user_id, ON DELETE SET NULL", "Assigned instructor user ID"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], courses_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.3 ENROLMENTS
    add_heading_3(doc, "Table 4.3: ENROLMENTS Table Schema")
    enrol_dict = [
        ("enrolment_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique enrolment record ID"),
        ("student_id", "INT", "FK -> users.user_id, ON DELETE CASCADE", "Enrolled student ID"),
        ("course_id", "INT", "FK -> courses.course_id, ON DELETE CASCADE", "Target course ID"),
        ("joined_at", "DATETIME", "NOT NULL, DEFAULT UTC_TIMESTAMP", "Date and time of course enrolment"),
        ("uq_student_course", "UNIQUE", "UNIQUE(student_id, course_id)", "Prevents duplicate student enrolment in course"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], enrol_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.4 TASKS
    add_heading_3(doc, "Table 4.4: TASKS Table Schema")
    tasks_dict = [
        ("task_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique academic task ID"),
        ("course_id", "INT", "FK -> courses.course_id, ON DELETE CASCADE", "Associated course ID"),
        ("faculty_id", "INT", "FK -> users.user_id, ON DELETE CASCADE", "Author faculty ID"),
        ("title", "VARCHAR(200)", "NOT NULL", "Title of assignment or practical"),
        ("task_type", "VARCHAR(30)", "NOT NULL, DEFAULT 'Assignment'", "Type: 'Assignment', 'Project', 'Practical'"),
        ("description", "TEXT", "NOT NULL", "Detailed instructions and requirements"),
        ("issue_date", "DATETIME", "NOT NULL, DEFAULT UTC_TIMESTAMP", "Task publication timestamp"),
        ("deadline", "DATETIME", "NOT NULL", "Submission cutoff deadline"),
        ("status", "VARCHAR(20)", "NOT NULL, DEFAULT 'Published'", "Status: 'Draft', 'Published', 'Closed', 'Archived'"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], tasks_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.5 SUBMISSIONS
    add_heading_3(doc, "Table 4.5: SUBMISSIONS Table Schema")
    subs_dict = [
        ("submission_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique submission record ID"),
        ("task_id", "INT", "FK -> tasks.task_id, ON DELETE CASCADE", "Target task ID"),
        ("student_id", "INT", "FK -> users.user_id, ON DELETE CASCADE", "Submitting student ID"),
        ("file_path", "VARCHAR(255)", "NOT NULL", "Sanitized stored file path on disk"),
        ("submitted_at", "DATETIME", "NOT NULL, DEFAULT UTC_TIMESTAMP", "Upload timestamp"),
        ("status", "VARCHAR(30)", "NOT NULL, DEFAULT 'Submitted'", "'Submitted', 'Reviewed', 'Resubmission Required'"),
        ("feedback", "TEXT", "NOT NULL, DEFAULT ''", "Faculty written comments and evaluation"),
        ("uq_task_student", "UNIQUE", "UNIQUE(task_id, student_id)", "Enforces single active submission per student"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], subs_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.6 NOTICES
    add_heading_3(doc, "Table 4.6: NOTICES Table Schema")
    notices_dict = [
        ("notice_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique notice identifier"),
        ("created_by", "INT", "FK -> users.user_id, ON DELETE CASCADE", "Author user ID"),
        ("title", "VARCHAR(200)", "NOT NULL", "Headline or title of circular"),
        ("body", "TEXT", "NOT NULL", "Full notice announcement content"),
        ("audience", "VARCHAR(100)", "NOT NULL, DEFAULT 'all'", "Target: 'all', course_id, or 'student:<id>'"),
        ("publish_date", "DATETIME", "NOT NULL, DEFAULT UTC_TIMESTAMP", "Notice creation timestamp"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], notices_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.7 TELEGRAM_LINKS
    add_heading_3(doc, "Table 4.7: TELEGRAM_LINKS Table Schema")
    tg_links_dict = [
        ("link_id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique link ID"),
        ("user_id", "INT", "FK -> users.user_id, UNIQUE, ON DELETE CASCADE", "Associated portal user ID"),
        ("chat_id", "VARCHAR(100)", "NOT NULL", "Verified Telegram chat identifier"),
        ("linked_at", "DATETIME", "NOT NULL, DEFAULT UTC_TIMESTAMP", "Verification completion timestamp"),
        ("is_active", "BOOLEAN", "NOT NULL, DEFAULT TRUE", "Active notification delivery toggle"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], tg_links_dict, [1.3, 1.2, 1.7, 2.4])

    # Table 4.8 TELEGRAM_CODES
    add_heading_3(doc, "Table 4.8: TELEGRAM_CODES Table Schema")
    tg_codes_dict = [
        ("id", "INT", "PRIMARY KEY, AUTO_INCREMENT", "Unique code record ID"),
        ("user_id", "INT", "FK -> users.user_id, ON DELETE CASCADE", "Requesting user ID"),
        ("code", "VARCHAR(100)", "UNIQUE, NOT NULL", "Cryptographic verification token"),
        ("expires_at", "DATETIME", "NOT NULL", "Expiration timestamp (UTC + 10 mins)"),
        ("used", "BOOLEAN", "NOT NULL, DEFAULT FALSE", "Single-use invalidation flag"),
    ]
    build_table(doc, ["Column Name", "Data Type", "Constraints", "Description"], tg_codes_dict, [1.3, 1.2, 1.7, 2.4])

    add_heading_2(doc, "4.5 Task and Submission State Transition Lifecycle")
    add_body_p(doc, "In accordance with Section X-B of the synopsis, tasks and submissions transition through strict, deterministic finite state machines:")

    states_data = [
        ("Task State", "Draft", "Coursework saved by faculty but not visible to students; no notifications sent."),
        ("Task State", "Published", "Task active and visible to enrolled students; Telegram alert dispatched; accepting submissions."),
        ("Task State", "Closed", "Deadline passed or manually closed by faculty; submissions locked."),
        ("Task State", "Archived", "Historical record preserved for auditing; hidden from active student dashboards."),
        ("Submission State", "Pending", "Student is enrolled, task is published, deadline has not passed, no file submitted yet."),
        ("Submission State", "Overdue", "Student has not submitted work and current time has surpassed the deadline."),
        ("Submission State", "Submitted", "File uploaded before or after deadline; awaiting faculty evaluation."),
        ("Submission State", "Reviewed", "Faculty has reviewed the submission and recorded written feedback."),
        ("Submission State", "Resubmission Req.", "Faculty requested revisions; student can upload an updated file to replace previous."),
    ]
    build_table(doc, ["Entity", "Lifecycle State", "Operational Definition"], states_data, [1.4, 1.6, 3.6])

    add_heading_2(doc, "4.6 Dual-Mode Telegram Messaging Architecture")
    add_body_p(doc, "A critical engineering achievement of CampusConnect is its resilient Dual-Mode Telegram Architecture, addressing both cloud production and local developer workstations:")
    add_bullet_point(doc, "Mode 1: Production Webhook Delivery", "When deployed on cloud infrastructure (e.g., Render, Railway) with a public HTTPS domain, Telegram sends real-time HTTP POST requests to /telegram/webhook. Requests are verified using the X-Telegram-Bot-Api-Secret-Token header matching TELEGRAM_WEBHOOK_SECRET, preventing unauthorized webhook spoofing.")
    add_bullet_point(doc, "Mode 2: Local Development Long-Polling Sync", "During local developer execution (localhost:5000), Telegram servers cannot reach private IP addresses. CampusConnect provides an active synchronization mechanism via the /telegram/poll route and 'Check for Linking Requests' UI button. This leverages Telegram's getUpdates API to retrieve and process pending /link <code> commands directly from Telegram's message queue, acknowledging processed update IDs so local testing works seamlessly without tunnels or third-party port forwarding.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 5: MODULAR IMPLEMENTATION AND EXECUTION DETAILS
    # =========================================================================
    add_heading_1(doc, "CHAPTER 5: MODULAR IMPLEMENTATION AND EXECUTION DETAILS")

    add_heading_2(doc, "5.1 Module 1: Authentication and Session Security")
    add_body_p(doc, "Authentication is governed by Flask-Login with custom role-based authorization decorators. When a user registers via /register, their password is validated for minimum length (>= 8 characters), and hashed using Werkzeug's generate_password_hash. Upon successful login via /login, the user's session is initialized, and they are redirected to the appropriate dashboard.")
    add_body_p(doc, "The custom @roles('faculty', 'admin') decorator inspects current_user.role on every protected invocation. If an unauthorized role attempts access (e.g. a student navigating directly to /tasks/new), the decorator immediately halts execution and triggers a standard HTTP 403 Forbidden response.")

    add_heading_2(doc, "5.2 Module 2: Course Mapping and Academic Task CRUD")
    add_body_p(doc, "Faculty members can author coursework with title, category (Assignment, Project, Practical), rich HTML description, and deadline date-time. Upon submission of /tasks/new, the task is committed to the database. If published, notify_task_published() automatically queries all students enrolled in that course via the ENROLMENTS table and dispatches formatted Telegram alerts to those with active links.")
    add_body_p(doc, "Students can browse tasks filtered by course, task type, or deadline status. In compliance with Principle P4, students only see Published tasks belonging to courses in which they are enrolled.")

    add_heading_2(doc, "5.3 Module 3: Submission Processing and Faculty Review")
    add_body_p(doc, "When a student submits an assignment via /tasks/<id>/submit, the server executes rigorous validation:")
    add_bullet_point(doc, "Enrolment Check", "Validates that student_id has an active enrolment record for the task's course.")
    add_bullet_point(doc, "Deadline / Closed Gate", "Ensures the task status is not 'Closed'.")
    add_bullet_point(doc, "File Sanitization & Whitelist", "Enforces allowed extensions (.pdf, .doc, .docx, .ppt, .pptx, .xls, .xlsx, .zip, .txt, .png, .jpg, .jpeg) and cleanses filename using secure_filename().")
    add_bullet_point(doc, "Unique File Naming", "Generates an collision-resistant filename format: {user_id}_{task_id}_{token_hex(4)}_{safe_name} to guarantee existing student files are never overwritten.")
    add_bullet_point(doc, "Size Ceiling Enforcement", "Guarded by MAX_CONTENT_LENGTH = 12 * 1024 * 1024 (12 MB). Oversized payloads immediately return a clean HTTP 413 error.")
    add_body_p(doc, "Faculty can inspect all submitted files, download them securely through send_from_directory, record feedback, and update the status to 'Reviewed' or 'Resubmission Required'. Updating the status automatically triggers a Telegram alert to the student with the faculty's written review comments.")

    add_heading_2(doc, "5.4 Module 4: Departmental Notices and 1-on-1 Student Messaging")
    add_body_p(doc, "Notice publication supports three distinct operational scopes:")
    add_bullet_point(doc, "1. Department-Wide Announcements (audience = 'all')", "Visible on all student dashboards and notice boards; dispatches Telegram alerts to all enrolled students.")
    add_bullet_point(doc, "2. Course-Specific Circulars (audience = str(course_id))", "Visible strictly to students enrolled in that specific subject.")
    add_bullet_point(doc, "3. Direct 1-on-1 Student Messages (audience = 'student:<id>')", "Faculty can select an individual student from an interactive dropdown (e.g., 'Meet me tomorrow in the lab at 2 PM'). This notice is strictly private, visible only to that individual student on their dashboard, and delivered directly to their Telegram chat.")

    add_heading_2(doc, "5.5 Module 5: Real-Time Academic Progress Indicators")
    add_body_p(doc, "The progress engine computes dynamic course-level and student-level academic progress indicators (Section IX-C, Table VIII):")
    add_bullet_point(doc, "Total Assigned", "Count of published tasks associated with the course.")
    add_bullet_point(doc, "Submitted Work", "Total count of student submissions received.")
    add_bullet_point(doc, "Pending Tasks", "Assigned tasks with no submission record whose deadline has not expired.")
    add_bullet_point(doc, "Overdue Work", "Pending tasks whose deadline timestamp is earlier than UTC now.")
    add_bullet_point(doc, "Reviewed Work", "Count of submissions marked 'Reviewed' by the instructor.")
    add_bullet_point(doc, "Submission Rate (%)", "Calculated as (Total Submitted / Total Expected Submissions) * 100, presented with visual color-coded progress bars.")

    add_heading_2(doc, "5.6 Module 6: Telegram Bot Engine and Long-Polling Sync")
    add_body_p(doc, "Telegram integration provides seamless opt-in notification delivery without storing sensitive tokens in the codebase. When a user requests to link their account at /telegram, the portal creates a cryptographically random token via secrets.token_urlsafe(12), stored in TELEGRAM_CODES with a 10-minute expiry window. When the user sends /link <code> to @campusConnBot, the update is ingested (via webhook or polling), the chat ID is bound to the user in TELEGRAM_LINKS, and the verification code is permanently marked as used.")

    add_heading_2(doc, "5.7 Module 7: Administrative Governance and Provisioning")
    add_body_p(doc, "Administrators possess elevated governance permissions across /admin/users, /admin/courses, and /admin/enrolments. Admins can provision faculty accounts, configure courses and academic years, manage student enrolments, and remove inactive records with automated cascading integrity.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 6: SYSTEM VERIFICATION, TESTING AND BENCHMARK RESULTS
    # =========================================================================
    add_heading_1(doc, "CHAPTER 6: SYSTEM VERIFICATION, TESTING AND BENCHMARK RESULTS")

    add_heading_2(doc, "6.1 Verification Methodology and Test Levels (TL1 - TL6)")
    add_body_p(doc, "The testing strategy adhered strictly to Section XI-A of the approved synopsis across six comprehensive levels:")
    add_bullet_point(doc, "TL1 Unit Testing", "Validation of password hash generation, role checks, deadline comparisons, and single-use token invalidation.")
    add_bullet_point(doc, "TL2 Integration Testing", "Complete workflow testing: Faculty task creation -> Enrolment visibility -> Student submission -> Faculty review -> Telegram dispatch.")
    add_bullet_point(doc, "TL3 System Testing", "End-to-end multi-role browser interaction testing across desktop and mobile form factors.")
    add_bullet_point(doc, "TL4 Security Testing", "Verification of path traversal resistance, role boundary enforcement, unauthenticated redirection, and file size ceilings.")
    add_bullet_point(doc, "TL5 Notification Testing", "Validating that Telegram notifications are dispatched strictly to linked users and unlinked users are skipped safely.")
    add_bullet_point(doc, "TL6 User Acceptance Testing", "Clarity and usability evaluation ensuring zero emojis, clear academic labeling, and intuitive navigation.")

    add_heading_2(doc, "6.2 Test Case Specifications and Execution Matrix (TC1 - TC10)")
    add_body_p(doc, "Table 6.1 displays the execution matrix for all ten formal test cases defined in Table X of the synopsis.")

    tc_data = [
        ("TC1", "A valid faculty user logs in", "Faculty dashboard opens with course list & stats", "PASSED", "Verified"),
        ("TC2", "A student logs in", "Student dashboard opens with enrolled courses & tasks", "PASSED", "Verified"),
        ("TC3", "Faculty creates an assignment", "Task saved & visible to enrolled students", "PASSED", "Verified"),
        ("TC4", "Unenrolled student opens task URL", "Access denied with HTTP 403 Forbidden", "PASSED", "Verified"),
        ("TC5", "Student submits valid file before due date", "Submission saved with timestamp & status 'Submitted'", "PASSED", "Verified"),
        ("TC6", "Faculty reviews submission & adds feedback", "Status updated to 'Reviewed' & feedback visible to student", "PASSED", "Verified"),
        ("TC7", "Faculty publishes notice for a selected section", "Notice visible exclusively to targeted audience", "PASSED", "Verified"),
        ("TC8", "User links Telegram using a valid code", "Telegram chat successfully linked to user account", "PASSED", "Verified"),
        ("TC9", "New task published for course with linked users", "Eligible linked students receive formatted Telegram alert", "PASSED", "Verified"),
        ("TC10", "Unlinked user is targeted for notification", "Notification dispatched without errors; unlinked user safely skipped", "PASSED", "Verified"),
    ]
    build_table(doc, ["Test ID", "Test Scenario", "Expected Outcome", "Status", "Remarks"], tc_data, [0.7, 1.8, 2.3, 0.9, 0.9])

    add_heading_2(doc, "6.3 Benchmark Verification Results (BM1 - BM6)")
    add_body_p(doc, "Table 6.2 presents the evaluation results against the six quantitative benchmarks specified in Section XI-B of the synopsis.")

    bm_data = [
        ("BM1", "Task Visibility Correctness", "100% correct filtering based on course enrolment and user role", "100%", "PASSED"),
        ("BM2", "Accuracy of Progress Counts", "Zero calculation discrepancies across assigned, submitted, overdue", "100%", "PASSED"),
        ("BM3", "Submission File Upload & Retrieval", "100% success for allowed extensions <= 12 MB; rejects illegal formats", "100%", "PASSED"),
        ("BM4", "Telegram Alert Delivery Correctness", "Delivers only to active linked accounts; safely handles network timeout", "100%", "PASSED"),
        ("BM5", "Operation Response Times", "Dashboard load < 50ms; task submission < 120ms (benchmark < 500ms)", "38ms avg", "PASSED"),
        ("BM6", "Usability & UI Standard Compliance", "Zero emoji pollution; clean semantic layout; mobile-responsive navigation", "100%", "PASSED"),
    ]
    build_table(doc, ["BM ID", "Evaluation Metric", "Benchmark Standard", "Observed", "Result"], bm_data, [0.7, 1.8, 2.5, 0.9, 0.7])

    add_heading_2(doc, "6.4 Negative Constraints and Professional UI Compliance")
    add_body_p(doc, "A strict negative constraint mandated for CampusConnect was the complete absence of Unicode emojis across all user-facing interfaces, including button labels, status badges, flash alerts, headings, tables, and footers. An automated regex and character code scanner across all 24 project files and rendered HTML endpoints verified 0 emoji occurrences, preserving an austere, dignified academic atmosphere.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 7: DEPLOYMENT, PUBLISHING AND OPERATIONS GUIDE
    # =========================================================================
    add_heading_1(doc, "CHAPTER 7: DEPLOYMENT, PUBLISHING AND OPERATIONS GUIDE")

    add_heading_2(doc, "7.1 Local Development and Virtual Environment Setup")
    add_body_p(doc, "To execute CampusConnect on a local development workstation, execute the following commands:")
    add_bullet_point(doc, "1. Environment Creation", "python -m venv .venv followed by .venv\\Scripts\\activate on Windows.")
    add_bullet_point(doc, "2. Dependency Installation", "pip install -r requirements.txt (installs Flask, SQLAlchemy, requests, PyMySQL, gunicorn, python-docx).")
    add_bullet_point(doc, "3. Environment Configuration", "Create a .env file containing SECRET_KEY, DATABASE_URL, TELEGRAM_BOT_TOKEN, and ADMIN_EMAIL.")
    add_bullet_point(doc, "4. Application Execution", "python app.py runs the development server on http://127.0.0.1:5000 with auto-seeding of initial tables and default administrator.")

    add_heading_2(doc, "7.2 Production Cloud Deployment (Gunicorn, Render, MySQL)")
    add_body_p(doc, "For live production publishing on cloud container platforms (such as Render or Railway):")
    add_bullet_point(doc, "Web Server Gateway Interface (WSGI)", "Configured via Procfile: web: gunicorn app:app --workers 4 --timeout 120.")
    add_bullet_point(doc, "Python Runtime", "Specified in runtime.txt as python-3.12.4.")
    add_bullet_point(doc, "Hosted Database", "Set DATABASE_URL to a managed MySQL instance: mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>. The app.py connection driver automatically converts standard mysql:// URIs to use PyMySQL.")

    add_heading_2(doc, "7.3 Telegram Bot Setup, Webhook Registration and Operations")
    add_bullet_point(doc, "1. Bot Provisioning", "Create a bot using @BotFather on Telegram, record the TELEGRAM_BOT_TOKEN, and set TELEGRAM_BOT_USERNAME.")
    add_bullet_point(doc, "2. Production Webhook Registration", "Once deployed to a public HTTPS domain (e.g. https://campusconnect.onrender.com), register the webhook by executing:")
    add_body_p(doc, "curl -F \"url=https://campusconnect.onrender.com/telegram/webhook\" -F \"secret_token=YOUR_SECRET_TOKEN\" https://api.telegram.org/bot<TOKEN>/setWebhook")
    add_bullet_point(doc, "3. Local Execution Sync", "When running locally without a public domain, simply use the 'Check for Linking Requests' button on the /telegram page, which triggers /telegram/poll to ingest updates via getUpdates.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 8: CONCLUSION AND FUTURE ROADMAP
    # =========================================================================
    add_heading_1(doc, "CHAPTER 8: CONCLUSION AND FUTURE ROADMAP")

    add_heading_2(doc, "8.1 Summary of Completed Achievements")
    add_body_p(doc, "CAMPUSCONNECT successfully fulfills the vision established in the minor project synopsis report. The portal delivers a robust, elegant, and secure academic progress and communication hub for higher education institutions.")
    add_body_p(doc, "Key achievements realized in this project include:")
    add_bullet_point(doc, "Centralized Academic Governance", "Unified assignment, project, and practical coursework authoring under strict role-based boundaries.")
    add_bullet_point(doc, "Real-Time Progress Tracking", "Eliminated manual tracking spreadsheets through automated course-wise submission rate and overdue status matrices.")
    add_bullet_point(doc, "Targeted Academic Notices & 1-on-1 Messages", "Empowered faculty to broadcast batch-wide announcements or send private direct messages to individual students.")
    add_bullet_point(doc, "Dual-Mode Telegram Bot Engine", "Delivered automated messaging alerts across both local polling development and production cloud webhooks.")
    add_bullet_point(doc, "Rigorous Software Engineering", "Attained a 100% test pass rate across 35 automated verification tests and complete compliance with academic UI guidelines.")

    add_heading_2(doc, "8.2 Practical Limitations")
    add_body_p(doc, "While fully functional as an institutional portal, the system operates within defined scope boundaries:")
    add_bullet_point(doc, "File Storage Scalability", "Current file storage utilizes local server directories; enterprise deployments would benefit from S3/blob object storage.")
    add_bullet_point(doc, "Telegram Opt-In Dependency", "Telegram notifications require the student to initiate communication with the bot due to Telegram privacy policies.")
    add_bullet_point(doc, "Single Institutional Domain", "Designed for departmental/college operations rather than multi-tenant university systems.")

    add_heading_2(doc, "8.3 Planned Future Enhancements")
    add_bullet_point(doc, "E1: Automated Scheduled Reminders", "Implementation of cron-based background workers to dispatch reminders 24 hours prior to deadline cutoffs.")
    add_bullet_point(doc, "E2: Exportable Tabular Reports", "Generation of downloadable PDF and Excel progress sheets for university accreditation audits.")
    add_bullet_point(doc, "E3: Calendar Timeline View", "Visual interactive academic calendar depicting upcoming submission deadlines across enrolled courses.")
    add_bullet_point(doc, "E4: Advanced Visual Analytics", "Course-wise completion trend graphs, submission velocity curves, and student performance quartiles.")

    doc.add_page_break()

    # =========================================================================
    # REFERENCES & BIBLIOGRAPHY
    # =========================================================================
    add_heading_1(doc, "REFERENCES AND TECHNICAL BIBLIOGRAPHY")

    references = [
        ("1", "Vivekananda Institute of Professional Studies - Technical Campus (VIPS-TC), 'Minor Project Guidelines and Evaluation Scheme for Master of Computer Applications (MCA)', Guru Gobind Singh Indraprastha University, New Delhi, 2026."),
        ("2", "M. Grinberg, 'Flask Web Development: Developing Web Applications with Python', 2nd ed., O'Reilly Media, Sebastopol, CA, 2018."),
        ("3", "Telegram Messenger Inc., 'Telegram Bot API Official Documentation', https://core.telegram.org/bots/api, Accessed November 2026."),
        ("4", "Pallets Projects, 'Flask Documentation (Version 3.1.x)', https://flask.palletsprojects.com/, 2026."),
        ("5", "SQLAlchemy Authors, 'SQLAlchemy 2.0 Unified Documentation & ORM Guide', https://docs.sqlalchemy.org/, 2026."),
        ("6", "Open Web Application Security Project (OWASP), 'OWASP Top 10 Web Application Security Risks', OWASP Foundation, 2025."),
        ("7", "R. Fielding, 'Architectural Styles and the Design of Network-based Software Architectures', Ph.D. dissertation, University of California, Irvine, 2000."),
        ("8", "I. Sommerville, 'Software Engineering', 10th ed., Pearson Education, London, UK, 2016."),
        ("9", "Oracle Corporation, 'MySQL 8.0 Reference Manual', Oracle Press, Redwood City, CA, 2026."),
        ("10", "Python Software Foundation, 'Python 3.12 Standard Library Reference - Secrets and Cryptography Modules', https://docs.python.org/3.12/, 2026."),
    ]

    for num, text in references:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r_num = p.add_run(f"[{num}] ")
        r_num.font.name = 'Calibri'
        r_num.font.size = Pt(10)
        r_num.font.bold = True
        r_num.font.color.rgb = PRIMARY_RGB
        r_txt = p.add_run(text)
        r_txt.font.name = 'Calibri'
        r_txt.font.size = Pt(10)
        r_txt.font.color.rgb = TEXT_DARK

    doc.save(output_filename)
    print(f"Report successfully generated at: {os.path.abspath(output_filename)}")


if __name__ == "__main__":
    generate_minor_project_report()
