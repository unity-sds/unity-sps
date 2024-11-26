#!/usr/share/cwl/venv/bin/python3

import argparse
import json

import yaml


def create_args():
    """Create and return argparser."""

    arg_parser = argparse.ArgumentParser(description="Retrieve entrypoint utilities arguments")
    arg_parser.add_argument("-c", "--catalogjson", type=str, default="", help="Path to catalog JSON file")
    arg_parser.add_argument("-j", "--jobargs", type=str, default="", help="Process CWL job argument file")
    arg_parser.add_argument("-i", "--processinput", type=str, default="", help="Process input directory")
    arg_parser.add_argument(
        "-d", "--collectionid", type=str, default="", help="Process and stage out collection identifier"
    )
    return arg_parser


def update_catalog_json(catalog_json):
    """Remove extra root directory in catalog.json file."""

    with open(catalog_json) as jf:
        catalog_data = json.load(jf)

    for link in catalog_data["links"]:
        if link["rel"] == "root":
            link["href"] = "catalog.json"

    with open(catalog_json, "w") as jf:
        json.dump(catalog_data, jf, indent=2)


def update_process_job_args(job_args, process_input, collection_id):
    """Update job arguments with input directory."""

    with open(job_args) as fh:
        if job_args.endswith("yaml") or job_args.endswith("yml"):
            json_data = yaml.safe_load(fh)
        else:
            json_data = json.load(fh)
    json_data["input"] = {"class": "Directory", "path": process_input}
    json_data["output_collection"] = collection_id
    with open(job_args, "w") as jf:
        json.dump(json_data, jf)


if __name__ == "__main__":
    arg_parser = create_args()
    args = arg_parser.parse_args()
    if args.catalogjson:
        update_catalog_json(args.catalogjson)

    if args.jobargs:
        update_process_job_args(args.jobargs, args.processinput, args.collectionid)
