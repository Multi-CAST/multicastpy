from multicastpy.__main__ import main
from cldfbench.__main__ import main as cldfbench


def test_corpus_list(fixtures, capsys):
    main([
        'cldfbench',
        str(fixtures)])
    out, _ = capsys.readouterr()
    assert 'veraa' in out


def test_version_list(fixtures, capsys):
    main([
        'cldfbench',
        '--corpus', 'veraa',
        str(fixtures)])
    out, _ = capsys.readouterr()
    assert '2311' in out


def test_all(tmp_path, fixtures):
    target = tmp_path / 'mcveraa'
    target.mkdir()
    main([
        'cldfbench',
        '--corpus', 'veraa',
        '--version', '2311',
        '--target-repos', str(target),
        str(fixtures)])
