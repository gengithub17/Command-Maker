import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
from functools import partial
import platform
import json
import subprocess

# メインウィンドウの作成
CELL_WIDTH, CELL_HEIGHT = 50, 50
WINDOW_WIDTH, WINDOW_HEIGHT = 16*CELL_WIDTH, 10*CELL_HEIGHT
root = tk.Tk()
root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
root.title("Command Maker")
ttk.Style().theme_use("default")

# データ保存ファイル
FILEPATH = os.path.dirname(os.path.abspath(__file__))
SAVEFILE = f"{FILEPATH}/.savedata.json"

# ショートカットキーのため、実行システムを判別
SYSTEM:str = None
CTRL = 0x0
if sys.platform.lower() == "darwin":
	CTRL = 0x8 #MacではCommandキー
	SYSTEM = "Mac"
elif sys.platform.lower() == "win":
	CTRL = 0x4
	SYSTEM = "Win"
elif sys.platform.lower() == "Linux":
	CTRL = 0x4
	SYSTEM = "Linux"
else:
	messagebox.showwarning("System Warning","Unrecognized Operation System.\nYou can't use shortcut keys.")

def put(widget:ttk.Widget, xy:tuple[int,int],w=1,h=1):
	widget.place(x=(xy[0]+w/2)*CELL_WIDTH,y=(xy[1]+h/2)*CELL_HEIGHT,width=w*CELL_WIDTH,height=h*CELL_HEIGHT,anchor=tk.CENTER)

