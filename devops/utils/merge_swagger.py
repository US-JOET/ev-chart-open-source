import os
import yaml
from deepdiff import DeepDiff

def get_base_swagger(base_file_path):
    if base_file_path is None:
        raise ValueError("Swagger path required.")

    base_swagger = {}

    if os.path.isfile(base_file_path):
        with open(base_file_path, "r", encoding="utf-8") as file:
            base_swagger = yaml.safe_load(file)
    else:
        raise ValueError(f"Path {base_file_path} does not exist")

    return base_swagger


def merge_paths(source_dict, new_dict):
    duplicate_paths = get_duplicate_keys(source_dict, new_dict)
    if len(duplicate_paths) > 0:
        for path in duplicate_paths:
            duplicate_methods = get_duplicate_keys(source_dict[path], new_dict[path])
            if len(duplicate_methods) > 0:
                # if same method but different implementation then throw error
                for method in duplicate_methods:
                    diff = DeepDiff(source_dict[path][method], new_dict[path][method])
                    if len(diff.values()) > 0:
                        raise ValueError(
                            "Duplicate Paths found where method implemented differently"
                        )
            else:
                # if different methods (get, post, put) merge
                merged_path = {**source_dict[path], **new_dict[path]}
                new_dict[path] = merged_path

    merged_dict = {**source_dict, **new_dict}

    return merged_dict


def merge_definitions(source_dict, new_dict):
    duplicates = get_duplicate_keys(source_dict, new_dict)
    if len(duplicates) > 0:
        for key in duplicates:
            diff = DeepDiff(source_dict[key], new_dict[key])
            if len(diff.values()) > 0:
                raise ValueError("Duplicate Model keys found with different values")
    merged_dict = {**source_dict, **new_dict}

    return merged_dict


def get_duplicate_keys(dict1, dict2):
    return set(dict1).intersection(dict2)


def merge_swagger_docs(file_paths, base_swagger):
    merged_swagger_dict = base_swagger
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as file:
            swagger_dict = yaml.safe_load(file)

            merged_paths = merge_paths(
                merged_swagger_dict["paths"], swagger_dict["paths"]
            )
            merged_defs = merge_definitions(
                merged_swagger_dict["definitions"], swagger_dict["definitions"]
            )

            merged_swagger_dict["paths"] = merged_paths
            merged_swagger_dict["definitions"] = merged_defs

    return merged_swagger_dict


def collect_swagger_docs(swagger_path):
    if swagger_path is None:
        raise ValueError("Swagger path required.")

    swagger_file_name = "swagger.yml"

    if os.path.isdir(swagger_path):
        file_path_list = []

        for root, dirs, files in os.walk(swagger_path): # pylint: disable=unused-variable
            for file in files:
                if file == swagger_file_name:
                    full_path = os.path.join(root, file)
                    file_path_list.append(full_path)

        if len(file_path_list) is 0:
            raise ValueError("No Swagger Documents Found.")
        return file_path_list
    else:
        raise ValueError(f"Directory {swagger_path} is not found.")


def create_mono_swagger(swagger_path, base_swagger_file, merged_swagger_file):
    swagger_files = collect_swagger_docs(swagger_path)
    base_swagger = get_base_swagger(base_swagger_file)
    mono_swagger_doc = merge_swagger_docs(swagger_files, base_swagger)

    with open(merged_swagger_file, "w+", encoding="utf-8") as output_file:
        yaml.dump(mono_swagger_doc, output_file, indent=2)

    return mono_swagger_doc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge swagger files")
    parser.add_argument(
        "--swagger-directory",
        required=True,
        help="location of the directory containing swagger files",
    )
    parser.add_argument(
        "--base-swagger-file", required=True, help="full path of the base swagger file"
    )
    parser.add_argument(
        "--output", required=True, help="file the output will be written to"
    )

    args = parser.parse_args()

    swagger_dict_result = create_mono_swagger(
        args.swagger_path, args.base_swagger_file, args.output
    )

    exit(swagger_dict_result)
