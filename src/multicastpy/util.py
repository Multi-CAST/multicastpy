import subprocess

__all__ = ['rmdir', 'is_same']


def rmdir(p):
    if p.exists():
        for pp in p.iterdir():
            if pp.is_dir():
                rmdir(pp)
            else:
                pp.unlink()
        p.rmdir()
    return p


def is_same(d1, d2):
    try:
        subprocess.check_call(['diff', str(d1), str(d2)], stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
