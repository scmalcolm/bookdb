from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Table, NextPageTemplate, Paragraph, TableStyle
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.units import cm

_default_filename = 'order.pdf'
PAGESIZE = pagesizes.letter
PAGE_WIDTH, PAGE_HEIGHT = PAGESIZE
MARGIN = 2 * cm

stylesheet = StyleSheet1()
stylesheet.add(ParagraphStyle(name='normal',
                              fontName='Times-Roman',
                              fontSize=12,
                              leading=12,
                              spaceBefore=0.25 * cm))
stylesheet.add(ParagraphStyle(name='heading',
                              fontName='Times-Bold',
                              fontSize=12,
                              leading=12,))
stylesheet.add(ParagraphStyle(name='table-heading',
                              fontName='Times-Bold',
                              fontSize=11,
                              leading=11,))
stylesheet.add(ParagraphStyle(name='table-body',
                              fontName='Times-Roman',
                              fontSize=11,
                              leading=11,))

styleN = stylesheet['normal']
styleB = stylesheet['heading']
styleTH = stylesheet['table-heading']
styleTR = stylesheet['table-body']
STORE_INFO = (
'''
The Bob Miller Book Room
180 Bloor Street West, Lower Concourse
Toronto ON M5S 2V6
Canada
Phone: (416) 922-3557 Fax: (416) 922-4281
Email: info@bobmillerbookroom.com
GST Registration: R105197891
''')


def generate_order_pdf(order, filename=_default_filename):
    firstpage = FirstPageTemplate(order=order)
    laterpages = LaterPageTemplate(order=order)
    doc = BaseDocTemplate(filename, pagesize=PAGESIZE, pageTemplates=[firstpage, laterpages])
    story = [NextPageTemplate('later')]

    columns = [1.0 * cm, 2.75 * cm, 6 * cm, 3.25 * cm, 3 * cm, 1.5 * cm]
    data = [['Qty', 'ISBN', 'Title', 'Author', 'Publisher', 'Binding']]

    def compare_titles(a, b):
        return cmp(a.book.title, b.book.title)

    for entry in sorted(order.order_entries, compare_titles):
        row = [
            entry.quantity,
            entry.book.isbn13,
            entry.book.title,
            entry.book.author_lastname(),
            entry.book.publisher,
            entry.book.binding,
            ]
        data.append(row)
    table = Table(data, colWidths=columns, repeatRows=1)
    table.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * cm),
                               ('FONT', (0, 0), (-1, 0), styleTH.fontName, styleTH.fontSize),
                               ('LEADING', (0, 0), (-1, 0), styleTH.leading),
                               ('FONT', (0, 1), (-1, -1), styleTR.fontName, styleTR.fontSize),
                               ('LEADING', (0, 1), (-1, -1), styleTR.leading)]))

    if len(order.order_entries) > 1:
        plural = 's'
    else:
        plural = ''

    story.append(Paragraph("ATTENTION: ORDER DEPARTMENT", styleN))
    story.append(Paragraph("<i>Special Instructions</i>:<b>" + order.comment + "</b>", styleN))
    story.append(Paragraph('<i>Please send the following title' + plural + ':</i>', styleN))
    story.append(table)
    doc.build(story, canvasmaker=NumberedCanvas)


