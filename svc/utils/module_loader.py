import importlib
import os.path
import pkgutil
import sys
from types import ModuleType
from typing import Dict


def import_submodules(package_name: str) -> Dict[str, ModuleType]:
    """Import all submodules of a module, recursively"""
    package: ModuleType = sys.modules[package_name]
    package_dir = os.path.dirname(package.__file__)  # type: ignore[type-var]

    return {
        name: importlib.import_module(package_name + "." + name)
        for loader, name, is_pkg in pkgutil.walk_packages([package_dir])  # type: ignore[list-item]
    }
