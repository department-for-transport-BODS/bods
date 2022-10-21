import zipfile

from lxml import etree


def file_to_etree(file_obj):
    xml_file_list = []
    etree_obj_list = {}
    file_name = file_obj.name
    if file_name.endswith(".xml"):
        xmlschema_doc = etree.parse(file_obj)
        etree_obj_list[file_name] = xmlschema_doc
    elif file_name.endswith(".zip"):
        with zipfile.ZipFile(file_obj, "r") as zout:
            filenames = [name for name in zout.namelist() if name.endswith("xml")]
            for file_name in filenames:
                if not file_name.startswith("__"):
                    with zout.open(file_name) as xmlout:
                        xml_file_list.append(xmlout)
                        xmlschema_doc = etree.parse(xmlout)
                        etree_obj_list[file_name] = xmlschema_doc

    return etree_obj_list
