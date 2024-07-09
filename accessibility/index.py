import json
import logging
import os

import chevron

logging.basicConfig(level=logging.INFO)


def get_wcag_reference(tags):
    if "best-practice" in tags:
        return "Best practice"

    found_wcag_tags = [tag for tag in tags if "wcag" in tag]
    if found_wcag_tags:
        return ", ".join(found_wcag_tags)

    return ", ".join(tags)


def simplify_axe_result_for_summary(results):
    summary = []
    for result_index, result in enumerate(results):
        nodes = result["nodes"]
        description = result["description"]
        help_text = result["help"]
        rule_id = result["id"]
        tags = result["tags"]
        impact = result["impact"] or "n/a"
        node_count = len(nodes)

        summary.append(
            {
                "index": result_index + 1,
                "description": description,
                "id": rule_id,
                "help": help_text,
                "wcag": get_wcag_reference(tags),
                "tags": tags,
                "impact": impact,
                "nodes": node_count,
            }
        )

    return summary


def prepare_fix_summary(failure_summary, default_highlight):
    fix_summaries = []
    failure_summaries_split = failure_summary.split("\n\n")

    for summary in failure_summaries_split:
        fix_summary_split = summary.split("\n")

        if len(fix_summary_split) == 0:
            fix_summaries.append(default_highlight)
        else:
            highlight = fix_summary_split.pop(0)
            fix_summaries.append({"highlight": highlight, "list": fix_summary_split})

    return fix_summaries


def prepare_report_data(violations, passes=None, incomplete=None, inapplicable=None):
    passed_checks = simplify_axe_result_for_summary(passes) if passes else None
    incomplete_checks = (
        simplify_axe_result_for_summary(incomplete) if incomplete else None
    )
    inapplicable_checks = (
        simplify_axe_result_for_summary(inapplicable) if inapplicable else None
    )

    violations_total = sum(len(result["nodes"]) for result in violations)

    if len(violations) == 0:
        return {
            "violationsSummary": 'axe-core found <span class="badge badge-success bg-success">0</span> violations',
            "checksPassed": passed_checks,
            "checksIncomplete": incomplete_checks,
            "checksInapplicable": inapplicable_checks,
        }

    violations_summary = f'BODS accessability scanner found <span class="badge bg-danger">{violations_total}</span> violation{"s" if violations_total > 1 else ""}'

    violations_summary_table = simplify_axe_result_for_summary(violations)

    violations_details = []
    for issue_index, issue in enumerate(violations):
        nodes = issue["nodes"]
        impact = issue["impact"] or "n/a"
        description = issue["description"]
        help_text = issue["help"]
        rule_id = issue["id"]
        tags = issue["tags"]
        help_url = issue["helpUrl"]
        path = issue["path"]

        nodes_data = []
        for node_index, node in enumerate(nodes):
            target_nodes = "\n".join(node["target"])
            html = node["html"]
            failure_summary = "failureSummary" in node and node["failureSummary"] or None
            any_nodes = node["any"]

            default_highlight = {
                "highlight": "Recommendation with the fix was not provided by axe result"
            }
            fix_summaries = (
                prepare_fix_summary(failure_summary=failure_summary, default_highlight=default_highlight)
                if failure_summary
                else [default_highlight]
            )

            related_nodes_any = []
            for check_result in any_nodes:
                related_nodes = check_result["relatedNodes"]
                for related_node in related_nodes:
                    if related_node["target"]:
                        related_nodes_any.append("\n".join(related_node["target"]))

            nodes_data.append(
                {
                    "targetNodes": target_nodes,
                    "html": html,
                    "fixSummaries": fix_summaries,
                    "relatedNodesAny": related_nodes_any,
                    "index": node_index + 1,
                }
            )

        violations_details.append(
            {
                "index": issue_index + 1,
                "wcag": get_wcag_reference(tags),
                "tags": tags,
                "id": rule_id,
                "impact": impact,
                "description": description,
                "help": help_text,
                "helpUrl": help_url,
                "path": path,
                "nodes": nodes_data,
            }
        )

    return {
        "violationsSummary": violations_summary,
        "violationsSummaryTable": violations_summary_table,
        "violationsDetails": violations_details,
        "checksPassed": passed_checks,
        "checksIncomplete": incomplete_checks,
        "checksInapplicable": inapplicable_checks,
    }


def save_html_report(
    html_content,
    report_file_name="result.html",
    output_dir="artifacts",
    output_dir_path=os.getcwd(),
):
    try:
        report_directory = os.path.join(output_dir_path, output_dir)
        os.makedirs(report_directory, exist_ok=True)

        report_file_path = os.path.join(report_directory, report_file_name)
        try:
            os.remove(report_file_path)
        except FileNotFoundError:
            pass
        with open(report_file_path, "w", encoding="utf8") as file:
            file.write(html_content)

        print(f"HTML report was saved into the following directory: {report_file_path}")
    except Exception as e:
        print(f"Error happened while trying to save html report: {e}")


def prepare_axe_rules(rules):
    reformatted_rules = []
    for index, rule_id in enumerate(rules.keys()):
        reformatted_rules.append(
            {"index": index + 1, "rule": rule_id, "enabled": rules[rule_id]["enabled"]}
        )

    return reformatted_rules


def create_html_report(results, options=None):
    if "violations" not in results:
        raise ValueError("'violations' is required for HTML accessibility report.")

    try:
        template_path = os.path.join(os.path.dirname(__file__), "template.html")

        prepared_report_data = prepare_report_data(
            violations=results["violations"],
            passes=results.get("passes"),
            incomplete=results.get("incomplete"),
            inapplicable=results.get("inapplicable"),
        )
        with open(template_path, mode="r", encoding="utf8") as file:
            html_content = chevron.render(
                template=file.read(),
                data={
                    "url": results.get("url"),
                    "path": results.get("path"),
                    "violationsSummary": prepared_report_data.get("violationsSummary") or "violationsSummary",
                    "violations": prepared_report_data.get("violationsSummaryTable"),
                    "violationDetails": prepared_report_data.get("violationsDetails"),
                    "checksPassed": prepared_report_data.get("checksPassed"),
                    "checksIncomplete": prepared_report_data.get("checksIncomplete"),
                    "checksInapplicable": prepared_report_data.get(
                        "checksInapplicable"
                    ),
                    "hasPassed": bool(results.get("passes")),
                    "hasIncomplete": bool(results.get("incomplete")),
                    "hasInapplicable": bool(results.get("inapplicable")),
                    "incompleteTotal": prepared_report_data.get("checksIncomplete")
                    and len(prepared_report_data.get("checksIncomplete"))
                    or 0,
                    "rules": prepare_axe_rules(rules=options.get("rules")),
                },
            )

        if options and options.get("doNotCreateReportFile") is True:
            print(
                "Report file will not be created because user passed options.doNotCreateReportFile = True. Use HTML output of the function to create report file"
            )
        else:
            save_html_report(
                html_content=html_content,
                report_file_name=options.get("reportFileName")
                if options
                else "template.html",
                output_dir=options.get("outputDir") if options else "artifacts",
                output_dir_path=options.get("outputDirPath")
                if options
                else os.getcwd(),
            )

        return html_content
    except Exception as e:
        logging.error(e, exc_info=True)
        return f"Failed to create HTML report due to an error: {e}"


def generate_html_from_json(directory,options=None):
    with open("accessibility/report/report.json", "r") as json_file:
        data=json.load(json_file)
        create_html_report(results=data,options=options)
