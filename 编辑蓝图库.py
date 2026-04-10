import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json,os,io,base64,sys

import regex as re
from PIL import Image, ImageTk, ImageGrab

class 蓝图库编辑器(tk.Tk):
    版本 = 0.3

    匹配HMname = re.compile( r'(Hname\s*=\s*")(.*?)(")')
    匹配HM蓝图库 = re.compile(r'(BPlist\s*=\s*)(\{(?:[^{}]|(?2))*\})')
    匹配蓝图代码 = re.compile(r'^DYBP:.*"[0-9A-F]{32}$')
    非法字符 = {' ', '"', '\'', '#', '.', '<', '>', '=', '/', '\\'}
    HTML模板路径 = "./模板.html"
    默认蓝图库路径 = "./默认蓝图库.json"
    新蓝图库 = json.dumps(
        {"我的蓝图":[{"name":"新蓝图","data":"在这输入蓝图代码"}]}
        )

    def __init__(self):
        super().__init__()
        if hasattr(sys, '_MEIPASS'):
            self.默认蓝图库路径 = os.path.join(sys._MEIPASS, self.默认蓝图库路径)
            self.HTML模板路径 = os.path.join(sys._MEIPASS, self.HTML模板路径)
        
        self.name = ""
        self.last_json = ""
        self.last_dir = ""

        self.蓝图库:dict[list[dict]] = {}

        self.当前类型 = None # 检查：修改时一同修改蓝图索引
        self.当前蓝图索引 = None
        self.图片数据 = None
        self._数据是否修改 = False
        self._当前蓝图是否锁定 = 0
        self._通知定时 = None

        self.title("戴森球计划球体蓝图库")
        self.minsize(850, 500)
        self.geometry(f"900x600+{(self.winfo_screenwidth()-900)//2}+{(self.winfo_screenheight()-600)//2}")

        self.样式 = ttk.Style()
        self.样式.configure("Category.TButton", padding=5)
        self.样式.configure("Selected.TButton", background="#4a86e8", padding=5)
        
        self.顶部框架 = ttk.Frame(self)
        self.顶部框架.pack(fill=tk.X, padx=10, pady=5)

        self.新建按钮 = ttk.Button(self.顶部框架, text="新建", command=lambda: self.打开菜单(self.新建按钮,self.新建菜单))
        self.新建按钮.pack(side=tk.LEFT, padx=5)
        self.导入按钮 = ttk.Button(self.顶部框架, text="导入", command=lambda: self.打开菜单(self.导入按钮,self.导入菜单))
        self.导入按钮.pack(side=tk.LEFT, padx=5)
        self.导出按钮 = ttk.Button(self.顶部框架, text="导出", command=lambda: self.打开菜单(self.导出按钮,self.导出菜单))
        self.导出按钮.pack(side=tk.LEFT, padx=5)
        self.并入按钮 = ttk.Button(self.顶部框架, text="并入", command=lambda: self.打开菜单(self.并入按钮,self.并入菜单))
        self.并入按钮.pack(side=tk.LEFT, padx=5)
        self.关于按钮 = ttk.Button(self.顶部框架, text="关于", command=self.显示关于信息)
        self.关于按钮.pack(side=tk.LEFT, padx=5)

        self.通知窗 = ttk.Label(self.顶部框架, width=55, foreground="#333", relief="solid", padding=2)
        self.通知窗.pack(side=tk.RIGHT, padx=5)

        self.新建菜单 = tk.Menu(self, tearoff=0)
        self.新建菜单.add_command(label="新建空蓝图", command=self.新建蓝图库)
        self.新建菜单.add_command(label="加载默认", command=self.载入默认库)

        self.导入菜单 = tk.Menu(self, tearoff=0)
        self.导入菜单.add_command(label="加载JSON", command=self.导入JSON)
        self.导入菜单.add_command(label="从HTML导入", command=self.导入HTML)

        self.导出菜单 = tk.Menu(self, tearoff=0)
        self.导出菜单.add_command(label="保存JSON", command=self.导出JSON)
        #self.导出菜单.add_separator()
        self.导出菜单.add_command(label="导出HTML", command=self.导出HTML)
        self.导出菜单.add_command(label="导出文件夹", command=self.导出文件夹)

        self.并入菜单 = tk.Menu(self, tearoff=0)
        self.并入菜单.add_command(label="从JSON并入", command=lambda: self.并入("从JSON"))
        self.并入菜单.add_command(label="从HTML并入", command=lambda: self.并入("从HTML"))

        self.主框架 = ttk.Frame(self)
        self.主框架.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.分类框架 = ttk.LabelFrame(self.主框架, text="蓝图分类")
        self.分类框架.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.分类项框架 = ttk.Frame(self.分类框架)
        self.分类项框架.pack(fill=tk.X, padx=5, pady=3)
        self.添加类按钮 = ttk.Button(self.分类框架, text="添加分类", width=8, command=self.添加蓝图分类)
        self.添加类按钮.pack(fill=tk.X, padx=5,pady=(10, 3))
        tk.Label(self.分类框架, text="右键更多操作", fg="#999999", anchor="w").pack(fill=tk.X, padx=5)
        self.分类右键菜单 = tk.Menu(self, tearoff=0)
        
        self.蓝图列表框架 = ttk.LabelFrame(self.主框架, text="蓝图列表 - 未选择分类")
        self.蓝图列表框架.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.蓝图列表操作框架 = ttk.Frame(self.蓝图列表框架)
        self.蓝图列表操作框架.pack(fill=tk.X, padx=5, pady=0)
        self.上移 = ttk.Button(self.蓝图列表操作框架, text="⬆️", width=2, command=lambda: self.排序蓝图(-1))
        self.上移.pack(side=tk.LEFT, padx=1)
        self.下移 = ttk.Button(self.蓝图列表操作框架, text="⬇️", width=2, command=lambda: self.排序蓝图(1))
        self.下移.pack(side=tk.LEFT, padx=1)
        self.新建蓝图按钮 = ttk.Button(self.蓝图列表操作框架, text="+",width=2,command=self.新建蓝图)
        self.新建蓝图按钮.pack(side=tk.LEFT, padx=1)
        self.删除蓝图按钮 = ttk.Button(self.蓝图列表操作框架, text="🗑", width=2, command=lambda: self.删除蓝图(True))
        self.删除蓝图按钮.pack(side=tk.LEFT, padx=1)
        self.移动蓝图按钮 = ttk.Button(self.蓝图列表操作框架, text="移动", width=4, command=lambda: self.批量操作窗口('移动'))
        self.移动蓝图按钮.pack(side=tk.LEFT, padx=1)
        self.批量删除按钮 = ttk.Button(self.蓝图列表操作框架, text="删除", width=4, command=lambda: self.批量操作窗口('删除'))
        self.批量删除按钮.pack(side=tk.LEFT, padx=1)
        self.批量导入按钮 = ttk.Button(self.蓝图列表操作框架, text="导入", width=4, command=lambda: self.批量操作窗口('导入'))
        self.批量导入按钮.pack(side=tk.LEFT, padx=1)

        self.滚动条 = tk.Scrollbar(self.蓝图列表框架)
        self.滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        self.蓝图列表 = tk.Listbox(self.蓝图列表框架, width=31, height=20, exportselection=False, yscrollcommand=self.滚动条.set)
        self.蓝图列表.pack(fill=tk.BOTH, expand=True, padx=5, pady=(1, 5))
        self.滚动条.config(command=self.蓝图列表.yview)
        self.蓝图列表.bind('<<ListboxSelect>>', self.点击蓝图)
        self.蓝图列表.bind('<Control-c>', self.快捷键_复制选中蓝图代码)
        self.蓝图列表.bind('<Control-C>', self.快捷键_复制选中蓝图代码)
        
        self.编辑区框架 = ttk.LabelFrame(self.主框架, text="蓝图编辑")
        self.编辑区框架.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, ipadx=8, ipady=5)

        self.编号显示标签 = ttk.Label(self.编辑区框架, text="新建蓝图：")
        self.编号显示标签.grid(row=0, column=0, columnspan=5, padx=8, pady=8, sticky="n")

        self.名称标签 = ttk.Label(self.编辑区框架, text="*蓝图名:")
        self.名称标签.grid(row=1, column=0, padx=4, pady=8, sticky=tk.W)
        self.名称输入框 = ttk.Entry(self.编辑区框架, width=30)
        self.名称输入框.grid(row=1, column=1, padx=4, pady=8, sticky=tk.W)
        self.导入蓝图按钮 = ttk.Button(self.编辑区框架, text="导入蓝图", width=10, command=self.导入蓝图文件)
        self.导入蓝图按钮.grid(row=1, column=2, columnspan=2, padx=2, sticky=tk.W)

        self.蓝图代码标签 = ttk.Label(self.编辑区框架, text="*蓝图代码:")
        self.蓝图代码标签.grid(row=2, column=0, padx=4, pady=8, sticky=tk.NW)
        self.代码输入框 = tk.Text(self.编辑区框架, width=30, height=1, wrap="none")
        self.代码输入框.grid(row=2, column=1, sticky="nsew",padx=4, pady=8)
        self.代码输入框.bind("<ButtonRelease-1>", self.自动全选)
        for key in ["<Return>", "<Up>", "<Down>", "<Left>", "<Right>"]:
            self.代码输入框.bind(key, self.禁止按键)
        self.复制按钮 = ttk.Button(self.编辑区框架, text="复制", width=4, command=self.复制蓝图代码)
        self.复制按钮.grid(row=2, column=2, padx=2, sticky=tk.W)
        self.粘贴按钮 = ttk.Button(self.编辑区框架, text="粘贴", width=4, command=self.粘贴蓝图代码)
        self.粘贴按钮.grid(row=2, column=3, padx=2, sticky=tk.W)
        self.图片预览标签 = ttk.Label(self.编辑区框架, text=" 蓝图图片:")
        self.图片预览标签.grid(row=3, column=0, padx=4, pady=8, sticky=tk.NW)
        self.预览画布 = tk.Canvas(self.编辑区框架, width=160, height=160, bg="#f5f5f5", bd=1, relief="solid")
        self.预览画布.grid(row=3, column=1, padx=4, pady=8)
        self.图片编辑框架 = ttk.Frame(self.编辑区框架)
        self.图片编辑框架.grid(row=3, column=2, columnspan=2, pady=8, sticky=tk.W)
        self.粘贴图片按钮 = ttk.Button(self.图片编辑框架, text="粘贴截图", width=10, command=self.粘贴图片)
        self.粘贴图片按钮.grid(padx=2, pady=2, sticky=tk.W)
        self.导入图片按钮 = ttk.Button(self.图片编辑框架, text="导入图片",  width=10, command=self.导入图片)
        self.导入图片按钮.grid(padx=2, pady=2, sticky=tk.W)
        self.删除图片按钮 = ttk.Button(self.图片编辑框架, text="删除图片", width=10, command=self.删除图片)
        self.删除图片按钮.grid(padx=2, pady=2, sticky=tk.W)

        self.备注标签 = ttk.Label(self.编辑区框架, text=" 蓝图备注:")
        self.备注标签.grid(row=4, column=0, padx=4, pady=8, sticky=tk.W)
        self.备注输入框 = ttk.Entry(self.编辑区框架, width=42)
        self.备注输入框.grid(row=4, column=1, columnspan=3, padx=4, pady=8, sticky=tk.W)
        
        self.按钮框架 = ttk.Frame(self.编辑区框架)
        self.按钮框架.grid(row=5, column=0, columnspan=4, pady=8)
        self.保存按钮 = ttk.Button(self.按钮框架, text="保存蓝图", command=self.保存蓝图)
        self.保存按钮.pack(side=tk.LEFT, padx=2)
        self.删除按钮 = ttk.Button(self.按钮框架, text="删除蓝图", command=self.删除蓝图)
        self.删除按钮.pack(side=tk.LEFT, padx=2)

        self.protocol("WM_DELETE_WINDOW", self.关闭窗口)

        self.加载配置()
        self.通知("提示：选择蓝图后Ctrl+C可直接复制蓝图代码",5000)
        self.加载默认数据()


    # ===========================  ===========================
    def 显示关于信息(self):
        messagebox.showinfo(title="关于",message=f"作者：氢碳钾\n版本：{self.版本}")

    def 打开菜单(self, 按钮:tk.Button, 菜单:tk.Menu):
        x = 按钮.winfo_x()
        y = 按钮.winfo_y() + 按钮.winfo_height()
        菜单.post(self.winfo_rootx() + x, self.winfo_rooty() + y)

    def 打开分类右键菜单(self, event:tk.Event, 类型:str):
        event.widget.focus()
        self.分类右键菜单.delete(0, tk.END)
        self.分类右键菜单.add_command(label="上移", command=lambda: self.排序分类(类型,-1))
        self.分类右键菜单.add_command(label="下移", command=lambda: self.排序分类(类型,1))
        self.分类右键菜单.add_command(label="改名", command=lambda: self.更名分类(类型))
        self.分类右键菜单.add_command(label="删除", command=lambda: self.删除蓝图分类(类型))
        self.分类右键菜单.post(event.x_root, event.y_root)

    def 关闭窗口(self):
        if self._数据是否修改:
            result = messagebox.askyesnocancel(
            title="保存提示",
            message="蓝图库未保存，是否保存为JSON？",
            )
            if result is None:
                return
            if result:
                self.导出JSON()
        self.保存配置()
        self.destroy()

    def 自动全选(self,event:tk.Event):
        event.widget.tag_add(tk.SEL, "1.0", tk.END)
    def 禁止按键(self,event:tk.Event):
        return "break"
    def 快捷键_复制选中蓝图代码(self, event:tk.Event=None):
        if self.当前类型 == None or self.当前蓝图索引 == None:
            self.通知("请选择蓝图")
            return "break"
        try:
            蓝图数据 = self.获取蓝图(self.当前类型, self.当前蓝图索引)
            代码 = 蓝图数据.get("data", "").strip()
            if 代码:
                self.clipboard_clear()
                self.clipboard_append(代码)
                self.通知(f"已将 {蓝图数据['name']} 复制到剪贴板")
        except:
            self.通知("复制失败")
        return "break"

    def 加载默认数据(self):
        try:
            if self.last_json and os.path.exists(self.last_json):
                self.从JSON字符串载入蓝图库(self.读取文件(self.last_json))
                self.通知("已加载最近使用的 JSON", 10000)
            else:
                self.从JSON字符串载入蓝图库(self.读取文件(self.默认蓝图库路径))
        except Exception:
            self.从JSON字符串载入蓝图库(self.新蓝图库)

        self.刷新页面()
        self.选择蓝图类型(self.获取类表()[0])


    # ===========================  ===========================
    def 刷新页面(self):
        self.当前类型 = None
        self.当前蓝图索引 = None
        self.刷新蓝图列表()

        类型列表 = self.获取类表()
        for 控件 in self.分类项框架.winfo_children():
            控件.destroy()
        for 蓝图类型 in 类型列表:
            按钮 = ttk.Button(self.分类项框架, width=16, text=蓝图类型, style="Category.TButton",command=lambda c=蓝图类型: self.选择蓝图类型(c))
            按钮.bind("<Button-3>", lambda event, c=蓝图类型: self.打开分类右键菜单(event, c))
            按钮.pack(fill=tk.X, padx=5, pady=3)

    def 选择蓝图类型(self, 蓝图类型:str|None):
        self.当前类型 = 蓝图类型
        self.当前蓝图索引 = None
        
        for 按钮 in self.分类项框架.winfo_children():
            if 按钮["text"] == 蓝图类型:
                按钮.config(style="Selected.TButton")
            else:按钮.config(style="Category.TButton")

        self.刷新蓝图列表()
        
    def 刷新蓝图列表(self):
        self.蓝图列表.delete(0, tk.END)
        if self.当前类型 != None:
            self.蓝图列表框架.config(text=f"蓝图列表 - {self.当前类型} -")
            for 蓝图数据 in self.获取蓝图列表(self.当前类型):
                if 蓝图数据.get('lock', 0) == 1:
                    显示名称 = f"{蓝图数据['name'] }🔒"
                else:
                    显示名称 = f"{蓝图数据['name']}"

                self.蓝图列表.insert(tk.END, 显示名称)
        else:
            self.蓝图列表框架.config(text=f"蓝图列表 - 未选择分类 -")
        if self.当前蓝图索引 != None:
            self.蓝图列表.selection_set(self.当前蓝图索引)
            self.蓝图列表.see(self.当前蓝图索引)
        self.刷新编辑区()

    def 刷新编辑区(self):
        self._当前蓝图是否锁定 = 0
        self.编号显示标签.config(text="新建蓝图：")
        self.名称输入框.config(state="normal")
        self.名称输入框.delete(0, tk.END)
        self.代码输入框.config(state="normal", bg="white", fg="black")
        self.代码输入框.delete("1.0", tk.END)
        self.备注输入框.config(state="normal")
        self.备注输入框.delete(0, tk.END)
        self.图片数据 = None
        self.加载图片预览()

        if self.当前蓝图索引 == None:
            return
        
        蓝图数据 =self.获取蓝图(self.当前类型, self.当前蓝图索引)
        self._当前蓝图是否锁定 = 蓝图数据.get('lock', 0)
        
        self.编号显示标签.config(text=f"修改蓝图：{self.当前类型} -- {蓝图数据["name"]}")
        self.名称输入框.insert(0, 蓝图数据['name'])
        self.代码输入框.insert("1.0", 蓝图数据['data'])
        self.备注输入框.insert(0,蓝图数据.get('memo', ''))
        self.图片数据 = 蓝图数据.get("img","")
        self.加载图片预览()
        
        if self._当前蓝图是否锁定:
            self.编号显示标签.config(text="该蓝图已锁定")
            self.名称输入框.config(state="disabled")
            self.代码输入框.config(state="disabled",bg="#f0f0f0", fg="#888888")
            self.备注输入框.config(state="disabled")

    def 加载图片预览(self):
        self.预览画布.delete("all")
        try:
            if not self.图片数据:
                self.预览画布.create_text(80, 80, text="暂无图片", fill="#999")
                self._预览图片缓存 = None
                return

            if self.图片数据.startswith("data:image/svg+xml;base64,"):
                self.预览画布.create_text(80, 80, text="这是svg图片\n导出html可正常显示", fill="#2E8B57")
                return

            base64_str = self.图片数据.split(",")[1]
            img_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_data))
            self._预览图片缓存 = ImageTk.PhotoImage(img)

            w = self.预览画布.winfo_width()
            h = self.预览画布.winfo_height()
            self.预览画布.create_image(w / 2, h / 2, image=self._预览图片缓存, anchor="center")
        except base64.binascii.Error:
            self.预览画布.create_text(80, 80, text="图片编码错误", fill="red")
        except Exception as e:
            self.预览画布.create_text(80, 80, text=f"预览失败：\n{str(e)[:20]}", fill="red")

    def 点击蓝图(self, event:tk.Event):
        选中 = self.蓝图列表.curselection()
        if not 选中: return
        
        self.当前蓝图索引 = 选中[0] if self.当前蓝图索引 != 选中[0] else None
        if self.当前蓝图索引 == None:
            self.蓝图列表.selection_clear(0, tk.END)
        self.刷新编辑区()
    
    def 通知(self,消息:str, 延迟时间:int=3000):
        if self._通知定时:
            self.after_cancel(self._通知定时)
        
        self.通知窗.config(text=消息)
        
        self._通知定时 = self.after(延迟时间, lambda: self.通知窗.config(text=""))


    # =========================== 数据处理 ===========================

    def 从JSON字符串载入蓝图库(self, JSON:str):
        数据:dict =json.loads(JSON)
        if not self.检查蓝图库格式(数据):
            raise TypeError("蓝图库格式错误")
        self.蓝图库 = 数据
        self._数据是否修改 = False
    
    def 读取蓝图库为JSON字符串(self, 缩进:int|None = None) -> str:
        self._数据是否修改 = False
        return json.dumps(dict(self.蓝图库) , ensure_ascii=False,indent=缩进)

    def 获取蓝图(self, 蓝图类型:str, 蓝图索引:int) -> dict:
        return self.蓝图库[蓝图类型][蓝图索引]
    
    def 获取蓝图列表(self,蓝图类型:str) -> list:
        return self.蓝图库[蓝图类型]
    
    def 添加蓝图(self, 蓝图类型:str, 蓝图数据:dict, 蓝图索引:int|None=None):
        if 蓝图索引 == None:
            self.蓝图库[蓝图类型].append(蓝图数据)
        else:
            self.蓝图库[蓝图类型].insert(蓝图索引, 蓝图数据)
        self._数据是否修改 = True
    
    def 更改蓝图(self, 蓝图类型:str, 新数据:dict, 蓝图索引:int):
        self.蓝图库[蓝图类型][蓝图索引] = 新数据
        self._数据是否修改 = True
    
    def 移出数据(self, 蓝图类型:str, 蓝图索引:int|None=None) -> list|dict:
        self._数据是否修改 = True
        if 蓝图索引 == None:
            return self.蓝图库.pop(蓝图类型)
        return self.蓝图库[蓝图类型].pop(蓝图索引)
    
    def 添加分类(self, 新类名:str):
        self.蓝图库[新类名] = []
        self._数据是否修改 = True
    
    def 修改类名(self,旧类名:str, 新类名:str):
        新数据 = {}
        for k, v in self.蓝图库.items():
            新数据[新类名 if k == 旧类名 else k] = v
        self.蓝图库 = 新数据

    def 获取类表(self, 排除项:str|None=None) ->list:
        分类列表 = list(self.蓝图库.keys())
        if 排除项 != None:
            分类列表.remove(排除项)
        return 分类列表
    
    def 列表写入(self, 蓝图类型:str, 蓝图列表:list, 模式='添加'):
        if 模式 == '添加':
            self.蓝图库.setdefault(蓝图类型, [])
            名字列表 = [名["name"] for 名 in self.获取蓝图列表(蓝图类型)]
            for 蓝图数据 in 蓝图列表:
                if 蓝图数据.get('lock', 0):
                    continue
                if 蓝图数据['name'] in 名字列表:
                    蓝图数据['name'] = self.添加序号(蓝图数据['name'],名字列表)
                self.蓝图库[蓝图类型].append(蓝图数据)
        elif 模式 == '修改':
            self.蓝图库[蓝图类型] = 蓝图列表
        self._数据是否修改 = True
        
    def 移动分类(self,蓝图类型:str|None,步:int):
        蓝图库列表 = list(self.蓝图库.items())
        索引 = [k[0] for k in 蓝图库列表].index(蓝图类型)
        目标 = 索引 + 步
        if 目标 < 0 or 目标 == len(蓝图库列表):
            return False
        蓝图库列表.insert(目标, 蓝图库列表.pop(索引))
        self.蓝图库 = dict(蓝图库列表)
        self._数据是否修改 = True
        return True


    # =========================== 工具 ===========================
    @staticmethod
    def 校验蓝图代码(蓝图代码:str) -> bool:
        return bool(蓝图库编辑器.匹配蓝图代码.match(蓝图代码.strip()))

    @staticmethod
    def 检查名字(名字:str, 模式='检测'):
        if 模式 == '检测':
            return 名字 and not any(c in 蓝图库编辑器.非法字符 for c in 名字)
        if 模式 == '规范':
            return ''.join([char for char in 名字 if char not in 蓝图库编辑器.非法字符])

    def 蓝图重名检测(self, 蓝图名:str, 蓝图分类:str, 排除项索引:int|None=None) -> bool:
        名字列表 = [名["name"] for 名 in self.获取蓝图列表(蓝图分类)]
        if 排除项索引 != None:
            名字列表.pop(排除项索引)
        if 蓝图名 in 名字列表:
            return False
        return True
    
    @staticmethod
    def 添加序号(名:str, 列表:list) ->str:
        编号 = 1
        while True:
            新名 = f"{名}-{编号}"
            if 新名 not in 列表:
                return 新名
            编号 += 1

    @staticmethod
    def 检查蓝图库格式(蓝图库:dict) -> bool:
        if not isinstance(蓝图库, dict) or len(蓝图库) == 0:
            return False
        for 蓝图列表 in 蓝图库.values():
            if not isinstance(蓝图列表, list):
                return False
            for 蓝图 in 蓝图列表:
                if not isinstance(蓝图, dict):
                    return False
                for 字段 in ['name', 'data']:
                    if 字段 not in 蓝图:
                        return False
        return True
    
    @staticmethod
    def 处理图片(图片: Image.Image) -> str:
        宽度, 高度 = 图片.size
        
        if 宽度 != 高度 or 高度 > 154 or 宽度 > 154:
            最小边 = min(宽度, 高度)
            左 = (宽度 - 最小边) // 2
            上 = (高度 - 最小边) // 2
            右 = 左 + 最小边
            下 = 上 + 最小边
            图片 = 图片.crop((左, 上, 右, 下))
            图片 = 图片.resize((150, 150), Image.Resampling.LANCZOS)

        # 保存到内存并转Base64
        内存缓冲区 = io.BytesIO()
        图片.save(内存缓冲区, format="PNG")
        内存缓冲区.seek(0)
        base64数据 = base64.b64encode(内存缓冲区.read()).decode("utf-8")

        return f"data:image/png;base64,{base64数据}"

    @staticmethod
    def 从剪贴板获取图片() -> str|None:
        try:
            图片 = ImageGrab.grabclipboard()
            if 图片 is None:
                return None

            DataURI = 蓝图库编辑器.处理图片(图片)
            return DataURI

        except Exception:
            return None
    
    @staticmethod
    def 判断DataURI类型(URI字符串: str) -> str|None:

        if not URI字符串.startswith('data:'):
            return None
        
        try:
            头部部分, _ = URI字符串.split(',', 1)
            头部参数列表 = 头部部分[5:].split(';')
            if 'base64' not in [参数.strip().lower() for 参数 in 头部参数列表[1:]]:
                return None
            媒体类型部分 = 头部参数列表[0].strip()
            类型映射 = {
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg',
                'image/png': 'png',
                'image/svg+xml': 'svg'
            }
            return 类型映射.get(媒体类型部分)

        except (ValueError, IndexError):
            return None
        
    @staticmethod
    def 读取并处理图片(文件路径:str) -> tuple[bool, str]:
        try:
            with Image.open(文件路径) as f:
                图片 = f.copy()
            
            DataURI = 蓝图库编辑器.处理图片(图片)
            return True, DataURI
            
        except Exception as e:
            return False, str(e)
        
    @staticmethod
    def 写入图片(文件路径:str, base64文本:str):
        二进制数据 = base64.b64decode(base64文本)
        with open(文件路径, "wb") as f:
            f.write(二进制数据)
            
    @staticmethod
    def 读取文件(文件路径:str) -> str:
        with open(文件路径,"r",encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def 写入文件(文件路径:str, 文本:str):
        with open(文件路径,"w",encoding="utf-8") as f:
            f.write(文本)
    
    @staticmethod
    def 从HTML读取蓝图库JSON(路径:str) -> str|None:
        html = 蓝图库编辑器.读取文件(路径)
        匹配数据 = 蓝图库编辑器.匹配HM蓝图库.search(html, re.DOTALL)
        if not 匹配数据:
            return None
        return 匹配数据.group(2)
    
    @staticmethod
    def 从文件夹读取蓝图列表(路径:str) -> list|None:
        蓝图数据列表 = []
        for 文件名 in os.listdir(路径):
            if 文件名.lower().endswith(".txt"):
                文件完整路径 = os.path.join(路径, 文件名)
                文件内容 = 蓝图库编辑器.读取文件(文件完整路径)
                if 蓝图库编辑器.校验蓝图代码(文件内容):
                    蓝图数据列表.append({
                    "name": 蓝图库编辑器.检查名字(os.path.splitext(文件名)[0],'规范'),
                    "data": 文件内容
                    })
        return 蓝图数据列表
    
    @staticmethod
    def 从文件夹读取图片到蓝图列表(路径:str,蓝图列表:list) -> list:
        for 索引, 蓝图 in enumerate(蓝图列表):
            for 文件名 in os.listdir(路径):
                名字, 后缀 = os.path.splitext(文件名)
                名字 = 蓝图库编辑器.检查名字(名字,'规范')
                if 名字 == 蓝图['name'] and 后缀.lower() in ('.jpg', '.jpeg', '.png'):
                    结果,信息 = 蓝图库编辑器.读取并处理图片(os.path.join(路径, 文件名))
                    if 结果:
                        蓝图列表[索引].update({"img": 信息})
        return 蓝图列表


    # =========================== 业务 ===========================

    def 导入图片(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        文件路径 = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not 文件路径:
            return
        状态,信息 = self.读取并处理图片(文件路径)
        if not 状态:
            messagebox.showerror("错误", f"图片导入失败：\n{信息}")
            self.通知('图片导入失败')
            return
        self.图片数据 = 信息
        self.加载图片预览()
        self.通知('成功导入图片')

    def 导入蓝图文件(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        try:
            目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
            文件路径 = filedialog.askopenfilename(filetypes=[("*.txt","*.txt")], initialdir=目录)
            if not 文件路径: return
            内容 = self.读取文件(文件路径)
            if self.校验蓝图代码(内容):
                文件名 = os.path.splitext(os.path.basename(文件路径))[0] #将文件名加载为蓝图名称
                self.名称输入框.delete(0, tk.END)
                self.名称输入框.insert(0, self.检查名字(文件名,'规范'))
                self.代码输入框.delete("1.0", tk.END)
                self.代码输入框.insert("1.0", 内容)
                self.通知('蓝图导入完成')
                self.last_dir = os.path.dirname(文件路径)
            else:
                messagebox.showwarning("警告", "蓝图格式不正确")
        except Exception as e:
            messagebox.showerror("错误",f"蓝图导入失败：\n{str(e)}")

    def 删除图片(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        if not self.图片数据:
            self.通知('没有图片')
            return
        self.图片数据 = None
        self.加载图片预览()
        self.通知('图片已删除')
    
    def 复制蓝图代码(self):
        try:
            文本 = self.代码输入框.get("1.0", tk.END).strip()
            if 文本:
                self.clipboard_clear()
                self.clipboard_append(文本)
                self.通知('蓝图已复制到剪贴板')
            else:
                self.通知('输入框无内容')
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：\n{str(e)}")
    
    def 粘贴蓝图代码(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        try:
            文本 = self.clipboard_get()
        except tk.TclError:
            self.通知('剪贴板无内容')
            return
        if not self.校验蓝图代码(文本):
            self.通知('剪贴板内容不是有效的蓝图代码')
            return
        self.代码输入框.delete("1.0", tk.END)
        self.代码输入框.insert("1.0", 文本)
        self.通知('已粘贴')

    def 粘贴图片(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        图片 = self.从剪贴板获取图片()
        if 图片:
            self.图片数据 = 图片
            self.加载图片预览()
            self.通知('成功粘贴截图')
        else:
            self.通知('剪贴板没有截图')

    def 新建蓝图(self):
        if self.当前类型 == None:
            self.通知("未选择蓝图类型")
            return
        蓝图列表 = self.获取蓝图列表(self.当前类型)
        新数据 = {
            "name": self.添加序号("新蓝图",[名["name"] for 名 in 蓝图列表]),
            "data": ""
        }
        列表长度 = len(蓝图列表)
        if self.当前蓝图索引 != None:
            if self.当前蓝图索引+1 < 列表长度 and 蓝图列表[self.当前蓝图索引+1].get('lock', 0):
                索引 = 列表长度
            else:
                索引 = self.当前蓝图索引 + 1
        else:
            索引 = 列表长度

        self.添加蓝图(self.当前类型, 新数据, 索引)
        self.当前蓝图索引 = 索引
        self.刷新蓝图列表()
        self.通知(f'已添加 {新数据["name"]}')


    def 保存蓝图(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        if self.当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        
        新数据 = {
            "name": self.名称输入框.get().strip(),
            "data": self.代码输入框.get("1.0", tk.END).strip(),
            "memo": self.备注输入框.get().strip(),
        }

        if not self.检查名字(新数据["name"]):
            messagebox.showwarning("警告", '蓝图名包含：空格\'"#.<>=/\\')
            return
        
        if not self.蓝图重名检测(新数据["name"], self.当前类型, self.当前蓝图索引):
            messagebox.showwarning("警告", "蓝图名重复")
            return

        if not self.校验蓝图代码(新数据["data"]):
            messagebox.showwarning("警告", "蓝图代码格式不正确")
            return
        
        if self.图片数据:
            新数据.update({"img": self.图片数据})

        # 如果没有选中蓝图则新增 没有则更改
        if self.当前蓝图索引 == None:
            self.添加蓝图(self.当前类型, 新数据)
            self.当前蓝图索引 = len(self.获取蓝图列表(self.当前类型)) -1
        else:
            self.更改蓝图(self.当前类型, 新数据, self.当前蓝图索引)
       
        self.刷新蓝图列表()
        self.通知(f'{新数据["name"]} 已保存')

    def 删除蓝图(self,快速删除:bool=False):
        if self.当前类型 == None or self.当前蓝图索引 == None:
            if not 快速删除:
                messagebox.showwarning("警告", "请先选择蓝图")
            else:
                self.通知('请先选择蓝图')
            return
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可删除')
            return
        if not 快速删除 and not messagebox.askyesno("确认", "确定删除？"):
            return
        垃圾 = self.移出数据(self.当前类型, self.当前蓝图索引)
        self.当前蓝图索引 = None

        self.刷新蓝图列表()
        self.通知(f'{垃圾["name"]} 已删除')

    def 排序蓝图(self,步:int):
        if self.当前类型 == None or self.当前蓝图索引 == None:
            self.通知('未选择蓝图')
            return
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可移动')
            return
        目标 = self.当前蓝图索引 + 步
        if 目标 < 0 or 目标 == len(self.获取蓝图列表(self.当前类型)):
            self.通知('已到顶了' if 步 < 0 else '已到底了')
            return
        if self.获取蓝图(self.当前类型, 目标).get('lock', 0):
            self.通知('目标位置蓝图不可移动')
            return
        
        self.添加蓝图(self.当前类型, self.移出数据(self.当前类型, self.当前蓝图索引), 目标)
        self.当前蓝图索引 = 目标
        self.刷新蓝图列表()
        self.通知('排序蓝图')

    def 添加蓝图分类(self):
        新类名 = simpledialog.askstring("输入", "请输入2~8个字符：")
        if not 新类名: return
        新类名 = 新类名.strip()
        if not self.检查名字(新类名):
            messagebox.showwarning("警告", '蓝图名包含：空格\'"#.<>=/\\')
            return
        if len(新类名) < 2 or len(新类名) > 8:
            messagebox.showwarning("警告","请输入2~8个字符")
            return
        if 新类名 in self.获取类表():
            messagebox.showwarning("警告","不可输入相同的类名")
            return

        self.列表写入(新类名, [], '修改')
        self.刷新页面()
        self.选择蓝图类型(新类名)
        self.通知(f'已添加 {新类名} 分类')
    
    def 排序分类(self, 类型:str, 步:int):
        if not self.移动分类(类型,步):
            self.通知('已到顶了' if 步 < 0 else '已到底了')
            return
        当类 = self.当前类型
        self.刷新页面()
        self.选择蓝图类型(当类)
        self.通知('排序蓝图类型')

    def 删除蓝图分类(self,类型:str):
        if len(self.获取类表()) <= 1:
            return messagebox.showwarning("警告", "不能删除最后一个分类")
        if not messagebox.askyesno("确认", f"确定删除 ‘{类型}’ 吗？"):
            return
        self.移出数据(类型)
        当类 = self.当前类型 if 类型 != self.当前类型 else None
        self.刷新页面()
        self.选择蓝图类型(当类)
        self.通知(f'已删除 {类型} 分类')

    def 更名分类(self,类型:str):
        新类名 = simpledialog.askstring("输入", "请输入2~8个字符：", initialvalue=类型)
        if not 新类名: return
        新类名 = 新类名.strip()
        if not self.检查名字(新类名):
            messagebox.showwarning("警告", '蓝图名包含：空格\'"#.<>=/\\')
            return
        if len(新类名) < 2 or len(新类名) > 8:
            messagebox.showwarning("警告","请输入2~8个字符")
            return
        if 新类名 in self.获取类表():
            messagebox.showwarning("警告","不可输入相同的类名")
            return
        当类 = self.当前类型 if 类型 != self.当前类型 else 新类名
        self.修改类名(类型,新类名)
        self.通知(f'已将 {类型} 更名为 {新类名}')
        self.刷新页面()
        self.选择蓝图类型(当类)

    def 新建蓝图库(self):
        提示 = "注意：当前数据未保存!" if self._数据是否修改 else  ""
        if not messagebox.askyesno("确认", f"确定新建蓝图库吗？\n{提示}"):
            return
        self.从JSON字符串载入蓝图库(self.新蓝图库)
        self.刷新页面()
        self.选择蓝图类型(self.获取类表()[0])
        self.通知("新建蓝图库")
    
    def 载入默认库(self):
        提示 = "注意：当前数据未保存!" if self._数据是否修改 else  ""
        if not messagebox.askyesno("确认", f"确定加载默认蓝图吗？\n{提示}"):
            return
        try:
            self.从JSON字符串载入蓝图库(self.读取文件(self.默认蓝图库路径))
            self.刷新页面()
            self.选择蓝图类型(self.获取类表()[0])
            self.通知("载入默认蓝图库")
        except Exception as e:
            messagebox.showerror("错误",f"默认蓝图加载失败：\n{str(e)}")

    def 导入JSON(self):
        if self._数据是否修改:
            if not messagebox.askyesno("确认", "当前蓝图库未保存，确定载入新蓝图库吗？"):
                return
        try:
            目录 = os.path.dirname(self.last_json) if hasattr(self, "last_json") and self.last_json else "."
            路径 = filedialog.askopenfilename(initialdir=目录,filetypes=[("*.json","*.json")],title="导入JSON文件")
            if not 路径: return
            内容 = self.读取文件(路径)
            self.从JSON字符串载入蓝图库(内容)
            self.刷新页面()
            self.选择蓝图类型(self.获取类表()[0])
            messagebox.showinfo("成功", "导入完成")
            self.通知('导入JSON')
            self.last_json = 路径
        except Exception as e:
            messagebox.showerror("错误",f"文件导入失败：\n{str(e)}")

    def 导出JSON(self):
        try:
            目录 = os.path.dirname(self.last_json) if hasattr(self, "last_json") and self.last_json else "."
            路径 = filedialog.asksaveasfilename(initialdir=目录,defaultextension=".json", filetypes=[("*.json","*.json")],title="导出JSON文件")
            if not 路径: return
            self.写入文件(路径,self.读取蓝图库为JSON字符串(4))
            messagebox.showinfo("成功", "导出完成")
            self.通知('导出JSON')
            self.last_json = 路径
        except Exception as e:
            messagebox.showerror("错误",f"文件导出失败：\n{str(e)}")

    def 导出HTML(self):
        try:
            html = self.读取文件(self.HTML模板路径)
            json字符串 = self.读取蓝图库为JSON字符串().replace("\\", "\\\\").replace("\n", "\\n")
            html = 蓝图库编辑器.匹配HM蓝图库.sub(
                rf"\1{json字符串}",
                html,
                re.DOTALL
            )
            html = 蓝图库编辑器.匹配HMname.sub(
                rf'\1{self.name}\3',
                html
            )

            目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
            路径 = filedialog.asksaveasfilename(initialdir=目录,defaultextension=".html", filetypes=[("HTML","*.html")],title="导出为HTML")
            if not 路径: return
            self.写入文件(路径,html)
            self.last_dir = os.path.dirname(路径)
            if messagebox.askyesno("导出完成", "导出完成，是否打开HTML文件？"):
                os.startfile(路径)
        except Exception as e:
            messagebox.showerror("错误",f"文件导出失败：\n{str(e)}")
    
    def 导入HTML(self):
        if self._数据是否修改:
            if not messagebox.askyesno("确认", "当前蓝图库未保存，确定载入新蓝图库吗？"):
                return
        try:
            目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
            路径 = filedialog.askopenfilename(initialdir=目录,filetypes=[("HTML","*.html")],title="导入HTML文件")
            if not 路径: return

            蓝图库JSON = self.从HTML读取蓝图库JSON(路径)
            if not 蓝图库JSON:
                return messagebox.showwarning("警告","这不是有效的HTML")
            
            self.从JSON字符串载入蓝图库(蓝图库JSON)
            self.刷新页面()
            self.选择蓝图类型(self.获取类表()[0])
            self.last_dir = os.path.dirname(路径)
            messagebox.showinfo("成功", "导入完成")
            self.通知('导入成功')

        except Exception as e:
            messagebox.showerror("错误",f"文件入失败：\n{str(e)}")

    def 导出文件夹(self):
        try:
            目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
            根目录 = filedialog.askdirectory(initialdir=目录, title="选择蓝图导出根目录")
            if not 根目录:return
            self.last_dir = 根目录
            
            计数 = 0
            for 分类名 in self.获取类表():
                分类路径 = os.path.join(根目录, 分类名)
                if not os.path.exists(分类路径):
                    os.makedirs(分类路径)
                
                for 蓝图数据 in self.获取蓝图列表(分类名):
                    名字 = f"{蓝图数据['name']}"
                    蓝图文件路径 = os.path.join(分类路径, 名字 + ".txt")
                    
                    self.写入文件(蓝图文件路径,蓝图数据["data"].strip())
                    计数 += 1
                    try:
                        图片DataURI = 蓝图数据["img"].strip()
                        图片类型 = self.判断DataURI类型(图片DataURI)
                        if 图片类型:
                            图片路径 = os.path.join(分类路径, f"{名字}.{图片类型}")
                            self.写入图片(图片路径,图片DataURI.split(",")[1])
                    except:continue

            messagebox.showinfo("成功", f"{计数}个蓝图已导出到：\n{根目录}")
            self.通知(f'导出文件夹完成：{根目录}')
        except Exception as e:
            messagebox.showerror("错误", f"导出异常中止，已导出了{计数}个蓝图：\n{str(e)}")

    def 并入(self,操作):
        允许值 = {'从HTML', '从JSON'}
        if 操作 not in 允许值:
            raise ValueError(f"操作只能是：{允许值}")
        try:
            if 操作 == '从HTML':
                目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
                路径 = filedialog.askopenfilename(initialdir=目录,filetypes=[("HTML","*.html")],title="导入HTML文件")
                if not 路径: return
                内容 = self.从HTML读取蓝图库JSON(路径)
                self.last_dir = os.path.dirname(路径)
            elif 操作 == '从JSON':
                目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
                路径 = filedialog.askopenfilename(initialdir=目录,filetypes=[("*.json","*.json")],title="导入JSON文件")
                if not 路径: return
                内容 = self.读取文件(路径)
                self.last_dir = os.path.dirname(路径)
            if not isinstance(内容, str):
                return messagebox.showwarning("警告", "不是有效的文件")
            读取的库 = json.loads(内容)
            if not self.检查蓝图库格式(读取的库):
                return messagebox.showwarning("警告", "不是有效的文件")
        except Exception as e:
            return messagebox.showerror("错误", f"读取文件失败：\n{str(e)}")
        
        def 确认():
            选中索引 = 列表框.curselection()
            if not 选中索引:
                messagebox.showwarning("提示", "请先选择要合并的分类")
                return
            选中分类 = [列表框.get(i) for i in 选中索引]
            待合并库 = {key: 读取的库[key] for key in 选中分类}
            for k,v in 待合并库.items():
                self.列表写入(k,v)
            当前类型 = self.当前类型
            self.刷新页面()
            self.选择蓝图类型(当前类型)
            self.通知("已合并")
            窗口.destroy()

        窗口 = tk.Toplevel()
        窗口.title("合并蓝图库")
        窗口.geometry(f"300x250+{(窗口.winfo_screenwidth()-300)//2}+{(窗口.winfo_screenheight()-250)//2}")
        窗口.resizable(False, False)  # 禁止缩放
        tk.Label(窗口, text="选择要合并的分类", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        tk.Label(窗口, text="鼠标拖动或按住Ctrl/Shift多选", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        列表框架 = ttk.Frame(窗口)
        列表框架.pack(padx=15, fill=tk.BOTH,expand=True)
        列表框架.pack_propagate(False)
        滚动条 = tk.Scrollbar(列表框架)
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        列表框 = tk.Listbox(列表框架, yscrollcommand=滚动条.set)
        列表框.pack(fill=tk.BOTH, expand=True)
        滚动条.config(command=列表框.yview)
        列表框.config(selectmode=tk.EXTENDED,exportselection=False)
        分类列表 = list(读取的库.keys())
        for 类名 in 分类列表:
            列表框.insert(tk.END,类名)
        tk.Label(窗口, text="如果蓝图重名将会自动添加序号", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        按钮框架 = ttk.Frame(窗口)
        按钮框架.pack(pady=15,fill=tk.Y)
        ttk.Button(按钮框架, text="确认", command=确认).pack(side=tk.LEFT, padx=10)
        ttk.Button(按钮框架, text="取消", command=窗口.destroy).pack(side=tk.LEFT, padx=10)
        窗口.grab_set()
        窗口.wait_window()

    def 批量操作窗口(self,操作):
        允许值 = {'移动', '删除','导入'}
        蓝图数据列表 = []
        # 初始校验
        if 操作 not in 允许值:
            raise ValueError(f"操作类型只能是：{允许值}")
        if 操作 in ('移动','删除') and self.当前类型 == None:
            return messagebox.showwarning("警告", "未选择蓝图类型")
        if 操作 == '导入':
            try:
                目录 = self.last_dir if hasattr(self, "last_dir") and self.last_dir else "."
                文件夹路径 = filedialog.askdirectory(initialdir=目录,title="请选择蓝图文件夹")
                if not 文件夹路径:return
                蓝图数据列表 = self.从文件夹读取蓝图列表(文件夹路径)
                self.last_dir = 文件夹路径
            except Exception as e:
                return messagebox.showerror("错误", f"文件夹读取失败：\n{str(e)}")
            if not 蓝图数据列表:
                return messagebox.showinfo("提示", "该文件夹下未找到蓝图.txt文件！")

        def 确认操作():
            nonlocal 蓝图数据列表
            # 操作前校验
            if 操作 in ('移动','删除') and not 列表框.curselection():
                return messagebox.showwarning("警告", "请至少选择一个蓝图")
            if 操作 == '移动' and not 选中项.get():
                return messagebox.showwarning("警告", "请选择移动的目标目录")
            if 操作 == '删除' and not messagebox.askyesno("确认", "确定删除选中的蓝图吗？"):
                return
            # 操作数据
            if 操作 == '导入':
                蓝图数据列表 = [蓝图数据列表[i] for i in 列表框.curselection()]
                if 导入同名图片.get():
                    蓝图数据列表 = self.从文件夹读取图片到蓝图列表(文件夹路径,蓝图数据列表)
                类型列表 = self.获取类表()
                类名 = self.检查名字(os.path.basename(文件夹路径),'规范')
                if 导入当前分类.get() and self.当前类型 != None:
                    目标 = self.当前类型
                else:
                    目标 = 类名 if not 类名 in 类型列表 else self.添加序号(类名,类型列表)
            elif 操作 in ('移动','删除'):
                索引列表 = [索引对照表[i][0] for i in 列表框.curselection()]
                for 索引 in sorted(索引列表, reverse=True): # 逆序删除，避免索引错乱
                    蓝图数据列表.append(self.移出数据(self.当前类型, 索引))
            if 操作 == '移动':
                蓝图数据列表.reverse()  # 恢复原顺序
                目标 = 选中项.get()
            if 操作 in ('移动','导入'):
                self.列表写入(目标,蓝图数据列表)
                选择 = 目标
            # 生成消息
            if 操作 == '移动':
                消息 =f'将{len(蓝图数据列表)}个蓝图从 {self.当前类型} 移动到 {选中项.get()}'
            elif 操作 == '导入':
                消息 =f'已将{len(蓝图数据列表)}个蓝图导入到 {目标}'
            elif 操作 == '删除':
                选择 = self.当前类型
                消息 =f'已删除{len(蓝图数据列表)}个蓝图'
            # 刷新界面
            self.刷新页面()
            self.选择蓝图类型(选择)
            self.通知(消息)
            窗口.destroy()
        
        # 初始化界面
        窗口 = tk.Toplevel()
        窗口.title("批量操作")
        窗口.geometry(f"500x350+{(窗口.winfo_screenwidth()-500)//2}+{(窗口.winfo_screenheight()-350)//2}")
        窗口.resizable(False, False)  # 禁止缩放
        if 操作 == '移动':
            窗口.title("移动蓝图")
            选项框架 = ttk.Frame(窗口)
            选项框架.pack(padx=15, fill=tk.X)
            tk.Label(选项框架, text=f"从 {self.当前类型} 移动到：").pack(side=tk.LEFT)
            选中项 = tk.StringVar()
            选项 = ttk.Combobox(
                选项框架,
                textvariable=选中项,
                values=list(self.获取类表(self.当前类型)),
                state="readonly",
            )
            选项.pack(side=tk.LEFT,)
            选项.configure(height=5)
        elif 操作 == '删除':
            窗口.title("删除蓝图")
        elif 操作 == '导入':
            窗口.title("批量导入")
            导入同名图片 = tk.IntVar(value=1)
            导入当前分类 = tk.IntVar(value=0)
            ttk.Checkbutton(窗口, text="导入同名图片", variable=导入同名图片).pack(padx=15, fill=tk.X)
            ttk.Checkbutton(窗口, text="导入到当前分类，如果已选择的话；否则创建新分类", variable=导入当前分类).pack(padx=15, fill=tk.X)
        tk.Label(窗口, text="鼠标拖动或按住Ctrl/Shift多选", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        列表框架 = ttk.Frame(窗口)
        列表框架.pack(padx=15, fill=tk.BOTH,expand=True)
        列表框架.pack_propagate(False)
        滚动条 = tk.Scrollbar(列表框架)
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        列表框 = tk.Listbox(列表框架, yscrollcommand=滚动条.set)
        列表框.pack(fill=tk.BOTH, expand=True)
        滚动条.config(command=列表框.yview)
        if 操作 in ('移动','导入'):
            tk.Label(窗口, text="如果重名将会自动添加序号", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        按钮框架 = ttk.Frame(窗口)
        按钮框架.pack(pady=15,fill=tk.Y)
        ttk.Button(按钮框架, text="确认", command=确认操作).pack(side=tk.LEFT, padx=10)
        ttk.Button(按钮框架, text="取消", command=窗口.destroy).pack(side=tk.LEFT, padx=10)
        # 填入内容
        if 操作 in ('移动','删除'):
            列表框.config(selectmode=tk.EXTENDED,exportselection=False)
            索引对照表 = [[索引, 蓝图['name']] for 索引, 蓝图 in enumerate(self.获取蓝图列表(self.当前类型)) if not (蓝图.get('lock',0))]
            for 索引, 蓝图名 in 索引对照表:
                列表框.insert(tk.END,蓝图名)
        elif 操作 == '导入':
            for 蓝图数据 in 蓝图数据列表:
                列表框.insert(tk.END, 蓝图数据["name"])
            列表框.config(selectmode=tk.EXTENDED,exportselection=False)

        窗口.grab_set()
        窗口.wait_window()

        
    def 加载配置(self):
        try:
            with open(self.获取配置文件路径(), "r", encoding="utf-8") as f:
                配置 = json.load(f)
            if not 配置:return
            键表 = ["last_json", "last_dir", "name"]
            for 键 in 键表:
                if 配置.get(键):
                    setattr(self, 键, 配置[键])
        except Exception: return
    
    def 保存配置(self):
        try:
            路径 = self.获取配置文件路径()
            配置 = {}
            if os.path.exists(路径):
                with open(路径, "r", encoding="utf-8") as f:
                    配置 = json.load(f)
            键表 = ["last_json", "last_dir"]
            for 键 in 键表:
                配置[键] = getattr(self, 键)
            with open(路径, "w", encoding="utf-8") as f:
                json.dump(配置, f, ensure_ascii=False, indent=4)
        except Exception: return

    @staticmethod
    def 获取配置文件路径() -> str:
        应用数据目录 = os.getenv("APPDATA") # 获取 Windows 用户目录下的 AppData/Roaming
        软件配置文件夹 = os.path.join(应用数据目录, "DsBlueprint_Lib")
        配置文件路径 = os.path.join(软件配置文件夹, "config.json")

        if not os.path.exists(软件配置文件夹):
            os.makedirs(软件配置文件夹)
        return 配置文件路径



if __name__ == "__main__":
    app = 蓝图库编辑器()
    app.mainloop()