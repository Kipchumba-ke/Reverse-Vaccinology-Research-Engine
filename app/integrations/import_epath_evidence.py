"""Import ePath experimental essentiality data into the local SQLite index."""

import argparse
import csv
import sqlite3
from pathlib import Path


DEFAULT_DATA_DIR = Path("data/reference/essentiality")

SUMMARY_COLUMNS = {
    "Experimental EG(*)",
    "Missing EG(o)",
    "Experimental Not EG(x)",
    "Not Present(-)",
}


def import_epath_evidence(
    database_path: Path,
    data_dir: Path,
) -> tuple[int, int]:
    database_path = database_path.expanduser().resolve()
    data_dir = data_dir.expanduser().resolve()

    combined_path = data_dir / "Combined_KOExpEG.txt"
    experimental_path = data_dir / "Experimental_EG.txt"

    for path in (database_path, combined_path, experimental_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required file not found: {path}")

    connection = sqlite3.connect(database_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS epath_ko_essentiality (
                ko_id TEXT NOT NULL,
                organism_abbreviation TEXT NOT NULL,
                symbol TEXT NOT NULL CHECK (symbol IN ('*', 'x', 'o', '-')),
                PRIMARY KEY (ko_id, organism_abbreviation)
            );

            CREATE INDEX IF NOT EXISTS idx_epath_ko_essentiality_org
            ON epath_ko_essentiality (organism_abbreviation, symbol);

            CREATE TABLE IF NOT EXISTS epath_experimental_records (
                organism_abbreviation TEXT PRIMARY KEY,
                organism TEXT NOT NULL,
                essential_gene_count INTEGER NOT NULL,
                screen_condition TEXT,
                reference TEXT
            );
            """
        )

        # Import KO-level symbols, keeping only the 31 organism columns.
        with combined_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            reader = csv.reader(source, delimiter="\t")
            header = next(reader)

            if not header or header[0].strip() != "KO":
                raise ValueError("Unexpected Combined_KOExpEG header.")

            organism_columns = [
                (index, name.strip())
                for index, name in enumerate(header[1:], start=1)
                if name.strip() not in SUMMARY_COLUMNS
            ]

            if len(organism_columns) != 31:
                raise ValueError(
                    f"Expected 31 organism columns; found "
                    f"{len(organism_columns)}."
                )

            if len(header) != 36:
                raise ValueError(
                    f"Expected 36 total columns; found {len(header)}."
                )

            connection.execute("DELETE FROM epath_ko_essentiality")

            batch = []
            ko_count = 0

            for line_number, row in enumerate(reader, start=2):

                if not row:
                    continue

                if len(row) != len(header):
                    raise ValueError(
                        f"Line {line_number}: expected {len(header)} "
                        f"columns, found {len(row)}."
                    )

                # ePath appends a single explanatory note after the KO records.
                # It is metadata, not an essentiality data row.
                if row and row[0].strip().startswith("Note: Experimental EG("):
                    continue

                ko_id = row[0].strip()
                if not ko_id:
                    raise ValueError(f"Missing KO identifier on line {line_number}.")

                for index, abbreviation in organism_columns:
                    symbol = row[index].strip()

                    if symbol not in {"*", "x", "o", "-"}:
                        raise ValueError(
                            f"Unexpected symbol {symbol!r} for {ko_id}, "
                            f"organism {abbreviation}, line {line_number}."
                        )

                    batch.append((ko_id, abbreviation, symbol))

                if len(batch) >= 5000:
                    connection.executemany(
                        """
                        INSERT INTO epath_ko_essentiality
                        (ko_id, organism_abbreviation, symbol)
                        VALUES (?, ?, ?)
                        """,
                        batch,
                    )
                    batch.clear()

                ko_count += 1

            if batch:
                connection.executemany(
                    """
                    INSERT INTO epath_ko_essentiality
                    (ko_id, organism_abbreviation, symbol)
                    VALUES (?, ?, ?)
                    """,
                    batch,
                )

        # Import organism-level experimental metadata.
        with experimental_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            reader = csv.DictReader(source, delimiter="\t")

            required = {
                "Organism",
                "Abbr",
                "EG#",
                "Screen Condition",
                "Reference",
            }

            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                raise ValueError(
                    f"Unexpected Experimental_EG columns: {reader.fieldnames}"
                )

            connection.execute("DELETE FROM epath_experimental_records")

            records = []
            for line_number, row in enumerate(reader, start=2):
                abbreviation = (row.get("Abbr") or "").strip()
                organism = (row.get("Organism") or "").strip()
                count_text = (row.get("EG#") or "").strip()

                if not abbreviation or not organism or not count_text:
                    raise ValueError(
                        f"Missing required metadata on line {line_number}."
                    )

                records.append(
                    (
                        abbreviation,
                        organism,
                        int(count_text),
                        (row.get("Screen Condition") or "").strip(),
                        (row.get("Reference") or "").strip(),
                    )
                )

            connection.executemany(
                """
                INSERT INTO epath_experimental_records
                (
                    organism_abbreviation,
                    organism,
                    essential_gene_count,
                    screen_condition,
                    reference
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                records,
            )

        connection.commit()

        return ko_count, len(records)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import ePath experimental essentiality evidence."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATA_DIR / "epath.sqlite3",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
    )
    args = parser.parse_args()

    ko_count, organism_count = import_epath_evidence(
        args.database,
        args.data_dir,
    )

    print(f"Imported {ko_count:,} KO records.")
    print(f"Imported {organism_count:,} experimental organism records.")
    print(f"Database: {args.database.resolve()}")


if __name__ == "__main__":
    main()