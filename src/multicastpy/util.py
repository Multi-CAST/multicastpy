__all__ = ['rmdir']

def rmdir(p):
    if p.exists():
        for pp in p.iterdir():
            if pp.is_dir():
                rmdir(pp)
            else:
                pp.unlink()
        p.rmdir()
    return p
