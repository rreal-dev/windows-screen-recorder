import os
from PyQt5.QtCore import QLibraryInfo

print("PyQt5 plugin path:", QLibraryInfo.location(QLibraryInfo.PluginsPath))
