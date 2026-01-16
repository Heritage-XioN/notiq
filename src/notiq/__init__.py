# import internal function.
from notiq.monitoring.builder import MetricBuilder
from notiq.monitoring.decorators import monitor

# and expose it publicly.
# __all__ defines what happens if someone types "from notiq import *"
__all__ = ["monitor", "MetricBuilder"]

__version__ = "0.0.1"
