#!/usr/bin/env python
import asyncio
import os
import re

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from hashlib import md5
from pprint import pprint
from typing import AsyncGenerator, AnyStr, Dict, Any, Tuple

import exifread
import fire

in_progress_images = {}
image_metadata = {}


async def file_listing(
        base_dir: AnyStr = None,
        filename_filter: AnyStr = '',
) -> AsyncGenerator[str, None]:
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

    chunk_size = 65 * 1024  # 65KiB.
    md5_hash = md5()

    with open(file_path, 'rb') as file_handle:
        data = file_handle.read(chunk_size)
        while data:
            md5_hash.update(data)
            data = file_handle.read(chunk_size)

    return md5_hash.hexdigest()


async def await_executor_result(future: asyncio.Future) -> Dict:
    """ Await on a future object."""
    await future


def process_executor_exif(future: asyncio.Future, executor_id: Tuple[AnyStr]) -> Dict:
    """Print the results of the executor future"""
    result = future.result()
    #  print(executor_id, result.get('Image DateTime', None))

    processed_file = executor_id[0]
    if processed_file in image_metadata:
        image_metadata[processed_file]['exif'] = result
    else:
        image_metadata[processed_file] = {'exif': result}

    del in_progress_images[executor_id]


def process_executor_hash(future: asyncio.Future, executor_id: Tuple[AnyStr]) -> Dict:
    """Print the results of the executor future"""
    result = future.result()
    #  print(executor_id, result)

    processed_file = executor_id[0]
    if processed_file in image_metadata:
        image_metadata[processed_file]['hash'] = result
    else:
        image_metadata[processed_file] = {'hash': result}

    del in_progress_images[executor_id]


async def main(base_dir: AnyStr = None):
    """Launch into the primary application from here.
    """
    loop = asyncio.get_running_loop()
    sync_thread_pool = ThreadPoolExecutor(max_workers=3)

    if not os.path.isdir(base_dir):
        base_dir = os.path.dirname(__file__)

    async for file_path in file_listing(base_dir, r'.*(?:jpg)|(?:JPG)|(?:JPEG)|(?:jpeg)$'):
        #  print(file_path)

        img_exif: asyncio.Future = loop.run_in_executor(sync_thread_pool, get_file_meta, file_path)
        img_md5: asyncio.Future = loop.run_in_executor(sync_thread_pool, get_file_hash, file_path)

        img_exif.add_done_callback(partial(process_executor_exif, executor_id=(file_path, 'exif')))
        img_md5.add_done_callback(
            partial(process_executor_hash, executor_id=(file_path, 'hash'))
        )

        in_progress_images[file_path, 'exif'] = img_exif
        in_progress_images[file_path, 'hash'] = img_md5

        loop.call_soon(await_executor_result, img_exif)
        loop.call_soon(await_executor_result, img_md5)

    while in_progress_images:
        await asyncio.sleep(0.5)
        print('{} tasks on the event loop'.format(len(asyncio.all_tasks(loop))))


    pprint(image_metadata, depth=2)
    #  image_results = []
    #  for result in asyncio.as_completed(image_metadata, loop=loop):
    #      image_results.append(result.result())

    #  #  print(image_results)
    #  print(image_results)


class CLI:

    @staticmethod
    def organise(base_dir: str):
        """Process images from the provided base_dir"""
        asyncio.run(main(base_dir))

    def __call__(self):
        asyncio.run(main())


if __name__ == '__main__':
    fire.Fire(CLI)
