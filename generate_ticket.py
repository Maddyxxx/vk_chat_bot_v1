from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor


class MakeTicket:

    def __init__(self, fio, from_, to, date):
        self.text_info = [fio, from_, to, date]
        self.text_points = [(50, 122), (50, 192), (50, 258), (260, 258)]
        self.source_image = 'files/ticket_template.png'
        self.font = 'files/ofont.ru_Enthalpy 298.ttf'

    def make_ticket(self):
        ticket = Image.open(self.source_image)

        draw = ImageDraw.Draw(ticket)
        font = ImageFont.truetype(self.font, size=17)
        color = ImageColor.colormap['black']

        for index, text in enumerate(self.text_info):
            x, y = self.text_points[index]
            draw.text((x, y), text, font=font, fill=color)

        temp_file = BytesIO()
        ticket.save(temp_file, 'png')
        temp_file.seek(0)

        return temp_file


def make_ticket(fio, from_, to, date):
    new_ticket = MakeTicket(fio, from_, to, date)
    ticket = new_ticket.make_ticket()
    return ticket
