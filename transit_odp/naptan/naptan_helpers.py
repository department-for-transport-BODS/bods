import os


# Get the directory of the 'latest' naptan download
def latest_naptan(naptan_base_dir: str) -> str:
    # Read the contents of 'latest' and build the download path
    download_path = naptan_base_dir
    latest = open(os.path.join(download_path, "latest"), "r").read().strip()
    download_path = os.path.join(download_path, latest + "/")

    return download_path
