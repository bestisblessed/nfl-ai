"""Utility helpers for parsing leader projection PDFs."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from numbers import Number
from typing import Iterable, List, Sequence

import pandas as pd
import pdfplumber


@dataclass
class Leaderboard:
    """Structured leaderboard information extracted from the PDF."""

    title: str
    dataframe: pd.DataFrame

    def normalize(self) -> "Leaderboard":
        """Return a leaderboard with standardized columns and cleaned values."""
        df = self.dataframe.copy()

        # Trim whitespace across string columns
        for column in df.select_dtypes(include="object"):
            df[column] = df[column].astype(str).str.strip()

        # Attempt to coerce numeric columns to floats/ints where appropriate
        numeric_candidates = [
            column
            for column in df.columns
            if column.lower() not in {"player", "opponent", "team", "pos", "position"}
        ]
        for column in numeric_candidates:
            df[column] = (
                df[column]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
            )
            df[column] = pd.to_numeric(df[column], errors="coerce")

        if "Rank" in df.columns:
            df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce").astype("Int64")
            df = df.sort_values("Rank")

        return Leaderboard(title=self.title, dataframe=df)


def _candidate_titles(lines: Sequence[str]) -> List[str]:
    """Identify leaderboard titles from PDF text lines."""
    titles: List[str] = []
    for line in lines:
        normalized = line.strip()
        if not normalized:
            continue
        if normalized.upper() != normalized:
            continue
        if normalized.startswith("RANK"):
            continue
        if any(normalized.startswith(prefix) for prefix in ("TOP", "LEADER", "PROJECTED")):
            titles.append(normalized.title())
    return titles


def _clean_rows(table: Sequence[Sequence[str]]) -> pd.DataFrame:
    if not table:
        return pd.DataFrame()

    header, *rows = table
    header = [col.strip().title() if isinstance(col, str) else col for col in header]
    data = [[cell.strip() if isinstance(cell, str) else cell for cell in row] for row in rows]
    return pd.DataFrame(data, columns=header)


def _parse_text_table(text_lines: List[str]) -> pd.DataFrame:
    """Parse a text-based table from PDF text lines."""
    import re

    if not text_lines:
        return pd.DataFrame()

    # Find the header line
    header_idx = -1
    headers = []
    for i, line in enumerate(text_lines):
        line = line.strip()
        if "Rank" in line and "Player" in line and "Opponent" in line:
            header_idx = i
            # Split headers on whitespace
            headers = line.split()
            break

    if header_idx == -1 or not headers:
        return pd.DataFrame()

    # Extract data rows
    data_rows = []
    for line in text_lines[header_idx + 1:]:
        line = line.strip()
        if not line or line.upper() == line:  # Skip empty lines or all-caps titles
            continue

        # Parse each line using regex pattern
        # Pattern: rank, player name in parentheses, vs opponent, yards
        match = re.match(r'^(\d+)\s+(.+?)\s+vs\s+(\w+)\s+([\d.]+)$', line)
        if match:
            rank, player, opponent, yards = match.groups()
            data_rows.append([rank, player, f"vs {opponent}", yards])

    if not data_rows:
        return pd.DataFrame()

    return pd.DataFrame(data_rows, columns=headers)


def parse_leader_pdf(pdf_bytes: bytes) -> List[Leaderboard]:
    """Parse a PDF and return structured leaderboard tables."""
    leaderboards: List[Leaderboard] = []

    title_tracker: Counter[str] = Counter()

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [line for line in text.splitlines() if line.strip()]
            titles = _candidate_titles(lines)

            # Try table extraction first
            extracted_tables = page.extract_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 5,
                    "intersection_tolerance": 5,
                }
            )

            tables_found = False
            for index, table in enumerate(extracted_tables):
                df = _clean_rows(table)
                if df.empty:
                    continue
                title = (
                    titles[index]
                    if index < len(titles)
                    else f"Leaderboard {len(leaderboards) + 1}"
                )
                title_tracker[title] += 1
                if title_tracker[title] > 1:
                    title = f"{title} ({title_tracker[title]})"
                leaderboards.append(Leaderboard(title=title, dataframe=df).normalize())
                tables_found = True

            # If no tables found via extraction, try parsing text
            if not tables_found and lines:
                df = _parse_text_table(lines)
                if not df.empty:
                    # Find title for this page
                    page_title = None
                    for line in lines:
                        if line.upper() == line and "TOP" in line and ("YARDS" in line or "TD" in line):
                            page_title = line.title()
                            break

                    if page_title:
                        title_tracker[page_title] += 1
                        if title_tracker[page_title] > 1:
                            page_title = f"{page_title} ({title_tracker[page_title]})"
                        leaderboards.append(Leaderboard(title=page_title, dataframe=df).normalize())

    return leaderboards


def leaderboard_summary(leaderboard: Leaderboard, top_n: int = 3) -> List[str]:
    """Create a short text summary for a leaderboard."""
    df = leaderboard.dataframe
    if df.empty:
        return []

    rank_col = None
    for column in df.columns:
        if column.lower() == "rank":
            rank_col = column
            break

    if rank_col is not None:
        df = df.sort_values(rank_col)

    player_column = "Player" if "Player" in df.columns else df.columns[1]
    players: Iterable[str] = df[player_column].head(top_n)

    metric_column = None
    for column in df.columns[::-1]:
        if pd.api.types.is_numeric_dtype(df[column]):
            metric_column = column
            break

    takeaways = []
    for player in players:
        if metric_column is not None:
            metric_value = df.loc[df[player_column] == player, metric_column]
            if metric_value.empty:
                takeaways.append(f"{player}")
            else:
                value = metric_value.iloc[0]
                if pd.isna(value):
                    takeaways.append(f"{player}")
                elif isinstance(value, Number):
                    if not float(value).is_integer():
                        takeaways.append(f"{player} – {metric_column}: {float(value):,.1f}")
                    else:
                        takeaways.append(f"{player} – {metric_column}: {int(value):,}")
                else:
                    takeaways.append(f"{player} – {metric_column}: {value}")
        else:
            takeaways.append(str(player))

    return takeaways
