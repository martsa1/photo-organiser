#!/usr/bin/env python
import asyncio
import logging
import os
import re

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from hashlib import md5
from pprint import pprint
from typing import AsyncGenerator, AnyStr, Dict, Any, Tuple, Mapping, Union, cast, AsyncIterable

import exifread
import fire

in_progress_images: Dict[Tuple[str, str], asyncio.Future] = {}
image_metadata: Dict[str, Dict[str, Any]] = {}

LOG = logging.getLogger(__name__)


async def file_listing(
        base_dir: str = None,
        filename_filter: str = '',
        #  ) -> AsyncGenerator[str, None]:
) -> AsyncIterable[str]:
    """Return a files list.
    """
    if not base_dir:
        base_dir = os.path.abspath(__file__)

    for directory, _, filenames in os.walk(base_dir):
        for filename in filenames:
            if file_listing is not None and re.search(filename_filter, filename):
                yield os.path.normpath(os.path.join(directory, filename))


def get_file_meta(file_path: AnyStr) -> Dict[str, Any]:
    """Retrieve metadata for the provided file path."""
    if not file_path:
        raise ValueError("Cannot operate on provided argument: {}".format(file_path))

    #  print('Retrieving EXIF data for {}'.format(file_path))
    with open(file_path, 'rb') as file_handle:
        file_exif_data = exifread.process_file(file_handle)
        file_exif_data = {
            tag: file_exif_data[tag]
            for tag in file_exif_data
            if tag not in (
                'EXIF MakerNote',
                'JPEGThumbnail',
                'TIFFThumbnail',
            )
        }

    return file_exif_data
    #  for tag in file_exif_data.keys():
    #     if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
    #         print("Key: {}, value {}".format(tag, a[tag]))


def get_file_hash(file_path: AnyStr) -> str:
    """Calculate the MD5 hash of the provided file path."""

    #  print('Hashing {}'.format(file_path))
    chunk_size = 65 * 1024  # 65KiB.
    md5_hash = md5()

    with open(file_path, 'rb') as file_handle:
        data = file_handle.read(chunk_size)
        while data:
            md5_hash.update(data)
            data = file_handle.read(chunk_size)

    #  print('MD5 for {}: {}'.format(file_path, md5_hash.hexdigest()))
    return md5_hash.hexdigest()


def process_executor_exif(future: asyncio.Future, executor_id: Tuple[str, str]) -> Dict:
    """Print the results of the executor future"""
    result: Dict[str, Union[str, int, float, Any]] = future.result()
    #  print(executor_id, result.get('Image DateTime', None))

    processed_file = executor_id[0]
    if processed_file in image_metadata:
        image_metadata[processed_file]['exif'] = result
    else:
        image_metadata[processed_file] = {'exif': result}

    del in_progress_images[executor_id]

    return result


def process_executor_hash(future: asyncio.Future, executor_id: Tuple[str, str]) -> None:
    """Print the results of the executor future"""
    result = future.result()
    #  print(executor_id, result)

    processed_file = executor_id[0]
    if processed_file in image_metadata:
        image_metadata[processed_file]['md5'] = result
    else:
        image_metadata[processed_file] = {'md5': result}

    del in_progress_images[executor_id]


async def main(base_dir: str = '', storage_dir: str = ''):
    """Launch into the primary application from here.
    """
    loop = asyncio.get_running_loop()
    sync_thread_pool = ThreadPoolExecutor(max_workers=3)

    if not os.path.isdir(base_dir):
        base_dir = os.path.dirname(__file__)

    # If we don't provide an option, default to organising the directory we are scanning.
    if not os.path.isdir(storage_dir):
        storage_dir = base_dir

    async for file_path in file_listing(base_dir, r'.*(?:jpg|JPG|JPEG|jpeg)$'):
        #  print(file_path)

        img_exif: asyncio.Future = cast(
            asyncio.Future, loop.run_in_executor(sync_thread_pool, get_file_meta, file_path)
        )
        img_md5: asyncio.Future = cast(
            asyncio.Future, loop.run_in_executor(sync_thread_pool, get_file_hash, file_path)
        )

        #  print('scheduling exif')
        img_exif.add_done_callback(partial(process_executor_exif, executor_id=(file_path, 'exif')))
        #  print('exif processing scheduled for {}'.format(file_path))

        #  print('scheduling md5')
        img_md5.add_done_callback(partial(process_executor_hash, executor_id=(file_path, 'hash')))
        #  print('md5 processing scheduled for {}'.format(file_path))

        in_progress_images[cast(str, file_path), 'exif'] = img_exif
        in_progress_images[cast(str, file_path), 'hash'] = img_md5

    while in_progress_images:
        await asyncio.sleep(0.5)
        print('{} images to process'.format(len(in_progress_images.keys())))

    pprint(
        {
            image_path: {
                'exif': image_metadata[image_path]['exif'].get('EXIF DateTimeOriginal', 'Unknown'),
                'md5': image_metadata[image_path].get('md5', 'No MD5?'),
            }
            for image_path in image_metadata
        }
    )
    #  image_results = []
    #  for result in asyncio.as_completed(image_metadata, loop=loop):
    #      image_results.append(result.result())

    #  #  print(image_results)
    #  print(image_results)


class CLI:

    @staticmethod
    def organise(base_dir: str, storage_dir: str = ''):
        """Process images from the provided base_dir"""
        asyncio.run(main(base_dir, storage_dir))

    def __call__(self):
        asyncio.run(main())


if __name__ == '__main__':
    fire.Fire(CLI)
