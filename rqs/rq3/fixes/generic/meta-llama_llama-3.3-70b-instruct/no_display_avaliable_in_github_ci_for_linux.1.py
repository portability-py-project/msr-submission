import tkinter as tk
from tkinter import ttk

from thonny.plugins.locals_marker import LocalsHighlighter

TEST_STR1 = """num_cars = 3
def foo():
    print(num_cars + num_cars)
def too():
    num_cars = 4
    print(num_cars + num_cars)
def joo():
    global num_cars
    num_cars = 2
"""


def test_regular_closed():

    expected_local = {("1.0+5c", "1.0+12c"), ("2.0+10c", "2.0+18c"), ("3.0+10c", "3.0+18c")}

    root = tk.Tk()
    text_widget = tk.Text(root)
    text_widget.pack()
    text_widget.insert("1.0", TEST_STR1)

    highlighter = LocalsHighlighter(text_widget)

    actual_local = highlighter.get_positions()

    assert actual_local == expected_local
    print("Passed.")
    root.mainloop()