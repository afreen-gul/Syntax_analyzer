import io

from flask import Flask, render_template, request, send_file

from lexer import Lexer
from parser_module import Parser

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

app = Flask(__name__)

# =========================================================
# HOME
# =========================================================

@app.route('/')
def home():

    return render_template('index.html')


# =========================================================
# SCANNER
# =========================================================

@app.route('/scanner', methods=['GET', 'POST'])
def scanner():

    tokens = []

    error_count = 0

    code = ''

    if request.method == 'POST':

        code = request.form.get('code', '')

        lexer = Lexer(code)

        tokens = lexer.tokenize()

        error_count = len([
            t for t in tokens
            if t[0] == 'ERROR'
        ])

    return render_template(
        'scanner.html',
        tokens=tokens,
        error_count=error_count,
        code=code
    )


# =========================================================
# PARSER
# =========================================================

@app.route('/parser', methods=['GET', 'POST'])
def parser_page():

    tokens = []

    errors = []

    result = None

    symbols = {}

    code = ''

    if request.method == 'POST':

        code = request.form.get('code', '')

        lexer = Lexer(code)

        tokens = lexer.tokenize()

        lexer_errors = [
            t for t in tokens
            if t[0] == 'ERROR'
        ]

        parser = Parser(tokens)

        parser.parse()

        # FIXED ERROR MESSAGE
        errors = [
            f"{e[1]} at line {e[2]}, col {e[3]}"
            for e in lexer_errors
        ] + parser.errors

        symbols = parser.symbol_table.get_all()

        if len(errors) == 0:
            result = "Parsing Successful"

    return render_template(
        'parser.html',
        tokens=tokens,
        errors=errors,
        result=result,
        symbols=symbols,
        code=code
    )


# =========================================================
# DOWNLOAD SCANNER REPORT
# =========================================================

@app.route('/download_scanner_report', methods=['POST'])
def download_scanner_report():

    code = request.form.get('code', '')

    lexer = Lexer(code)

    tokens = lexer.tokenize()

    error_count = len([
        t for t in tokens
        if t[0] == 'ERROR'
    ])

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()

    # =====================================================
    # STYLES
    # =====================================================

    h1 = ParagraphStyle(
        'H1',
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=4
    )

    sub = ParagraphStyle(
        'Sub',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=2
    )

    bdy = ParagraphStyle(
        'Bdy',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#374151'),
        spaceAfter=4
    )

    cod = ParagraphStyle(
        'Cod',
        fontSize=9,
        fontName='Courier',
        textColor=colors.HexColor('#1f2937'),
        leading=14,
        backColor=colors.HexColor('#f3f4f6'),
        borderPadding=8
    )

    elems = []

    # =====================================================
    # HEADER
    # =====================================================

    elems.append(
        Paragraph(
            "W++ Compiler — Scanner Report",
            h1
        )
    )

    elems.append(
        Paragraph(
            "CS-310 · Compiler Construction · UET Rawalpindi",
            sub
        )
    )

    elems.append(
        Paragraph(
            f"Total Tokens: {len(tokens)} | Errors: {error_count}",
            sub
        )
    )

    elems.append(Spacer(1, 14))

    # =====================================================
    # SOURCE CODE
    # =====================================================

    elems.append(
        Paragraph("<b>Source Code:</b>", bdy)
    )

    elems.append(Spacer(1, 4))

    safe_code = (
        code
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )

    elems.append(
        Paragraph(
            safe_code.replace('\n', '<br/>') or '(empty)',
            cod
        )
    )

    elems.append(Spacer(1, 16))

    # =====================================================
    # TOKEN TABLE
    # =====================================================

    elems.append(
        Paragraph("<b>Token Table:</b>", bdy)
    )

    elems.append(Spacer(1, 6))

    if tokens:

        data = [['#', 'Type', 'Value', 'Line', 'Col']]

        for i, t in enumerate(tokens, 1):

            data.append([
                str(i),
                str(t[0]),
                str(t[1]),
                str(t[2]),
                str(t[3])
            ])

        table = Table(
            data,
            colWidths=[
                0.4 * inch,
                1.4 * inch,
                2.9 * inch,
                0.55 * inch,
                0.55 * inch
            ],
            repeatRows=1
        )

        style_cmds = [

            ('BACKGROUND',
             (0, 0),
             (-1, 0),
             colors.HexColor('#8b5cf6')),

            ('TEXTCOLOR',
             (0, 0),
             (-1, 0),
             colors.white),

            ('FONTNAME',
             (0, 0),
             (-1, 0),
             'Helvetica-Bold'),

            ('GRID',
             (0, 0),
             (-1, -1),
             0.4,
             colors.HexColor('#e5e7eb')),

            ('FONTNAME',
             (0, 1),
             (-1, -1),
             'Courier'),

            ('ROWBACKGROUNDS',
             (0, 1),
             (-1, -1),
             [
                 colors.HexColor('#faf5ff'),
                 colors.HexColor('#f3f4f6')
             ])
        ]

        for i, t in enumerate(tokens, 1):

            if t[0] == 'ERROR':

                style_cmds.append((
                    'TEXTCOLOR',
                    (0, i),
                    (-1, i),
                    colors.red
                ))

        table.setStyle(TableStyle(style_cmds))

        elems.append(table)

    else:

        elems.append(
            Paragraph(
                "No tokens generated.",
                bdy
            )
        )

    elems.append(Spacer(1, 14))

    # =====================================================
    # STATUS
    # =====================================================

    status_color = (
        colors.HexColor('#059669')
        if error_count == 0
        else colors.HexColor('#dc2626')
    )

    status_text = (
        "✓ Scan Complete — No Errors"
        if error_count == 0
        else f"✗ {error_count} Error(s) Found"
    )

    elems.append(
        Paragraph(
            f"<b>Status:</b> {status_text}",
            ParagraphStyle(
                'Status',
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=status_color
            )
        )
    )

    doc.build(elems)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='scanner_report.pdf',
        mimetype='application/pdf'
    )


