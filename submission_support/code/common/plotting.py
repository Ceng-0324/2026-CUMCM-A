"""统一中文论文图件的 Matplotlib 环境配置。"""
from pathlib import Path
import os


def configure(root: Path) -> str:
    """设置可写缓存目录、中文字体和稳定的 PDF 字体类型。"""
    cache = root / ".mpl-cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache))
    import matplotlib
    from matplotlib import font_manager
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    candidates = ["STHeiti", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC",
                  "Arial Unicode MS", "DejaVu Sans"]
    family = next((name for name in candidates if name in fonts), "DejaVu Sans")
    matplotlib.rcParams.update({
        "font.family": [family, "DejaVu Sans"],
        "font.sans-serif": [family, "DejaVu Sans"],
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
    })
    return family
