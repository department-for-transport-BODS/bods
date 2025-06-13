import os
import re
import logging

GOVUK_SCSS_ROOT = "node_modules/govuk-frontend/dist/govuk"
CUSTOM_SCSS_ROOT = "transit_odp/frontend/assets/sass"
PROJECT_ROOT = "transit_odp"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLOR_MAP = {
    "#5e2ca5": 'govuk-colour("bright-purple")',
    "#a463f2": 'govuk-colour("light-purple")',
    "#d5008f": 'govuk-colour("pink")',
    "#ff41b4": 'govuk-colour("pink")',
    "#ff80cc": 'govuk-colour("light-pink")',
    "#ffa3d7": 'govuk-colour("light-pink")',
    "#e7040f": 'govuk-colour("red")',
    "#ff4136": 'govuk-colour("red")',
    "#ff725c": 'govuk-colour("orange")',
    "#ff6300": 'govuk-colour("orange")',
    "#ffb700": 'govuk-colour("yellow")',
    "#fbf1a9": 'govuk-colour("yellow")',
    "#19a974": 'govuk-colour("green")',
    "#9eebcf": 'govuk-colour("light-green")',
    "#137752": 'govuk-colour("green")',
    "#001b44": 'govuk-colour("dark-blue")',
    "#00449e": 'govuk-colour("dark-blue")',
    "#357edd": 'govuk-colour("blue")',
    "#96ccff": 'govuk-colour("light-blue")',
    "#cdecff": 'govuk-colour("light-blue")',
    "#f6fffe": 'govuk-colour("light-grey")',
    "#e8fdf5": 'govuk-colour("light-green")',
    "#ffdfdf": 'govuk-colour("light-pink")',
    "#111": 'govuk-colour("black")',
    "#333": 'govuk-colour("dark-grey")',
    "#555": 'govuk-colour("mid-grey")',
    "#777": 'govuk-colour("mid-grey")',
    "#999": 'govuk-colour("mid-grey")',
    "#aaa": 'govuk-colour("light-grey")',
    "#ccc": 'govuk-colour("light-grey")',
    "#eee": 'govuk-colour("light-grey")',
    "#f4f4f4": 'govuk-colour("white")',
    "#ebebeb": 'govuk-colour("light-grey")',
    "#3b4151": 'govuk-colour("dark-grey")',
    "#f93e3e": 'govuk-colour("red")',
    "#fca130": 'govuk-colour("orange")',
    "#49cc90": 'govuk-colour("green")',
    "#50e3c2": 'govuk-colour("turquoise")',
    "#9012fe": 'govuk-colour("bright-purple")',
    "#0d5aa7": 'govuk-colour("blue")',
    "#00823b": 'govuk-colour("green")',
    "#7d8293": 'govuk-colour("mid-grey")',
    "#d3341c": 'govuk-colour("red")',
    "#62a03f": 'govuk-colour("green")',
    "#41444e": 'govuk-colour("dark-grey")',
    "#606060": 'govuk-colour("mid-grey")',
    "#909090": 'govuk-colour("mid-grey")',
    "#7d8492": 'govuk-colour("mid-grey")',
    "#f7f7f7": 'govuk-colour("light-grey")',
    "#e8e8e8": 'govuk-colour("light-grey")',
    "#feebeb": 'govuk-colour("light-pink")',
    "#ff0000": 'govuk-colour("red")',
    "#55a": 'govuk-colour("blue")',
}


def find_scss_files(root):
    logger.info("Scanning for SCSS files in %s...", root)
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(".scss"):
                yield os.path.join(dirpath, fname)


def extract_classes_from_scss(scss_path):
    """Extract all class selectors from a SCSS file."""
    logger.debug(f"Extracting classes from {scss_path}")
    with open(scss_path, "r", encoding="utf-8") as f:
        content = f.read()
    return set(re.findall(r"\.([a-zA-Z0-9_-]+)", content))


def find_project_files(root, exts=None):
    logger.info(f"Scanning for project files in {root} with extensions {exts}...")
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not exts or any(fname.endswith(ext) for ext in exts):
                yield os.path.join(dirpath, fname)


def replace_class_in_file(filepath, class_map):
    logger.debug(f"Processing file: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"Could not read file {filepath}: {e}")
        return False

    original_content = content
    for old, new in class_map.items():
        content = re.sub(rf"\.{old}(\b|(?=[\s\.:{{,[]))", f".{new}\\1", content)
        content = re.sub(
            rf'(\bclass\s*=\s*["\'][^"\']*)\b{old}\b',
            lambda m: m.group(1) + new,
            content,
        )
        content = re.sub(
            rf'([\'"])({old})([\'"])',
            lambda m: m.group(1)
            + (new if m.group(2) == old else m.group(2))
            + m.group(3),
            content,
        )

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Updated class names in {filepath}")
        return True
    return False


def replace_colors_in_file(filepath, color_map):
    logger.info(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original_content = content
    for pattern, replacement in color_map.items():
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        content= content.replace(pattern.lower()+"000", replacement)
    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Updated color codes in {filepath}")


def main():
    logger.info("Starting GOV.UK class migration process.")

    # 1. Extract GOV.UK classes
    # govuk_classes = set()
    # logger.info("Extracting GOV.UK classes...")
    # for scss_file in find_scss_files(GOVUK_SCSS_ROOT):
    #     govuk_classes.update(extract_classes_from_scss(scss_file))
    # logger.info(f"Found {len(govuk_classes)} GOV.UK classes.")

    # # 2. Extract custom classes
    custom_classes = set()
    custom_scss_files = list(find_scss_files(CUSTOM_SCSS_ROOT))
    logger.info("Extracting custom classes from SCSS files...")
    for scss_file in custom_scss_files:
        custom_classes.update(extract_classes_from_scss(scss_file))
    logger.info(f"Found {len(custom_classes)} custom classes.")

    # # 3. Find intersection
    # common_classes = custom_classes & govuk_classes
    # logger.info(f"Classes to replace with GOV.UK style: {common_classes}")

    # # 4. Build class map (custom -> govuk, but names are the same)
    # class_map = {cls: cls for cls in common_classes}

    # # 5. Replace in custom SCSS files
    # logger.info("Replacing class names in custom SCSS files...")
    # for scss_file in custom_scss_files:
    #     replace_class_in_file(scss_file, class_map)

    # # 6. Replace in all project files (HTML, JS, etc.)
    # text_exts = [".html", ".js", ".jsx", ".ts", ".tsx", ".py", ".txt", ".md"]
    # logger.info("Replacing class names in all project files...")
    # for filepath in find_project_files(PROJECT_ROOT, exts=text_exts):
    #     replace_class_in_file(filepath, class_map)

    # 7. Replace colors in custom SCSS files
    logger.info("Replacing color codes in custom SCSS files...")
    for scss_file in custom_scss_files:
        replace_colors_in_file(scss_file, COLOR_MAP)

    logger.info("Replacement complete.")


if __name__ == "__main__":
    main()
