#creator: oralc 
#function: The script allows the user to determine and classify 3 different types of up to 6 objects and transmit the data via CAN protocol

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import can
import cantools
import time

class Object_Detection_on_Static_Frame(tk.Tk):
    
    # Define the CAN Info below
    #specify the dbc file directory
    dbc = cantools.db.load_file("C:/Users-xxx-.dbc") 
    #specify the dbc file directory
    bus = can.interface.Bus(channel='PCAN_USBBUS1', interface='pcan', bitrate=500000)
    message = dbc.get_message_by_name("CAM_OBJ_Detection") 
    arbit_id = 0x665
    
    def __init__(self):
        super().__init__()

        # window basic settings
        self.title("Adaptive High Beam Simulator")
        self.geometry("1400x1400")
        self.init_widgets()
        
        # flag for image_loaded to 
        self.image_uploaded = False
        
        self.rect_counter = 1

    def init_widgets(self):
        
        # buttons and widgets
        self.description = tk.Label(self, text="Welcome to the Object Detection Simulator for ADB.\n \n 1. Load an image for the background. \n 2. Choose the object type from the drop-down menu \n 3. Draw the object boundries by drawing on canvas \n 4. Report object information or Delete the incorrectly created objects \n 5. Send the object information via CAN." , font=('Arial',10, 'bold'))
        self.description.pack(pady=15)

        # buttons to upload image
        self.upload_btn = tk.Button(self, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(pady=20)

        # canvas to display image and allow drawing
        self.canvas = tk.Canvas(self, width=256*5, height=32*5)
        self.canvas.pack(pady=10)
        
        # horizontal alligment
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=15)
        
        self.current_obj = tk.Button(self.button_frame, text="Report Object Infomation", command=self.report_object)
        self.current_obj.grid(row=0, column=1, padx=10)
        
        self.reset_btn = tk.Button(self.button_frame, text="Reset Objects", command=self.reset_image)
        self.reset_btn.grid(row=0, column=2, padx=30)
        
        
        # object type dropdown for OBJ type
        self.obj_types = ["Vehicle", "Traffic Sign", "Pedestrian", "Wet Road", "Animal"]
        self.current_obj_type = tk.StringVar()
        self.obj_type_dd = ttk.Combobox(self.button_frame, textvariable=self.current_obj_type, values=self.obj_types)
        self.obj_type_dd.set("Vehicle")  # default value
        self.obj_type_dd.grid(row=0, column=0, padx=10)  # adjust grid to fit it in
        
        # dropdown for OBJ state
        self.obj_states = ["Same Direction", "Incoming", "Static"]
        self.current_obj_state = tk.StringVar()
        self.obj_state_dd = ttk.Combobox(self.button_frame, textvariable=self.current_obj_state, values=self.obj_states)
        self.obj_state_dd.set("Same Direction")  # def
        self.obj_state_dd.grid(row=1, column=0, padx=10)  # right-below the Obj type


        
        self.report_text = tk.Text(self, height=10, width=80)
        self.report_text.pack(pady=20)

       
        self.send_btn = tk.Button(self, text="Send Coordinates", command=self.send_image)
        self.send_btn.pack(pady=20)
        
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_relese)

        # variables for drawing
        self.start_x = None
        self.start_y = None
        self.rects = {}

        self.max_rects = 6  # max number of rectangles/objects


    def upload_image(self):
        # get image file path
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
            
        # validate and set image as a canvas
        if file_path: #check if file is selected
            with Image.open(file_path) as img:
                # validate image ratio
                if  3.9 < img.width / img.height < 4.1 :  # e3nsure that aspect ratio is 4:1 or close
                    # resizing and setting the image only for display
                    img_resized = img.resize((256*5, 64*5), Image.LANCZOS) 
                    # set up and display the resized image on Tk
                    self.tk_img = ImageTk.PhotoImage(img_resized)
                    self.canvas.config(width=img_resized.width, height=img_resized.height)
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
                    # flag true now user able to draw
                    self.image_uploaded = True
              
                else:
                    messagebox.showerror("Invalid Image", "Please upload an image with a 4:1 aspect ratio.")

    ##events for oject drawing ##
    #store starting points..
    def on_press(self,event):
        if not self.image_uploaded:
            messagebox.showwarning("Warning", "Please upload an image before drawing")
            return       
        
        #check the number of 
        if len(self.rects) >= self.max_rects:
            messagebox.showwarning("Warning", "You can only draw up to 6 obejects")
            return

        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        
    # store end points, save coordinates, store rec's ID & print
    def on_relese(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        #draw the yellow rectangular boundry
        self.canvas.create_rectangle(self.start_x, self.start_y, end_x, end_y, outline = "yellow", tags = "rect")

        # fit the x and y-coordinates into reserved bit lenght in        
        ax = max(0, min(int(self.start_x/5), 255))  
        ay = max(0, min(int(self.start_y/5), 63))  
        dx = max(0, min(int(end_x/5), 255))  
        dy = max(0, min(int(end_y/5), 63))  

      
        # save the rect's coordinates
        self.rects[self.rect_counter] = (ax, ay, dx, dy, self.current_obj_type.get(), self.current_obj_state.get())

        print(f" Rectangle No:{self.rect_counter} \n Type:{self.current_obj_type.get()} \n Type:{self.current_obj_state.get()} \n Coordinates:A_X={ax}, A_Y={ay}, D_X={dx}, D_Y={dy} \n \n ")
        self.rect_counter += 1
        #reset starting points
        self.start_x = None
        self.start_y = None
    

    
    def report_object(self):
        # clear the report_text widget
        self.report_text.delete(1.0, tk.END)
    
        # infor users by reporting rects infos to the report_text widget.
        for idss, data in self.rects.items():
            coords = data[:4]  # first four values are coordinates
            obj_type = data[4]  # fifth value is the object type
            obj_state = data[5]  # fifth value is the object type
            self.report_text.insert(tk.END, f"Rectangle ID: {idss}\n")
            self.report_text.insert(tk.END, f"Object Type: {obj_type}\n")
            self.report_text.insert(tk.END, f"Object State: {obj_state}\n")
            self.report_text.insert(tk.END, f"Coordinates: A_X={coords[0]}, A_Y={coords[1]}, D_X={coords[2]}, D_Y={coords[3]}\n")
            self.report_text.insert(tk.END, "-"*30 + "\n")
            
        

    def reset_image(self):
        # delete all rectangles from the canvas
        self.canvas.delete("rect")
        # clear the stored rectangle coordinates
        self.rects.clear()
        # clear the report text widget
        self.report_text.delete(1., tk.END)
        #reset to counter again
        self.rect_counter = 1
        return


    # obj type to integer mapping
    def get_object_type_int(self, obj_type):
        # map object types to integers
        choices = {
            "Vehicle": 0, 
            "Traffic Sign": 1, 
            "Pedestrian": 2, 
            "Wet Road": 3, 
            "Animal": 4,
        }
        return choices[obj_type]  # returns the intobj_type
    # obj state to integer mapping
    def get_obj_state_int(self, obj_state):
        state_map = {
            "Same Direction": 0,
            "Incoming": 1,
            "Static": 2
        }
        return state_map[obj_state]

    
    def send_image(self):
        for idss, data in self.rects.items():
            # convert object type to its integer representation
            obj_type_int = self.get_object_type_int(data[4])
            obj_state_int = self.get_obj_state_int(data[5])

            # send current object coordinates
            data_store = self.message.encode({
                "CAM_OBJ_Type": obj_type_int ,  # length: 3-bit [0-7]
                "CAM_OBJ_State": obj_state_int,  # length: 2-bit 
                "CAM_OBJ_ID" : idss,    # length: 3-bit [0-7]
                "CAM_OBJ_D_Y" : data[3], # length: 6-bit
                "CAM_OBJ_A_Y" : data[1], # length: 6-bit
                "CAM_OBJ_D_X" : data[2], # length: 8-bit
                "CAM_OBJ_A_X" : data[0],  # length: 8-bit
                })
            
            print(f"Sending data: {data_store}")
            msg = can.Message(arbitration_id = 0x666, data = data_store, is_extended_id=False)
            self.bus.send(msg)
            time.sleep(0.001)
        messagebox.showinfo("Success", "Object data has been sent successfully!")
        
        return

# run the application
if __name__ == "__main__":
    app = Object_Detection_on_Static_Image()
    app.mainloop()
