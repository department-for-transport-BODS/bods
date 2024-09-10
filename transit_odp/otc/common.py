import re
from typing import List


def process_brackets(text: str) -> List:
    """Get the processed string based on paranthesis

    Args:
        text (str): input string with brackets

    Returns:
        List
    """
    if text.count("(") == 1:
        prefix, suffix = text.split("(", 1)
        if "," not in suffix:
            return [text]
        suffix = suffix.rstrip(")")
        parts = [f"{prefix.strip()} {part.strip()}" for part in suffix.split(",")]
        return parts
    elif text.count("(") > 1:
        first_part = text.split("(", 1)[0].strip()
        parts = re.split(r"(\(.*?\))", text)
        result = []
        for part in parts:
            if part.startswith("(") and part.endswith(")"):
                result.append(part)
            else:
                if "(" in part:
                    segments = re.split(r"(\(.*?\))", part)
                    for seg in segments:
                        if seg.startswith("(") and seg.endswith(")"):
                            text_before_bracket = part.split(seg)[0]
                            result.append(f"{text_before_bracket}{seg}")
                        else:
                            result.append(seg)
        final_result = []
        for item in result:
            if item.startswith("(") and item.endswith(")"):
                final_result.append(f"{first_part} {item}")
            else:
                final_result.append(item)
        return final_result
    else:
        return text


def process_service_number(string: str) -> List:
    """
    Evaluate a given service number based on different operators |, parantheses, ",", " ", ":"
    and return a single

    If a string starts with digit and has characters in it then it should be kept as it is
    If a string starts with digit and has only numeric values then it should be parsed like
    other strings
    E.g.
    192 Rural Rider -> will stay as it is
    33 66 -> will be parsed and changed to 33|66

    Args:
        string (str): string to be processed

    Returns:
        List: List of service numbers after processing
    """
    if not string:
        return []

    if "(" in string or ")" in string:
        return process_brackets(string)
    else:
        delimiters = [",", ":", "-", "|"]
        if string[0].isdigit():
            if (
                has_only_space_delimiter(string)
                and not string.replace(" ", "").isdigit()
            ):
                return [string]
            delimiters.append(" ")
        regex_pattern = "|".join(map(re.escape, delimiters))
        return re.split(regex_pattern, string)


def has_only_space_delimiter(s):
    delimiters = [",", ":", "-", "|"]
    return " " in s and all(d not in s for d in delimiters)


def format_service_number(service_number: str, other_service_number: str) -> str:
    """Get unique service numbers seprated with | by handling parantheses

    Excel (A,B,C) -> Excel A|Excel B|Excel C
    418 (418W)(418R) -> 418 (418W)|418 (418R)
    ("192 Rural Rider", "193 Rural Rider") -> 192 Rural Rider|193 Rural Rider

    Args:
        service_number (str): service_number value
        other_service_number (str): other_service_number value

    Returns:
        str: evaluated string
    """
    service_list = other_service_list = []
    if service_number:
        service_list = process_service_number(service_number)
    if other_service_number:
        other_service_list = process_service_number(other_service_number)

    combined_list = list(service_list + other_service_list)

    if len(combined_list) == 0:
        return ""

    unique_list = []
    unique_list_lowercase = []
    for item in combined_list:
        item = item.strip()
        if item and item.lower() not in unique_list_lowercase:
            unique_list.append(item)
            unique_list_lowercase.append(item.lower())
    return "|".join(unique_list)
