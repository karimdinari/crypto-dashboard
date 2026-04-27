"""
Gold layer data viewer (Parquet under GOLD_PATH, default backend/lakehouse/gold/).

Run from backend/:
    python view_gold_data.py
    python view_gold_data.py --export
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from app.config.settings import GOLD_PATH


class Colors:
    HEADER = "\033[95m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(text: str) -> None:
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")


def _read_parquet(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception as exc:
        print(f"{Colors.FAIL}Error reading {path}: {exc}{Colors.ENDC}")
        return None


def view_market_features(base: Path) -> pd.DataFrame | None:
    print_section("GOLD: MARKET FEATURES")

    path = base / "market_features" / "data.parquet"
    df = _read_parquet(path)
    if df is None:
        print(
            f"{Colors.WARNING}No file: {path}{Colors.ENDC}\n"
            "  Run: python -m app.etl.gold.build_market_features_gold"
        )
        return None

    print(f"{Colors.OKGREEN}{len(df):,} rows{Colors.ENDC}")
    print(f"{Colors.BOLD}Path:{Colors.ENDC} {path.resolve()}")
    print(f"{Colors.BOLD}Columns:{Colors.ENDC} {len(df.columns)}")

    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        print(f"{Colors.BOLD}Timestamp range:{Colors.ENDC} {ts.min()} ... {ts.max()}")

    if "display_symbol" in df.columns:
        print(f"{Colors.BOLD}Rows by symbol:{Colors.ENDC}")
        print(df.groupby("display_symbol").size().to_string())

    preview_n = 5
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", 40)
    print(f"\n{Colors.BOLD}First {preview_n} rows:{Colors.ENDC}")
    print(df.head(preview_n).to_string(index=False))
    print(f"\n{Colors.BOLD}Last {preview_n} rows:{Colors.ENDC}")
    print(df.tail(preview_n).to_string(index=False))
    return df


def view_news_aggregates(base: Path) -> pd.DataFrame | None:
    print_section("GOLD: NEWS AGGREGATES")

    path = base / "news_aggregates" / "data.parquet"
    df = _read_parquet(path)
    if df is None:
        print(
            f"{Colors.WARNING}No file: {path}{Colors.ENDC}\n"
            "  Run: python -m app.etl.gold.build_news_aggregates_gold"
        )
        return None

    print(f"{Colors.OKGREEN}{len(df):,} rows{Colors.ENDC}")
    print(f"{Colors.BOLD}Path:{Colors.ENDC} {path.resolve()}")
    print(f"{Colors.BOLD}Columns:{Colors.ENDC} {', '.join(df.columns)}")

    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        print(f"{Colors.BOLD}Timestamp range:{Colors.ENDC} {ts.min()} ... {ts.max()}")

    preview_n = 5
    print(f"\n{Colors.BOLD}First {preview_n} rows:{Colors.ENDC}")
    print(df.head(preview_n).to_string(index=False))
    print(f"\n{Colors.BOLD}Last {preview_n} rows:{Colors.ENDC}")
    print(df.tail(preview_n).to_string(index=False))
    return df


def view_correlation_matrix(base: Path) -> pd.DataFrame | None:
    print_section("GOLD: CORRELATION MATRIX")

    path = base / "correlation_matrix" / "data.parquet"
    df = _read_parquet(path)
    if df is None:
        print(
            f"{Colors.WARNING}No file: {path}{Colors.ENDC}\n"
            "  Run: python -m app.etl.gold.build_correlation_matrix_gold"
        )
        return None

    print(f"{Colors.OKGREEN}{len(df):,} rows{Colors.ENDC}")
    print(f"{Colors.BOLD}Path:{Colors.ENDC} {path.resolve()}")
    print(f"{Colors.BOLD}Columns:{Colors.ENDC} {', '.join(df.columns)}")

    preview_n = 10
    print(f"\n{Colors.BOLD}Preview ({preview_n} rows):{Colors.ENDC}")
    print(df.head(preview_n).to_string(index=False))
    return df


def show_gold_stats(base: Path) -> None:
    print_section("GOLD LAYER SUMMARY")

    datasets: dict[str, Path] = {
        "market_features": base / "market_features" / "data.parquet",
        "news_aggregates": base / "news_aggregates" / "data.parquet",
        "correlation_matrix": base / "correlation_matrix" / "data.parquet",
    }

    total_records = 0
    total_mb = 0.0

    print(f"{Colors.BOLD}Dataset files:{Colors.ENDC}\n")
    for label, path in datasets.items():
        if path.exists():
            try:
                df = pd.read_parquet(path)
                size_mb = path.stat().st_size / (1024 * 1024)
                total_records += len(df)
                total_mb += size_mb
                print(
                    f"  {Colors.OKGREEN}OK{Colors.ENDC}  {label:20} "
                    f"{len(df):>8,} rows  {size_mb:>8.2f} MB"
                )
            except OSError:
                print(f"  {Colors.FAIL}ERR{Colors.ENDC} {label:20} (read failed)")
        else:
            print(f"  {Colors.WARNING} --{Colors.ENDC} {label:20} (not present)")

    print(f"\n{Colors.BOLD}Gold root:{Colors.ENDC} {base.resolve()}")
    print(f"{Colors.BOLD}Total (present files):{Colors.ENDC} {total_records:,} rows, {total_mb:.2f} MB")


def export_to_csv(base: Path) -> None:
    print_section("EXPORT TO CSV")

    export_dir = Path("gold_exports")
    export_dir.mkdir(exist_ok=True)

    datasets = ["market_features", "news_aggregates", "correlation_matrix"]
    exported = 0

    for name in datasets:
        src = base / name / "data.parquet"
        if not src.exists():
            continue

        try:
            df = pd.read_parquet(src)
            out = export_dir / f"{name}.csv"
            df.to_csv(out, index=False)
            print(f"{Colors.OKGREEN}Wrote {out} ({len(df):,} rows){Colors.ENDC}")
            exported += 1
        except Exception as exc:
            print(f"{Colors.FAIL}{name}: {exc}{Colors.ENDC}")

    if exported == 0:
        print(f"{Colors.WARNING}No gold Parquet files to export.{Colors.ENDC}")
    else:
        print(f"\n{Colors.OKGREEN}Exported {exported} file(s) under {export_dir.resolve()}{Colors.ENDC}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print_header("GOLD LAYER DATA VIEWER")

    base = Path(GOLD_PATH).resolve()
    if not base.exists():
        print(
            f"{Colors.FAIL}Gold directory not found: {base}{Colors.ENDC}\n"
            "Create it by running gold builders first."
        )
        sys.exit(1)

    view_market_features(base)
    view_news_aggregates(base)
    view_correlation_matrix(base)
    show_gold_stats(base)

    if "--export" in sys.argv:
        export_to_csv(base)
    else:
        print(f"\n{Colors.BOLD}Tip:{Colors.ENDC} add --export to write CSVs under gold_exports/")

    print_header("VIEWER COMPLETE")


if __name__ == "__main__":
    main()
