import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import json
from typing import List, Dict
import threading

class ChatUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chat Application")
        self.root.geometry("600x800")
        
        # Create main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create chat display area
        self.chat_display = scrolledtext.ScrolledText(
            self.main_container,
            wrap=tk.WORD,
            width=50,
            height=30,
            font=("Arial", 10)
        )
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.chat_display.config(state=tk.DISABLED)
        
        # Create input area
        self.input_var = tk.StringVar()
        self.input_field = ttk.Entry(
            self.main_container,
            textvariable=self.input_var,
            font=("Arial", 10)
        )
        self.input_field.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        
        # Create send button
        self.send_button = ttk.Button(
            self.main_container,
            text="Send",
            command=self.send_message
        )
        self.send_button.grid(row=1, column=1, sticky=(tk.E), pady=5)
        
        # Configure grid weights
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.columnconfigure(1, weight=0)
        self.main_container.rowconfigure(0, weight=1)
        
        # Bind enter key to send message
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        # API endpoint
        self.api_url = "http://localhost:8000"
        
        # Load chat history on startup
        self.load_chat_history()

    def append_message_to_display(self, message: str, is_user: bool = True):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{'You' if is_user else 'Assistant'}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def send_message(self):
        message = self.input_var.get().strip()
        if not message:
            return
        
        # Clear input field
        self.input_var.set("")
        
        # Display user message
        self.append_message_to_display(message)
        
        # Disable input while waiting for response
        self.input_field.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        
        # Send message in a separate thread
        threading.Thread(target=self.send_message_to_api, args=(message,), daemon=True).start()

    def send_message_to_api(self, message: str):
        try:
            response = requests.post(
                f"{self.api_url}/ask",
                json={"prompt": message}
            )
            response.raise_for_status()
            reply = response.json().get("reply", "Sorry, I couldn't process that.")
            
            # Update UI in the main thread
            self.root.after(0, self.handle_api_response, reply)
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            self.root.after(0, self.handle_api_response, error_message)
        
        # Re-enable input in the main thread
        self.root.after(0, self.enable_input)

    def handle_api_response(self, reply: str):
        self.append_message_to_display(reply, is_user=False)

    def enable_input(self):
        self.input_field.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.input_field.focus()

    def load_chat_history(self):
        try:
            response = requests.get(f"{self.api_url}/chat")
            response.raise_for_status()
            
            history = response.json()
            messages = history.get("messages", [])
            
            for message in messages:
                self.append_message_to_display(message["prompt"])
                self.append_message_to_display(message["reply"], is_user=False)
                
        except Exception as e:
            self.append_message_to_display(f"Error loading chat history: {str(e)}", is_user=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatUI(root)
    root.mainloop()