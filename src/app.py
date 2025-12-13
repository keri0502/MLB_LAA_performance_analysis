from dash import Dash
from layout_home import layout as layout_home

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.layout = layout_home

def main():
    print("MLB Dashboard placeholder - connect DB and dashboard here in the future.")

if __name__ == "__main__":
    app.run(debug=True) 