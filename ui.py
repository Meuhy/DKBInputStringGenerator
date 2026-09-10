import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import sys
import json
import os
from dataclasses import asdict

from PIL import Image, ImageTk

from main import generate_input_sequence, InputSequenceParams

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent

    return base_path / relative_path

def get_last_settings_path():
    app_data = Path(
        os.environ["LOCALAPPDATA"]
    ) / "InputSequenceGenerator"

    app_data.mkdir(
        parents=True,
        exist_ok=True
    )

    return app_data / "last_settings.txt"

class InputSequenceUI:
    BG_COLOR = "#202020"
    PANEL_COLOR = "#2b2b2b"
    ENTRY_COLOR = "#3a3a3a"
    TEXT_COLOR = "#eeeeee"
    BUTTON_COLOR = "#444444"
    BUTTON_ACTIVE = "#555555"

    def __init__(self, root):
        self.root = root
        self.root.title("Input Sequence Generator")

        self.example_sequence = "Afat>Unsurf>Stall>Chunk Jump>Elefart"
        self.example_title = "Example Sequence"

        # Window icon
        icon_path = resource_path("icon.ico")
        self.root.iconbitmap(icon_path)

        window_width = 1200
        window_height = 450

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(
            f"{window_width}x{window_height}+{x}+{y}"
        )

        self.root.minsize(600, 450)

        self.generated_image = None
        self.image_tk = None
        self.resize_job = None
        self.settings_path = None
        self.last_settings_path = get_last_settings_path()

        self.show_title = tk.BooleanVar(value=False)
        self.show_text = tk.BooleanVar(value=True)
        self.show_expanded = tk.BooleanVar(value=False)
        self.show_a_jump = tk.BooleanVar(value=True)
        self.show_b_jump = tk.BooleanVar(value=True)
        self.show_jump_button = tk.BooleanVar(value=True)
        self.colored_buttons = tk.BooleanVar(value=True)
        self.directional_colors = tk.BooleanVar(value=True)

        self.configure_theme()
        self.create_menu()
        self.create_widgets()

        self.load_last_settings()

        # Window resizing
        self.root.bind("<Configure>", self.on_resize)

        # Keyboard shortcuts
        self.root.bind("<Return>", self.on_enter)
        self.root.bind("<Control-s>", self.on_save)

        self.generate()

    def create_menu(self):
        menu_bar = tk.Menu(
            self.root,
            bg=self.PANEL_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.BUTTON_ACTIVE,
            activeforeground=self.TEXT_COLOR
        )

        file_menu = tk.Menu(
            menu_bar,
            tearoff=False,
            bg=self.PANEL_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.BUTTON_ACTIVE,
            activeforeground=self.TEXT_COLOR
        )

        file_menu.add_command(
            label="Save Sequence...",
            command=self.save
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Save Settings as...",
            command=self.save_settings_as
        )

        file_menu.add_command(
            label="Save Settings",
            command=self.save_settings
        )

        file_menu.add_command(
            label="Load Settings...",
            command=self.load_settings
        )

        tk.Frame(
            file_menu,
            height=1,
            bg="#444444"
        ).pack(
            fill="x",
            padx=5
        )

        file_menu.add_command(
            label="Reset to Default Settings",
            command=self.reset_settings
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            command=self.root.destroy
        )

        menu_bar.add_cascade(
            label="File",
            menu=file_menu
        )

        self.root.config(
            menu=menu_bar
        )

    def configure_theme(self):
        self.root.configure(bg=self.BG_COLOR)

        self.root.option_add(
            "*Label.background",
            self.BG_COLOR
        )
        self.root.option_add(
            "*Label.foreground",
            self.TEXT_COLOR
        )

        self.root.option_add(
            "*Checkbutton.background",
            self.BG_COLOR
        )
        self.root.option_add(
            "*Checkbutton.foreground",
            self.TEXT_COLOR
        )
        self.root.option_add(
            "*Checkbutton.selectColor",
            self.ENTRY_COLOR
        )
        self.root.option_add(
            "*Checkbutton.activeBackground",
            self.BG_COLOR
        )
        self.root.option_add(
            "*Checkbutton.activeForeground",
            self.TEXT_COLOR
        )

        self.root.option_add(
            "*Entry.background",
            self.ENTRY_COLOR
        )
        self.root.option_add(
            "*Entry.foreground",
            self.TEXT_COLOR
        )
        self.root.option_add(
            "*Entry.insertBackground",
            self.TEXT_COLOR
        )

        self.root.option_add(
            "*Button.background",
            self.BUTTON_COLOR
        )
        self.root.option_add(
            "*Button.foreground",
            self.TEXT_COLOR
        )
        self.root.option_add(
            "*Button.activeBackground",
            self.BUTTON_ACTIVE
        )
        self.root.option_add(
            "*Button.activeForeground",
            self.TEXT_COLOR
        )

    def get_params(self):
        return InputSequenceParams(
            output_path="output.png",
            show_title=self.show_title.get(),
            show_text=self.show_text.get(),
            show_expanded=self.show_expanded.get(),
            show_a_jump=self.show_a_jump.get(),
            show_b_jump=self.show_b_jump.get(),
            show_jump_button=self.show_jump_button.get(),
            colored_buttons=self.colored_buttons.get(),
            directional_colors=self.directional_colors.get(),

            font_size=int(self.font_size.get()),
            stroke_width=int(self.stroke_width.get()),
            vertical_spacing=int(self.vertical_spacing.get()),
            input_spacing=int(
                self.input_spacing.get()
            ),
            tech_spacing=int(
                self.tech_spacing.get()
            ),
        )

    def apply_params(self, params):
        self.show_title.set(params.show_title)
        self.show_text.set(params.show_text)
        self.show_expanded.set(params.show_expanded)
        self.show_a_jump.set(params.show_a_jump)
        self.show_b_jump.set(params.show_b_jump)
        self.show_jump_button.set(params.show_jump_button)
        self.colored_buttons.set(params.colored_buttons)
        self.directional_colors.set(params.directional_colors)

        self.set_entry(
            self.font_size,
            params.font_size
        )

        self.set_entry(
            self.stroke_width,
            params.stroke_width
        )

        self.set_entry(
            self.vertical_spacing,
            params.vertical_spacing
        )

        self.set_entry(
            self.input_spacing,
            params.input_spacing
        )

        self.set_entry(
            self.tech_spacing,
            params.tech_spacing
        )

        # Automatically regenerate if a sequence
        # has already been entered.
        if self.sequence_entry.get().strip():
            self.generate()

    def set_entry(self, entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    def checkbox_changed(self):
        if self.sequence_entry.get().strip():
            self.generate()

    def create_widgets(self):

        # ==================================================
        # Main layout
        # ==================================================

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        # ==================================================
        # Input sequence
        # ==================================================

        tk.Label(
            self.root,
            text="Input sequence:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=(10, 2)
        )

        sequence_frame = tk.Frame(
            self.root,
            bg=self.BG_COLOR
        )

        sequence_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=10,
            pady=(0, 10)
        )

        sequence_frame.columnconfigure(0, weight=1)

        self.sequence_entry = tk.Entry(
            sequence_frame
        )

        self.sequence_entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.clear_button = tk.Button(
            sequence_frame,
            text="Clear",
            command=self.clear_sequence,
            width=8
        )

        self.clear_button.grid(
            row=0,
            column=1,
            padx=(5, 0)
        )

        # ==================================================
        # Options
        #
        # Column 0 = checkboxes
        # Column 1 = numeric parameters
        # ==================================================

        options_frame = tk.Frame(
            self.root,
            bg=self.BG_COLOR
        )

        options_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=10,
            pady=5
        )

        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(2, weight=1)

        # --------------------------------------------------
        # Left column: checkboxes
        # --------------------------------------------------

        checkbox_frame = tk.Frame(
            options_frame,
            bg=self.BG_COLOR
        )

        checkbox_frame.grid(
            row=0,
            column=0,
            sticky="nw",
            padx=(0, 20)
        )

        tk.Checkbutton(
            checkbox_frame,
            text="Show title",
            variable=self.show_title,
            command=self.checkbox_changed
        ).pack(anchor="w")

        tk.Checkbutton(
            checkbox_frame,
            text="Show sequence text",
            variable=self.show_text,
            command=self.checkbox_changed
        ).pack(anchor="w")

        tk.Checkbutton(
            checkbox_frame,
            text="Show expanded sequence",
            variable=self.show_expanded,
            command=self.checkbox_changed
        ).pack(anchor="w")

        tk.Checkbutton(
            checkbox_frame,
            text="Show A jumper inputs",
            variable=self.show_a_jump,
            command=self.checkbox_changed
        ).pack(anchor="w")

        tk.Checkbutton(
            checkbox_frame,
            text="Show B jumper inputs",
            variable=self.show_b_jump,
            command=self.checkbox_changed
        ).pack(anchor="w")

        checkbox_frame_2 = tk.Frame(
            options_frame,
            bg=self.BG_COLOR
        )

        checkbox_frame_2.grid(
            row=0,
            column=1,
            sticky="nw"
        )

        tk.Checkbutton(
            checkbox_frame_2,
            text="Show jump button",
            variable=self.show_jump_button,
            command=self.checkbox_changed
        ).pack(anchor="w")

        tk.Checkbutton(
            checkbox_frame_2,
            text="Colored icons",
            variable=self.colored_buttons,
            command=self.checkbox_changed
        ).pack(anchor="w")

        tk.Checkbutton(
            checkbox_frame_2,
            text="Directional icon coloring",
            variable=self.directional_colors,
            command=self.checkbox_changed
        ).pack(anchor="w")

        # --------------------------------------------------
        # Right column: numeric parameters
        # --------------------------------------------------

        parameter_frame = tk.Frame(
            options_frame,
            bg=self.BG_COLOR
        )

        parameter_frame.grid(
            row=0,
            column=2,
            sticky="nw"
        )

        self.font_size = self.add_number_entry(
            parameter_frame,
            "Font size:",
            32
        )

        self.stroke_width = self.add_number_entry(
            parameter_frame,
            "Stroke width:",
            2
        )

        self.vertical_spacing = self.add_number_entry(
            parameter_frame,
            "Vertical spacing:",
            1
        )

        self.tech_spacing = self.add_number_entry(
            parameter_frame,
            "Tech spacing:",
            15
        )

        self.input_spacing = self.add_number_entry(
            parameter_frame,
            "Input spacing:",
            0
        )

        # ==================================================
        # Title
        # ==================================================

        title_frame = tk.Frame(
            self.root,
            bg=self.BG_COLOR
        )

        title_frame.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=10,
            pady=5
        )

        title_frame.columnconfigure(1, weight=1)

        tk.Label(
            title_frame,
            text="Title:"
        ).grid(
            row=0,
            column=0,
            padx=(0, 10)
        )

        self.title_entry = tk.Entry(
            title_frame
        )

        self.title_entry.grid(
            row=0,
            column=1,
            sticky="ew"
        )

        # ==================================================
        # Preview area
        # ==================================================

        self.preview_frame = tk.Frame(
            self.root,
            bg=self.PANEL_COLOR
        )

        self.preview_frame.grid(
            row=4,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        self.image_label = tk.Label(
            self.preview_frame,
            bg=self.PANEL_COLOR
        )

        self.image_label.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        # ==================================================
        # Buttons
        # ==================================================

        button_frame = tk.Frame(
            self.root,
            bg=self.BG_COLOR
        )

        button_frame.grid(
            row=5,
            column=0,
            pady=(0, 10)
        )

        self.generate_button = tk.Button(
            button_frame,
            text="Generate",
            command=self.generate,
            width=12
        )

        self.generate_button.pack(
            side="left",
            padx=5
        )

        self.save_button = tk.Button(
            button_frame,
            text="Save",
            command=self.save,
            width=12,
            state="disabled"
        )

        self.save_button.pack(
            side="left",
            padx=5
        )

        self.apply_params(self.get_default_params())

        self.sequence_entry.insert(0, self.example_sequence)
        self.title_entry.insert(0, self.example_title)

    def on_enter(self, event):
        self.generate()

        # Prevent Enter from inserting a newline or
        # triggering other widgets.
        return "break"

    def on_save(self, event):
        self.save()

        return "break"

    def clear_sequence(self):
        self.sequence_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)

        self.generated_image = None
        self.image_tk = None

        self.image_label.config(
            image=""
        )

        self.save_button.config(
            state="disabled"
        )

        self.sequence_entry.focus_set()

    def add_number_entry(self, parent, label, default):
        row = parent.grid_size()[1]

        tk.Label(
            parent,
            text=label
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=2
        )

        entry = tk.Entry(
            parent,
            width=10
        )

        entry.insert(0, str(default))

        entry.grid(
            row=row,
            column=1,
            sticky="w",
            pady=2
        )

        return entry

    def generate(self):
        sequence = self.sequence_entry.get().strip()
        title = self.title_entry.get().strip()

        if not sequence:
            return

        params = self.get_params()
        if not params.show_title and not params.show_text and not params.show_expanded and not params.show_a_jump and not params.show_b_jump:
            return

        try:
            generate_input_sequence(
                sequence,
                params,
                title
            )

            self.generated_image = Image.open(
                params.output_path
            ).convert("RGBA")

            self.update_preview()

            self.save_button.config(
                state="normal"
            )

        except ValueError:
            messagebox.showerror(
                "Invalid parameter",
                "Font size, stroke width, vertical spacing, "
                "input spacing, and tech spacing "
                "must be numbers."
            )

        except Exception as e:
            messagebox.showerror(
                "Generation error",
                str(e)
            )

    def update_preview(self):
        self.resize_job = None

        if self.generated_image is None:
            return

        available_width = self.preview_frame.winfo_width()
        available_height = self.preview_frame.winfo_height()

        if available_width <= 1 or available_height <= 1:
            return

        original_width, original_height = self.generated_image.size

        # Calculate the scale needed to fit the image
        # within both dimensions.
        width_scale = available_width / original_width
        height_scale = available_height / original_height

        scale = min(width_scale, height_scale)

        new_width = max(1, int(original_width * scale))
        new_height = max(1, int(original_height * scale))

        preview = self.generated_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        self.image_tk = ImageTk.PhotoImage(preview)

        self.image_label.config(
            image=self.image_tk
        )

    def on_resize(self, event):
        if event.widget != self.root:
            return

        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)

        self.resize_job = self.root.after(
            100,
            self.update_preview
        )

    def save(self):
        if self.generated_image is None:
            return

        defaultfilename = self.title_entry.get().strip() + ".png"
        path = filedialog.asksaveasfilename(
            title="Save input sequence",
            initialfile=(defaultfilename if defaultfilename != ".png" else "output.png"),
            defaultextension=".png",
            filetypes=[
                ("PNG image", "*.png"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        # Save the original full-resolution image,
        # not the resized preview.
        self.generated_image.save(
            path,
            "PNG"
        )

    def save_settings_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Settings As",
            initialfile="settings.json",
            defaultextension=".json",
            filetypes=[
                ("Input Sequence Settings", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self.settings_path = path

        self.save_settings()

    def save_settings(self):
        if self.settings_path is None:
            self.save_settings_as()
            return

        try:
            params = self.get_params()

            settings = asdict(params)

            with open(
                    self.settings_path,
                    "w",
                    encoding="utf-8"
            ) as file:
                json.dump(
                    settings,
                    file,
                    indent=4
                )

            self.remember_settings_path()

        except ValueError:
            messagebox.showerror(
                "Invalid parameter",
                "Font size, stroke width, vertical spacing, "
                "input spacing, and tech spacing "
                "must be numbers."
            )

        except Exception as e:
            messagebox.showerror(
                "Save Settings Error",
                str(e)
            )

    def load_settings(self):
        path = filedialog.askopenfilename(
            title="Load Settings",
            filetypes=[
                ("Input Sequence Settings", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            with open(
                    path,
                    "r",
                    encoding="utf-8"
            ) as file:
                settings = json.load(file)

            params = InputSequenceParams(**settings)

            self.settings_path = path

            self.apply_params(params)

        except Exception as e:
            messagebox.showerror(
                "Load Settings Error",
                str(e)
            )

    def remember_settings_path(self):
        try:
            with open(
                    self.last_settings_path,
                    "w",
                    encoding="utf-8"
            ) as file:
                file.write(str(self.settings_path))

        except OSError:
            pass

    def load_last_settings(self):
        if not self.last_settings_path.exists():
            return

        try:
            with open(
                    self.last_settings_path,
                    "r",
                    encoding="utf-8"
            ) as file:
                path = file.read().strip()

            if not path:
                return

            settings_path = Path(path)

            if not settings_path.exists():
                return

            with open(
                    settings_path,
                    "r",
                    encoding="utf-8"
            ) as file:
                settings = json.load(file)

            params = InputSequenceParams(**settings)

            self.settings_path = str(settings_path)

            self.apply_params(params)

        except Exception:
            # Don't prevent the application from starting
            # if the previous settings file is invalid.
            self.settings_path = None

    def get_default_params(self):
        return InputSequenceParams()

    def reset_settings(self):
        result = messagebox.askyesno(
            "Reset Settings",
            "Reset all settings to their default values?"
        )

        if not result:
            return

        params = self.get_default_params()

        self.settings_path = None
        self.forget_settings_path()

        self.apply_params(params)

    def forget_settings_path(self):
        try:
            self.last_settings_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


if __name__ == "__main__":
    root = tk.Tk()

    app = InputSequenceUI(root)

    root.mainloop()