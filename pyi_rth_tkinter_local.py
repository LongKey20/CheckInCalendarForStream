import os
import sys

bundle = getattr(sys, "_MEIPASS", "")
if bundle:
    os.environ["TCL_LIBRARY"] = os.path.join(bundle, "_tcl_data")
    os.environ["TK_LIBRARY"] = os.path.join(bundle, "_tk_data")
