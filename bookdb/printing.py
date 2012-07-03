from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Table, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

_default_filename = 'order.pdf'
PAGESIZE = pagesizes.letter
PAGE_WIDTH, PAGE_HEIGHT = PAGESIZE
MARGIN = 2 * cm
styles = getSampleStyleSheet()
styleN = styles['Normal']
styleB = styleN

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

    columns = [0.75 * cm, 2.75 * cm, 6 * cm, 3.5 * cm, 3 * cm, 1.5 * cm]
    data = [['Qty', 'ISBN', 'Title', 'Author', 'Publisher', 'Binding']]
    for entry in order.order_entries:
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
    story.append(table)

    doc.build(story, canvasmaker=NumberedCanvas)


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


class FirstPageTemplate(PageTemplate):
    """docstring for FirstPageTemplate"""
    def __init__(self, order=None):
        frames = [Frame(MARGIN, MARGIN,
            PAGE_WIDTH - (2 * MARGIN),
            PAGE_HEIGHT - (2 * MARGIN) - (10 * cm))]
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
            PAGE_HEIGHT - MARGIN - styleN.leading,
            STORE_INFO,
            styleN,
            align='center')
        canvas.drawText(top_text)
        canvas.setFont('Times-Bold', styleB.fontSize)
        canvas.drawString(
            MARGIN,
            PAGE_HEIGHT - MARGIN - 4 * cm - styleB.leading,
            "Distributor")
        address_text = create_text_object(
            canvas,
            MARGIN,
            PAGE_HEIGHT - MARGIN - 4 * cm - styleB.leading - styleN.leading,
            order.distributor.mailing_address(),
            styleN)
        canvas.drawText(address_text)
        canvas.restoreState()


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
        left_text = "The Bob Miller Book Room\nAcct#: {}".format('placeholder!')
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
