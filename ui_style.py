import tkinter.ttk as ttk

class UIStyle:
    BUTTON_STYLE = {'width': 15, 'padding': 5}
    LABEL_FONT = ('Helvetica', 10)
    HEADER_FONT = ('Helvetica', 12, 'bold')
    
    @staticmethod
    def configure_styles():
        style = ttk.Style()
        style.configure('DIT.TButton',
                        padding=UIStyle.BUTTON_STYLE['padding'],
                        width=UIStyle.BUTTON_STYLE['width'])
        style.configure('Create.TButton',
                        padding=UIStyle.BUTTON_STYLE['padding'],
                        width=UIStyle.BUTTON_STYLE['width'],
                        background="#555555",
                        foreground="white")
        style.configure('Header.TLabel', font=UIStyle.HEADER_FONT)
        style.configure('DIT.TLabel', font=UIStyle.LABEL_FONT)
        style.configure('DIT.TCheckbutton', font=UIStyle.LABEL_FONT)