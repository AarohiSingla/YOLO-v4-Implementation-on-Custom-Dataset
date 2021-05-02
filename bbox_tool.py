from __future__ import division
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'purple', 'grey', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256
# regex for graphics file format
FILES_FORMAT_REGEX = '*.[JjPp]*[Gg]'


class LabelTool:
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=False, height=False)
        

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.save_to_yolo_format = IntVar()
        self.entry_text = StringVar()
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.imagepath = ''
        self.labelname = ''
        self.labelfilename = ''
        self.file_will_not_remove = True
        self.tkimg = None
        self.folder = ''
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'classes.txt'
        self.cls = 0

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        
        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text="Image Dir:")
        self.label.grid(row=0, column=0, sticky=E)
        self.entry = Entry(self.frame, textvariable=self.entry_text)
        self.entry.grid(row=0, column=1, sticky=W+E)
        self.ldBtn = Button(self.frame, text="Open Folder", command=self.loadDir)
        self.ldBtn.grid(row=0, column=2, sticky=W+E)


        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 1, column= 1, rowspan = 4, sticky = W+N)
        self.checkbox = Checkbutton(self.frame, text = 'Save to Yolo format', onvalue=1, offvalue=0, variable = self.save_to_yolo_format)
        self.checkbox.grid(row = 0, column = 3,  sticky = W+N)
        self.checkbox.select()
        self.info_box_ctr_panel = Frame(self.frame)
        self.info_box_ctr_panel.grid(row=5, column=1, sticky=W + E)
        self.info_box = Text(self.info_box_ctr_panel, height=4)
        self.info_box.pack(side=LEFT, fill=Y)
        self.scroll_info_box = Scrollbar(self.info_box_ctr_panel)
        self.scroll_info_box.pack(side=LEFT, fill=Y)
        self.scroll_info_box.config(command=self.info_box.yview)
        self.info_box.config(yscrollcommand=self.scroll_info_box.set)

        # choose class
        self.classname_label = Label(self.frame, text = 'Chose classname')
        self.classname_label.grid(row=1,column =2)
        self.classcandidate = ttk.Combobox(self.frame, state='readonly')
        self.classcandidate.grid(row=2, column=2)
        if os.path.exists(self.classcandidate_filename):
            with open(self.classcandidate_filename) as cf:
                for line in cf.readlines():
                    # print line
                    self.cla_can_temp.append(line.strip('\n'))
        # print self.cla_can_temp
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.bind("<<ComboboxSelected>>", self.setClass)
        # self.btnclass = Button(self.frame, text='ComfirmClass', command=self.setClass)
        # self.btnclass.grid(row=2, column=2, sticky=W + E)


        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 26, height = 20)
        self.listbox.grid(row = 4, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 5, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 6, column = 2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)
        self.btnRm = Button(self.ctrPanel, text='Remove Picture', command=self.remove_image)
        self.btnRm.pack(side = LEFT, padx = 25, pady = 3)
     


        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def loadDir(self):
        folder = filedialog.askdirectory()
        self.imageDir = folder + os.sep
        self.entry_text.set(self.imageDir)
        # get image list
        self.imageList = glob.glob(os.path.join(self.imageDir, FILES_FORMAT_REGEX))
        if len(self.imageList) == 0:
            self.print_log('Files .jpg or .png NOT FOUND in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         
        # load example bboxes
        self.egDir = os.path.join(r'./Examples')
        if not os.path.exists(self.egDir):
            return
        filelist = glob.glob(os.path.join(self.egDir, FILES_FORMAT_REGEX))
        self.tmp = []
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])
        self.loadImage()
        self.print_log(str(self.total) + ' images loaded from ' + self.imageDir)

    def loadImage(self):
        # load image
        basewidth = 900
        self.imagepath = self.imageList[self.cur - 1]
        self.entry_text.set(self.imagepath)
        self.img = Image.open(self.imagepath)
        wpercent = (basewidth/float(self.img.size[0]))
        hsize = int((float(self.img.size[1])*float(wpercent)))
        img = self.img.resize((basewidth,hsize), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(img)
        self.mainPanel.config(width = max(self.tkimg.width(), basewidth), height = max(self.tkimg.height(), basewidth))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(self.imagepath)[-1].split('.')[0]
        self.labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.imageDir, self.labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0 and len(line.strip()) == 1:
                        bbox_cnt = int(line.strip())
                        continue
                        # check yolo format annotation
                    if line[1].isdecimal():
                        self.save_to_yolo_format.set(0)
                        tmp = line.split()
                        self.bboxList.append(tuple(tmp))
                        tmp_id = self.mainPanel.create_rectangle(int(tmp[0]), int(tmp[1]), \
                                                                int(tmp[2]), int(tmp[3]), \
                                                                width=2, \
                                                                outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
                        self.bboxIdList.append(tmp_id)
                        self.listbox.insert(END, '%s: (%d, %d) -> (%d, %d)' %(tmp[4], int(tmp[0]), int(tmp[1]),
                                                                           int(tmp[2]), int(tmp[3])))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                                fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

                    else:
                        self.save_to_yolo_format.set(1)
                        width = self.tkimg.width()
                        height = self.tkimg.height()
                        tmp = line.split()
                        tmp_alt = self.convert_from_yolo_format(width, height, tmp)
                        cls = self.cla_can_temp[int(tmp[0])]
                        self.bboxList.append(tmp)
                        tmp_id = self.mainPanel.create_rectangle(tmp_alt[0], tmp_alt[1], \
                                                                tmp_alt[2], tmp_alt[3], \
                                                                width=2, \
                                                                outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
                        self.bboxIdList.append(tmp_id)
                        self.listbox.insert(END, '%s: %.3f, %.3f , %.3f, %.3f' % (cls, float(tmp[1]), float(tmp[2]),
                                                                                  float(tmp[3]), float(tmp[4])))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                                fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        if self.file_will_not_remove:
            with open(self.labelfilename, 'w') as f:
                if self.save_to_yolo_format.get():
                    for bbox in self.bboxList:
                        f.write(' '.join(map(str, bbox)) + '\n')
                else:
                    f.write('%d\n' %len(self.bboxList))
                    for bbox in self.bboxList:
                        f.write(' '.join(map(str, bbox)) + '\n')
            self.print_log('Label saved to ' + self.labelname)
			
			
			
			
    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    
    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)


    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        self.file_will_not_remove = True
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        self.file_will_not_remove = True
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()
        elif self.cur == self.total:
            self.create_images_list()           
            messagebox.showinfo("Done", "That's All!")

    #remove picture
    def remove_image(self):
        if messagebox.askyesno("Remove picture", "Are you sure?"):
            if self.imagepath == '':
               self.print_log('--Folder path is empty--')
            else:
                index = self.imageList.index(self.imagepath)
                os.remove(self.imagepath)
                if os.path.exists(self.labelfilename):
                    os.remove(self.labelfilename)
                self.file_will_not_remove = False
                del self.imageList[index]
                self.total -= 1
                self.print_log('Remove ' + os.path.split(self.imagepath)[-1])
                if self.cur < self.total:
                    self.loadImage()
                elif self.cur - 1 == self.total:
                    self.cur -= 1
                    self.loadImage()   
                
                


    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def print_log(self, msg):
        self.info_box.insert(END, msg + '\n')
    
    
    def setClass(self, event):
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to : %s', self.currentLabelclass)

    #convert func from convert.py Guanghan Ning
    def convert_to_yolo_format(self,widht_img, height_img, box):
        dw = 1./widht_img
        dh = 1./height_img
        x = (box[0] + box[1])/2.0
        y = (box[2] + box[3])/2.0
        w = box[1] - box[0]
        h = box[3] - box[2]
        x = x*dw
        w = w*dw
        y = y*dh
        h = h*dh
        return (x,y,w,h)

    #TODO save file to xml format for VOC    
    def convert_from_yolo_format(self,widht_img, height_img, box):
        bboxW = float(box[3])*widht_img
        bboxH = float(box[4])*height_img
        centerX = float(box[1])*widht_img
        centerY = float(box[2])*height_img
        xmin = int(centerX - (bboxW/2))
        ymin = int(centerY - (bboxH/2))
        xmax = int(centerX + (bboxW/2))
        ymax = int(centerY + (bboxH/2))
        return (xmin,ymin,xmax,ymax)


    def create_images_list(self):
         with open(self.imageDir + 'images_list.txt', 'w') as inFile:
             for im in self.imageList:
                inFile.write(im+'\n')
             

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width = True, height = True)
    root.mainloop()