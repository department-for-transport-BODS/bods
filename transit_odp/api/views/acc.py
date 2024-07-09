import json
import os
from django.http import JsonResponse
import logging

from accessibility.index import generate_html_from_json

logger = logging.getLogger("django")


def write_acc(request) -> JsonResponse:
    # logger.info(request.POST.get("violation"))
    data = request.POST.get("violation")
    url = request.POST.get("url")
    data = json.loads(data)
    name = (
        "accessibility/report/"
        + url.replace("http://", "").replace("https://", "").replace("/", "_")
        + ".json"
    )
    options = {
        "doNotCreateReportFile": False,
        "reportFileName": "index.html",
        "outputDirPath": "transit_odp/frontend/static",
        "outputDir": "report/",
    }
    if name:
        filepath = os.path.abspath(name)
    else:
        filepath = os.path.join(os.path.getcwd(), name)

    if "violations" not in data or not data["violations"]:
        try:
            os.remove(path=filepath)
        except FileNotFoundError:
            pass
    else:
        data = data["violations"]
        data[0].update({"path": url})
        with open(filepath, "w", encoding="utf8") as f:
            f.write(json.dumps(data, indent=4))

    generate_html_from_json(directory="accessibility/report/", options=options)
    return JsonResponse(data=data, safe=False)
