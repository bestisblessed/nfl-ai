"""Bokeh version of the NFL AI home page."""

from bokeh.io import curdoc
from bokeh.models import Div


div = Div(text="""
    <h1>NFL AI</h1>
    <p>Welcome to NFL AI.</p>
""", width=400)

curdoc().add_root(div)

