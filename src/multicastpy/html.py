from lxml.etree import parse, HTMLParser

from .xml import text


def iter_corpus_metadata(index_html, corpora):
    """
    Parses metadata about corpora from the HTML page of Multi-CAST.
    """
    doc = parse(index_html, HTMLParser())
    for sec in doc.xpath('.//section'):
        desc, img_description = None, None
        title = sec.xpath('h1')
        if not title:
            continue

        cid = sec.xpath('div')[0].get('id')
        if cid not in corpora:
            continue
        for i, block in enumerate(sec.xpath("div[@class='block' or @class='block extraskip']")):
            if i == 0:  # Language and corpus description.
                desc = '\n\n'.join(text(p, markdown=True) for p in block.xpath('p'))
            else:
                if block.xpath(".//div[@class='corpusimage']"):
                    div = block.xpath(".//div[@class='corpusimage']")[0]
                    img_description = text(div.xpath('span')[0], markdown=True)
        yield dict(
            id=cid,
            lname=title[0].text.strip(),  # LanguageTable
            lgc=sec.xpath(
                ".//span[@class='iso']/a")[0].text
                if sec.xpath(".//span[@class='iso']/a") else None,  # LanguageTable
            contributors=[n.strip() for n in sec.xpath('h4')[0].text.split(',')],# ContributionTable
            description=desc,  # metadata.json
            image_description=img_description,
        )
