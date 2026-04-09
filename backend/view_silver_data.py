"""
Silver layer data viewer (Parquet under lakehouse/silver/).

Run from backend/:
    python view_silver_data.py
    python view_silver_data.py --export
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from app.config.settings import SILVER_PATH


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


def view_market_data(base: Path) -> pd.DataFrame | None:
    """Unified OHLCV market table (crypto + forex + metals)."""
    print_section("SILVER: MARKET (merged)")

    path = base / "market_data" / "data.parquet"
    df = _read_parquet(path)
    if df is None:
        print(
            f"{Colors.WARNING}No file: {path}{Colors.ENDC}\n"
            "  Run: python -m app.lakehouse.silver.clean_market_silver"
        )
        return None

    print(f"{Colors.OKGREEN}{len(df):,} rows{Colors.ENDC}\n")
    print(f"{Colors.BOLD}Path:{Colors.ENDC} {path.resolve()}")
    print(f"{Colors.BOLD}Columns:{Colors.ENDC} {', '.join(df.columns)}")

    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        print(f"{Colors.BOLD}Timestamp range:{Colors.ENDC} {ts.min()} … {ts.max()}")

    if "market_type" in df.columns:
        print(f"{Colors.BOLD}Rows by market_type:{Colors.ENDC}")
        print(df.groupby("market_type").size().to_string())

    if "display_symbol" in df.columns:
        print(f"{Colors.BOLD}Rows by display_symbol:{Colors.ENDC}")
        print(df.groupby("display_symbol").size().to_string())

    preview_n = 5
    print(f"\n{Colors.BOLD}First {preview_n} rows:{Colors.ENDC}")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", 40)
    print(df.head(preview_n).to_string(index=False))
    print(f"\n{Colors.BOLD}Last {preview_n} rows:{Colors.ENDC}")
    print(df.tail(preview_n).to_string(index=False))
    print(
        f"\n{Colors.WARNING}(Full table omitted — use pandas or --export.){Colors.ENDC}"
    )
    return df


def view_news_data(base: Path) -> pd.DataFrame | None:
    print_section("SILVER: NEWS")

    path = base / "news_data" / "data.parquet"
    df = _read_parquet(path)
    if df is None:
        print(
            f"{Colors.WARNING}No file: {path}{Colors.ENDC}\n"
            "  Run: python -m app.lakehouse.silver.clean_news_silver"
        )
        return None

    print(f"{Colors.OKGREEN}{len(df)} articles{Colors.ENDC}\n")
    print(f"{Colors.BOLD}Path:{Colors.ENDC} {path.resolve()}")
    print(f"{Colors.BOLD}Columns:{Colors.ENDC} {', '.join(df.columns)}")

    if "timestamp" in df.columns:
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        latest = df.sort_values("timestamp", ascending=False).head(5)
        print(f"\n{Colors.BOLD}Latest 5 headlines:{Colors.ENDC}")
        for _, row in latest.iterrows():
            title = str(row.get("title", ""))[:100]
            print(f"  - [{row.get('display_symbol', row.get('symbol'))}] {title}")
    return df


def view_optional_asset_silver(base: Path, name: str, folder: str) -> None:
    """crypto_data / forex_data / metals_data if present (standalone runs)."""
    path = base / folder / "data.parquet"
    if not path.exists():
        return
    df = _read_parquet(path)
    if df is None:
        return
    print_section(f"SILVER: {name} (per-asset table)")
    print(f"{Colors.OKGREEN}{len(df):,} rows{Colors.ENDC} at {path.resolve()}")
    if len(df) <= 20:
        print(df.to_string(index=False))
    else:
        print(df.head(5).to_string(index=False))
        print(f"\n{Colors.WARNING}(… {len(df) - 10:,} more rows …){Colors.ENDC}")
        print(df.tail(5).to_string(index=False))


def show_silver_stats(base: Path) -> None:
    print_section("SILVER LAYER SUMMARY")

    datasets: dict[str, Path] = {
        "market_data": base / "market_data" / "data.parquet",
        "news_data": base / "news_data" / "data.parquet",
        "crypto_data": base / "crypto_data" / "data.parquet",
        "forex_data": base / "forex_data" / "data.parquet",
        "metals_data": base / "metals_data" / "data.parquet",
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
                    f"  {Colors.OKGREEN}OK{Colors.ENDC}  {label:16} "
                    f"{len(df):>8,} rows  {size_mb:>8.2f} MB"
                )
            except OSError:
                print(f"  {Colors.FAIL}ERR{Colors.ENDC} {label:16} (read failed)")
        else:
            print(f"  {Colors.WARNING} --{Colors.ENDC} {label:16} (not present)")

    print(f"\n{Colors.BOLD}Silver root:{Colors.ENDC} {base.resolve()}")
    print(f"{Colors.BOLD}Total (present files):{Colors.ENDC} {total_records:,} rows, {total_mb:.2f} MB")


def export_to_csv(base: Path) -> None:
    print_section("EXPORT TO CSV")

    export_dir = Path("silver_exports")
    export_dir.mkdir(exist_ok=True)

    datasets = [
        "market_data",
        "news_data",
        "crypto_data",
        "forex_data",
        "metals_data",
    ]
    n = 0
    for name in datasets:
        p = base / name / "data.parquet"
        if not p.exists():
            continue
        try:
            df = pd.read_parquet(p)
            out = export_dir / f"{name}.csv"
            df.to_csv(out, index=False)
            print(f"{Colors.OKGREEN}Wrote {out} ({len(df):,} rows){Colors.ENDC}")
            n += 1
        except Exception as exc:
            print(f"{Colors.FAIL}{name}: {exc}{Colors.ENDC}")

    if n == 0:
        print(f"{Colors.WARNING}No silver Parquet files to export.{Colors.ENDC}")
    else:
        print(f"\n{Colors.OKGREEN}Exported {n} file(s) under {export_dir.resolve()}{Colors.ENDC}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print_header("SILVER LAYER DATA VIEWER")

    base = Path(SILVER_PATH).resolve()
    if not base.exists():
        print(
            f"{Colors.FAIL}Silver directory not found: {base}{Colors.ENDC}\n"
            "Create it by running silver cleaners, e.g.\n"
            "  python -m app.lakehouse.silver.clean_market_silver"
        )
        sys.exit(1)

    view_market_data(base)
    view_news_data(base)
    view_optional_asset_silver(base, "CRYPTO", "crypto_data")
    view_optional_asset_silver(base, "FOREX", "forex_data")
    view_optional_asset_silver(base, "METALS", "metals_data")
    show_silver_stats(base)

    if "--export" in sys.argv:
        export_to_csv(base)
    else:
        print(
            f"\n{Colors.BOLD}Tip:{Colors.ENDC} add --export to write CSVs under silver_exports/"
        )

    print_header("VIEWER COMPLETE")


if __name__ == "__main__":
    main()
