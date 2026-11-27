import tkinter as tk
from PIL import ImageTk, Image

def show_image(image_path):
    # Load the PNG and keep a reference so Python doesn't garbage-collect it
    pic = Image.open(image_path)
    resized = pic.resize((800, 600))
    new_pic = ImageTk.PhotoImage(resized)
    image_label.config(image=new_pic)
    image_label.image = new_pic  

# Set up the main window
root = tk.Tk()
root.title("PNG Viewer")
root.geometry("1000x700")

# Frame to hold the buttons at the top
button_frame = tk.Frame(root)
button_frame.pack(pady=0)

# Create buttons for each PNG
btn1 = tk.Button(button_frame, text="Sales by Genre", command=lambda: show_image("GitHub/AgileProjectManagement/outputs/genre_sales.png"))
btn1.pack(side=tk.LEFT, padx=5)

btn2 = tk.Button(button_frame, text="Sales by Region", command=lambda: show_image("GitHub/AgileProjectManagement/outputs/regional_sales.png"))
btn2.pack(side=tk.LEFT, padx=5)

btn3 = tk.Button(button_frame, text="Top 10 Games", command=lambda: show_image("GitHub/AgileProjectManagement/outputs/top_10_games.png"))
btn3.pack(side=tk.LEFT, padx=5)

# Label widget where the PNG will be displayed
image_label = tk.Label(root, text="Click a button to load an image")
image_label.pack(expand=True)


if __name__ == '__main__':
    root.mainloop()