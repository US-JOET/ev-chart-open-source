import os
import tempfile

import pytest
import yaml

from devops.utils.merge_swagger import create_mono_swagger, get_base_swagger
from devops.utils.merge_swagger import merge_paths
from devops.utils.merge_swagger import merge_definitions
from devops.utils.merge_swagger import collect_swagger_docs


def test_merge_definitions_given_different_models_merge_both():
    json_model_1 = empty_model_dict["definitions"]
    json_model_2 = csvFileImport_model_dict["definitions"]

    result_dict = merge_definitions(json_model_1, json_model_2)

    assert len(result_dict) == 2
    assert "Empty" in result_dict
    assert "CsvFileImport" in result_dict


def test_merge_definitions_multiple_models_in_source_with_multiple_models_in_new():
    json_source = multi_model_1_dict["definitions"]
    json_new = multi_model_2_dict["definitions"]

    result_dict = merge_definitions(json_source, json_new)

    assert len(result_dict) == 4
    assert "Empty" in result_dict
    assert "Item1" in result_dict
    assert "Item2" in result_dict
    assert "Item3" in result_dict


def test_merge_definitions_duplicate_models_merge():
    json_source = multi_model_2_dict["definitions"]
    json_new = empty_model_dict["definitions"]

    result_dict = merge_definitions(json_source, json_new)

    assert len(result_dict) == 2
    assert "Empty" in result_dict
    assert "Item3" in result_dict


def test_merge_definitions_duplicate_model_keys_different_values_throws_error():
    json_source = empty_model_dict["definitions"]
    json_new = empty_model_different_dict["definitions"]
    with pytest.raises(ValueError) as raised_error:
        merge_definitions(json_source, json_new)
    assert (
        raised_error.value.args[0] == "Duplicate Model keys found with different values"
    )


def test_merge_paths_two_paths_merges():
    json_source = test_path_dict["paths"]
    json_new = hello_path_post_dict["paths"]

    result_dict = merge_paths(json_source, json_new)

    assert len(result_dict) == 2
    assert "/hello_world" in result_dict
    assert "/test" in result_dict


def test_merge_path_given_multiple_paths_to_start_add_new_merges():
    json_source = multi_path_dict["paths"]
    json_new = test_path_dict["paths"]

    result_dict = merge_paths(json_source, json_new)

    assert len(result_dict) == 3
    assert "/hello_world" in result_dict
    assert "/goodbye_world" in result_dict
    assert "/test" in result_dict


def test_merge_path_given_duplicate_return_only_1_of_the_duplicated_paths():
    json_source = multi_path_dict["paths"]
    json_new = hello_path_get_dict["paths"]

    result_dict = merge_paths(json_source, json_new)

    assert len(result_dict) == 2
    assert "/hello_world" in result_dict
    assert "/goodbye_world" in result_dict


def test_merge_path_duplicate_path_different_method_merges():
    json_source = hello_path_get_dict["paths"]
    json_new = hello_path_post_dict["paths"]

    result_dict = merge_paths(json_source, json_new)

    assert len(result_dict) == 1
    assert len(result_dict["/hello_world"]) == 2


def test_get_base_swagger_given_bad_file_path_raises_value_error():
    path = os.path.join("./tests/devops/utils/test_files/architechture/nothing.yml")
    with pytest.raises(ValueError) as raised_error:
        get_base_swagger(path)

    assert raised_error.value.args[0] == f"Path {path} does not exist"


def test_get_base_swagger_given_parameters_create_base_swagger_dict():
    base_path = os.path.join(
        "./tests/devops/utils/test_files/architechture/base_swagger.yml"
    )
    title = "TEST_API"
    version = "alpha"
    stage = "/dev"
    host = "test.us-east-1.amazonaws.com"

    result = get_base_swagger(base_path)

    assert result["swagger"] == "2.0"
    assert result["info"]["version"] == version
    assert result["info"]["title"] == title
    assert result["host"] == host
    assert result["basePath"] == stage
    assert result["schemes"] == ["https"]
    assert len(result["paths"]) == 0
    assert len(result["definitions"]) == 0


def test_collect_swagger_docs_given_path_with_no_docs_raise_error():
    path = os.path.join("./tests/devops/utils/test_files/empty")
    with pytest.raises(ValueError) as raised_error:
        collect_swagger_docs(path)

    assert raised_error.value.args[0] == "No Swagger Documents Found."


def test_collect_swagger_docs_given_bad_path_raise_error():
    path = "./bad_path"
    with pytest.raises(ValueError) as raised_error:
        collect_swagger_docs(path)

    assert raised_error.value.args[0] == f"Directory {path} is not found."


def test_collect_swagger_docs_given_null_path_raise_error():
    path = None
    with pytest.raises(ValueError) as raised_error:
        collect_swagger_docs(path)

    assert raised_error.value.args[0] == "Swagger path required."


def test_collect_swagger_docs_given_path_with_a_doc_return_doc():
    path = os.path.join("./tests/devops/utils/test_files/lambda_1")

    result = collect_swagger_docs(path)

    assert len(result) == 1


def test_collect_swagger_docs_given_path_with_multiple_docs_return_docs():
    path = os.path.join("./tests/devops/utils/test_files")

    result = collect_swagger_docs(path)

    assert len(result) == 2


