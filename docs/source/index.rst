Welcome to kw6's documentation!
===============================

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

Command line tool for converting a kw6 file to a folder with png images:

.. code-block::

    python -m kw6.to_png path/to/kw6


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   stream
   position
   camera
   to_png

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
