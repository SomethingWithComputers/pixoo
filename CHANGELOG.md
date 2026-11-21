# Changelog

## 0.10.0

### Fixed

- `draw_line()` now draws the final endpoint and handles zero-length lines.
- `draw_image_frame()` now has a valid default frame, clips to the image bounds, and supports `Image.Image` objects.
- `draw_image()` now uses proper alpha blending, closes image files deterministically, and honors `pad_resample=True` for small images.
- `reboot()` now respects simulator mode.
- Device discovery now initializes debugging correctly, fixes the multi-device message, and handles discovery errors.
- `get_device_time()` no longer prints its response.
- Frame counter resets are consistent and reset the local counter.
- `validate_connection()` now handles device error responses and request exceptions correctly.
- `rgb_to_hex_color()` clamps out-of-range values.
- `send_text()` uses the display size for its default width and validates documented field ranges.
- `Pixoo.__all__` entries are strings, and `PixooREST` can be imported lazily.
- The simulator now supports 16, 32, and 64 pixel displays.

### Changed

- On/off command payloads use the integer values required by the Divoom API:
  - `Channel/OnOffScreen` → `OnOff` is `1`/`0`
  - `Device/SetHighLightMode` → `Mode` is `1`/`0`
  - `Device/SetMirrorMode` → `Mode` is `1`/`0`
  - `Tools/SetNoiseStatus` → `NoiseStatus` is `1`/`0`
- Device command failures raise `PixooError` instead of being silently ignored.
- `Flask` is now an optional dependency (`pixoo[rest]`); `import pixoo` no longer requires it.
- The simulator imports `tkinter` only when simulation is enabled.
- Packaging metadata lives in `pyproject.toml` only; `setup.py` was removed.
- Added a single-source version in `pixoo.__about__.__version__`.
- Added a `Channel.BLACK_SCREEN` value for the documented channel `4`.
