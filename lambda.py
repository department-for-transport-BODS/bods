import os
import csv
import logging
from datetime import datetime, timezone

import xml.etree.ElementTree as ET
import boto3
import psycopg2
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database using environment variables.
    Returns:
        psycopg2.connection: Database connection object.
    """
    logger.info("Establishing database connection...")
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=25432,
            dbname="abods",
            user="brahma_ro",
            password="zS7O5il4RJ",
        )
        logger.info("Database connection established.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def fetch_noc_mapping():
    """
    Fetches the NOC mapping from the Traveline API.
    Returns:
        tuple: (mapping dict of Licence -> NOCCODE, error message or None)
    """
    url = "https://www.travelinedata.org.uk/noc/api/1.0/nocrecords.xml"
    logger.info("Fetching NOC mapping from Traveline API...")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        mapping = {}
        for record in root.findall(".//NocRecord"):
            noc = record.findtext("NOCCODE")
            licence = record.findtext("Licence")
            if noc and licence:
                mapping[licence.strip()] = noc.strip()
        logger.info("Fetched %d NOC mappings.", len(mapping))
        return mapping, None
    except (requests.RequestException, ET.ParseError) as e:
        logger.error(f"ERROR: Could not fetch Traveline NOC API: {e}")
        return {}, str(e)

def run_dashboard_query(cur, date_of_journey):
    """
    Executes the dashboard SQL query for the given date_of_journey.
    Args:
        cur (psycopg2.cursor): Database cursor.
        date_of_journey (str): Date string in 'YYYY-MM-DD' format.
    Returns:
        tuple: (rows, column names)
    """
    logger.info(f"Running dashboard query for date: {date_of_journey}")
    sql = """
    WITH filtered_timetable AS (
      SELECT DISTINCT
        date_of_journey,
        operator_noc,
        line_name,
        direction,
        journey_code
      FROM "Timetable"
      WHERE date_of_journey = %s
        AND incomplete_reason NOT IN (1, 2)
        AND registered = 'True'
        AND previous_group_id IS NULL
    ),
    filtered_journey_refs AS (
      SELECT
        sv.date_of_journey,
        sv.operator_ref,
        sv.line_name,
        sv.direction_ref,
        STRING_AGG(DISTINCT sv.journey_ref, ', ') AS journey_ref
      FROM "SiriVMPositions" sv
      LEFT JOIN filtered_timetable ft
        ON sv.date_of_journey = ft.date_of_journey
        AND sv.operator_ref = ft.operator_noc
        AND sv.line_name = ft.line_name
        AND sv.direction_ref = ft.direction
        AND sv.journey_ref = ft.journey_code
      WHERE sv.date_of_journey = %s
        AND sv.journey_ref IS NOT NULL
        AND ft.journey_code IS NULL
      GROUP BY
        sv.date_of_journey,
        sv.operator_ref,
        sv.line_name,
        sv.direction_ref
    ),
    operator_lookup AS (
        SELECT DISTINCT
            operator_noc,
            operator_name
        FROM expected_operators
        WHERE date_of_journey = %s
    ),
    lta_lookup as (
        SELECT DISTINCT
         SPLIT_PART(es.noc_and_line_and_servicecode, '-', 1) AS operator_noc,
         SPLIT_PART(es.noc_and_line_and_servicecode, '-', 2) AS line_name,
         SPLIT_PART(es.noc_and_line_and_servicecode, '-', 3) AS service_code,
         ul.name AS local_transport_authority
        FROM expected_services es
        JOIN naptan_adminarea na ON na.id = ANY(es.admin_area_id)
        JOIN ui_lta ul ON na.ui_lta_id = ul.id
        WHERE es.date_of_journey = %s)
    SELECT DISTINCT
        t.date_of_journey,
        t.operator_noc,
        REPLACE(t.service_code, ':', '/') AS service_code,
        t.line_name,
        t.direction,
        t.journey_code,
        COALESCE(
            CASE t.incomplete_reason
                WHEN 1 THEN 'Missing NOC in real-time data'
                WHEN 2 THEN 'Missing service in real-time data'
                WHEN 3 THEN 'Missing journey code in real-time data'
                WHEN 4 THEN 'Missing real-time data within the zone of a stop'
                WHEN 5 THEN 'Invalid real-time data within the zone of a stop'
                ELSE t.incomplete_reason::text
            END,
            t.incomplete_reason::text
        ) AS incomplete_reason_details,
        CASE
            WHEN t.incomplete_reason = 3 THEN fjr.journey_ref
            ELSE NULL
        END AS avl_journey_ref,
        ol.operator_name,
        ll.local_transport_authority
    FROM "Timetable" t
    LEFT JOIN filtered_journey_refs fjr
      ON t.incomplete_reason = 3
      AND t.date_of_journey = fjr.date_of_journey
      AND t.operator_noc = fjr.operator_ref
      AND t.line_name = fjr.line_name
      AND t.direction = fjr.direction_ref
    LEFT JOIN operator_lookup ol
        ON t.operator_noc = ol.operator_noc
    left join lta_lookup ll
        on t.operator_noc = ll.operator_noc
        and t.line_name = ll.line_name
        and t.service_code = ll.service_code
    WHERE t.date_of_journey = %s
      AND t.registered = 'True'
      AND t.incomplete_reason IS NOT NULL
      AND t.previous_group_id IS null
    """
    params = [date_of_journey] * 5
    cur.execute(sql, params)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    logger.info(f"Dashboard query returned {len(rows)} rows.")
    return rows, colnames

def add_registered_noc(rows, colnames, noc_mapping):
    """
    Adds a 'Registered NOC' column to the output, mapping registration:licence_number to NOCCODE.
    Args:
        rows (list): List of row data.
        colnames (list): List of column names.
        noc_mapping (dict): Licence to NOCCODE mapping.
    Returns:
        tuple: (output_rows, updated_colnames)
    """
    logger.info("Adding 'Registered NOC' column to output rows.")
    output_rows = []
    reg_lic_idx = (
        colnames.index("registration:licence_number")
        if "registration:licence_number" in colnames
        else None
    )
    txc_noc_idx = colnames.index("txc:noc") if "txc:noc" in colnames else None
    colnames = colnames + ["Registered NOC"]
    for row in rows:
        row = list(row)
        reg_noc = ""
        if reg_lic_idx is not None:
            reg_lic = row[reg_lic_idx]
            if reg_lic and reg_lic in noc_mapping:
                reg_noc = noc_mapping[reg_lic]
        if not reg_noc and txc_noc_idx is not None:
            reg_noc = row[txc_noc_idx] or ""
        row.append(reg_noc)
        output_rows.append(row)
    logger.info(f"Added 'Registered NOC' for {len(output_rows)} rows.")
    return output_rows, colnames

def write_csv(colnames, rows, filename):
    """
    Writes the provided rows and column names to a CSV file.
    Args:
        colnames (list): List of column names.
        rows (list): List of row data.
        filename (str): Path to the output CSV file.
    """
    logger.info(f"Writing output to CSV file: {filename}")
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(colnames)
        writer.writerows(rows)
    logger.info("CSV file writing complete.")

def upload_to_s3(local_path, bucket, key):
    """
    Uploads a file to an S3 bucket.
    Args:
        local_path (str): Local file path.
        bucket (str): S3 bucket name.
        key (str): S3 object key.
    """
    logger.info(f"Uploading {local_path} to s3://{bucket}/{key}")
    s3 = boto3.client("s3")
    s3.upload_file(local_path, bucket, key)
    logger.info("Upload to S3 complete.")

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    Orchestrates the process: fetches data, adds Registered NOC, writes CSV, uploads to S3.
    """
    S3_BUCKET = "bodds-prod-qs-source"
    DATE_OF_JOURNEY = "2025-05-10" #datetime.now(timezone.utc).strftime("%Y-%m-%d")
    csv_filename = f"incomplete_dashboard_{DATE_OF_JOURNEY}.csv"
    local_csv_path = f"./{csv_filename}"

    logger.info("Lambda handler started.")
    conn = get_db_connection()
    cur = conn.cursor()
    rows, colnames = run_dashboard_query(cur, DATE_OF_JOURNEY)
    noc_mapping, noc_error = fetch_noc_mapping()
    output_rows, colnames = add_registered_noc(rows, colnames, noc_mapping)
    write_csv(colnames, output_rows, local_csv_path)
    # upload_to_s3(local_csv_path, S3_BUCKET, csv_filename)
    cur.close()
    conn.close()
    logger.info("Database connection closed.")

    result = {
        "statusCode": 200,
        "body": f"Exported {len(rows)} rows to s3://{S3_BUCKET}/{csv_filename}",
    }
    if noc_error:
        logger.warning(f"NOC mapping error: {noc_error}")
        result["noc_error"] = noc_error
    logger.info("Lambda handler completed.")
    return result

if __name__ == "__main__":
    # For local testing, you can call the lambda_handler directly
    event = {}
    context = {}
    print(lambda_handler(event, context))
