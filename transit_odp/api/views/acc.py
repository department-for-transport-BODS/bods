import json
import os
from django.http import JsonResponse
import logging

from accessibility.index import generate_html_from_json

logger = logging.getLogger("django")


def write_acc(request) -> JsonResponse:
    data = request.POST.get("violation")
    url = request.POST.get("url")
    data = json.loads(data)
    options = {
        "doNotCreateReportFile": False,
        "reportFileName": "index.html",
        "outputDirPath": "transit_odp/frontend/static",
        "outputDir": "report/",
        "rules": {},
    }
    filepath = os.path.abspath("accessibility/report/report.json")
    if "violations" in data and data["violations"]:
        add_violations(file_path=filepath, new_data=data, url=url)
    generate_html_from_json(directory="accessibility/report/", options=options)
    return JsonResponse(data=data, safe=False)


def add_violations(file_path, new_data, url):
    # Load the existing data
    with open(file_path, "r") as file:
        data = json.load(file)

    data = insert_new_data(old_data=data, new_data=new_data, key="violations", path=url)
    data = insert_new_data(
        old_data=data, new_data=new_data, key="inapplicable", path=url
    )
    data = insert_new_data(old_data=data, new_data=new_data, key="incomplete", path=url)
    data["toolOptions"] = new_data["toolOptions"]
    data["timestamp"] = new_data["timestamp"]
    data["testEngine"] = new_data["testEngine"]

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def insert_new_data(old_data, new_data, key, path):
    if key in new_data:
        for new_item in new_data[key]:
            if not is_duplicate(new_item=new_item, old_data=old_data, key=key, path=path):
                old_data[key].append(new_item)
    return old_data


def is_duplicate(new_item, old_data, key, path):
    new_item["path"] = path
    new_value_str = json.dumps(new_item, sort_keys=True)
    return any([new_value_str== json.dumps(old_item, sort_keys=True) for old_item in old_data[key]])
