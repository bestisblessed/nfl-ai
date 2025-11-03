"""Bokeh app showing teams by division."""

import os

import pandas as pd
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
teams_path = os.path.join(BASE_DIR, "..", "Streamlit", "data", "Teams.csv")
df = pd.read_csv(teams_path)

division_counts = df["Division"].value_counts().reset_index()
division_counts.columns = ["Division", "Count"]
source = ColumnDataSource(division_counts)

p = figure(
    x_range=division_counts["Division"],
    title="Teams by Division",
    toolbar_location=None,
)
p.vbar(x="Division", top="Count", width=0.9, source=source)
p.xgrid.grid_line_color = None
p.y_range.start = 0

curdoc().add_root(p)

