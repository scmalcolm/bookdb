from reportlab.lib import pagesizes
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Table, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

_default_filename = 'order.pdf'
PAGESIZE = pagesizes.letter
PAGE_WIDTH, PAGE_HEIGHT = PAGESIZE
MARGIN = 2 * cm
styles = getSampleStyleSheet()
styleN = styles['Normal']

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

    # TODO: get order data

    doc.build(story)


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
            PAGE_HEIGHT - (2 * MARGIN) - (10 * cm)
        )]
        self.order = order
        PageTemplate.__init__(self, id='first', frames=frames)

    def beforPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(2.0 * cm, PAGE_HEIGHT - 2.0 * cm, "Ship/Invoice to:")
        top_text = create_text_object(canvas, PAGE_WIDTH / 2.0, PAGE_HEIGHT - 2.0 * cm, STORE_INFO, styleN, align='center')
        canvas.drawText(top_text)
        canvas.restoreState()


class LaterPageTemplate(PageTemplate):
    """docstring for LaterPageTemplate"""
    def __init__(self, order=None):
        frames = [Frame(MARGIN, MARGIN,
            PAGE_WIDTH - (2 * MARGIN),
            PAGE_HEIGHT - (2 * MARGIN) - (10 * cm)
        )]
        self.order = order
        PageTemplate.__init__(self, id='later', frames=frames)

    def beforPage(self, canvas, doc):
        order = self.order
        canvas.saveState()
        left_text = "The Bob Miller Book Room\nAcct#: {}".format(order.distributor.account)
        center_text = "PO#: {}\n{}".format(order.po, order.date)
        right_text = "{}\nPage #".format(order.distributor.full_name)
        tx = create_text_object(canvas, 2 * cm, PAGE_HEIGHT - 2 * cm,
            left_text, styleN, align='left')
        canvas.drawText(tx)
        tx = create_text_object(canvas, PAGE_WIDTH / 2.0, PAGE_HEIGHT - 2 * cm,
            center_text, styleN, align='center')
        canvas.drawText(tx)
        tx = create_text_object(canvas, PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 2 * cm,
            right_text, styleN, align='right')
        canvas.restoreState()
