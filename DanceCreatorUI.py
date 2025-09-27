import tkinter as tk
from tkinter import simpledialog, messagebox

from SimpleFigure import SimpleFigure
from ComplexFigure import ComplexFigure

class SimpleFigureUI(SimpleFigure):
    def __init__(self, name, Anchor=None):
        if Anchor is None:
            Anchor = [1,1]
        super().__init__(name, Anchor)

class ComplexFigureUI(ComplexFigure):
    def __init__(self, name, Anchor=None, mode='sequential'):
        if Anchor is None:
            Anchor = [1,1]
        super().__init__(name, Anchor)
        self.mode = mode
        self.figures = []

class DanceUI(ComplexFigureUI):
    def __init__(self, name="Dance"):
        super().__init__('Dance', [0,0])

class FigureChainUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DanceCreator")
        self.margin = 20  # Rand für DanceUI
        self.figures = [DanceUI("Dance")]
        # Frame für Canvas und Scrollbars
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # Scrollbars
        self.v_scroll = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL)
        # Canvas
        self.canvas = tk.Canvas(self.main_frame, width=1000, height=600, bg="white",
                               yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        # Bindings
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Button-1>", self.on_left_down)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<Configure>", self.on_resize)
        self.create_main_context_menu()
        self.figure_boxes = []
        self.drag_data = None
        self.redraw()

    def create_main_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        #self.context_menu.add_command(label="Add Simple Figure", command=self.add_simple)
        #self.context_menu.add_command(label="Add Complex Figure", command=self.add_complex)
        #self.context_menu.add_separator()
        self.context_menu.add_command(label="Redraw", command=self.redraw)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit", command=self.destroy)

    def create_figure_context_menu(self, figure, parent, index):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Info", command=lambda: self.show_info(figure))
        self.context_menu.add_separator()
        menu.add_command(label="Edit Figure", command=lambda: self.edit_figure(figure))
        if not isinstance(figure, DanceUI):
            menu.add_command(label="Remove", command=lambda: self.remove_figure(figure, parent, index))
        if isinstance(figure, ComplexFigureUI) and not isinstance(figure, DanceUI):
            menu.add_command(label="Change Mode", command=lambda: self.change_mode(figure))
        self.context_menu.add_separator()
        if isinstance(figure, DanceUI):
            menu.add_command(label="Save Dance", command=lambda: self.save_figure(figure))
            menu.add_command(label="Load Dance", command=lambda: self.load_figure(figure))
        else:
            menu.add_command(label="Save Figure", command=lambda: self.save_figure(figure))
            menu.add_command(label="Load Figure", command=lambda: self.load_figure(figure))
        self.context_menu.add_separator()
        if isinstance(figure, ComplexFigureUI):
            menu.add_command(label="Add Simple figure", command=lambda: self.add_simple(figure))
            menu.add_command(label="Add Complex figure", command=lambda: self.add_complex(figure))
        return menu

    def show_info(self, figure):
        info_win = tk.Toplevel(self)
        info_win.title("Figur Info")
        info_win.geometry("+%d+%d" % (self.winfo_rootx()+200, self.winfo_rooty()+200))
        text = tk.Text(info_win, width=60, height=20)
        text.pack(padx=10, pady=10)
        def format_figure(fig, indent=0):
            ind = '  ' * indent
            s = f"{ind}Name: {getattr(fig, 'name', getattr(fig, 'Name', ''))}\n"
            anchor = getattr(fig, 'Anchor', getattr(fig, 'anchor', None))
            s += f"{ind}Anker: {anchor}\n"
            if hasattr(fig, 'figures') and fig.figures:
                s += f"{ind}Subfiguren ("+ fig.mode +"):\n"
                for sub in fig.figures:
                    s += format_figure(sub, indent+1)
            return s
        text.insert(tk.END, format_figure(figure))
        text.config(state=tk.DISABLED)
        tk.Button(info_win, text="Schließen", command=info_win.destroy).pack(pady=5)

    def save_figure(self, figure):
        filename = simpledialog.askstring("Save", "Filename:", initialvalue=figure.name)
        if not filename:
            return
        data = {}
        if isinstance(figure, SimpleFigureUI):
            messagebox.showinfo("Attention", "Simple Figures can not be saved.")
        else:
            if isinstance(figure, ComplexFigureUI):
                data['Version'] = 3
                data['Name'] = figure.name
                data['Desc'] = getattr(figure, 'desc', '')
                def build_figure_list(fig):
                    if isinstance(fig, SimpleFigureUI):
                        return [[fig.Anchor[0], fig.Anchor[1]], [fig.name, [getattr(addon, 'name', 'Unnamed') for addon in getattr(fig, '_Addons', [])]]]
                    elif isinstance(fig, ComplexFigureUI):
                        sublist = [build_figure_list(sub) for sub in fig.figures]
                        mode = 's' if fig.mode == 'sequential' else 'p'
                        return [[fig.Anchor[0], fig.Anchor[1]], [mode, sublist]]
                data['FigureList'] = build_figure_list(figure)
            try:
                with open(f'Figures/{filename}.json', 'w') as f:
                    import json
                    json.dump(data, f, indent=4)
                messagebox.showinfo("Success", f"Figure saved as {filename}.json")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save figure: {e}")

    def load_figure(self, figure):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(title="Figur laden", filetypes=[("JSON Dateien", "*.json")], initialdir="Figures")
        if not filename:
            return
        import json
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geladen werden: {e}")
            return
        def parse_figurelist(fl):
            # Leere Liste
            if not fl or (isinstance(fl, list) and len(fl) == 0):
                return []
            # SimpleFigure: [[x,y], [name, [addons]]]
            if (isinstance(fl, list) and len(fl) == 2 and isinstance(fl[0], list) and isinstance(fl[1], list)
                and len(fl[1]) > 0 and isinstance(fl[1][0], str)):
                name = fl[1][0]
                anchor = fl[0]
                addons = fl[1][1] if len(fl[1]) > 1 else []
                fig = SimpleFigureUI(name, anchor)
                fig._Addons = [SimpleFigureUI(a) for a in addons]
                return fig
            # ComplexFigure: [modus, [subfiguren]]
            if (isinstance(fl, list) and len(fl) == 2 and isinstance(fl[0], str) and fl[0] in ['s','p'] and isinstance(fl[1], list)):
                mode = 'sequential' if fl[0] == 's' else 'parallel'
                fig = ComplexFigureUI("", [0,0], mode)
                fig.figures = [parse_figurelist(sub) for sub in fl[1] if sub]
                return fig
            # Verschachtelte ComplexFigure: [[modus, [subfiguren]], ...]
            if isinstance(fl, list) and all(isinstance(sub, list) for sub in fl):
                return [parse_figurelist(sub) for sub in fl if sub]
            # Fallback: Fehler anzeigen
            raise Exception(f"Unbekanntes FigureList-Format: {fl}")
        def load_from_data(target, d):
            target.name = d.get('Name', target.name)
            if hasattr(target, 'desc'):
                target.desc = d.get('Desc', getattr(target, 'desc', ''))
            anchor = d.get('Anchor', None)
            if anchor:
                target.Anchor = anchor
            if isinstance(target, SimpleFigureUI):
                addons = d.get('Addons', [])
                if hasattr(target, '_Addons'):
                    target._Addons = []
                    for addon_name in addons:
                        target._Addons.append(SimpleFigureUI(addon_name))
            elif isinstance(target, ComplexFigureUI):
                figurelist = d.get('FigureList', None)
                if figurelist:
                    parsed = parse_figurelist(figurelist)
                    if isinstance(parsed, list):
                        target.figures = parsed
                    else:
                        target.figures = [parsed]
        # Root-Figur ersetzen
        if isinstance(figure, DanceUI):
            if 'FigureList' in data:
                anchor = data.get('Anchor', [0,0])
                newfig = DanceUI(data.get('Name', 'Dance'))
                newfig.Anchor = anchor
                newfig.desc = data.get('Desc', '')
                figurelist = data.get('FigureList', None)
                if figurelist:
                    parsed = parse_figurelist(figurelist)
                    if isinstance(parsed, list):
                        newfig.figures = parsed
                    else:
                        newfig.figures = [parsed]
                self.figures[0] = newfig
            else:
                name = data.get('Name', 'Dance')
                anchor = data.get('Anchor', [0,0])
                newfig = SimpleFigureUI(name, anchor)
                self.figures[0] = newfig
        else:
            load_from_data(figure, data)
        self.redraw()

    def on_right_click(self, event):
        # Suche von hinten nach vorne, damit die innerste Figur gewählt wird
        for bbox, figure, parent, index in reversed(self.figure_boxes):
            x1, y1, x2, y2 = bbox
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                menu = self.create_figure_context_menu(figure, parent, index)
                menu.tk_popup(event.x_root, event.y_root)
                return
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_resize(self, event):
        self.redraw()

    def add_simple(self, figure):
        name = simpledialog.askstring("Name", "Figure name:")
        Anchor_tuple = [1,1]
        try:
            figure.figures.append(SimpleFigureUI(name, Anchor_tuple))
            self.redraw()
        except:
            messagebox.showerror("Error", "add_simple. FigureChainUI")

    def add_complex(self, figure):
        name = simpledialog.askstring("Name", "Complex Figure name:")
        #mode = simpledialog.askstring("Mode", "Mode (sequential/parallel):", initialvalue="sequential")
        Anchor_tuple = [1,1]
        try:
            cf = ComplexFigureUI(name, Anchor_tuple, "sequential")
            #self.change_mode(cf)
            #EditComplexDialog(self, cf)
            figure.figures.append(cf)
            self.redraw()
        except:
            messagebox.showerror("Error", "Fehler add_complex. FigureChainUI")

    def edit_figure(self, figure):
        name = simpledialog.askstring("Edit Name", "Figure name:", initialvalue=figure.name)
        #Anchor = simpledialog.askstring("Edit Anchor", "Anchor (x, y) [default: 1,1]:", initialvalue=f"{figure.Anchor[0]},{figure.Anchor[1]}")
        try:
            if name:
                figure.name = name
            self.redraw()
        except:
            messagebox.showerror("Error", "edit_figure. FigureChainUI")

    def remove_figure(self, figure, parent, index):
        # Prevent removing any root-level figure
        if parent is None:
            messagebox.showinfo("Info", "Root-level figures cannot be removed.")
            return
        del parent.figures[index]
        self.redraw()

    def change_mode(self, figure):
        # Dropdown statt Eingabedialog
        dialog = tk.Toplevel(self)
        dialog.title("Change Mode")
        dialog.geometry("+%d+%d" % (self.winfo_rootx()+150, self.winfo_rooty()+150))
        tk.Label(dialog, text="Mode auswählen:").pack(pady=10)
        mode_var = tk.StringVar(value=figure.mode)
        options = ["sequential", "parallel"]
        dropdown = tk.OptionMenu(dialog, mode_var, *options)
        dropdown.pack(pady=5)
        def set_mode():
            figure.mode = mode_var.get()
            dialog.destroy()
            self.redraw()
        tk.Button(dialog, text="OK", command=set_mode).pack(pady=10)
        dialog.transient(self)
        dialog.grab_set()
        dialog.wait_window(dialog)

    def add_subfigure(self, cf):
        EditComplexDialog(self, cf)
        self.redraw()

    def on_left_down(self, event):
        for bbox, figure, parent, index in reversed(self.figure_boxes):
            x1, y1, x2, y2 = bbox
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drag_data = {
                    "figure": figure,
                    "parent": parent,
                    "index": index,
                    "offset_x": event.x - x1,
                    "offset_y": event.y - y1,
                    "orig_x": event.x,
                    "orig_y": event.y,
                }
                break

    def on_left_drag(self, event):
        if self.drag_data:
            self.redraw(dragged=self.drag_data, drag_x=event.x, drag_y=event.y)

    def on_left_up(self, event):
        if not self.drag_data:
            return
        fig, parent, idx = self.drag_data["figure"], self.drag_data["parent"], self.drag_data["index"]
        # Prevent dragging root "Dance" out of root
        if parent is None and idx == 0 and isinstance(fig, ComplexFigureUI) and fig.name == "Dance":
            self.drag_data = None
            self.redraw()
            return
        drop_target = None
        for bbox, figure, _, _ in self.figure_boxes:
            x1, y1, x2, y2 = bbox
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                if isinstance(figure, ComplexFigureUI) and figure is not fig:
                    if not self._is_descendant(fig, figure):
                        drop_target = figure
                break
        # Remove from old parent
        if parent is None:
            del self.figures[idx]
        else:
            del parent.figures[idx]
        # Add to new parent if valid drop target
        if drop_target:
            drop_target.figures.append(fig)
        else:
            self.figures.append(fig)
        self.drag_data = None
        self.redraw()

    def _is_descendant(self, child, parent):
        if isinstance(parent, ComplexFigureUI):
            for sub in parent.figures:
                if sub is child or self._is_descendant(child, sub):
                    return True
        return False

    def redraw(self, dragged=None, drag_x=0, drag_y=0):
        self.canvas.delete("all")
        self.figure_boxes = []
        margin = getattr(self, "margin", 20)
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 100)
        x, y = margin, margin
        w = width - 2 * margin
        h = height - 2 * margin
        for idx, fig in enumerate(self.figures):
            if isinstance(fig, DanceUI):
                self._draw_figure(fig, x, y, None, idx, area=(x, y, x + w, y + h))
            else:
                self._draw_figure(fig, x, y, None, idx)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _draw_figure(self, fig, x, y, parent, index, depth=0, area=None):
        pad = 10
        title_h = 30
        min_w = 120
        min_h = 50
        # Wenn area übergeben, nutze diese Fläche
        if area:
            x1, y1, x2, y2 = area
            w = x2 - x1
            h = y2 - y1
        else:
            x1, y1 = x, y
            w, h = min_w, min_h
            x2, y2 = x1 + w, y1 + h
        # SimpleFigure: nur Kasten mit Name
        if isinstance(fig, SimpleFigureUI):
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue")
            self.canvas.create_text((x1 + x2) / 2, y1 + title_h / 2, text=fig.name)
            self.figure_boxes.append(((x1, y1, x2, y2), fig, parent, index))
            return x1, y1, x2, y2
        # ComplexFigure: Kasten mit Name und Subfiguren
        elif isinstance(fig, ComplexFigureUI):
            # Titelbereich
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightgreen")
            self.canvas.create_text((x1 + x2) / 2, y1 + title_h / 2, text=fig.name)
            self.figure_boxes.append(((x1, y1, x2, y2), fig, parent, index))
            # Subfiguren dynamisch anordnen
            sub_bboxes = []
            n = len(fig.figures)
            if n > 0:
                if fig.mode == "sequential":
                    # nebeneinander, horizontal verteilt
                    sub_w = max((w - (n + 1) * pad) // n, min_w)
                    sub_h = h - title_h - 2 * pad
                    sub_y = y1 + title_h + pad
                    sub_x = x1 + pad
                    for idx2, sub in enumerate(fig.figures):
                        sub_area = (sub_x, sub_y, sub_x + sub_w, sub_y + sub_h)
                        bbox = self._draw_figure(sub, sub_x, sub_y, fig, idx2, depth + 1, area=sub_area)
                        sub_bboxes.append(bbox)
                        sub_x += sub_w + pad
                else:
                    # untereinander, vertikal verteilt
                    sub_h = max((h - title_h - (n + 1) * pad) // n, min_h)
                    sub_w = w - 2 * pad
                    sub_x = x1 + pad
                    sub_y = y1 + title_h + pad
                    for idx2, sub in enumerate(fig.figures):
                        sub_area = (sub_x, sub_y, sub_x + sub_w, sub_y + sub_h)
                        bbox = self._draw_figure(sub, sub_x, sub_y, fig, idx2, depth + 1, area=sub_area)
                        sub_bboxes.append(bbox)
                        sub_y += sub_h + pad
            return x1, y1, x2, y2

if __name__ == "__main__":
    FigureChainUI().mainloop()
