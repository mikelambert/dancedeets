import dateparser
import datetime
import urlparse

from .. import items


def parse_times(times):
    start, end = times.split(u' - ')
    return dateparser.parse(start).time(), dateparser.parse(end).time()

def extract_text(cell):
    return ' '.join(cell.xpath('.//text()').extract()).strip()

class EDGE(items.StudioScraper):
    name = 'EDGE'
    allowed_domains = ['www.edgepac.com']
    latlong = (34.0889302, -118.3310113)
    address = '6300 Romaine St, Suite 100, Los Angeles CA 90038'

    start_urls = [
        'http://www.edgepac.com/schedule.htm',
    ]

    def parse_classes(self, response):
        table = response.xpath('//text()[normalize-space(.)="TIME"]/ancestor::table[1]')
        date = None
        for row in table.xpath('./tr'):
            a_name = row.xpath('.//a[@name]//text()')
            if a_name:
                # Grab day-of-week
                day = a_name.extract()[0].strip()
                date = dateparser.parse(day).date()
                if date < datetime.date.today():
                    date += datetime.timedelta(days=7)
            elif date: # Don't process rows as classes until we've seen Monday
                # Grab class
                cells = row.css('td')
                time_cell, studio_cell, style_cell, teacher_cell, date_cell, substitute_cell = cells
                times = extract_text(time_cell)

                style = extract_text(style_cell)
                if not self._street_style(style):
                    continue

                teacher = extract_text(teacher_cell)
                teacher_link = None
                teacher_href = teacher_cell.xpath('.//a/@href')
                if teacher_href:
                    teacher_link = teacher_href.extract()[0]
                substitute_date_string = extract_text(date_cell)
                substitute_teacher = extract_text(substitute_cell)

                start_time, end_time = parse_times(times)
                item = items.StudioClass()
                item['start_time'] = datetime.datetime.combine(date, start_time)
                item['end_time'] = datetime.datetime.combine(date, end_time)
                item['style'] = style
                item['teacher'] = teacher
                if teacher_link:
                    url = urlparse.urljoin(response.url, teacher_link)
                    item['teacher_link'] = url

                if substitute_date_string:
                    substitute_date = dateparser.parse(substitute_date_string).date()
                    print substitute_date
                    print date
                    if substitute_date != date:
                        # Return our existing item as-is, without any sub information
                        yield item.copy()
                        # But also now operate on a second copy, for the different date
                        item['start_time'] = datetime.datetime.combine(substitute_date, start_time)
                        item['end_time'] = datetime.datetime.combine(substitute_date, end_time)
                    item['teacher'] = '%s sub for %s' % (substitute_teacher, teacher)
                print item
                yield item

"""
                <tr>
                    <td width="162" align="left" height="27" style="border-left-style: none; border-left-width: medium; border-right-style: solid; border-right-width: 1px; border-bottom-style: solid; border-bottom-width: 1px; text-decoration:none; color:#000000; font-family:Arial; font-size:10pt">
                    <font face="Arial" size="2">10:00 a.m. - 11:30 a.m.</font></td>
                    <td width="36" align="left" height="27" style="border-right-style: solid; border-right-width: 1px; border-bottom-style: solid; border-bottom-width: 1px; text-decoration:none; color:#000000; font-family:Arial; font-size:10pt">
                    1</td>
                    <td width="206" align="left" height="27" style="border-right-style: solid; border-right-width: 1px; border-bottom-style: solid; border-bottom-width: 1px; text-decoration:none; color:#000000; font-family:Arial; font-size:10pt">
                    <font face="Arial" size="2">Jazz 2 Technique</font></td>
                    <td width="198" align="left" height="27" style="border-right-style: solid; border-right-width: 1px; border-bottom-style: solid; border-bottom-width: 1px; text-decoration:none; color:#000000; font-family:Arial; font-size:10pt">
    <font face="Arial" size="2">
    <a style="text-decoration: none; color: #000000" href="teachers/prudich_bill/prudich_bill.htm">Bill Prudich</a></font></td>
                    <td width="72" align="left" height="27" style="border-right-style: solid; border-right-width: 1px; border-bottom-style: solid; border-bottom-width: 1px; text-decoration:none; color:#000000; font-family:Arial; font-size:10pt">
                    &nbsp;</td>
                    <td width="298" height="27" style="border-right-style: none; border-right-width: medium; border-bottom-style: solid; border-bottom-width: 1px; text-decoration:none; color:#000000; font-family:Arial; font-size:10pt">
                    &nbsp;</td>
                </tr>
"""