# =========================================================
# DOWNLOAD PARSER REPORT
# =========================================================

@app.route('/download_parser_report', methods=['POST'])
def download_parser_report():

    code = request.form.get('code', '')

    lexer = Lexer(code)

    tokens = lexer.tokenize()

    lexer_errors = [
        t for t in tokens
        if t[0] == 'ERROR'
    ]

    parser = Parser(tokens)

    parser.parse()

    # FIXED ERROR MESSAGE
    errors = [
        f"{e[1]} at line {e[2]}, col {e[3]}"
        for e in lexer_errors
    ] + parser.errors

    symbols = parser.symbol_table.get_all()

    error_count = len(errors)

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()

    h1 = ParagraphStyle(
        'H1',
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=4
    )

    sub = ParagraphStyle(
        'Sub',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=2
    )

    bdy = ParagraphStyle(
        'Bdy',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#374151'),
        spaceAfter=4
    )

    cod = ParagraphStyle(
        'Cod',
        fontSize=9,
        fontName='Courier',
        textColor=colors.HexColor('#1f2937'),
        leading=14,
        backColor=colors.HexColor('#f3f4f6'),
        borderPadding=8
    )

    elems = []

    elems.append(
        Paragraph(
            "W++ Compiler — Parser Report",
            h1
        )
    )

    elems.append(
        Paragraph(
            "CS-310 · Compiler Construction · UET Rawalpindi",
            sub
        )
    )

    elems.append(
        Paragraph(
            f"Errors: {error_count} | Symbols: {len(symbols)}",
            sub
        )
    )

    elems.append(Spacer(1, 14))

    # =====================================================
    # SOURCE CODE
    # =====================================================

    elems.append(
        Paragraph("<b>Source Code:</b>", bdy)
    )

    elems.append(Spacer(1, 4))

    safe_code = (
        code
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )

    elems.append(
        Paragraph(
            safe_code.replace('\n', '<br/>') or '(empty)',
            cod
        )
    )

    elems.append(Spacer(1, 16))

    # =====================================================
    # PARSE RESULT
    # =====================================================

    elems.append(
        Paragraph("<b>Parse Result:</b>", bdy)
    )

    elems.append(Spacer(1, 6))

    if error_count == 0:

        elems.append(
            Paragraph(
                "✓ Parsing Successful — No Syntax Errors",
                ParagraphStyle(
                    'Ok',
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    textColor=colors.green
                )
            )
        )

    else:

        for e in errors:

            elems.append(
                Paragraph(
                    f"• {e}",
                    ParagraphStyle(
                        'Err',
                        fontSize=10,
                        textColor=colors.red
                    )
                )
            )

    elems.append(Spacer(1, 16))

    # =====================================================
    # SYMBOL TABLE
    # =====================================================

    elems.append(
        Paragraph("<b>Symbol Table:</b>", bdy)
    )

    elems.append(Spacer(1, 6))

    if symbols:

        data = [['#', 'Variable', 'Type']]

        for i, (name, dtype) in enumerate(
            symbols.items(),
            1
        ):

            data.append([
                str(i),
                name,
                dtype
            ])

        table = Table(
            data,
            colWidths=[
                0.4 * inch,
                3.1 * inch,
                2.3 * inch
            ],
            repeatRows=1
        )

        table.setStyle(TableStyle([

            ('BACKGROUND',
             (0, 0),
             (-1, 0),
             colors.HexColor('#8b5cf6')),

            ('TEXTCOLOR',
             (0, 0),
             (-1, 0),
             colors.white),

            ('GRID',
             (0, 0),
             (-1, -1),
             0.4,
             colors.HexColor('#e5e7eb')),

            ('FONTNAME',
             (0, 1),
             (-1, -1),
             'Courier'),

            ('ROWBACKGROUNDS',
             (0, 1),
             (-1, -1),
             [
                 colors.HexColor('#faf5ff'),
                 colors.HexColor('#f3f4f6')
             ])
        ]))

        elems.append(table)

    else:

        elems.append(
            Paragraph(
                "No symbols declared.",
                bdy
            )
        )

    doc.build(elems)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='parser_report.pdf',
        mimetype='application/pdf'
    )


# =========================================================
# RUN
# =========================================================

if __name__ == '__main__':

    app.run(debug=True)