def test_create_mono_swagger_happy_path():
    path = os.path.join("./tests/devops/utils/test_files")
    title = "TEST_API"
    version = "alpha"
    base_path = "/dev"
    host = "test.us-east-1.amazonaws.com"

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "swagger.yml")

        # create file inside the temporary directory
        base_swagger_yaml_path = os.path.join(temp_dir, "base_swagger.yml")
        convert_dict_to_yaml_file(base_swagger_dict, base_swagger_yaml_path)

        result = create_mono_swagger(path, base_swagger_yaml_path, output_file)
        assert result is not None
        assert os.path.exists(output_file)
        with open(output_file, "r", encoding="utf-8") as result_file:
            result2 = yaml.safe_load(result_file)
            assert result2["info"]["version"] == version
            assert result2["info"]["title"] == title
            assert result2["host"] == host
            assert result2["basePath"] == base_path

            swagger_defs2 = result2["definitions"]
            assert "Empty" in swagger_defs2
            assert "CsvImportStatus" in swagger_defs2
            assert "CsvFileImport" in swagger_defs2

            swagger_paths2 = result2["paths"]
            swagger_root_path2 = swagger_paths2["/"]
            assert "get" in swagger_root_path2
            assert "post" in swagger_root_path2

def convert_dict_to_yaml_file(dict_input, file_path):
    with open(file_path, "w+", encoding="utf-8") as file:
        yaml.dump(dict_input, file)


empty_model_dict = {
    "definitions": {"Empty": {"type": "object", "title": "Empty Schema"}}
}

csvFileImport_model_dict = {
    "definitions": {
        "CsvFileImport": {
            "type": "object",
            "properties": {
                "fileName": {"type": "string", "format": "binary"},
                "csv": {"type": "string"},
                "csv_content": {"type": "string"},
            },
            "title": "CsvImportModel",
        }
    }
}

multi_model_1_dict = {
    "definitions": {"Item1": {"type": "string"}, "Item2": {"type": "integer"}}
}

multi_model_2_dict = {
    "definitions": {
        "Empty": {"type": "object", "title": "Empty Schema"},
        "Item3": {"type": "integer"},
    }
}

empty_model_different_dict = {
    "definitions": {"Empty": {"type": "string", "title": "Empty String"}}
}

test_path_dict = {
    "paths": {
        "/test": {
            "post": {
                "consumes": ["multipart/form-data"],
                "produces": ["application/json"],
                "parameters": [
                    {
                        "in": "body",
                        "name": "CsvFileImport",
                        "required": True,
                        "schema": {"$ref": "#/definitions/CsvFileImport"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {"$ref": "#/definitions/Empty"},
                    }
                },
                "x-amazon-apigateway-integration": {
                    "type": "aws",
                    "httpMethod": "POST",
                    "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:414275662771:function:Josh_Test_Lambda/invocations",
                    "responses": {"default": {"statusCode": "200"}},
                    "passthroughBehavior": "when_no_match",
                    "contentHandling": "CONVERT_TO_TEXT",
                },
            }
        }
    }
}

test_path_diff_dict = {
    "paths": {
        "/test": {
            "post": {
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {"$ref": "#/definitions/Empty"},
                    }
                },
                "x-amazon-apigateway-integration": {
                    "type": "aws",
                    "httpMethod": "POST",
                    "uri": "",
                    "responses": {"default": {"statusCode": "200"}},
                    "passthroughBehavior": "when_no_match",
                    "contentHandling": "CONVERT_TO_TEXT",
                },
            }
        }
    }
}

hello_path_post_dict = {
    "paths": {
        "/hello_world": {
            "post": {
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "parameters": [
                    {
                        "in": "body",
                        "name": "HelloWorld",
                        "required": False,
                        "schema": {"$ref": "#/definitions/Empty"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {"$ref": "#/definitions/string"},
                    }
                },
                "x-amazon-apigateway-integration": {
                    "type": "aws",
                    "httpMethod": "POST",
                    "uri": "",
                    "responses": {"default": {"statusCode": "200"}},
                    "passthroughBehavior": "when_no_match",
                    "contentHandling": "CONVERT_TO_TEXT",
                },
            }
        }
    }
}

hello_path_get_dict = {
    "paths": {
        "/hello_world": {
            "get": {
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "parameters": [
                    {
                        "in": "body",
                        "name": "HelloWorld",
                        "required": False,
                        "schema": {"$ref": "#/definitions/Empty"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {"$ref": "#/definitions/string"},
                    }
                },
                "x-amazon-apigateway-integration": {
                    "type": "aws",
                    "httpMethod": "POST",
                    "uri": "",
                    "responses": {"default": {"statusCode": "200"}},
                    "passthroughBehavior": "when_no_match",
                    "contentHandling": "CONVERT_TO_TEXT",
                },
            }
        }
    }
}

multi_path_dict = {
    "paths": {
        "/hello_world": {
            "get": {
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "parameters": [
                    {
                        "in": "body",
                        "name": "HelloWorld",
                        "required": False,
                        "schema": {"$ref": "#/definitions/Empty"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {"$ref": "#/definitions/string"},
                    }
                },
                "x-amazon-apigateway-integration": {
                    "type": "aws",
                    "httpMethod": "POST",
                    "uri": "",
                    "responses": {"default": {"statusCode": "200"}},
                    "passthroughBehavior": "when_no_match",
                    "contentHandling": "CONVERT_TO_TEXT",
                },
            }
        },
        "/goodbye_world": {
            "get": {
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {"$ref": "#/definitions/string"},
                    }
                },
                "x-amazon-apigateway-integration": {
                    "type": "aws",
                    "httpMethod": "POST",
                    "uri": "",
                    "responses": {"default": {"statusCode": "200"}},
                    "passthroughBehavior": "when_no_match",
                    "contentHandling": "CONVERT_TO_TEXT",
                },
            }
        },
    }
}

base_swagger_dict = {
    "swagger": "2.0",
    "info": {"description": "Test", "version": "alpha", "title": "TEST_API"},
    "host": "test.us-east-1.amazonaws.com",
    "basePath": "/dev",
    "schemes": ["https"],
    "paths": {},
    "definitions": {},
}
