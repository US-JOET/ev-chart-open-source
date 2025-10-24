import pytest
from evchart_helper.module_enums import (
    Module1Attributes,
    Module2Attributes, 
    Module3Attributes,
    Module4Attributes, 
    Module5Attributes, 
    Module6Attributes, 
    Module7Attributes,
    Module8Attributes, 
    Module9Attributes, 
    get_module_class_name) 

from evchart_helper.custom_exceptions import EvChartJsonOutputError

def test_get_module_class_name_valid():
    class_names = []
    for x in range (1,10):
        class_names.append(get_module_class_name(x))
    
    expected = [Module1Attributes, Module2Attributes, Module3Attributes, Module4Attributes,
                Module5Attributes, Module6Attributes, Module7Attributes, Module8Attributes, 
                Module9Attributes
    ]
    
    assert class_names == expected
    
def test_invalid_module_number_for_getting_module_class_name():
    with pytest.raises(EvChartJsonOutputError):
        get_module_class_name(11)
            