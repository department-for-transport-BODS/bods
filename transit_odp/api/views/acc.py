import json
import os
from django.http import JsonResponse
import logging

logger = logging.getLogger("django")

def report(violations):
    """
    Return readable report of accessibility violations found.

    :param violations: Dictionary of violations.
    :type violations: dict
    :return report: Readable report of violations.
    :rtype: string
    """
    string = ""
    string += "Found " + str(len(violations)) + " accessibility violations:"
    for violation in violations:
        string += (
            "\n\n\nRule Violated:\n"
            + violation["id"]
            + " - "
            + violation["description"]
            + "\n\tURL: "
            + violation["helpUrl"]
            + "\n\tImpact Level: "
            + violation["impact"]
            + "\n\tTags:"
        )
        for tag in violation["tags"]:
            string += " " + tag
        string += "\n\tElements Affected:"
        i = 1
        for node in violation["nodes"]:
            for target in node["target"]:
                string += "\n\t" + str(i) + ") Target: " + target
                i += 1
            for item in node["all"]:
                string += "\n\t\t" + item["message"]
            for item in node["any"]:
                string += "\n\t\t" + item["message"]
            for item in node["none"]:
                string += "\n\t\t" + item["message"]
        string += "\n\n\n"
    return string

def write_acc(request) -> JsonResponse:
    # logger.info(request.POST.get("violation"))
    data = request.POST.get("violation")
    name = request.POST.get("url")
    logger.error(name)
    data = json.loads(data)
    logger.error(data)
    data[0].update({"path": name})
    name = (
        "report/"
        + name.replace("http://", "")
        .replace("https://", "")
        .replace("/", "_")
        + ".json"
    )
    if name:
        filepath = os.path.abspath(name)
    else:
        filepath = os.path.join(os.path.getcwd(), name)

    with open(filepath, "w", encoding="utf8") as f:
        try:
            f.write(json.dumps(data, indent=4))
        except NameError:
            f.write(json.dumps(data, indent=4))
    return JsonResponse(data=data, safe=False)
