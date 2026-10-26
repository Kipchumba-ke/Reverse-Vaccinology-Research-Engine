"""Build a local SQLite index from the ePath gene-to-KO reference table."""

import argparse
import csv
import sqlite3
from pathlib import Path


EXPECTED_COLUMNS = 7


def build_epath_index(source_path: Path, database_path: Path) -> int:
    """Build a SQLite index from a tab-separated ePath gene mapping file.

    Expected columns:
        organism, organism_abbreviation, gene_id, ko_id,
        annotation, score1, score2

    Rows are inserted in batches to avoid loading the full source into memory.
    The source file is never modified.
    """
    source_path = source_path.expanduser().resolve()
    database_path = database_path.expanduser().resolve()

    if not source_path.is_file():
        raise FileNotFoundError(
            f"ePath source file does not exist: {source_path}"
        )

    if source_path == database_path:
        raise ValueError("Source and database paths must be different.")

    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    count = 0
    batch_size = 5000

    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")

        connection.execute("DROP TABLE IF EXISTS epath_gene")

        connection.execute(
            """
            CREATE TABLE epath_gene (
                id INTEGER PRIMARY KEY,
                organism TEXT NOT NULL,
                organism_abbreviation TEXT NOT NULL,
                gene_id TEXT NOT NULL,
                ko_id TEXT NOT NULL,
                annotation TEXT NOT NULL,
                score1 TEXT,
                score2 TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_epath_gene_organism_gene
            ON epath_gene (organism_abbreviation, gene_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_epath_gene_organism_ko
            ON epath_gene (organism_abbreviation, ko_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_epath_gene_organism_name
            ON epath_gene (organism)
            """
        )

        insert_sql = """
            INSERT INTO epath_gene (
                organism,
                organism_abbreviation,
                gene_id,
                ko_id,
                annotation,
                score1,
                score2
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        batch = []

        with source_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as source:
            reader = csv.reader(source, delimiter="\t")

            for line_number, row in enumerate(reader, start=1):
                if not row or all(not value.strip() for value in row):
                    continue

                if len(row) != EXPECTED_COLUMNS:
                    raise ValueError(
                        f"Expected {EXPECTED_COLUMNS} columns on line "
                        f"{line_number}, found {len(row)}."
                    )

                organism, abbreviation, gene_id, ko_id, annotation, score1, score2 = (
                    value.strip() for value in row
                )

                if not organism or not abbreviation or not gene_id:
                    raise ValueError(
                        f"Missing required organism, abbreviation, or gene ID "
                        f"on line {line_number}."
                    )

                batch.append(
                    (
                        organism,
                        abbreviation,
                        gene_id,
                        ko_id,
                        annotation,
                        score1,
                        score2,
                    )
                )

                if len(batch) >= batch_size:
                    connection.executemany(insert_sql, batch)
                    count += len(batch)
                    batch.clear()

            if batch:
                connection.executemany(insert_sql, batch)
                count += len(batch)

        connection.commit()

        return count

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a SQLite index for the ePath gene-to-KO dataset."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/reference/essentiality/a_Gene_sort.txt"),
        help="Path to the source TSV file.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/reference/essentiality/epath.sqlite3"),
        help="Path for the SQLite database to create.",
    )
    args = parser.parse_args()

    count = build_epath_index(args.source, args.database)

    print(f"Indexed {count:,} gene mappings.")
    print(f"SQLite database: {args.database.resolve()}")


if __name__ == "__main__":
    main()