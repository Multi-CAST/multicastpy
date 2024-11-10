from argparse import Namespace

from cldfbench import CLDFWriter


def test_dataset(dataset, mocker):
    assert dataset.lid == 'veraa'
    assert dataset.with_refind

    class GLang:
        id = 'abcd1234'
        macroareas = [mocker.Mock(name='abcd')]
        latitude = 1
        longitude = 2

    with CLDFWriter(cldf_spec=dataset.cldf_specs()) as writer:
        dataset.cmd_makecldf(Namespace(
            log=mocker.Mock(),
            writer=writer,
            glottolog=mocker.Mock(api=mocker.Mock(languoid=mocker.Mock(return_value=GLang()))),
        ))

    # FIXME: must run makecldf first!
    md = dataset.cmd_readme(None)
    assert 'image.jpg' in md
    assert dataset.cldf_reader().validate()