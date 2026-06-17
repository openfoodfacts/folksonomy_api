"""
Change product barcode definition
"""

from yoyo import step

__depends__ = {"000-init-db"}

steps = [
    step("ALTER TABLE folksonomy ALTER COLUMN product TYPE VARCHAR(24)"),
    step("ALTER TABLE folksonomy_versions ALTER COLUMN product TYPE VARCHAR(24)"),
]
