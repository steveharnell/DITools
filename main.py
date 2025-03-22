import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import importlib
import sys

THEME_SETTINGS = {
    "light": {"bg": "#FFFFFF", "fg": "#000000", "canvas_bg": "#F0F0F0", "button_bg": "#EFEFEF", "highlight_bg": "#E0E0E0"},
    "dark": {"bg": "#2D2D2D", "fg": "#FFFFFF", "canvas_bg": "#333333", "button_bg": "#404040", "highlight_bg": "#3D3D3D"}
}

def get_macos_appearance():
    try:
        result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True)
        return "dark" if "Dark" in result.stdout else "light"
    except:
        return "light"

def apply_theme(root, theme):
    style = ttk.Style()
    settings = THEME_SETTINGS[theme]
    style.configure("TFrame", background=settings["bg"])
    style.configure("TLabel", background=settings["bg"], foreground=settings["fg"])
    style.configure("TNotebook", background=settings["bg"], bordercolor=settings["highlight_bg"])
    style.configure("TNotebook.Tab", background=settings["button_bg"], foreground=settings["fg"])
    style.map("TNotebook.Tab", background=[("selected", settings["highlight_bg"])])
    root.configure(background=settings["bg"])
    root.current_theme = theme
    root.theme_settings = settings

def safe_import(module_name):
    try:
        return importlib.import_module(module_name)
    except Exception as e:
        messagebox.showwarning("Module Import Warning", f"Module '{module_name}' failed to load: {e}")
        return None

modules = {
    "project": safe_import("project"),
    "sync": safe_import("sync"),
    "file_comparator": safe_import("file_comparator"),
    "render_check": safe_import("render_check"),
    "tree_generator": safe_import("tree_generator"),
    "trash": safe_import("trash"),
}

def create_scrollable_tab(notebook, theme_settings, FrameClass):
    container = ttk.Frame(notebook)
    canvas = tk.Canvas(container, bg=theme_settings["canvas_bg"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    def configure_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", configure_scroll_region)

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Keep track of the last width to avoid redundant updates
    last_width = canvas.winfo_width()
    resize_timer_id = None
    
    def resize_canvas(event):
        nonlocal last_width, resize_timer_id
        
        # Cancel any pending resize operation
        if resize_timer_id is not None:
            canvas.after_cancel(resize_timer_id)
            resize_timer_id = None
        
        # Only update if width actually changed
        if event.width != last_width:
            # Debounce the resize event with a 50ms delay
            resize_timer_id = canvas.after(50, lambda: update_canvas_width(event.width))
    
    def update_canvas_width(width):
        nonlocal last_width, resize_timer_id
        canvas.itemconfig(window_id, width=width)
        last_width = width
        resize_timer_id = None

    canvas.bind("<Configure>", resize_canvas)

    canvas.configure(yscrollcommand=scrollbar.set)
    
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/60)), "units")
    
    canvas.bind('<MouseWheel>', on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    frame_content = FrameClass(scrollable_frame)
    frame_content.pack(fill="both", expand=True)

    return container

def main():
    root = tk.Tk()
    root.title("DITools")
    root.geometry("900x1100")
    root.minsize(600, 700)

    current_theme = get_macos_appearance()
    apply_theme(root, current_theme)
    theme_settings = root.theme_settings

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    tab_frames = {}
    available_tabs = {
        "Project": modules["project"].ProjectFrame if modules["project"] else None,
        "Sync": modules["sync"].NewSyncFrame if modules["sync"] else None,
        "File Comparator": modules["file_comparator"].FileComparatorFrame if modules["file_comparator"] else None,
        "Render Check": modules["render_check"].RenderCheckFrame if modules["render_check"] else None,
        "Tree Generator": modules["tree_generator"].TreeGeneratorFrame if modules["tree_generator"] else None,
        "Trash .drx Files": modules["trash"].TrashDrxFrame if modules["trash"] else None,
    }

    for tab_name, FrameClass in available_tabs.items():
        if FrameClass:
            tab_frame = create_scrollable_tab(notebook, theme_settings, FrameClass)
            tab_frames[tab_name] = tab_frame
            notebook.add(tab_frame, text=tab_name)

    # Force theme refresh when tab is changed
    def on_tab_changed(event):
        # Update the current theme when switching tabs
        new_theme = get_macos_appearance()
        if new_theme != root.current_theme:
            apply_theme(root, new_theme)
        
        # Also re-apply even if it's the same theme to ensure all elements are updated
        selected_tab = notebook.select()
        if selected_tab:
            index = notebook.index(selected_tab)
            tab_name = list(tab_frames.keys())[index]
            # Update canvas background for the selected tab
            for frame in tab_frames.values():
                for child in frame.winfo_children():
                    if isinstance(child, tk.Canvas):
                        child.config(bg=root.theme_settings["canvas_bg"])
    
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    def monitor_theme_changes():
        nonlocal current_theme
        new_theme = get_macos_appearance()
        if new_theme != current_theme:
            current_theme = new_theme
            apply_theme(root, new_theme)
            
            # Update all tab frames when theme changes
            for frame in tab_frames.values():
                for child in frame.winfo_children():
                    if isinstance(child, tk.Canvas):
                        child.config(bg=root.theme_settings["canvas_bg"])
                    
                    # Force text widgets to update foreground color
                    for widget in child.winfo_children():
                        if isinstance(widget, tk.Text):
                            widget.config(fg=root.theme_settings["fg"])
        
        root.after(5000, monitor_theme_changes)  # Check more frequently

    root.after(5000, monitor_theme_changes)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

if __name__ == "__main__":
    main()