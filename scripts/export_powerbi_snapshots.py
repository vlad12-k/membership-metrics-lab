"""Export deterministic local Power BI CSV snapshots and KPI reconciliation evidence.

Credentials are read only from environment variables supplied by the caller.
This script requires the existing lightdash_reader role and enforces a read-only
repeatable-read transaction. No database writes or model changes are performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import psycopg2

EXPECTED_ROWS = {
    "mart_executive_kpis": 18,
    "mart_member_engagement": 95148,
    "mart_partner_performance": 2279,
    "mart_cohort_retention": 171,
}
EXPECTED_RECONCILIATION_ROWS = {
    **{f"KPI-{index:02d}": 18 for index in range(1, 10)},
    "KPI-10": 171,
    "XREF-05": 18,
}

TABLES = {
    "mart_executive_kpis": {
        "grain": "one row per reporting month",
        "time_semantics": "month_start is UTC calendar-month start; month_end_date is the inclusive UTC calendar date; snapshot values are non-additive over months.",
        "order_by": "month_start",
        "period_column": "month_start",
        "columns": [
            "month_start",
            "month_end_date",
            "is_complete_month",
            "total_registered_members",
            "eligible_members",
            "active_members_30d",
            "monthly_active_members",
            "offer_redemption_count",
            "eligible_member_offer_pairs",
            "redeemed_member_offer_pairs",
            "offer_redemption_rate",
            "active_partners_as_of_month_end",
            "partner_offer_available_count",
            "engaged_eligible_partner_count",
            "partner_engagement_rate",
            "members_with_redemption",
            "repeat_redeemers",
            "repeat_redemption_rate",
        ],
    },
    "mart_member_engagement": {
        "grain": "one row per member_id and month_start",
        "time_semantics": "registration_date and cohort_month are UTC business dates; month_start/month_end_date define the reporting calendar month; activity windows are UTC calendar dates.",
        "order_by": 'member_id COLLATE "C", month_start',
        "period_column": "month_start",
        "columns": [
            "member_id",
            "registration_date",
            "cohort_month",
            "month_start",
            "month_end_date",
            "is_complete_month",
            "is_eligible_as_of_month_end",
            "is_monthly_active",
            "is_active_30d_as_of_month_end",
            "qualifying_event_count",
            "qualifying_event_count_30d",
        ],
    },
    "mart_partner_performance": {
        "grain": "one row per partner_id and month_start",
        "time_semantics": "month_start is UTC calendar-month start and month_end_date is the inclusive UTC calendar date; partner availability and activity are evaluated within that month.",
        "order_by": 'partner_id COLLATE "C", month_start',
        "period_column": "month_start",
        "columns": [
            "partner_id",
            "category_id",
            "category_name",
            "month_start",
            "month_end_date",
            "is_active_as_of_month_end",
            "eligible_member_offer_pairs",
            "has_available_offer",
            "valid_redemption_count",
            "is_engaged_eligible_partner",
        ],
    },
    "mart_cohort_retention": {
        "grain": "one row per cohort_month and age_month",
        "time_semantics": "cohort_month is the UTC registration calendar month; age_month is relative calendar-month age; incomplete months have NULL retention rates.",
        "order_by": "cohort_month, age_month",
        "period_column": "cohort_month",
        "columns": [
            "cohort_month",
            "age_month",
            "cohort_size",
            "retained_members",
            "is_complete_month",
            "cohort_retention_rate",
        ],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_query(cursor, query: str, destination: Path) -> None:
    copy_sql = (
        "COPY (" + query.strip().rstrip(";") + ") "
        "TO STDOUT WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8')"
    )
    with destination.open("w", encoding="utf-8", newline="") as output:
        cursor.copy_expert(copy_sql, output)


def validate_csv(path: Path, expected_columns: list[str], expected_rows: int) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if header != expected_columns:
            raise RuntimeError(f"CSV header mismatch for {path.name}: {header!r}")
        actual_rows = sum(1 for _ in reader)
    if actual_rows != expected_rows:
        raise RuntimeError(
            f"CSV row-count mismatch for {path.name}: {actual_rows} != {expected_rows}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/powerbi/snapshots/2026-10-28"),
        help="Snapshot directory (default: data/powerbi/snapshots/2026-10-28)",
    )
    parser.add_argument(
        "--reconciliation-sql",
        type=Path,
        default=Path("docs/evidence/powerbi-kpi-reconciliation.sql"),
        help="Read-only SQL query used for KPI reconciliation",
    )
    args = parser.parse_args()

    password = os.environ.get("LIGHTDASH_WAREHOUSE_PASSWORD")
    if not password:
        parser.error("Set LIGHTDASH_WAREHOUSE_PASSWORD by sourcing the local .env.lightdash file")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    extraction_started = datetime.now(UTC)
    manifest = {
        "project": "Membership Metrics Lab",
        "data_classification": "synthetic; no real member or partner records",
        "extracted_at_utc": extraction_started.isoformat(timespec="seconds"),
        "database": {
            "host": os.environ.get("MML_DB_HOST", "127.0.0.1"),
            "port": int(os.environ.get("MML_DB_PORT", "54329")),
            "database": os.environ.get("MML_DB_NAME", "membership_metrics"),
            "role": "lightdash_reader",
            "transaction": "repeatable read, read only",
            "session_timezone": "UTC",
            "session_datestyle": "ISO, YMD",
        },
        "dbt_context": {
            "dbt_core": "1.12.6",
            "dbt_postgres": "1.11.0",
            "models": "locally validated G3 mart outputs; no model change performed",
        },
        "snapshots": {},
    }

    connection = psycopg2.connect(
        host=os.environ.get("MML_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("MML_DB_PORT", "54329")),
        dbname=os.environ.get("MML_DB_NAME", "membership_metrics"),
        user="lightdash_reader",
        password=password,
        connect_timeout=10,
        options="-c default_transaction_read_only=on -c TimeZone=UTC -c DateStyle=ISO,YMD",
    )
    try:
        connection.set_session(isolation_level="REPEATABLE READ", readonly=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_user, current_database(), current_setting('transaction_read_only')"
            )
            identity = cursor.fetchone()
            if identity is None:
                raise RuntimeError("Database identity query returned no row")
            role, database, read_only = identity
            if (role, database, read_only) != ("lightdash_reader", "membership_metrics", "on"):
                raise RuntimeError(
                    "Connected role/database/read-only state did not match the approved reader"
                )

            cursor.execute(
                "SELECT schema_name, has_schema_privilege(current_user, schema_name, 'USAGE') "
                "FROM (VALUES ('marts'), ('raw'), ('staging'), ('intermediate')) AS s(schema_name)"
            )
            schema_access = dict(cursor.fetchall())
            if schema_access != {
                "marts": True,
                "raw": False,
                "staging": False,
                "intermediate": False,
            }:
                raise RuntimeError(
                    f"Unexpected schema access for lightdash_reader: {schema_access!r}"
                )

            cursor.execute(
                "SELECT has_table_privilege(current_user, 'marts.' || table_name, 'SELECT'), "
                "has_table_privilege(current_user, 'marts.' || table_name, 'INSERT'), "
                "has_table_privilege(current_user, 'marts.' || table_name, 'UPDATE'), "
                "has_table_privilege(current_user, 'marts.' || table_name, 'DELETE') "
                "FROM information_schema.tables WHERE table_schema='marts' "
                "AND table_name = ANY(%s) ORDER BY table_name",
                (list(TABLES),),
            )
            privileges = cursor.fetchall()
            if len(privileges) != len(TABLES) or any(
                not can_select or can_insert or can_update or can_delete
                for can_select, can_insert, can_update, can_delete in privileges
            ):
                raise RuntimeError(f"Unexpected table privileges for reader: {privileges!r}")

            for table, details in TABLES.items():
                cursor.execute(
                    "SELECT column_name, data_type, udt_name, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema='marts' AND table_name=%s "
                    "ORDER BY ordinal_position",
                    (table,),
                )
                columns = [
                    {
                        "name": name,
                        "data_type": data_type,
                        "udt_name": udt_name,
                        "nullable": nullable == "YES",
                    }
                    for name, data_type, udt_name, nullable in cursor.fetchall()
                ]
                actual_column_names = [column["name"] for column in columns]
                if actual_column_names != details["columns"]:
                    raise RuntimeError(f"Schema drift for marts.{table}: {actual_column_names!r}")

                cursor.execute(
                    f"SELECT count(*), min({details['period_column']}), max({details['period_column']}) FROM marts.{table}"
                )
                period_summary = cursor.fetchone()
                if period_summary is None:
                    raise RuntimeError(f"No period summary returned for marts.{table}")
                row_count, first_period, last_period = period_summary
                if row_count != EXPECTED_ROWS[table]:
                    raise RuntimeError(
                        f"Unexpected source row count for marts.{table}: "
                        f"{row_count} != {EXPECTED_ROWS[table]}"
                    )

                destination = args.output_dir / f"{table}.csv"
                query = (
                    f"SELECT {', '.join(details['columns'])} FROM marts.{table} "
                    f"ORDER BY {details['order_by']}"
                )
                export_query(cursor, query, destination)
                validate_csv(destination, details["columns"], row_count)
                manifest["snapshots"][table] = {
                    "source_relation": f"marts.{table}",
                    "grain": details["grain"],
                    "time_semantics": details["time_semantics"],
                    "period_column": details["period_column"],
                    "period_min": first_period.isoformat() if first_period else None,
                    "period_max": last_period.isoformat() if last_period else None,
                    "row_count": row_count,
                    "columns": columns,
                    "schema_sha256": hashlib.sha256(
                        json.dumps(columns, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                    "csv_file": destination.name,
                    "csv_bytes": destination.stat().st_size,
                    "csv_sha256": sha256(destination),
                    "ordering": details["order_by"],
                    "csv_types_note": "CSV has no embedded types; PostgreSQL schema is recorded above and must be applied explicitly in Power BI.",
                }

            reconciliation_sql = args.reconciliation_sql.read_text(encoding="utf-8")
            reconciliation_path = args.output_dir / "kpi-reconciliation.csv"
            export_query(cursor, reconciliation_sql, reconciliation_path)

            report_rows = 0
            matched_rows = 0
            by_kpi: dict[str, dict[str, int]] = {}
            with reconciliation_path.open("r", encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    report_rows += 1
                    counts = by_kpi.setdefault(
                        row["kpi_id"], {"rows": 0, "matches": 0, "failures": 0}
                    )
                    counts["rows"] += 1
                    if row["matches"].lower() in {"true", "t", "1"}:
                        matched_rows += 1
                        counts["matches"] += 1
                    else:
                        counts["failures"] += 1
            if report_rows == 0:
                raise RuntimeError("KPI reconciliation returned no rows")
            if set(by_kpi) != set(EXPECTED_RECONCILIATION_ROWS):
                raise RuntimeError(
                    "KPI reconciliation ID set changed: "
                    f"{sorted(by_kpi)!r} != {sorted(EXPECTED_RECONCILIATION_ROWS)!r}"
                )
            for kpi_id, expected_count in EXPECTED_RECONCILIATION_ROWS.items():
                if by_kpi[kpi_id]["rows"] != expected_count:
                    raise RuntimeError(
                        f"Unexpected reconciliation row count for {kpi_id}: "
                        f"{by_kpi[kpi_id]['rows']} != {expected_count}"
                    )

            manifest["reconciliation"] = {
                "sql_file": str(args.reconciliation_sql),
                "csv_file": reconciliation_path.name,
                "row_count": report_rows,
                "matched_rows": matched_rows,
                "failed_rows": report_rows - matched_rows,
                "by_kpi_or_crosscheck": by_kpi,
                "csv_bytes": reconciliation_path.stat().st_size,
                "csv_sha256": sha256(reconciliation_path),
            }
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    manifest["completed_at_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Snapshot manifest: {manifest_path}")
    for table, details in manifest["snapshots"].items():
        print(f"{table}: {details['row_count']} rows sha256={details['csv_sha256']}")
    result = manifest["reconciliation"]
    print(
        f"KPI reconciliation: {result['matched_rows']}/{result['row_count']} matched; "
        f"{result['failed_rows']} failures; csv sha256={result['csv_sha256']}"
    )
    return 0 if result["failed_rows"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # emit bounded diagnostics without connection secrets
        print(f"snapshot export failed: {error}", file=sys.stderr)
        raise