class FirstPageTemplate(PageTemplate):
    """docstring for FirstPageTemplate"""
    def __init__(self, order=None):
        frames = [Frame(MARGIN, MARGIN,
            PAGE_WIDTH - (2 * MARGIN),
            PAGE_HEIGHT - (2 * MARGIN) - (8.5 * cm))]
        self.order = order
        PageTemplate.__init__(self, id='first', frames=frames)

    def afterDrawPage(self, canvas, doc):
        order = self.order
        canvas.saveState()
        canvas.setFont(styleN.fontName, styleN.fontSize)
        canvas.drawString(
            MARGIN,
            PAGE_HEIGHT - MARGIN - styleN.leading,
            "Ship/Invoice to:")
        top_text = create_text_object(
            canvas,
            PAGE_WIDTH / 2.0,
            PAGE_HEIGHT - MARGIN,
            STORE_INFO,
            styleN,
            align='center')
        canvas.drawText(top_text)

        # draw left column of upper section
        LEFT = MARGIN
        LINE_HEIGHT = styleB.leading
        TOP = PAGE_HEIGHT - MARGIN - 4 * cm
        DIST_HEIGHT = 7 * LINE_HEIGHT
        HEADING_WIDTH = 2 * cm
        canvas.setFont(styleB.fontName, styleB.fontSize)
        canvas.drawString(
            LEFT,
            TOP - LINE_HEIGHT,
            "Distributor")
        address_text = create_text_object(
            canvas,
            LEFT,
            TOP - styleB.leading - LINE_HEIGHT,
            order.distributor.mailing_address(),
            styleN)
        canvas.drawText(address_text)
        canvas.setFont(styleB.fontName, styleB.fontSize)
        canvas.drawString(
            LEFT,
            TOP - DIST_HEIGHT - LINE_HEIGHT,
            "Phone:")
        canvas.drawString(
            LEFT,
            TOP - DIST_HEIGHT - 3 * LINE_HEIGHT,
            "Fax:")
        canvas.setFont(styleN.fontName, styleN.fontSize)
        if order.distributor.phone is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - DIST_HEIGHT - LINE_HEIGHT,
                order.distributor.phone)
        if order.distributor.fax is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - DIST_HEIGHT - 3 * LINE_HEIGHT,
                order.distributor.fax)

        # draw right column of upper section
        LEFT = PAGE_WIDTH / 2.0
        HEADING_WIDTH = 3.5 * cm
        canvas.setFont(styleB.fontName, styleB.fontSize)
        canvas.drawString(
            LEFT,
            TOP - LINE_HEIGHT,
            'Purchase Order #:')
        canvas.drawString(
            LEFT,
            TOP - 3 * LINE_HEIGHT,
            'Date:')
        canvas.drawString(
            LEFT,
            TOP - 5 * LINE_HEIGHT,
            'Account Number:')
        canvas.drawString(
            LEFT,
            TOP - 7 * LINE_HEIGHT,
            'Account Rep:')
        canvas.drawString(
            LEFT,
            TOP - 9 * LINE_HEIGHT,
            'Shipping Method:')
        canvas.setFont(styleN.fontName, styleN.fontSize)
        if order.po is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - LINE_HEIGHT,
                order.po)
        if order.date is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - 3 * LINE_HEIGHT,
                order.date.isoformat())
        if order.distributor.account_number is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - 5 * LINE_HEIGHT,
                order.distributor.account_number)
        if order.distributor.sales_rep is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - 7 * LINE_HEIGHT,
                order.distributor.sales_rep)
        if order.shipping_method is not None:
            canvas.drawString(
                LEFT + HEADING_WIDTH,
                TOP - 9 * LINE_HEIGHT,
                str(order.shipping_method))


class LaterPageTemplate(PageTemplate):
    """docstring for LaterPageTemplate"""
    def __init__(self, order=None):
        frames = [Frame(MARGIN, MARGIN,
            PAGE_WIDTH - (2 * MARGIN),
            PAGE_HEIGHT - (2 * MARGIN) - (1.5 * cm))]
        self.order = order
        PageTemplate.__init__(self, id='later', frames=frames)

    def afterDrawPage(self, canvas, doc):
        order = self.order
        canvas.saveState()
        left_text = "The Bob Miller Book Room\nAcct#: {}".format(order.distributor.account_number)
        center_text = "PO#: {}\n{}".format(order.po, order.date)
        right_text = "{}".format(order.distributor.full_name)
        tx = create_text_object(canvas, 2 * cm, PAGE_HEIGHT - 2 * cm,
            left_text, styleN, align='left')
        canvas.drawText(tx)
        tx = create_text_object(canvas, PAGE_WIDTH / 2.0, PAGE_HEIGHT - 2 * cm,
            center_text, styleN, align='center')
        canvas.drawText(tx)
        canvas.setFont(styleN.fontName, styleN.fontSize)
        canvas.drawRightString(PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 2 * cm, right_text)
        canvas.restoreState()


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._codes = []

    def showPage(self):
        self._codes.append({'code': self._code, 'stack': self._codeStack})
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        # reset page counter
        self._pageNumber = 0
        for code in self._codes:
            # recall saved page
            self._code = code['code']
            self._codeStack = code['stack']
            self.setFont(styleN.fontName, styleN.fontSize)
            X, Y = (PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 2 * cm)
            if self._pageNumber != 0:  # offset so distributor name is above, except page 1
                Y = Y - styleN.leading
            self.drawRightString(X, Y,
                "Page %(this)i of %(total)i" % {
                   'this': self._pageNumber + 1,
                   'total': len(self._codes),
                }
            )
            canvas.Canvas.showPage(self)
        self._doc.SaveToFile(self._filename, self)


def create_text_object(canv, x, y, text, style, align='left'):
    font = (style.fontName, style.fontSize, style.leading)
    lines = text.split("\n")
    offsets = []
    if align == 'center':
        maxwidth = 0
        for line in lines:
            offsets.append(canv.stringWidth(line, *font[:2]))
        maxwidth = max(*offsets)
        offsets = [(maxwidth - i) / 2 for i in offsets]
        x = x - maxwidth / 2.0
    elif align == 'left':
        offsets = [0] * len(lines)
    elif align == 'right':
        maxwidth = 0
        for line in lines:
            offsets.append(canv.stringWidth(line, *font[:2]))
        maxwidth = max(*offsets)
        offsets = [(maxwidth - i) for i in offsets]
        x = x - maxwidth
    else:
        raise ValueError("'{}' is not a supported alignment".format(align))
    tx = canv.beginText(x, y)
    tx.setFont(*font)
    for offset, line in zip(offsets, lines):
        tx.setXPos(offset)
        tx.textLine(line)
        tx.setXPos(-offset)
    return tx
