from TexSoup import TexSoup


def iter_text_metadata(tex, tsv, corpus, globalmd):
    """
    Side effect: some corpus-level metadata is parsed "on the side" and assigned to globalmd.

    \label{ssec:corpus-kalamang}

    \item[sources]>->-------\bcite{Kimoto2017}, \ycite{Kimoto2018}

    \begin{itemize} -> text metadata

    \subsubsection*{Background to the recordings}
    \paragraph{alisiya} -> text descriptions
    ...
    \subsection ... -> stop!
    """
    tsvmd = {}
    for i, row in enumerate(tsv):
        if row['corpus'] == corpus:
            tsvmd[row['text']] = {k: v for k, v in row.items() if k not in ['corpus', 'text']}

    lines = [l.split('%')[0].strip() for l in tex.read_text(encoding='utf8').split('\n')]
    lines = [l for l in lines if l]
    in_section, in_subsection, in_itemize, in_description = False, False, False, False
    tids, text, itemize, sources = None, [], [], []
    res = {}
    for line in lines:
        if in_subsection:
            if line[0].replace('\\', '?') == '?':
                if 'paragraph' in line:
                    if tids and text:
                        for tid in tids:
                            res[tid] = '\n'.join(text)
                    tids = [s.strip() for s in TexSoup(line).paragraph.string.split(',')]
                    text = []
                else:
                    break
            else:
                text.append(line)
            continue
        if in_section:
            if 'subsubsection' in line:
                line = TexSoup(line.replace('*', ''))
                if line.subsubsection.string == 'Background to the recordings':
                    in_subsection = True
                    continue
            if 'itemize' in line and ('begin' in line):
                in_itemize = True
            if in_itemize:
                itemize.append(line)
                if 'itemize' in line and ('end' in line):
                    in_itemize = False
            if in_description:
                if 'description' in line and ('end' in line):
                    in_description = False
                else:
                    line = TexSoup(line)
                    if line.item:
                        if line.item.string == 'sources':
                            for dd in line.descendants:
                                name = getattr(dd, 'name', '')
                                if name.endswith('cite'):
                                    for sid in dd.string.split(','):
                                        sources.append(sid.strip().lower())
                        elif line.item.string == 'affiliation':
                            globalmd['affiliation'] = ''.join(line.text[1:]).strip()
                        elif line.item.string == 'area spoken':
                            globalmd['areas'] = ''.join(line.text[1:]).strip()
                        elif line.item.string == "varieties rec'd":
                            globalmd['varieties'] = ''.join(line.text[1:]).strip()

            if 'description' in line and ('begin' in line):
                in_description = True
        if 'label' in line:
            try:
                line = TexSoup(line)
                if line.label:
                    if line.label.string.strip() == 'ssec:corpus-{}'.format(corpus):
                        in_section = True
                    elif in_section:
                        in_section = False
            except EOFError:
                pass
    if tids and text:
        for tid in tids:
            res[tid] = '\n'.join(text)
    res2 = {}
    if itemize:
        itemize = TexSoup('\n'.join(itemize))
        for item in itemize.itemize.contents:
            if item.tit:
                tid = item.text[0]
                rem = TexSoup(str(item).split('tab')[1].strip().split(r'\\\hspace')[0])
                lid = rem.tit.string if rem.tit else None
                lname = rem.sqt.string if rem.sqt else None
                res2[tid] = (lid.replace(r'\_', '_') if lid else lid, lname)
    #assert set(res.keys()).issubset(tsvmd.keys()), '{} -- {}'.format(set(res.keys()), set(tsvmd.keys()))
    #assert set(res2.keys()).issubset(tsvmd.keys()), '{} -- {}'.format(set(res2.keys()), set(tsvmd.keys()))
    globalmd['sources'] = sources
    for tid, md in tsvmd.items():
        yield dict(
            id=tid,
            local_id=res2.get(tid, (None, None))[0],
            title=res2.get(tid, (None, None))[1],
            description=res.get(tid),
            **md)
