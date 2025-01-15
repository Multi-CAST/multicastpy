"""
Functionality to parse ELAN's .eaf files.
"""
from lxml.etree import parse

__all__ = ['remap_refind', 'add_orthography']


def remap_refind(doc, refind_map, tid):
    for e in doc.xpath(
            ".//TIER[@TIER_ID='refind']/ANNOTATION/REF_ANNOTATION/ANNOTATION_VALUE"):
        try:
            e.text = str(refind_map[tid, e.text])
        except KeyError:  # pragma: no cover
            stem = doc.xpath('.//MEDIA_DESCRIPTOR')[0].attrib['MEDIA_URL'].split('.')[0]
            e.text = str(refind_map['_'.join(stem.split('_')[2:]), e.text])


def add_orthography(p):
    eaf = parse(p).getroot()
    if not eaf.xpath(".//TIER[@TIER_ID='add_orthography' and @PARENT_REF='utterance']"):
        return {}
    add_orthography = {
        a.attrib['ANNOTATION_REF']: a.xpath('ANNOTATION_VALUE')[0].text
        for a in eaf.xpath(".//TIER[@TIER_ID='add_orthography' and @PARENT_REF='utterance']"
                           "/ANNOTATION/REF_ANNOTATION")
    }
    for a in eaf.xpath(".//TIER[@TIER_ID='utterance']/ANNOTATION/REF_ANNOTATION"):
        add_orthography[a.attrib['ANNOTATION_REF']] = add_orthography.pop(a.attrib['ANNOTATION_ID'])
    for a in eaf.xpath(".//TIER[@TIER_ID='utterance_id']/ANNOTATION/ALIGNABLE_ANNOTATION"):
        add_orthography[tuple(a.xpath('ANNOTATION_VALUE')[0].text.split('_'))] = (
            add_orthography.pop(a.attrib['ANNOTATION_ID']))
    # Make sure we only have utterances from exactly one text:
    assert len({k[0] for k in add_orthography}) == 1 and len({k[1] for k in add_orthography}) == 1
    return {k[2]: v for k, v in add_orthography.items()}
