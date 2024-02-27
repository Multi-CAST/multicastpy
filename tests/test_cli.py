from multicastpy.__main__ import main


def test_all(tmp_path, fixtures):
    target = tmp_path / 'mcveraa'
    target.mkdir()
    main([
        'cldfbench',
        '--corpus', 'veraa',
        '--version', '2311',
        '--target-repos', str(target),
        str(fixtures)])
