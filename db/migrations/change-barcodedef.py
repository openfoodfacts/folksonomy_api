"""
Change product barcode definition
"""

from yoyo import step

__depends__ = {}

steps = [
    step("ALTER TABLE folksonomy ALTER COLUMN product TYPE VARCHAR"),
    step("ALTER TABLE folksonomy_versions ALTER COLUMN product TYPE VARCHAR")
]
