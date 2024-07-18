# Blender Lottie Exporter

Support exporting Grease Pencil as Lottie:
- `Export > Grease Pencil as Lottie(.json)`

## Install

1. Open blender preferences > addons > install from disk > select `lottie_exporter.py` in this repo.
2. In this addons preferences, click `Install` to install scour package( required if `optimize_svg` is enabled when exporting )

## How it works

this addons renders grease pencil animation to svg frame by frame, then embeds each frame into the Lottie image layer. Animation is played by changeing the visibilty of each image layer.
