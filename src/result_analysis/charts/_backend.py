"""Set Matplotlib backend before any submodule imports ``pyplot``."""

import matplotlib

matplotlib.use("Agg")
