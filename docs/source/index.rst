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

    path = Path("...")

    for position in kw6.Reader.from_path(path):
        for camera in position.cameras:
            camera.image.save(
                f"{position.header.frame_index}_{camera.header.camera_index}.png"
            )

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   reader
   position
   camera

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
