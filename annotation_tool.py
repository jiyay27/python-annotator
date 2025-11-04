import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import sys

class CsvAnnotationApp:
    """
    A simple GUI application for annotating CSV data.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("CSV Annotation Tool")
        self.root.geometry("800x700")

        # --- State Variables ---
        self.df = None
        self.current_index = 0
        self.total_rows = 0
        self.filepath = ""
        self.annotation_column = "annotation" # Name of the column to store annotations

        # --- Configuration ---
        # Ask the user for classification labels
        self.annotation_classes = self.get_annotation_classes()
        if not self.annotation_classes:
            root.destroy()  # Quit if user cancels
            sys.exit("No annotation classes provided.")

        # --- UI Setup ---

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 10, 'bold'), padding=5)
        style.configure('success.TButton', background='green', foreground='white')
        style.configure('nav.TButton', font=('Helvetica', 10), padding=5)
        style.configure('TLabel', font=('Helvetica', 10))
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 10, 'italic'))

        # --- ADD THIS ---
        # Style for the currently selected annotation button
        style.configure('Selected.TButton', font=('Helvetica', 10, 'bold'), padding=5, background="#a9d1de")
        # ---------------

        # --- Main Frame ---
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- 1. File Loading Frame ---
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill="x", pady=(0, 10))

        self.load_button = ttk.Button(file_frame, text="Load CSV", command=self.load_csv)
        self.load_button.pack(side="left", padx=(0, 10))

        self.file_label = ttk.Label(file_frame, text="No file loaded.", anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True)

        # --- 2. Progress Frame ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(5, 10))

        self.progress_label = ttk.Label(progress_frame, text="Row 0 / 0", style='Header.TLabel', anchor="center")
        self.progress_label.pack(fill="x")

        # --- 3. Data Display Frame ---
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill="both", expand=True, pady=10)

        # Add scrollbars to the Text widget
        text_scrollbar_y = ttk.Scrollbar(display_frame, orient="vertical")
        # text_scrollbar_x = ttk.Scrollbar(display_frame, orient="horizontal") # Removed horizontal scrollbar

        self.text_display = tk.Text(
            display_frame,
            height=20,
            width=80,
            wrap="word",  # Changed from "none" to "word" for email body
            font=("Calibri", 12),
            bg="#fdfdfd",
            relief="solid",
            borderwidth=1,
            yscrollcommand=text_scrollbar_y.set,
            # xscrollcommand=text_scrollbar_x.set # Removed horizontal scrollbar command
        )

        text_scrollbar_y.config(command=self.text_display.yview)
        # text_scrollbar_x.config(command=self.text_display.xview) # Removed

        text_scrollbar_y.pack(side="right", fill="y")
        # text_scrollbar_x.pack(side="bottom", fill="x") # Removed
        self.text_display.pack(side="left", fill="both", expand=True)

        # --- 4. Annotation Buttons Frame ---
        annotation_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 10))
        annotation_frame.pack(fill="x")

        self.annotation_buttons = {}
        # Distribute buttons evenly
        num_classes = len(self.annotation_classes)
        for i, label in enumerate(self.annotation_classes):
            btn = ttk.Button(
                annotation_frame,
                text=label,
                command=lambda l=label: self.annotate_and_next(l)
            )
            # Use grid to make buttons fill the space
            btn.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            annotation_frame.grid_columnconfigure(i, weight=1)
            self.annotation_buttons[label] = btn

        # --- 5. Navigation Frame ---
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill="x", pady=10)

        self.prev_button = ttk.Button(
            nav_frame, text="< Previous", command=self.prev_row, style='nav.TButton'
        )
        self.prev_button.pack(side="left", expand=True, fill="x", padx=5)

        self.next_button = ttk.Button(
            nav_frame, text="Next (Skip) >", command=self.next_row, style='nav.TButton'
        )
        self.next_button.pack(side="right", expand=True, fill="x", padx=5)

        # --- 6. Save Frame ---
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill="x", pady=(10, 0))

        self.save_button = ttk.Button(
            save_frame, text="Save Annotations", command=self.save_csv, style='success.TButton'
        )
        self.save_button.pack(fill="x")

        # --- Initial State ---
        self.disable_controls()

    def get_annotation_classes(self):
        """
        Shows a simple dialog to ask the user for the annotation classes.
        """
        classes_str = simpledialog.askstring(
            "Setup",
            "Enter your classification labels, separated by a comma:",
            initialvalue="Deceptive, Targeted, Extortion/Blackmail" # Changed labels
        )
        if classes_str:
            return [label.strip() for label in classes_str.split(',') if label.strip()]
        return None

    def load_csv(self):
        """
        Loads a CSV file into a pandas DataFrame.
        """
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            # --- NEW ROBUST LOADING ---
            # Try loading with default UTF-8 first
            try:
                self.df = pd.read_csv(
                    filepath,
                    dtype=str,              # Read all columns as text
                    keep_default_na=False,  # Don't auto-detect 'NA', 'NULL'
                    na_values=[''],         # Only treat empty strings as NA
                    engine='python'         # Use the more flexible python engine
                )
            except UnicodeDecodeError:
                # If UTF-8 fails, try 'latin1' (common for many datasets)
                self.df = pd.read_csv(
                    filepath,
                    dtype=str,
                    keep_default_na=False,
                    na_values=[''],
                    engine='python',
                    encoding='latin1'       # Try a different encoding
                )
            # --- END NEW ROBUST LOADING ---

            # Check if annotation column exists, if not, create it
            if self.annotation_column not in self.df.columns:
                self.df[self.annotation_column] = pd.NA

            # Fill Na/NaN with pd.NA for consistent handling
            # We use pd.NA (pandas's newer, better NA)
            self.df[self.annotation_column] = self.df[self.annotation_column].replace('', pd.NA).fillna(pd.NA)

            self.filepath = filepath
            self.file_label.config(text=f"Loaded: ...{self.filepath[-40:]}")
            self.current_index = 0
            self.total_rows = len(self.df)

            self.update_display()
            self.enable_controls()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.disable_controls()

    def update_display(self):
        """
        Updates the GUI elements with the data from the current row.
        """
        if self.df is None or self.total_rows == 0:
            return

        # Update progress label
        self.progress_label.config(
            text=f"Row {self.current_index + 1} / {self.total_rows}"
        )

        # Get row data
        row_data = self.df.iloc[self.current_index]

        # Format display text
        display_text = ""
        try:
            # Get the name of the first column (Column A)
            first_col_name = self.df.columns[0]
            # Get the value from that column
            email_body = row_data[first_col_name]
            # Ensure it's a string, handle potential None/NaN values
            display_text = str(email_body) if pd.notna(email_body) else ""
        except IndexError:
            display_text = "Error: Could not read first column."
        except Exception as e:
            display_text = f"An error occurred displaying data: {e}"

        # max_col_width = max(len(col) for col in self.df.columns if col != self.annotation_column) + 3 # Removed

        # for col, value in row_data.items(): # Removed loop
        #     if col != self.annotation_column:
        #         # Add padding to align values
        #         padding = " " * (max_col_width - len(col))
        #         display_text += f"{col.upper()}:{padding}{value}\n\n"

        # Update text widget
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", display_text)
        self.text_display.config(state="disabled")

        # Update button states (highlight current annotation)
        current_annotation = row_data.get(self.annotation_column)

        for label, btn in self.annotation_buttons.items():
            # This check is now robust against pd.NA
            if pd.notna(current_annotation) and label == current_annotation:
                btn.config(style='Selected.TButton') # Apply the selected style
            else:
                btn.config(style='TButton') # Apply the default style

        # Update nav button states
        self.prev_button.config(state="normal" if self.current_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_index < self.total_rows - 1 else "disabled")

    def annotate_and_next(self, label):
        """
        Saves the annotation for the current row and moves to the next.
        """
        if self.df is None:
            return

        self.df.at[self.current_index, self.annotation_column] = label

        # Auto-save every 10 annotations (optional, but good practice)
        if self.current_index % 10 == 0:
            self.auto_save()

        self.next_row()

    def next_row(self):
        """
        Moves to the next row, if possible.
        """
        if self.df is not None and self.current_index < self.total_rows - 1:
            self.current_index += 1
            self.update_display()

    def prev_row(self):
        """
        Moves to the previous row, if possible.
        """
        if self.df is not None and self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def save_csv(self):
        """
        Saves the DataFrame with annotations to a new CSV file.
        """
        if self.df is None:
            messagebox.showwarning("No Data", "No data loaded to save.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="annotated_data.csv",
            title="Save Annotations As"
        )
        if not save_path:
            return

        try:
            # Save without the pandas index
            self.df.to_csv(save_path, index=False)
            messagebox.showinfo("Success", f"Annotations saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def auto_save(self):
        """
        Performs an automatic save to the original file path.
        """
        if self.df is not None and self.filepath:
            try:
                self.df.to_csv(self.filepath, index=False)
                print(f"Auto-saved progress to {self.filepath}")
            except Exception as e:
                print(f"Auto-save failed: {e}")

    def disable_controls(self):
        """Disables all controls except the 'Load' button."""
        for btn in self.annotation_buttons.values():
            btn.config(state="disabled")
        self.prev_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", "Please load a CSV file to begin.")
        self.text_display.config(state="disabled")

    def enable_controls(self):
        """Enables all controls after a file is loaded."""
        for btn in self.annotation_buttons.values():
            btn.config(state="normal")
        self.save_button.config(state="normal")
        # Nav buttons are enabled/disabled by update_display()


# --- Main execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CsvAnnotationApp(root)
    root.mainloop()





