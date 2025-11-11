import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import sys

class CsvAnnotationApp:
    """
    Enhanced GUI application for annotating phishing emails.
    Features: Auto-save, skip tracking, notes functionality
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Phishing Email Annotation Tool")
        
        # Maximize window to full screen
        self.root.state('zoomed')  # Windows: maximized
        
        # Set minimum size
        self.root.minsize(1200, 800)

        # --- State Variables ---
        self.df = None
        self.current_index = 0
        self.total_rows = 0
        self.filepath = ""
        self.annotation_column = "phishing_type"  # Column for phishing classification
        self.note_column = "note"  # Column for annotator notes
        self.skip_column = "skip_flag"  # Column to track skipped emails persistently
        self.skipped_indices = set()  # Track skipped emails in current session

        # --- Configuration ---
        # Phishing taxonomy classes (0-3 based on guidelines)
        self.annotation_classes = ["0", "1", "2", "3"]
        self.class_labels = {
            "0": "0: Legitimate",
            "1": "1: Deceptive",
            "2": "2: Targeted", 
            "3": "3: Extortion"
        }

        # --- UI Setup ---

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 10, 'bold'), padding=5)
        style.configure('success.TButton', background='#27ae60', foreground='white', font=('Helvetica', 10, 'bold'), padding=8)
        style.configure('warning.TButton', background='#e67e22', foreground='white', font=('Helvetica', 10, 'bold'), padding=5)
        style.configure('skip.TButton', background='#95a5a6', foreground='white', font=('Helvetica', 10, 'bold'), padding=5)
        style.configure('nav.TButton', font=('Helvetica', 10), padding=5)
        style.configure('TLabel', font=('Helvetica', 10))
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 10, 'italic'))

        # Style for the currently selected annotation button
        style.configure('Selected.TButton', font=('Helvetica', 10, 'bold'), padding=5, background="#3498db", foreground="white")

        # --- Main Frame ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- 1. File Frame ---
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill="x")

        load_button = ttk.Button(file_frame, text="Load CSV", command=self.load_csv)
        load_button.pack(side="left", padx=(0, 10))

        # Navigation buttons next to Load CSV
        self.prev_button = ttk.Button(
            file_frame, text="< Previous", command=self.prev_row, style='nav.TButton'
        )
        self.prev_button.pack(side="left", padx=5)

        self.skip_button = ttk.Button(
            file_frame, text="Skip", command=self.skip_email, style='skip.TButton'
        )
        self.skip_button.pack(side="left", padx=5)

        self.next_button = ttk.Button(
            file_frame, text="Next >", command=self.next_row, style='nav.TButton'
        )
        self.next_button.pack(side="left", padx=5)

        # Skipped emails dropdown
        ttk.Label(file_frame, text="Skipped:", font=('Helvetica', 9)).pack(side="left", padx=(10, 5))
        
        self.skipped_combobox = ttk.Combobox(
            file_frame,
            state="readonly",
            width=15,
            font=('Helvetica', 9)
        )
        self.skipped_combobox.pack(side="left", padx=5)
        self.skipped_combobox.bind("<<ComboboxSelected>>", self.jump_to_skipped_from_dropdown)

        self.file_label = ttk.Label(file_frame, text="No file loaded.", style='Status.TLabel', anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # --- 2. Progress and Status Frame ---
        progress_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 10))
        progress_frame.pack(fill="x")

        self.progress_label = ttk.Label(progress_frame, text="Row 0 / 0", style='Header.TLabel', anchor="w")
        self.progress_label.pack(side="left", pady=5)

        # Skipped counter
        self.skipped_label = ttk.Label(progress_frame, text="Skipped: 0", style='Status.TLabel', foreground="#e67e22")
        self.skipped_label.pack(side="left", padx=20, pady=5)

        # Jump to Row controls
        self.jump_button = ttk.Button(
            progress_frame,
            text="Go",
            command=self.jump_to_row_event,
            style='nav.TButton'
        )
        self.jump_button.pack(side="right", padx=(5, 0))

        self.jump_entry = ttk.Entry(
            progress_frame,
            width=8,
            font=('Helvetica', 10)
        )
        self.jump_entry.pack(side="right", padx=5)
        self.jump_entry.bind("<Return>", self.jump_to_row_event)

        jump_label = ttk.Label(progress_frame, text="Jump to Row:")
        jump_label.pack(side="right")

        # --- 3. Data Display Frame ---
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill="both", expand=True, pady=10)

        # Add scrollbars to the Text widget
        text_scrollbar_y = ttk.Scrollbar(display_frame, orient="vertical")

        self.text_display = tk.Text(
            display_frame,
            wrap="word",
            font=("Calibri", 11),
            bg="#fdfdfd",
            relief="solid",
            borderwidth=1,
            yscrollcommand=text_scrollbar_y.set
        )

        text_scrollbar_y.config(command=self.text_display.yview)
        text_scrollbar_y.pack(side="right", fill="y")
        self.text_display.pack(side="left", fill="both", expand=True)

        # --- 4. Notes Frame ---
        notes_frame = ttk.Frame(main_frame, padding=(0, 5, 0, 10))
        notes_frame.pack(fill="x")

        notes_label = ttk.Label(notes_frame, text="Note (optional):", font=('Helvetica', 10, 'bold'))
        notes_label.pack(side="left", padx=(0, 5))

        self.note_entry = ttk.Entry(notes_frame, font=('Helvetica', 10))
        self.note_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.note_entry.bind("<Return>", lambda e: self.save_note())

        self.save_note_button = ttk.Button(
            notes_frame,
            text="Save Note",
            command=self.save_note,
            style='warning.TButton',
            width=12
        )
        self.save_note_button.pack(side="right", padx=(5, 0))

        # --- 5. Classification Buttons Frame ---
        annotation_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 10))
        annotation_frame.pack(fill="x")

        classification_label = ttk.Label(annotation_frame, text="Classify Email:", font=('Helvetica', 11, 'bold'))
        classification_label.pack(side="top", anchor="w", pady=(0, 5))

        buttons_subframe = ttk.Frame(annotation_frame)
        buttons_subframe.pack(fill="x")

        self.annotation_buttons = {}
        num_classes = len(self.annotation_classes)
        for i, class_num in enumerate(self.annotation_classes):
            label_text = self.class_labels[class_num]
            btn = ttk.Button(
                buttons_subframe,
                text=label_text,
                command=lambda c=class_num: self.annotate_and_next(c)
            )
            btn.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            buttons_subframe.grid_columnconfigure(i, weight=1)
            self.annotation_buttons[class_num] = btn

        # --- 6. Save Frame ---
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill="x", pady=(10, 0))

        # Progress statistics
        self.stats_label = ttk.Label(
            save_frame, 
            text="Annotated: 0 / 0 (0.0%)",
            style='Status.TLabel',
            anchor="w"
        )
        self.stats_label.pack(fill="x", pady=(0, 5))

        self.save_button = ttk.Button(
            save_frame, text="💾 Save Progress (Auto-saves every 10 annotations)", 
            command=self.manual_save, style='success.TButton'
        )
        self.save_button.pack(fill="x")

        # --- Initial State ---
        self.disable_controls()

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
            # Try loading with default UTF-8 first
            try:
                self.df = pd.read_csv(
                    filepath,
                    keep_default_na=False,
                    na_values=[''],
                    engine='python'
                )
            except UnicodeDecodeError:
                # If UTF-8 fails, try 'latin1'
                self.df = pd.read_csv(
                    filepath,
                    keep_default_na=False,
                    na_values=[''],
                    engine='python',
                    encoding='latin1'
                )

            # Check if annotation column exists, if not, create it
            if self.annotation_column not in self.df.columns:
                self.df[self.annotation_column] = pd.NA

            # Check if note column exists, if not, create it
            if self.note_column not in self.df.columns:
                self.df[self.note_column] = pd.NA

            # Check if skip_flag column exists, if not, create it
            if self.skip_column not in self.df.columns:
                self.df[self.skip_column] = 0  # 0 = not skipped, 1 = skipped

            # Ensure proper data types
            self.df[self.annotation_column] = self.df[self.annotation_column].astype(str).replace(['', 'nan', '<NA>'], pd.NA)
            self.df[self.note_column] = self.df[self.note_column].astype(str).replace(['', 'nan', '<NA>'], pd.NA)
            self.df[self.skip_column] = pd.to_numeric(self.df[self.skip_column], errors='coerce').fillna(0).astype(int)

            self.filepath = filepath
            self.file_label.config(text=f"Loaded: {self.filepath.split('/')[-1]}")
            self.total_rows = len(self.df)
            
            # Load previously skipped emails from CSV
            self.skipped_indices = set(self.df[self.df[self.skip_column] == 1].index.tolist())

            # Auto-detect where to resume (find first unannotated email)
            self.current_index = self.find_resume_position()

            # Auto-save immediately after loading to add new columns
            self.auto_save()

            # Update the skipped dropdown with loaded skip flags
            self.update_skipped_dropdown()

            self.update_display()
            self.update_stats()
            self.enable_controls()

            # Show resume message
            if self.current_index > 0:
                annotated_count = self.df[self.annotation_column].notna().sum()
                messagebox.showinfo(
                    "Resuming Progress", 
                    f"Loaded {self.total_rows} emails.\n\n"
                    f"✅ Found {annotated_count} already annotated.\n"
                    f"📍 Resuming from email #{self.current_index + 1}\n\n"
                    f"Auto-save enabled - progress saved every 10 annotations."
                )
            else:
                messagebox.showinfo(
                    "Success", 
                    f"Loaded {self.total_rows} emails.\n\n"
                    f"Auto-save enabled - progress saved every 10 annotations."
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.disable_controls()

    def find_resume_position(self):
        """
        Finds the first row that hasn't been annotated yet.
        Returns the index to resume from.
        """
        if self.df is None or len(self.df) == 0:
            return 0
        
        # Find first row where phishing_type is not annotated (NA/empty)
        unannotated_mask = self.df[self.annotation_column].isna()
        
        if unannotated_mask.any():
            # Return the index of the first unannotated row
            first_unannotated = unannotated_mask.idxmax()
            return first_unannotated
        else:
            # All rows are annotated, start from the beginning
            return 0

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

        # Update skipped label
        self.skipped_label.config(text=f"Skipped: {len(self.skipped_indices)}")

        # Get row data
        row_data = self.df.iloc[self.current_index]

        # Format display text - show the text_cleaned column (first column with email content)
        display_text = ""
        try:
            # Try to find text_cleaned column, otherwise use first column
            if 'text_cleaned' in self.df.columns:
                email_body = row_data['text_cleaned']
            else:
                first_col_name = self.df.columns[0]
                email_body = row_data[first_col_name]
            
            display_text = str(email_body) if pd.notna(email_body) else "[No email content]"
            
            # Add metadata if available
            metadata = []
            if 'sender' in self.df.columns and pd.notna(row_data.get('sender')):
                metadata.append(f"Sender: {row_data['sender']}")
            if 'receiver' in self.df.columns and pd.notna(row_data.get('receiver')):
                metadata.append(f"Receiver: {row_data['receiver']}")
            if 'subject' in self.df.columns and pd.notna(row_data.get('subject')):
                metadata.append(f"Subject: {row_data['subject']}")
            if 'source_dataset' in self.df.columns and pd.notna(row_data.get('source_dataset')):
                metadata.append(f"Source: {row_data['source_dataset']}")
            
            if metadata:
                display_text = "\n".join(metadata) + "\n" + "="*80 + "\n\n" + display_text
                
        except Exception as e:
            display_text = f"Error displaying email: {e}"

        # Update text widget
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", display_text)
        self.text_display.config(state="disabled")

        # Update note entry with existing note
        current_note = row_data.get(self.note_column)
        self.note_entry.delete(0, "end")
        if pd.notna(current_note):
            self.note_entry.insert(0, str(current_note))

        # Update button states (highlight current annotation)
        current_annotation = row_data.get(self.annotation_column)

        for class_num, btn in self.annotation_buttons.items():
            if pd.notna(current_annotation) and str(class_num) == str(current_annotation):
                btn.config(style='Selected.TButton')
            else:
                btn.config(style='TButton')

        # Highlight if this email is skipped
        if self.current_index in self.skipped_indices:
            self.text_display.config(bg="#fff3cd")  # Light yellow background
        else:
            self.text_display.config(bg="#fdfdfd")  # Normal background

        # Update nav button states
        self.prev_button.config(state="normal" if self.current_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_index < self.total_rows - 1 else "disabled")

    def update_stats(self):
        """
        Updates the annotation statistics display.
        """
        if self.df is None:
            return
        
        # Count annotated emails (non-null phishing_type)
        annotated_count = self.df[self.annotation_column].notna().sum()
        percentage = (annotated_count / self.total_rows * 100) if self.total_rows > 0 else 0
        
        self.stats_label.config(
            text=f"Annotated: {annotated_count} / {self.total_rows} ({percentage:.1f}%) | Skipped: {len(self.skipped_indices)}"
        )

    def save_note(self):
        """
        Saves the note for the current email.
        """
        if self.df is None:
            return

        note_text = self.note_entry.get().strip()
        
        if note_text:
            self.df.at[self.current_index, self.note_column] = note_text
            messagebox.showinfo("Note Saved", "Note saved successfully!")
        else:
            # Clear note if entry is empty
            self.df.at[self.current_index, self.note_column] = pd.NA
            messagebox.showinfo("Note Cleared", "Note cleared.")
        
        # Auto-save
        self.auto_save()
        self.update_stats()

    def skip_email(self):
        """
        Marks the current email as skipped and moves to next.
        """
        if self.df is None:
            return

        # Add to skipped set
        self.skipped_indices.add(self.current_index)
        
        # Mark in DataFrame
        self.df.at[self.current_index, self.skip_column] = 1
        
        # Update dropdown
        self.update_skipped_dropdown()
        
        # Auto-save to persist the skip flag
        self.auto_save()
        
        # Move to next
        self.next_row()

    def update_skipped_dropdown(self):
        """
        Updates the dropdown list with currently skipped emails.
        """
        if not self.skipped_indices:
            self.skipped_combobox['values'] = ["No skipped emails"]
            self.skipped_combobox.set("No skipped emails")
        else:
            skipped_list = sorted(list(self.skipped_indices))
            # Format as "Row X" for display
            dropdown_values = [f"Row {idx + 1}" for idx in skipped_list]
            self.skipped_combobox['values'] = dropdown_values
            self.skipped_combobox.set(f"{len(skipped_list)} skipped email(s)")

    def jump_to_skipped_from_dropdown(self, event=None):
        """
        Jumps to the email selected in the skipped dropdown.
        """
        selected = self.skipped_combobox.get()
        if selected and selected.startswith("Row "):
            try:
                row_num = int(selected.split("Row ")[1])
                self.current_index = row_num - 1  # Convert to 0-based
                self.update_display()
            except (ValueError, IndexError):
                pass

    def show_skipped_emails(self):
        """
        Shows a list of all skipped email indices.
        """
        if not self.skipped_indices:
            messagebox.showinfo("No Skipped Emails", "You haven't skipped any emails yet.")
            return

        skipped_list = sorted(list(self.skipped_indices))
        skipped_rows = [str(idx + 1) for idx in skipped_list]  # Convert to 1-based
        
        message = f"Skipped emails (Row numbers):\n\n{', '.join(skipped_rows)}\n\nTotal: {len(skipped_list)}"
        
        messagebox.showinfo("Skipped Emails", message)

    def goto_next_skipped(self):
        """
        Navigates to the next skipped email after the current position.
        """
        if not self.skipped_indices:
            messagebox.showinfo("No Skipped Emails", "No skipped emails to navigate to.")
            return

        # Find next skipped index after current position
        skipped_list = sorted(list(self.skipped_indices))
        
        next_skipped = None
        for idx in skipped_list:
            if idx > self.current_index:
                next_skipped = idx
                break
        
        # If no skipped after current, wrap to first skipped
        if next_skipped is None:
            next_skipped = skipped_list[0]
        
        self.current_index = next_skipped
        self.update_display()

    def annotate_and_next(self, label):
        """
        Saves the annotation for the current row and moves to the next.
        """
        if self.df is None:
            return

        self.df.at[self.current_index, self.annotation_column] = label
        
        # Remove from skipped set if it was skipped and clear skip flag
        if self.current_index in self.skipped_indices:
            self.skipped_indices.remove(self.current_index)
            self.df.at[self.current_index, self.skip_column] = 0
            self.update_skipped_dropdown()

        # Auto-save every 10 annotations
        if (self.df[self.annotation_column].notna().sum()) % 10 == 0:
            self.auto_save()

        self.update_stats()
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


    def jump_to_row_event(self, event=None):
        """
        Handles the 'Go' button click or <Return> key press to jump to a row.
        """
        if self.df is None:
            return

        try:
            row_str = self.jump_entry.get()
            if not row_str:
                return

            row_num = int(row_str)

            if 1 <= row_num <= self.total_rows:
                self.current_index = row_num - 1
                self.update_display()
            else:
                messagebox.showwarning(
                    "Invalid Row",
                    f"Please enter a row number between 1 and {self.total_rows}."
                )
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid number."
            )
        finally:
            self.jump_entry.delete(0, "end")

    def manual_save(self):
        """
        Manually saves the current state to the same CSV file.
        """
        if self.df is None:
            messagebox.showwarning("No Data", "No data loaded to save.")
            return

        try:
            self.df.to_csv(self.filepath, index=False)
            messagebox.showinfo("Success", f"Progress saved to:\n{self.filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def auto_save(self):
        """
        Performs an automatic save to the original file path.
        """
        if self.df is not None and self.filepath:
            try:
                self.df.to_csv(self.filepath, index=False)
                print(f"✓ Auto-saved to {self.filepath}")
            except Exception as e:
                print(f"✗ Auto-save failed: {e}")

    def disable_controls(self):
        """Disables all controls except the 'Load' button."""
        for btn in self.annotation_buttons.values():
            btn.config(state="disabled")
        self.prev_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.skip_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.save_note_button.config(state="disabled")
        self.jump_button.config(state="disabled")
        self.jump_entry.config(state="disabled")
        self.note_entry.config(state="disabled")
        # Some controls may not exist yet depending on init order; guard with hasattr
        if hasattr(self, 'view_skipped_button') and self.view_skipped_button is not None:
            try:
                self.view_skipped_button.config(state="disabled")
            except Exception:
                pass
        if hasattr(self, 'skipped_combobox') and self.skipped_combobox is not None:
            try:
                self.skipped_combobox.config(state="disabled")
            except Exception:
                pass
        if hasattr(self, 'goto_next_skipped_button') and self.goto_next_skipped_button is not None:
            try:
                self.goto_next_skipped_button.config(state="disabled")
            except Exception:
                pass

        self.text_display.config(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", "Please load a CSV file to begin annotation.\n\nThis tool will auto-save your progress to the same file every 10 annotations.")
        self.text_display.config(state="disabled")

    def enable_controls(self):
        """Enables all controls after a file is loaded."""
        for btn in self.annotation_buttons.values():
            btn.config(state="normal")
        self.skip_button.config(state="normal")
        self.save_button.config(state="normal")
        self.save_note_button.config(state="normal")
        self.jump_button.config(state="normal")
        self.jump_entry.config(state="normal")
        self.note_entry.config(state="normal")
        # Guard optional controls
        if hasattr(self, 'view_skipped_button') and self.view_skipped_button is not None:
            try:
                self.view_skipped_button.config(state="normal")
            except Exception:
                pass
        if hasattr(self, 'skipped_combobox') and self.skipped_combobox is not None:
            try:
                self.skipped_combobox.config(state="readonly")
            except Exception:
                pass
        # Nav and goto_next_skipped buttons are managed by update_display()
        self.update_display()


# --- Main execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CsvAnnotationApp(root)
    root.mainloop()
