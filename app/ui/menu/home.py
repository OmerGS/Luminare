import dearpygui.dearpygui as dpg

import tkinter as tk

root = tk.Tk()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

dpg.create_context()
dpg.create_viewport(title='Luminare', width=screen_width, height=screen_height)

with dpg.window(tag="Primary Window"):
    dpg.add_button(label="createProject", height=, width=, )
    dpg.add_text("Projects : ")
    for i in vids:
        dpg.add_image_button(i,height=, width=, )
    
