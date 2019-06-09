"""Inline images and file transfers for iTerm2."""

from base64 import b64encode
import copy
from dataclasses import dataclass, field
from enum import Enum
import io
from pathlib import Path
import sys
from typing import ByteString, Optional

try:
    import numpy as np
except ImportError:
    pass

from PIL import Image

__all__ = ['FileEsc', 'ImageLenUnit', 'ImageDim', 'ImageEsc']


@dataclass
class FileEsc:
    """Generates escape sequences for a file transfer."""
    data: ByteString = field(default=b'', repr=False)
    name: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.data, ByteString):
            raise TypeError("'data' field must be a bytes-like object")

    @classmethod
    def open(cls, path):
        """Open a file, read it into memory, and prepare to generate escape
        sequences which encode its contents."""
        path = Path(path)
        name = path.parts[-1] if path.parts else None
        return cls(path.read_bytes(), name)

    @property
    def file(self):
        """Gets a new binary stream copy of the object's :attr:`data` field."""
        return io.BytesIO(self.data)

    @classmethod
    def _get_binary_stream(cls, b):
        if isinstance(b, (io.RawIOBase, io.BufferedIOBase)):
            return b
        if hasattr(b, 'buffer'):
            return cls._get_binary_stream(b.buffer)
        msg = '{} is not a binary stream nor is it convertible to one'
        raise TypeError(msg.format(type(b).__name__))

    def _write_args(self, b, args):
        b = self._get_binary_stream(b)
        fmt_args = ';'.join('{}={}'.format(k, v) for k, v in args.items())
        b.write(b'\x1b]1337;File=' + fmt_args.encode() + b':')
        b.write(b64encode(self.data))
        b.write(b'\a\n')
        b.flush()

    def write(self, b=sys.stdout.buffer):
        """Writes the escape sequences to a binary stream (by default
        `sys.stdout.buffer`)."""
        args = {}
        if self.name is not None:
            args['name'] = b64encode(self.name.encode()).decode()
        args['size'] = len(self.data)
        self._write_args(b, args)
        return self


class ImageLenUnit(Enum):
    """Represents units of measure of inline image size."""
    CELLS = ''
    PIXELS = 'px'
    PERCENT = '%'
    AUTO = 'auto'


@dataclass
class ImageDim:
    """Represents inline image sizes as a quantity (a pair of a numerical value
    with a unit of measure)."""
    value: float = 0
    unit: ImageLenUnit = ImageLenUnit.AUTO

    def __str__(self):
        if self.unit == ImageLenUnit.AUTO:
            return self.unit.value
        return '{!s}{!s}'.format(self.value, self.unit.value)


@dataclass
class ImageEsc(FileEsc):
    """Generates escape sequences which encode the contents of an image."""
    width: ImageDim = field(default_factory=ImageDim)
    height: ImageDim = field(default_factory=ImageDim)
    preserve_aspect_ratio: bool = True

    def copy(self):
        """Returns a copy of the object."""
        return copy.deepcopy(self)

    def detect_size(self, retina=True):
        """Sets the image's displayed size in pixels to its true pixel count."""
        scale = 2 if retina else 1
        w, h = Image.open(self.file).size
        self.width = ImageDim(w / scale, ImageLenUnit.PIXELS)
        self.height = ImageDim(h / scale, ImageLenUnit.PIXELS)
        return self

    @classmethod
    # pylint: disable=redefined-builtin
    def from_pil(cls, image, format='png', **params):
        """Creates a new :class:`ImageEsc` containing a compressed image, saved
        to it by Pillow. It is PNG format by default. Arguments which you would
        give to :meth:`PIL.Image.save` can be given here.

        To go in the reverse direction, to create a Pillow image object from an
        :class:`ImageEsc`, do: ``Image.open(image_esc.file)``.
        """
        fp = io.BytesIO()
        image.save(fp, format, **params)
        w, h = image.size
        try:
            path = Path(image.filename)
            name = path.parts[-1]
        except (AttributeError, IndexError):
            name = None
        return cls(fp.getvalue(), name,
                   ImageDim(w / 2, ImageLenUnit.PIXELS),
                   ImageDim(h / 2, ImageLenUnit.PIXELS))

    @classmethod
    def from_numpy(cls, arr, *, save_params=None):
        """Creates a new :class:`ImageEsc` containing an image from a NumPy
        array, saved to it by Pillow (via :meth:`from_pil`). By default it
        creates PNG format images; if you want to customize this, items in the
        `save_params` dict will be passed on to :meth:`from_pil` and thus to
        :meth:`PIL.Image.save`.

        Allowed array shapes and data types:

            * Arrays must have dtype `np.uint8`. The range of values is 0–255.

            * Arrays must either be 2D or 3D. 2D arrays correspond to grayscale
                images, and (most) 3D arrays to color.

            * 3D arrays must follow the dimension order HWC (channels last).

            * 3D arrays may have 1 to 4 channels. 3D arrays with 1 channel are
                grayscale; with 2 channels, grayscale with alpha; with 3
                channels, RGB; with 4 channels, RGB with alpha.
        """
        if 'numpy' not in sys.modules:
            raise ImportError('numpy is not imported')

        if arr.ndim not in (2, 3):
            raise ValueError('Array must be 2 or 3 dimensional')

        if not all(arr.shape):
            raise ValueError('All array dimensions must be nonzero')

        if arr.ndim == 3:
            if arr.shape[-1] == 1:
                arr = arr[:, :, 0]
            elif arr.shape[-1] > 4:
                msg = 'Number of channels (last dimension) must be 1-4'
                raise ValueError(msg)

        if np.issubdtype(arr.dtype, np.floating):
            arr = np.uint8(np.round(np.clip(arr, 0, 1) * 255))

        if not np.issubdtype(arr.dtype, np.uint8):
            raise ValueError('Array dtype must be uint8 (range 0-255) '
                             'or float[16, 32, 64, 128] (range 0-1)')

        save_params = {} if save_params is None else save_params
        return cls.from_pil(Image.fromarray(arr), **save_params)

    def write(self, b=sys.stdout.buffer):
        args = {}
        if self.name is not None:
            args['name'] = b64encode(self.name.encode()).decode()
        args['size'] = len(self.data)
        args['width'] = str(self.width)
        args['height'] = str(self.height)
        args['preserveAspectRatio'] = int(self.preserve_aspect_ratio)
        args['inline'] = 1
        self._write_args(b, args)
        return self

    def __imul__(self, other):
        if not isinstance(other, (int, float)):
            return NotImplemented
        if other < 0:
            raise ValueError('Cannot multiply or divide by a negative number')
        self.width.value *= other
        self.height.value *= other
        return self

    def __itruediv__(self, other):
        return self.__imul__(1 / other)

    def __mul__(self, other):
        return self.copy().__imul__(other)

    def __truediv__(self, other):
        return self.copy().__itruediv__(other)

    def __rmul__(self, other):
        return self * other
