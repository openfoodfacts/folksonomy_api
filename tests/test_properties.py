"""Tests for property documentation system."""


from folksonomy import property_loader
from folksonomy.models import PropertyDocumentation, PropertyList


def test_load_property_docs():
    """Test loading all property documentation files."""
    properties = property_loader.load_property_docs()
    assert isinstance(properties, dict)
    assert len(properties) > 0
    # Check that scoville_scale is loaded
    assert "scoville_scale" in properties
    assert isinstance(properties["scoville_scale"], PropertyDocumentation)


def test_get_all_properties():
    """Test getting list of all properties."""
    properties = property_loader.get_all_properties()
    assert isinstance(properties, list)
    assert len(properties) > 0
    # Check structure
    for prop in properties:
        assert isinstance(prop, PropertyList)
        assert hasattr(prop, "key")
        assert hasattr(prop, "name")
        assert isinstance(prop.name, dict)


def test_get_property_doc_scoville():
    """Test getting specific property documentation."""
    prop = property_loader.get_property_doc("scoville_scale")
    assert prop is not None
    assert prop.key == "scoville_scale"
    assert "en" in prop.name
    assert prop.name["en"] == "Scoville Scale"
    assert prop.icon == "🌶️"
    assert prop.value_type == "number"
    assert prop.unit == "SHU"
    assert prop.permitted_values is not None
    assert len(prop.permitted_values) > 0
    assert prop.input_widget is not None
    assert prop.input_widget["type"] == "slider"
    assert prop.knowledge_panel is not None


def test_get_property_doc_storage_capacity():
    """Test getting storage_capacity property."""
    prop = property_loader.get_property_doc("storage_capacity")
    assert prop is not None
    assert prop.key == "storage_capacity"
    assert prop.value_type == "enum"
    assert prop.images is not None
    assert "16GB" in prop.images


def test_get_property_doc_organic():
    """Test getting organic property."""
    prop = property_loader.get_property_doc("organic")
    assert prop is not None
    assert prop.key == "organic"
    assert prop.value_type == "boolean"
    assert prop.icon == "🌱"


def test_get_property_doc_not_found():
    """Test getting non-existent property."""
    prop = property_loader.get_property_doc("nonexistent_property")
    assert prop is None


def test_get_property_knowledge_panel():
    """Test getting knowledge panel configuration."""
    panel = property_loader.get_property_knowledge_panel("scoville_scale")
    assert panel is not None
    assert "panel_id" in panel
    assert panel["panel_id"] == "scoville_scale"
    assert "property_key" in panel
    assert panel["property_key"] == "scoville_scale"
    assert "property_name" in panel
    assert "property_icon" in panel


def test_get_property_knowledge_panel_not_found():
    """Test getting knowledge panel for non-existent property."""
    panel = property_loader.get_property_knowledge_panel("nonexistent_property")
    assert panel is None


def test_search_properties_by_name():
    """Test searching properties by name."""
    results = property_loader.search_properties("scoville", "en")
    assert isinstance(results, list)
    assert len(results) > 0
    keys = [p.key for p in results]
    assert "scoville_scale" in keys


def test_search_properties_by_tag():
    """Test searching properties by tag."""
    results = property_loader.search_properties("spicy", "en")
    assert isinstance(results, list)
    # Should find properties tagged with 'spicy'
    if results:
        keys = [p.key for p in results]
        assert "scoville_scale" in keys


def test_property_multilingual_support():
    """Test that properties support multiple languages."""
    prop = property_loader.get_property_doc("organic")
    assert prop is not None
    # Check multilingual name
    assert "en" in prop.name
    assert "fr" in prop.name
    assert "es" in prop.name
    assert "de" in prop.name
    # Check multilingual description
    assert "en" in prop.description
    assert "fr" in prop.description


def test_property_wikidata_links():
    """Test that properties include Wikidata links."""
    prop = property_loader.get_property_doc("scoville_scale")
    assert prop is not None
    assert prop.wikidata_property == "P5196"
    assert prop.wikidata_url is not None
    assert "wikidata.org" in prop.wikidata_url


def test_property_input_widget_types():
    """Test different input widget types."""
    # Slider widget
    scoville = property_loader.get_property_doc("scoville_scale")
    assert scoville.input_widget["type"] == "slider"
    assert "min" in scoville.input_widget
    assert "max" in scoville.input_widget

    # Select widget
    storage = property_loader.get_property_doc("storage_capacity")
    assert storage.input_widget["type"] == "select"

    # Multiselect widget
    allergen = property_loader.get_property_doc("allergen_free")
    assert allergen.input_widget["type"] == "multiselect"


def test_property_examples():
    """Test that properties include usage examples."""
    prop = property_loader.get_property_doc("caffeine_content")
    assert prop is not None
    assert prop.examples is not None
    assert isinstance(prop.examples, list)
    assert len(prop.examples) > 0
    # Check example structure
    example = prop.examples[0]
    assert "value" in example
    assert "description" in example
    assert isinstance(example["description"], dict)


def test_property_categories():
    """Test that properties include category information."""
    prop = property_loader.get_property_doc("scoville_scale")
    assert prop is not None
    assert prop.categories is not None
    assert isinstance(prop.categories, list)
    assert len(prop.categories) > 0
    assert "en:spices" in prop.categories


def test_property_permitted_values_multilingual():
    """Test that permitted values support multilingual labels."""
    prop = property_loader.get_property_doc("organic")
    assert prop is not None
    assert prop.permitted_values is not None
    for value in prop.permitted_values:
        assert "value" in value
        assert "label" in value
        assert isinstance(value["label"], dict)
        assert "en" in value["label"]
