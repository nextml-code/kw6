==========
kw6 reader
==========

Minimalistic library for reading files in the kw6 file format.

Install
=======

.. code-block::

    pip install kw6

Usage
=====

.. code-block:: python

    from pathlib import Path
    import kw6

    path = Path('...')

    for position in kw6.Stream(path):
        for camera in position.cameras:
            camera.image.save(
                f'{position.header.frame_index}_{camera.header.camera_index}.png'
            )
