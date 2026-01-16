# import internal function.
from notiq.monitoring.decorators import monitor

# and expose it publicly.
# __all__ defines what happens if someone types "from notiq import *"
__all__ = ["monitor"]

__version__ = "0.0.1"