class CmdFrame(ttk.Frame):
	SYSTEM = platform.system()

	def __init__(self, root:tk.Tk):
		super().__init__(root,width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
		self.pack()
		self.parent = root
		self.name = tk.StringVar()
		self.cmd = tk.StringVar()
		self.pwd = tk.StringVar()
		self.relpath = tk.BooleanVar()
		self.args:list[Arg] = []
		self.saved = True
		self.extended = False
		self.consoleArea = ttk.Frame(self.parent,width=WINDOW_WIDTH, height=5*CELL_HEIGHT)
		self.console = tk.Text(self.consoleArea, wrap=tk.WORD, state=tk.DISABLED)
		self.scrollbar = ttk.Scrollbar(self.consoleArea,command=self.console.yview)
		self.console.config(yscrollcommand=self.scrollbar.set)
		self.console.tag_config("success",foreground="blue",font=("Arial",12))
		self.console.tag_config("fail",foreground="red",font=("Arial",12))
		self.console.pack(fill=tk.BOTH)
		self.scrollbar.pack(fill=tk.Y,side=tk.RIGHT)
		self.placement()
		self.name.trace("w",lambda *args:setattr(self,'saved',False))
		self.cmd.trace("w",lambda *args:setattr(self,'saved',False))
		self.pwd.trace("w",lambda *args:setattr(self,'saved',False))
		self.relpath.trace("w",lambda *args:setattr(self,'saved',False))

	def clear_data(self):
		self.name.set("")
		self.cmd.set("")
		self.pwd.set("")
		self.relpath.set(False)
		self.args.clear()
		self.saved = True
	
	def placement(self, start=0):
		self.parent.bind('<Key>',self.shortcut)
		for child in self.winfo_children():
			child.destroy()
		y = 0
		put(ttk.Label(self,text="Name:",font=self.font(),anchor=tk.E),xy=(0,y),w=2)
		put(ttk.Entry(self,textvariable=self.name),xy=(2,y),w=2)
		put(ttk.Button(self,text="Save As", command=self.saveas),xy=(4,y),w=2)
		put(ttk.Button(self,text="Save", command=self.save),xy=(6,y),w=2)
		put(ttk.Button(self,text="Open", command=self.open),xy=(8,y),w=2)
		put(ttk.Button(self,text="Clear", command=self.clear),xy=(10,y),w=2)
		if not SYSTEM is None:
			put(ttk.Button(self,text="Execute", command=self.execute),xy=(12,y),w=2)
		put(ttk.Button(self, text="Stored Data", command=self.savedlist_window), xy=(14,y),w=2)

		y += 1
		put(ttk.Label(self,text="pwd:",font=self.font(),anchor=tk.E),xy=(0,y),w=2)
		put(ttk.Entry(self,textvariable=self.pwd),xy=(2,y),w=8)
		put(ttk.Button(self,text="Select Folder", command=partial(self.select_file,self.pwd,True)),xy=(10,y),w=2)
		put(ttk.Checkbutton(self, text="Rel Path",command=self.translate_path,variable=self.relpath),xy=(13,y),w=2)

		y += 1
		# Main Command
		put(ttk.Label(self,text="Command:",font=self.font(),anchor=tk.E),xy=(0,y),w=2)
		put(ttk.Entry(self,textvariable=self.cmd),xy=(2,y),w=8)
		put(ttk.Button(self,text="Select File", command=partial(self.select_file,self.cmd)),xy=(10,y),w=2)
		put(ttk.Button(self, text="Copy", command=self.copy),xy=(13,y),w=2)

		y += 1
		# Args
		put(ttk.Label(self, text="Arg", font=self.font(), anchor=tk.CENTER),xy=(0,y),w=2)
		put(ttk.Label(self, text="Arg Value", font=self.font(), anchor=tk.CENTER), xy=(2,y),w=8)
		if start>0:
			put(ttk.Button(self, text="▲", command=partial(self.placement,start-1)),xy=(15,y))
		y += 1
		for i,flag in enumerate(self.args):
			if i<start: continue
			if i>start+3:
				put(ttk.Button(self, text="▼", command=partial(self.placement,start+1)),xy=(15,y))
				break
			flag.recreate_obj()
			put(flag.argFrame, xy=(0,y),w=2)
			put(flag.valueFrame, xy=(2,y),w=8)
			put(flag.fileButton, xy=(10,y),w=2)
			put(flag.removeButton, xy=(13,y),w=1)
			y += 1
		
		# Args add Button
		put(ttk.Button(self, text="Add an Arg", command=partial(self.addArg,start)), xy=(7,y),w=2)

		y = 9 # lowest level
		if self.extended:
			put(ttk.Button(self, text="Close Console", command=self.shorten),xy=(0,y),w=2)
			put(ttk.Button(self, text="Clear Console", command=self.clear_console),xy=(2,y),w=2)
		else:
			put(ttk.Button(self, text="extend", command=self.extend),xy=(0,y),w=2)
	
	def select_file(self,variable:tk.StringVar,directory=False):
		if directory:
			file_path = filedialog.askdirectory(title="Select a directory")
		else:
			file_path = filedialog.askopenfilename(title="Select a file", filetypes=[("All Files", "*.*")])

		if not file_path: return

		if self.relpath.get() and os.path.isdir(self.pwd.get()):
			file_path = os.path.relpath(file_path,self.pwd.get())
		variable.set(file_path)
	
	def addArg(self,start):
		self.args.append(Arg(self))
		self.focus_set() # フォーカスがそのままだと、押下後のキー操作でもう一度ボタンが押されてしまう
		self.saved = False
		self.placement(start+(len(self.args)>4))

	def copy(self):
		self.parent.clipboard_append(str(self))
		self.parent.focus_set()
	
	def shortcut(self, event:tk.Event):
		if event.state & CTRL != 0:
			if event.keysym == 'c':
				self.copy()
			elif event.keysym == 's':
				self.save()
			elif event.keysym == 'S':
				self.saveas()
			elif event.keysym == 'o':
				self.open()
			elif event.keysym == 'r':
				self.clear()
			elif event.keysym == 'Return':
				self.execute()

	def export(self)->dict:
		name = self.name.get()
		ret = {name : dict()}
		ret[name]["cmd"] = self.cmd.get()
		ret[name]["pwd"] = self.pwd.get()
		ret[name]["relpath"] = self.relpath.get()
		ret[name]["args"] = [(arg.arg.get(),arg.value.get()) for arg in self.args\
					if arg.arg.get() or arg.value.get()]
		return ret

	def innport(self,data:dict[str,dict]):
		name = next(iter(data.keys()))
		try:
			self.name.set(name)
			self.cmd.set(data[name]["cmd"])
			self.pwd.set(data[name]["pwd"])
			self.relpath.set(data[name]["relpath"])
			self.args.clear()
			for arg_data in data[name]["args"]:
				self.args.append(Arg(self,arg=arg_data[0],value=arg_data[1]))
		except KeyError:
			messagebox.showerror("System Error","Invalid data")
			print("Invalid data",file=sys.stderr)
	
	def save(self):
		self.parent.focus_set()
		with open(SAVEFILE, "r") as json_file:
			json_data:dict[str,dict[str,dict]] = json.load(json_file)
		if self.name.get() not in json_data["data"].keys():
			if messagebox.askokcancel(title="Save Warning", message=f"{self.name.get()} has not yet been registered.\nDo you want to save as a new data?"):
				self.saveas()
			return
		json_data["data"].update(self.export())
		with open(SAVEFILE, "w") as json_file:
			json.dump(json_data, json_file)
		self.saved = True
	
	def saveas(self):
		self.parent.focus_set()
		if not self.name.get() or self.name.get().isspace():
			messagebox.showerror(title="Save Error", message="Name must not be blank")
			return
		with open(SAVEFILE, "r") as json_file:
			json_data:dict[str,dict[str,dict]] = json.load(json_file)
		if self.name.get() in json_data["data"].keys():
			if not messagebox.askokcancel(title="Save Warning", message=f'"{self.name.get()}" is already existing.\nDo you want to overwrite it?'):
				return
		json_data["data"].update(self.export())
		with open(SAVEFILE, "w") as json_file:
			json.dump(json_data, json_file)
		self.saved = True
	
	def open(self):
		self.parent.focus_set()
		if not self.unsaved_ok():
			return
		window = tk.Toplevel(self.parent)
		window.title("Select a data")
		window.bind('<Escape>',lambda event:(window.destroy(),self.placement()))
		listbox = tk.Listbox(window,selectmode=tk.SINGLE)
		listbox.focus_set()
		for name in self.stored_list():
			listbox.insert(tk.END,name)
		listbox.pack(side=tk.LEFT,fill=tk.Y)
		scrollbar = tk.Scrollbar(window,command=listbox.yview)
		scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
		listbox.config(yscrollcommand=scrollbar.set)
		def selected(event:tk.Event):
			selected_name = listbox.get(listbox.curselection()[0])
			with open(SAVEFILE, "r") as json_file:
				json_data:dict[str,dict[str,dict]] = json.load(json_file)
			self.innport({selected_name:json_data["data"][selected_name]})
			self.saved = True
			window.destroy()
			self.placement()
		listbox.bind("<<ListboxSelect>>",selected)
	
	def unsaved_ok(self):
		if self.saved or not self.command(): return True
		return messagebox.askokcancel("Save Warning","Currently data is not saved.\nIgnore and continue?")
	
	def translate_path(self):
		self.parent.focus_set()
		if not os.path.isdir(self.pwd.get()):
			messagebox.showerror("System Error","Invalid pwd")
			self.relpath.set(not self.relpath.get())
		if self.relpath.get():
			if os.path.isfile(self.cmd.get()):
				self.cmd.set(os.path.relpath(self.cmd.get(),self.pwd.get()))
			for arg in self.args:
				if os.path.isfile(arg.value.get()):
					arg.value.set(os.path.relpath(arg.value.get()))
		else:
			abspath = os.path.join(self.pwd.get(),self.cmd.get())
			if os.path.isfile(abspath):
				self.cmd.set(abspath)
			for arg in self.args:
				abspath = os.path.join(self.pwd.get(),arg.value.get())
				if os.path.isfile(abspath):
					arg.value.set(abspath)
	
	def clear(self):
		if not self.unsaved_ok():
			return
		self.clear_data()
		self.placement()
	
	def execute(self):
		self.parent.focus_set()
		if not self.command():
			messagebox.showerror("Execution Error","No command entered.")
			return
		cdcmd = ""
		if os.path.isdir(self.pwd.get()):
			if SYSTEM == "Win": cdcmd = f"cd {self.pwd.get()} ; "
			else: cdcmd = f"cd {self.pwd.get()} && "
		result = subprocess.run(f"{cdcmd}{self.command()}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
		self.console.config(state=tk.NORMAL)
		if result.returncode == 0:
			self.console.insert(tk.END, f"$ {self.command()}\n", "success")
		else:
			self.console.insert(tk.END, f"$ {self.command()}\n", "fail")
		self.console.insert(tk.END, result.stdout)
		self.console.config(state=tk.DISABLED)
		self.extend()

	def extend(self):
		global WINDOW_HEIGHT, CELL_HEIGHT, WINDOW_WIDTH
		self.parent.focus_set()
		self.parent.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT+5*CELL_HEIGHT}')
		self.consoleArea.pack()
		self.extended = True
		self.placement()

	def shorten(self):
		global WINDOW_HEIGHT, WINDOW_WIDTH
		self.parent.focus_set()
		self.parent.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
		self.extended = False
		self.placement()
	
	def clear_console(self):
		self.parent.focus_set()
		self.console.config(state=tk.NORMAL)
		self.console.delete("1.0",tk.END)
		self.console.config(state=tk.DISABLED)

	def command(self):
		return str(self)
	
	def stored_list(self):
		with open(SAVEFILE, "r") as json_file:
			json_data:dict[str,dict[str,dict]] = json.load(json_file)
		return json_data["data"].keys()
	
	def savedlist_window(self, start=0):
		self.parent.unbind('<Key>')
		self.parent.focus_get()
		if not self.unsaved_ok():
			return
		for child in self.winfo_children():
			child.destroy()
		y = 0
		put(ttk.Button(self, text="Back", command=self.placement), xy=(0,y), w=2)

		if start>0:
			put(ttk.Button(self, text="▲", command=partial(self.savedlist_window,start-1)),xy=(14,y))

		y = 1
		with open(SAVEFILE, "r") as json_file:
			json_data:dict[str,dict[str,dict]] = json.load(json_file)
		vardict:dict[str, tk.BooleanVar] = dict()
		for i,name in enumerate(json_data["data"].keys()):
			if i<start: continue
			if i>start+8:
				put(ttk.Button(self, text="▼", command=partial(self.savedlist_window,start+1)),xy=(15,0))
				break
			vardict[name] = tk.BooleanVar(value=False)
			put(ttk.Checkbutton(self, text=name, variable=vardict[name], command=self.parent.focus_set),xy=(0,y),w=16)
			y += 1
		
		# Buttons and Commands
		def edit(start=0,new_name_list:list[tk.StringVar]=None):
			self.parent.focus_get()
			for child in self.winfo_children():
				child.destroy()
			old_name_list = list(self.stored_list())
			# new_name_list:list[tk.StringVar] = list()
			if new_name_list is None:
				new_name_list = [tk.StringVar(value=old) for old in old_name_list]
			def ok():
				if len(new_name_list)>len({var.get() for var in new_name_list}):
					messagebox.showerror("Save Error","Duplicated names cannot be registered.")
					edit()
					return
				with open(SAVEFILE, "r") as json_file:
					json_data:dict[str,dict[str,dict]] = json.load(json_file)
				new_data:dict[str,dict[str,dict]] = {"data":{}}
				for i, old in enumerate(old_name_list):
					new_data["data"][new_name_list[i].get()] = json_data["data"].pop(old)
				with open(SAVEFILE, "w") as json_file:
					json.dump(new_data, json_file)
				self.savedlist_window()
			y = 0
			put(ttk.Label(self, text="Old Name",font=self.font()),xy=(0,y),w=8)
			put(ttk.Label(self, text="New Name",font=self.font()),xy=(8,y),w=2)
			put(ttk.Button(self, text="Back",command=self.savedlist_window), xy=(10,y),w=2)
			if start>0:
				put(ttk.Button(self, text="▲", command=partial(edit,start-1,new_name_list)),xy=(12,y))
			if len(old_name_list)>start+9:
				put(ttk.Button(self, text="▼", command=partial(edit,start+1,new_name_list)),xy=(13,0))
			put(ttk.Button(self, text="OK",command=ok),xy=(14,y),w=2)

			y += 1
			for i,name in enumerate(old_name_list):
				if i<start or i>start+8: continue
				put(ttk.Label(self, text=name, font=self.font()), xy=(0,y),w=8)
				put(ttk.Entry(self, textvariable=new_name_list[i]),xy=(8,y),w=8)
				y += 1
		put(ttk.Button(self, text="Edit", command=edit), xy=(2,0),w=2)
		
		
		def delete():
			for name, var in vardict.items():
				if var.get():
					json_data["data"].pop(name)
			with open(SAVEFILE, "w") as json_file:
					json.dump(json_data, json_file)
			self.savedlist_window()
		put(ttk.Button(self, text="Delete", command=delete), xy=(4,0),w=2)

		def copy():
			for name, var in vardict.items():
				if var.get():
					i = 1
					new_name = name + f"({i})"
					while new_name in json_data["data"].keys():
						new_name = name + f"({i})"
						i += 1
					json_data["data"][new_name] = json_data["data"][name].copy()
			with open(SAVEFILE, "w") as json_file:
					json.dump(json_data, json_file)
			self.savedlist_window()
		put(ttk.Button(self, text="Copy", command=copy), xy=(6,0),w=2)

		def select_all():
			for var in vardict.values():
				var.set(True)
		put(ttk.Button(self, text="Select All", command=select_all), xy=(8,0),w=2)

	@classmethod
	def font(cls,size=20):
		return ("Arial",size)
	
	@classmethod
	def create_savefile(cls):
		with open(SAVEFILE, "w") as json_file:
			json.dump({"data":{}}, json_file)

	def __str__(self) -> str:
		return " ".join([self.cmd.get()]+list(map(str, self.args)))
	
class Arg:
	def __init__(self, parent:'CmdFrame',arg="",value=""):
		self.parent = parent
		self.arg = tk.StringVar()
		self.value = tk.StringVar()
		self.argFrame = ttk.Entry(self.parent, textvariable=self.arg)
		self.valueFrame = ttk.Entry(self.parent, textvariable=self.value)
		self.fileButton = ttk.Button(self.parent, text="Select File",
							command=partial(self.parent.select_file, self.value))
		self.removeButton = ttk.Button(self.parent, text="Del", command=self.remove)
		self.arg.set(arg)
		self.value.set(value)
		self.arg.trace("w",lambda *args:setattr(self.parent,'saved',False))
		self.value.trace("w",lambda *args:setattr(self.parent,'saved',False))
	
	def remove(self):
		self.parent.args.remove(self)
		self.parent.focus_set()
		self.parent.saved = False
		self.parent.placement()
		del self
	
	def recreate_obj(self):
		self.argFrame = ttk.Entry(self.parent, textvariable=self.arg)
		self.valueFrame = ttk.Entry(self.parent, textvariable=self.value)
		self.fileButton = ttk.Button(self.parent, text="Select File",
							command=partial(self.parent.select_file, self.value))
		self.removeButton = ttk.Button(self.parent, text="Del", command=self.remove)

	def __str__(self) -> str:
		buf = self.arg.get()
		if self.value.get():
			buf += " " + self.value.get()
		return buf

	def __repr__(self) -> str:
		return self.__str__()

cmdframe = CmdFrame(root)

# メインループの開始
root.mainloop()