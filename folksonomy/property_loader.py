"""Utilities for loading and managing property documentation from YAML files."""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import PropertyDocumentation, PropertyList

# Path to property documentation files
PROPERTIES_DIR = Path(__file__).parent.parent / "data" / "properties"


def load_property_docs() -> Dict[str, PropertyDocumentation]:
    """Load all property documentation files from the data/properties directory."""
    properties = {}

    if not PROPERTIES_DIR.exists():
        return properties

    for yaml_file in PROPERTIES_DIR.glob("*.yaml"):
        if yaml_file.stem == "README":
            continue

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "key" in data:
                    properties[data["key"]] = PropertyDocumentation(**data)
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
            continue

    return properties


def get_property_doc(key: str) -> Optional[PropertyDocumentation]:
    """Get documentation for a specific property by key."""
    properties = load_property_docs()
    return properties.get(key)


def get_all_properties() -> List[PropertyList]:
    """Get a list of all documented properties with basic information."""
    properties = load_property_docs()
    return [
        PropertyList(
            key=prop.key,
            name=prop.name,
            icon=prop.icon,
            value_type=prop.value_type,
        )
        for prop in properties.values()
    ]


def get_property_knowledge_panel(key: str) -> Optional[dict]:
    """Get knowledge panel configuration for a specific property."""
    prop = get_property_doc(key)
    if prop and prop.knowledge_panel:
        return {
            **prop.knowledge_panel,
            "property_key": key,
            "property_name": prop.name,
            "property_icon": prop.icon,
        }
    return None


def search_properties(query: str, language: str = "en") -> List[PropertyList]:
    """Search properties by name or description in a specific language."""
    properties = load_property_docs()
    query_lower = query.lower()
    results = []

    for prop in properties.values():
        # Search in name
        name = prop.name.get(language, prop.name.get("en", ""))
        if query_lower in name.lower():
            results.append(
                PropertyList(
                    key=prop.key,
                    name=prop.name,
                    icon=prop.icon,
                    value_type=prop.value_type,
                )
            )
            continue

        # Search in description
        desc = prop.description.get(language, prop.description.get("en", ""))
        if query_lower in desc.lower():
            results.append(
                PropertyList(
                    key=prop.key,
                    name=prop.name,
                    icon=prop.icon,
                    value_type=prop.value_type,
                )
            )
            continue

        # Search in tags
        if prop.tags and any(query_lower in tag.lower() for tag in prop.tags):
            results.append(
                PropertyList(
                    key=prop.key,
                    name=prop.name,
                    icon=prop.icon,
                    value_type=prop.value_type,
                )
            )

    return results
