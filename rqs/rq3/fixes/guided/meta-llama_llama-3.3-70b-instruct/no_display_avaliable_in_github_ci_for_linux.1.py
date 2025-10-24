import os
import tkinter

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

    expected_local = {("5.4", "5.12"), ("6.10", "6.18"), ("6.21", "6.29")}

    if os.environ.get('DISPLAY') is None:
        os.environ['DISPLAY'] = ':99'

    text_widget = tkinter.Tk()
    text_widget.title("Locals Highlighter Test")

    text_box = tkinter.Text(text_widget)
    text_box.pack()

    text_box.insert("end", TEST_STR1)

    highlighter = LocalsHighlighter(text_box)

    actual_local = highlighter.get_positions()

    assert actual_local == expected_local
    print("Passed.")
    text_widget.destroy()