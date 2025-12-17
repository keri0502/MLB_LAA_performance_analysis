from dash import Dash
import dash_bootstrap_components as dbc

from src.layout_home import layout as layout_home

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
server = app.server
app.layout = layout_home


def main():
    print("MLB Dashboard placeholder - connect DB and dashboard here in the future.")


if __name__ == "__main__":
    app.run()
