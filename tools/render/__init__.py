"""Curious Mind render tools (episode-independent).

mathx       matrices, easing curves, keyframe tracks
raster      mip-mapped sprites/plates, affine drawing, unit-space canvas
encode      FFmpeg pipe encoder, ffprobe verification, frame extraction
testassets  clearly-labelled TEST plates/leaf (never final environment)
cli         `python -m tools.render render|stills|test-assets|plate-spec|qc --config <episode>/config/<x>.json`

Episode code (rig, camera, compositor, transitions) lives in the episode folder,
e.g. pilot/PILOT_01_STOP_TIME/. The CLI loads it from the config's location.
"""
