import re


def process_brackets(text):
    if text.count("(") == 1:
        prefix, suffix = text.split("(", 1)
        suffix = suffix.rstrip(")")
        parts = [f"{prefix.strip()} {part.strip()}" for part in suffix.split(",")]
        return parts
    elif text.count("(") > 1:
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
                else:
                    result.append(part)
        final_result = []
        for item in result:
            if item.startswith("(") and item.endswith(")"):
                final_result.extend(item[1:-1].split(","))
            else:
                final_result.append(item)
        return final_result
    else:
        return text


def process_string(string):
    if "|" in string:
        return string.split("|")
    elif "(" in string or ")" in string:
        return process_brackets(string)
    else:
        if any(
            char.isdigit()
            for char in string.replace(" ", "").replace(",", "").replace(":", "")
        ):
            delimiters = [",", " ", ":"]
            regex_pattern = "|".join(map(re.escape, delimiters))
            return re.split(regex_pattern, string)
        else:
            return [string]


def format_service_number(service_number, other_service_number):
    service_list = process_string(service_number)
    other_service_list = process_string(other_service_number)

    combined_list = list(dict.fromkeys((service_list + other_service_list)))
    combined_list.sort()

    unique_list = []
    unique_list_lowercase = []
    for item in combined_list:
        item = item.strip()
        if item and item.lower() not in unique_list_lowercase:
            unique_list.append(item)
            unique_list_lowercase.append(item.lower())
    return "|".join(unique_list)
