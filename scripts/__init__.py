"""Package marker for the scripts package.

This file ensures `import scripts.model_cache` works on a fresh clone where implicit namespace packages
may not be relied upon across Python environments used in Colab.
"""

__all__ = []
