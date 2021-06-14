import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np
import pandas as pd
import cv2
import kw6


def to_videos(kw6_path: Path, output_directory: Path = None, fourcc='FFV1'):
    '''Convert a kw6 file to videos'''
    if output_directory is None:
        output_directory = kw6_path.parent / kw6_path.stem

    output_directory.mkdir(exist_ok=True)

    camera_videos = dict()
    position_headers = list()

    try:
        for position in tqdm(kw6.Stream.from_path(kw6_path), desc='writing videos'):

            position_headers.append(position.header.dict())
            for camera in position.cameras:

                camera_index = camera.header.camera_index

                if camera_index not in camera_videos:
                    camera_videos[camera_index] = cv2.VideoWriter(
                        str(output_directory / f'{camera_index}.avi'),
                        cv2.VideoWriter_fourcc(*fourcc),
                        10,
                        (camera.image.width, camera.image.height),
                        isColor=0,
                    )

                camera_videos[camera_index].write(
                    np.array(camera.image)
                )
    except ValueError:
        print('Error when reading file, stopping after writing incomplete results')

    for video in camera_videos.values():
        video.release()

    (
        pd.DataFrame.from_records(position_headers)
        [['frame_index', 'time']]
        .to_csv(
            output_directory / 'positions.csv',
            index=False,
        )
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('kw6_path', type=str, help='Path to kw6 file')
    parser.add_argument(
        '-o', '--output_directory', type=str, help='Output directory', default=None
    )
    parser.add_argument(
        '--fourcc', type=str, help='Video codec https://www.fourcc.org/codecs.php', default='FFV1'
    )
    args = parser.parse_args()

    to_videos(
        Path(args.kw6_path),
        (None if args.output_directory is None else Path(args.output_directory)),
        args.fourcc,
    )


def test_to_videos():
    from pytest import raises

    kw6_path = Path('test/test.kw6')
    output_directory = Path('test_videos')

    to_videos(
        kw6_path,
        output_directory,
    )

    with raises(ValueError):
        videos = dict()

        for position in kw6.Stream.from_path(kw6_path):
            for camera in position.cameras:

                camera_index = camera.header.camera_index

                if camera_index not in videos:
                    videos[camera_index] = cv2.VideoCapture(
                        str(output_directory / f'{camera_index}.avi'),
                    )

                exists, frame = videos[camera_index].read()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                assert (np.array(camera.image) == frame).all()
