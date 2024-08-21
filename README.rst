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

Iterating over all positions and cameras in a kw6 file:

.. code-block:: python

    from pathlib import Path
    import kw6

    path = Path("...")

    for position in kw6.Reader.from_path(path):
        for camera in position.cameras:
            camera.image.save(
                f"{position.header.frame_index}_{camera.header.camera_index}.png"
            )

Accessing specific positions by frame index:

.. code-block:: python

    from pathlib import Path
    import kw6

    reader = kw6.Reader.from_path(Path("..."))
    
    # Access a single position
    position = reader[10]
    
    # Access a range of positions
    positions = reader[10:20]
    
    # Access specific positions
    positions = reader[[5, 7, 9]]

Additional Features
===================

- Supports reading from file-like objects and file paths
- Efficient indexing and slicing of positions
- Automatic handling of file versions and headers
- Built-in error handling for corrupt or incomplete files

For more detailed information on the API and advanced usage, please refer to the
`full documentation <https://kw6.readthedocs.io/en/latest/>`_.
