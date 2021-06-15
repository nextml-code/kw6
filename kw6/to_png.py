import argparse
from pathlib import Path
from tqdm import tqdm
import kw6


def to_png(kw6_path: Path, output_directory: Path = None):
    '''Convert a kw6 file to a folder of png images'''
    if output_directory is None:
        output_directory = kw6_path.parent / kw6_path.stem

    output_directory.mkdir(exist_ok=True)
    for position in tqdm(kw6.Reader.from_path(kw6_path), desc='saving images'):
        for camera in position.cameras:
            file_name = f'{position.header.frame_index}_{camera.header.camera_index}.png'
            camera.image.save(output_directory / file_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('kw6_path', type=str, help='Path to kw6 file')
    parser.add_argument(
        '-o', '--output_directory', type=str, help='Output directory', default=None
    )
    args = parser.parse_args()

    to_png(
        Path(args.kw6_path),
        (None if args.output_directory is None else Path(args.output_directory)),
    )


def test_to_png():
    from pytest import raises

    with raises(ValueError):
        to_png(
            Path('test/test.kw6'),
            Path('test_png'),
        )
