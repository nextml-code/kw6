==========
kw6 reader
==========

.. image:: https://badge.fury.io/py/kw6.svg
    :target: https://badge.fury.io/py/kw6

Minimalistic library for reading files in the kw6 file format. See the
`documentation <https://kw6.readthedocs.io/en/latest/>`_
for more information on the API.

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


.. code-block:: python

    from pathlib import Path
    import kw6

    reader = kw6.Reader.from_path(
        Path("...")
    )
    position = reader[100]
