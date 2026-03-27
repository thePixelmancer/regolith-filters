import numpy as np
from PIL import Image

# Maps R channel value to slot index (0-based).
# Values are spaced 10 apart so a tolerance of ±4 can match each value
# unambiguously even with minor compression artifacts.
SLOT_R_VALUES: dict[int, int] = {
    10:  0,   # slot 0  (shaped: top-left,  furnace: input)
    20:  1,   # slot 1  (shaped: top-mid,   furnace: output)
    30:  2,   # slot 2
    40:  3,   # slot 3
    50:  4,   # slot 4
    60:  5,   # slot 5
    70:  6,   # slot 6
    80:  7,   # slot 7
    90:  8,   # slot 8
    100: 9,   # slot 9  (result)
}

_TOLERANCE = 4  # Max deviation from an R value to still count as a match


def _find_bbox_in_channel(channel: np.ndarray, r_value: int) -> tuple[int, int, int, int] | None:
    """
    Find the bounding box of all pixels within tolerance of r_value in a single channel.

    Args:
        channel: 2D numpy array of uint8 pixel values.
        r_value: Target R value to search for.

    Returns:
        (x_min, y_min, x_max, y_max) or None if fewer than 2 pixels match.
    """
    mask = np.abs(channel.astype(int) - r_value) <= _TOLERANCE
    ys, xs = np.where(mask)

    if len(xs) < 2:
        return None

    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def read_slot_template(template_path: str) -> dict[int, tuple[int, int, int, int]]:
    """
    Parse a slot template PNG and return a dict mapping slot index to bounding box.

    The template must be the same pixel dimensions as the final output canvas
    (i.e. the base image after its scale has been applied). Bounding box
    coordinates are used directly as canvas-space pixel coordinates.

    Encoding rules:
      - Image is treated as RGB (alpha is ignored)
      - R values 10, 20, 30 ... 100 map to slot indices 0-9
      - For each slot, channels R, G, B are checked in order — the first channel
        with at least 2 matching pixels wins. This allows up to 3 slots to share
        a pixel without ambiguity on their corner markers.
      - Bounding box = min/max x and y of all matching pixels in the winning channel.
        Fill the entire slot rectangle if desired — only the extremes matter.
      - A slot missing from all channels produces a warning and is omitted.

    Returns:
        dict mapping slot_index to (x_min, y_min, x_max, y_max)
    """
    img = Image.open(template_path).convert("RGB")
    arr = np.array(img)  # shape: (height, width, 3)

    channels = {
        "R": arr[:, :, 0],
        "G": arr[:, :, 1],
        "B": arr[:, :, 2],
    }

    slots: dict[int, tuple[int, int, int, int]] = {}

    for r_value, slot_index in SLOT_R_VALUES.items():
        bbox = None
        for channel_name, channel in channels.items():
            bbox = _find_bbox_in_channel(channel, r_value)
            if bbox is not None:
                break

        if bbox is None:
            print(
                f"[WARNING] Slot template '{template_path}': "
                f"slot {slot_index} (R={r_value}) not found in any channel — slot will be skipped."
            )
        else:
            x_min, y_min, x_max, y_max = bbox
            print(
                f"[TEMPLATE] Slot {slot_index} (R={r_value}): "
                f"bbox=({x_min},{y_min})->({x_max},{y_max}) "
                f"size={x_max - x_min + 1}x{y_max - y_min + 1}"
            )
            slots[slot_index] = bbox

    return slots
