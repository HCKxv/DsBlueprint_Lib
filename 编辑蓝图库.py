import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json,os,io,base64,sys

import regex as re
from PIL import Image, ImageTk

class 蓝图库编辑器(tk.Tk):

    匹配HMname = re.compile( r'(Hname\s*=\s*")(.*?)(")')
    匹配HM蓝图库 = re.compile(r'(BPlist\s*=\s*)(\{(?:[^{}]|(?2))*\})')
    匹配蓝图代码 = re.compile(r'^DYBP:.*"[0-9A-F]{32}$')
    非法字符 = {' ', '"', '\'', '#', '.', '<', '>', '=', '/', '\\'}
    HTML模板路径 = "./模板.html"
    默认蓝图库路径 = "./默认蓝图库.json"
    默认蓝图库_备用 = {"实用":[{"name":"演示1","data":"《蓝图代码》"},{"name":"演示2","data":"《蓝图代码》"}],"观赏":[{"name":"演示3","data":"《蓝图代码》"}]}

    def __init__(self):
        super().__init__()
        if hasattr(sys, '_MEIPASS'):
            self.默认蓝图库路径 = os.path.join(sys._MEIPASS, self.默认蓝图库路径)
            self.HTML模板路径 = os.path.join(sys._MEIPASS, self.HTML模板路径)
        
        self.name = ""

        self.蓝图库 = {}
        self.当前类型 = None
        self.当前蓝图索引 = None
        self.图片数据 = None
        self._数据是否未保存 = False
        self._当前蓝图是否锁定 = 0
        self._通知定时 = None

        self.title("戴森球计划球体蓝图库：by氢碳钾")
        self.geometry("900x600")
        self.minsize(850, 500)

        ttk.Button(self, takefocus=0)
        self.样式 = ttk.Style()
        self.样式.configure("Category.TButton", padding=5)
        self.样式.configure("Selected.TButton", background="#4a86e8", padding=5)
        
        self.顶部框架 = ttk.Frame(self)
        self.顶部框架.pack(fill=tk.X, padx=10, pady=5)
        
        self.导入JSON按钮 = ttk.Button(self.顶部框架, text="加载JSON", command=self.导入JSON)
        self.导入JSON按钮.pack(side=tk.LEFT, padx=5)
        self.导入HTML按钮 = ttk.Button(self.顶部框架, text="从HTML导入", command=self.导入HTML)
        self.导入HTML按钮.pack(side=tk.LEFT, padx=5)
        self.导出JSON按钮 = ttk.Button(self.顶部框架, text="导出JSON", command=self.导出JSON)
        self.导出JSON按钮.pack(side=tk.LEFT, padx=5)
        self.导出HTML按钮 = ttk.Button(self.顶部框架, text="导出为HTML", command=self.导出HTML)
        self.导出HTML按钮.pack(side=tk.LEFT, padx=5)
        self.导出文件夹按钮 = ttk.Button(self.顶部框架, text="导出文件夹", command=self.导出文件夹)
        self.导出文件夹按钮.pack(side=tk.LEFT, padx=5)
        self.通知窗 = ttk.Label(self.顶部框架, width=50, foreground="#333", relief="solid", padding=2)
        self.通知窗.pack(side=tk.RIGHT, padx=5)

        self.主框架 = ttk.Frame(self)
        self.主框架.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.分类框架 = ttk.LabelFrame(self.主框架, text="蓝图分类")
        self.分类框架.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.分类项框架 = ttk.Frame(self.分类框架)
        self.分类项框架.pack(fill=tk.X, padx=5, pady=3)
        self.类选项框架 = ttk.Frame(self.分类框架)
        self.类选项框架.pack(fill=tk.X, padx=5,pady=(10, 3))
        self.删除类按钮 = ttk.Button(self.类选项框架, text="删除分类", width=8, command=self.删除蓝图分类)
        self.删除类按钮.grid(row=0, column=0, columnspan=2, pady=2)
        self.增序类按钮 = ttk.Button(self.类选项框架, text="⬆️", width=3, command=lambda: self.排序分类(-1))
        self.增序类按钮.grid(row=0, column=2, pady=2)
        self.降序类按钮 = ttk.Button(self.类选项框架, text="⬇️", width=3, command=lambda: self.排序分类(1))
        self.降序类按钮.grid(row=0, column=3,pady=2)
        self.添加类按钮 = ttk.Button(self.类选项框架, text="添加分类", width=8, command=self.添加蓝图分类)
        self.添加类按钮.grid(row=1, column=0, columnspan=2, pady=2)
        self.修改类名按钮 = ttk.Button(self.类选项框架, text="修改类名", width=8, command=self.更名分类)
        self.修改类名按钮.grid(row=1, column=2, columnspan=2, pady=2)
        
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
        self.蓝图列表.bind('<<ListboxSelect>>', self.选中蓝图)
        self.蓝图列表.bind('<Control-c>', self.快捷键_复制选中蓝图代码)
        self.蓝图列表.bind('<Control-C>', self.快捷键_复制选中蓝图代码)
        
        self.编辑区框架 = ttk.LabelFrame(self.主框架, text="蓝图编辑")
        self.编辑区框架.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, ipadx=8, ipady=5)

        self.编号显示标签 = ttk.Label(self.编辑区框架, text="新建蓝图：")
        self.编号显示标签.grid(row=0, column=0, columnspan=5, padx=8, pady=8, sticky="n")

        self.名称标签 = ttk.Label(self.编辑区框架, text="*蓝图名:")
        self.名称标签.grid(row=1, column=0, padx=8, pady=8, sticky=tk.W)
        self.名称输入框 = ttk.Entry(self.编辑区框架, width=30)
        self.名称输入框.grid(row=1, column=1, padx=8, pady=8, sticky=tk.W)
        self.导入蓝图按钮 = ttk.Button(self.编辑区框架, text="导入蓝图", width=10, command=self.导入蓝图文件)
        self.导入蓝图按钮.grid(row=1, column=2, columnspan=2, padx=2, sticky=tk.W)

        self.蓝图代码标签 = ttk.Label(self.编辑区框架, text="*蓝图代码:")
        self.蓝图代码标签.grid(row=2, column=0, padx=8, pady=8, sticky=tk.NW)
        self.代码输入框 = tk.Text(self.编辑区框架, width=30, height=1, wrap="none")
        self.代码输入框.grid(row=2, column=1, sticky="nsew",padx=8, pady=8)
        self.代码输入框.bind("<ButtonRelease-1>", self.自动全选)
        for key in ["<Return>", "<Up>", "<Down>", "<Left>", "<Right>"]:
            self.代码输入框.bind(key, self.禁止按键)
        self.复制按钮 = ttk.Button(self.编辑区框架, text="复制", width=4, command=self.复制蓝图代码)
        self.复制按钮.grid(row=2, column=2, padx=2, sticky=tk.W)
        self.粘贴按钮 = ttk.Button(self.编辑区框架, text="粘贴", width=4, command=self.粘贴蓝图代码)
        self.粘贴按钮.grid(row=2, column=3, padx=2, sticky=tk.W)
        self.图片预览标签 = ttk.Label(self.编辑区框架, text="蓝图图片:")
        self.图片预览标签.grid(row=3, column=0, padx=8, pady=8, sticky=tk.NW)
        self.预览画布 = tk.Canvas(self.编辑区框架, width=160, height=160, bg="#f5f5f5", bd=1, relief="solid")
        self.预览画布.grid(row=3, column=1, padx=8, pady=8)
        self.图片编辑框架 = ttk.Frame(self.编辑区框架)
        self.图片编辑框架.grid(row=3, column=2, columnspan=2, pady=5)
        self.导入图片按钮 = ttk.Button(self.图片编辑框架, text="导入图片",  width=10, command=self.导入图片)
        self.导入图片按钮.grid(padx=2, sticky=tk.W)
        self.删除图片按钮 = ttk.Button(self.图片编辑框架, text="删除图片", width=10, command=self.删除图片)
        self.删除图片按钮.grid(padx=2, sticky=tk.W)

        self.备注标签 = ttk.Label(self.编辑区框架, text="蓝图备注:")
        self.备注标签.grid(row=4, column=0, padx=8, pady=8, sticky=tk.W)
        self.备注输入框 = ttk.Entry(self.编辑区框架, width=40)
        self.备注输入框.grid(row=4, column=1, columnspan=3, padx=8, pady=8, sticky=tk.W)
        
        self.按钮框架 = ttk.Frame(self.编辑区框架)
        self.按钮框架.grid(row=5, column=0, columnspan=4, pady=5)
        self.保存按钮 = ttk.Button(self.按钮框架, text="保存蓝图", command=self.保存蓝图)
        self.保存按钮.pack(side=tk.LEFT, padx=2)
        self.删除按钮 = ttk.Button(self.按钮框架, text="删除蓝图", command=self.删除蓝图)
        self.删除按钮.pack(side=tk.LEFT, padx=2)

        self.protocol("WM_DELETE_WINDOW", self.关闭窗口)
        
        self.加载默认数据()
        self.通知("提示：选择蓝图后Ctrl+C可直接复制蓝图代码",5000)
    
    def 关闭窗口(self):
        if self._数据是否未保存:
            result = messagebox.askyesnocancel(
            title="保存提示",
            message="蓝图库未保存，是否保存为JSON？",
            )
            if result is None:
                return
            if result:
                self.导出JSON()
        self.destroy()


    def 自动全选(self,event):
        event.widget.tag_add(tk.SEL, "1.0", tk.END)
    def 禁止按键(self,event):
        return "break"
    def 快捷键_复制选中蓝图代码(self, event=None):
        if self.当前类型 == None or self.当前蓝图索引 == None:
            self.通知("请选择蓝图")
            return
        try:
            蓝图数据 = self.获取数据(self.当前类型, self.当前蓝图索引)
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
            with open(self.默认蓝图库路径,"r",encoding="utf-8") as f:
                self.蓝图库 = json.load(f)
        except FileNotFoundError:
            self.蓝图库 = self.默认蓝图库_备用
        self.刷新页面()
        self.选择蓝图类型(self.获取类表()[0])

    def 刷新页面(self):
        self.当前类型 = None
        self.当前蓝图索引 = None
        self.刷新蓝图列表()

        for 控件 in self.分类项框架.winfo_children(): 控件.destroy()
        类型列表 = self.获取类表()
        for 蓝图类型 in 类型列表:
            按钮 = ttk.Button(self.分类项框架, text=蓝图类型, style="Category.TButton",command=lambda c=蓝图类型: self.选择蓝图类型(c))
            按钮.pack(fill=tk.X, padx=5, pady=3)

    def 选择蓝图类型(self, 蓝图类型):
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
            for 蓝图数据 in self.获取数据(self.当前类型):
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
        
        蓝图数据 =self.获取数据(self.当前类型, self.当前蓝图索引)
        self._当前蓝图是否锁定 = 蓝图数据.get('lock', 0)
        
        self.编号显示标签.config(text=f"修改蓝图：{self.当前类型} -- {蓝图数据["name"]}")
        self.名称输入框.insert(0, 蓝图数据['name'])
        self.代码输入框.insert("1.0", 蓝图数据['data'])
        self.备注输入框.insert(0,蓝图数据.get('memo', ''))
        self.图片数据 = 蓝图数据.get("img","")
        self.加载图片预览()
        
        if self._当前蓝图是否锁定:
            self.编号显示标签.config(text="该蓝图不可修改")
            self.名称输入框.config(state="disabled")
            self.代码输入框.config(state="disabled",bg="#f0f0f0", fg="#888888")
            self.备注输入框.config(state="disabled")

    def 加载图片预览(self):
        try:
            if not self.图片数据:
                self.预览画布.delete("all")
                self.预览画布.create_text(80, 80, text="暂无图片", fill="#999")
                self._预览图片缓存 = None
                return

            if self.图片数据.startswith("data:image/svg+xml;base64,"):
                self.预览画布.delete("all")
                self.预览画布.create_text(80, 80, text="这是svg图片\n导出html可正常显示", fill="#2E8B57")
                return

            base64_str = self.图片数据.split(",")[1]
            img_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_data))

            self._预览图片缓存 = ImageTk.PhotoImage(img)
            w = self.预览画布.winfo_width()
            h = self.预览画布.winfo_height()
            self.预览画布.delete("all")
            self.预览画布.create_image(w / 2, h / 2, image=self._预览图片缓存, anchor="center")
        except base64.binascii.Error:
            self.预览画布.delete("all")
            self.预览画布.create_text(80, 80, text="图片编码错误", fill="red")
        except Exception as e:
            self.预览画布.delete("all")
            self.预览画布.create_text(80, 80, text=f"预览失败：\n{str(e)}", fill="red")

    def 选中蓝图(self, event):
        选中 = self.蓝图列表.curselection()
        if not 选中: return
        
        self.当前蓝图索引 = 选中[0] if self.当前蓝图索引 != 选中[0] else None
        if self.当前蓝图索引 == None:
            self.蓝图列表.selection_clear(0, tk.END)
        self.刷新编辑区()
    
    def 通知(self,消息, 延迟时间=3000):
        if self._通知定时:
            self.after_cancel(self._通知定时)
        
        self.通知窗.config(text=消息)
        
        self._通知定时 = self.after(延迟时间, lambda: self.通知窗.config(text=""))

    
    def 获取数据(self,蓝图类型,蓝图索引=None):
        if 蓝图索引 == None:
            return self.蓝图库[蓝图类型]
        return self.蓝图库[蓝图类型][蓝图索引]
    
    def 添加数据(self,蓝图类型,蓝图数据,蓝图索引=None):
        if 蓝图索引 == None:
            self.蓝图库[蓝图类型].append(蓝图数据)
        else:
            self.蓝图库[蓝图类型].insert(蓝图索引, 蓝图数据)
        self._数据是否未保存 = True
    
    def 更改数据(self,蓝图类型,新数据,蓝图索引):
        self.蓝图库[蓝图类型][蓝图索引] = 新数据
        self._数据是否未保存 = True
    
    def 移出数据(self,蓝图类型,蓝图索引=None):
        self._数据是否未保存 = True
        if 蓝图索引 == None:
            return self.蓝图库.pop(蓝图类型)
        return self.蓝图库[蓝图类型].pop(蓝图索引)
    
    def 添加分类(self,新类名):
        self.蓝图库[新类名] = []
        self._数据是否未保存 = True

    def 获取类表(self,排除项=None):
        分类列表 = list(self.蓝图库.keys())
        if 排除项 != None:
            分类列表.remove(排除项)
        return 分类列表
    
    def 列表写入(self,蓝图类型,蓝图列表,模式='添加'):
        if 模式 == '添加':
            self.蓝图库.setdefault(蓝图类型, [])
            名字列表 = [名["name"] for 名 in self.获取数据(蓝图类型)]
            for 蓝图数据 in 蓝图列表:
                if 蓝图数据['name'] in 名字列表:
                    蓝图数据['name'] = self.添加序号(蓝图数据['name'],名字列表)
                self.蓝图库[蓝图类型].append(蓝图数据)
        elif 模式 == '修改':
            self.蓝图库[蓝图类型] = 蓝图列表
            self._数据是否未保存 = True

    def 排序分类(self, 步):
        类型 = self.当前类型
        if 类型 == None:
            self.通知('未选择分类')
            return
        
        蓝图列表 = list(self.蓝图库.items())
        索引 = [k[0] for k in 蓝图列表].index(类型)
        目标 = 索引 + 步

        if 目标 < 0 or 目标 == len(蓝图列表):
            self.通知('已到顶了' if 步 < 0 else '已到底了')
            return
        蓝图列表.insert(目标, 蓝图列表.pop(索引))
        self.蓝图库 = dict(蓝图列表)
        self._数据是否未保存 = True

        self.刷新页面()
        self.选择蓝图类型(类型)
        self.通知('排序蓝图类型')
    
    def 排序蓝图(self,步):
        if self.当前类型 == None or self.当前蓝图索引 == None:
            self.通知('未选择蓝图')
            return
        if self.获取数据(self.当前类型, self.当前蓝图索引).get('lock', 0):
            self.通知('该蓝图不可移动')
            return
        目标 = self.当前蓝图索引 + 步
        if 目标 < 0 or 目标 == len(self.获取数据(self.当前类型)):
            self.通知('已到顶了' if 步 < 0 else '已到底了')
            return
        if self.获取数据(self.当前类型, 目标).get('lock', 0):
            self.通知('目标位置蓝图不可移动')
            return
        
        self.添加数据(self.当前类型, self.移出数据(self.当前类型, self.当前蓝图索引), 目标)
        self.当前蓝图索引 = 目标
        self._数据是否未保存 = True

        self.刷新蓝图列表()
        self.通知('排序蓝图')

    def 校验蓝图代码(self,蓝图代码):
        return bool(self.匹配蓝图代码.match(蓝图代码.strip()))

    def 检查名字(self,名字, 模式='检测'):
        if 模式 == '检测':
            return 名字 and not any(c in self.非法字符 for c in 名字)
        if 模式 == '规范':
            return ''.join([char for char in 名字 if char not in self.非法字符])

    def 蓝图重名检测(self, 蓝图名, 蓝图分类,排除项索引=None):
        名字列表 = [名["name"] for 名 in self.获取数据(蓝图分类)]
        if 排除项索引 != None:
            名字列表.pop(排除项索引)
        if 蓝图名 in 名字列表:
            return False
        return True
    
    @staticmethod
    def 添加序号(名, 列表):
        编号 = 1
        while True:
            新名 = f"{名}-{编号}"
            if 新名 not in 列表:
                return 新名
            编号 += 1

    @staticmethod
    def 检查蓝图库格式(蓝图库):
        if not isinstance(蓝图库, dict):
            return False
        if len(蓝图库) == 0:
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
    def 处理图片(文件路径):
        try:
            with Image.open(文件路径) as 图片:
    
                宽度, 高度 = 图片.size
                if 宽度 != 高度 or 高度 > 154 or 宽度 > 154:
                    最小边 = min(宽度, 高度)
                    左 = (宽度 - 最小边) // 2
                    上 = (高度 - 最小边) // 2
                    右 = 左 + 最小边
                    下 = 上 + 最小边
                    图片 = 图片.crop((左, 上, 右, 下))
                    图片 = 图片.resize((150, 150), Image.Resampling.LANCZOS)

                # 保存到内存
                内存缓冲区 = io.BytesIO()
                图片.save(内存缓冲区, format="PNG")
                内存缓冲区.seek(0)

                # 转Base64
                base64数据 = base64.b64encode(内存缓冲区.read()).decode("utf-8")
            return [True, f"data:image/png;base64,{base64数据}"]
        except Exception as e:
            return [False, str(e)]


    def 导入图片(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
            return
        文件路径 = filedialog.askopenfilename(initialdir=".", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not 文件路径:
            return
        状态,信息 = self.处理图片(文件路径)
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
        文件路径 = filedialog.askopenfilename(filetypes=[("*.txt","*.txt")], initialdir=".")
        if not 文件路径: return
        try:
            with open(文件路径,"r",encoding="utf-8") as f:
                内容 = f.read()
            if self.校验蓝图代码(内容):
                #将文件名加载为蓝图名称
                文件名 = os.path.splitext(os.path.basename(文件路径))[0]
                self.名称输入框.delete(0, tk.END)
                self.名称输入框.insert(0, self.检查名字(文件名,'规范'))
                self.代码输入框.delete("1.0", tk.END)
                self.代码输入框.insert("1.0", 内容)
                self.通知('蓝图导入完成')
            else:
                messagebox.showwarning("警告", "蓝图格式不正确")
        except Exception as e:
            messagebox.showerror("错误",f"蓝图导入失败：\n{str(e)}")

    def 删除图片(self):
        if self._当前蓝图是否锁定:
            self.通知('该蓝图不可修改')
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
            if not self.校验蓝图代码(文本):
                self.通知('剪贴板内容不是有效的蓝图代码')
                return
            self.代码输入框.delete("1.0", tk.END)
            self.代码输入框.insert("1.0", 文本)
            self.通知('已粘贴')
        except Exception:
            self.通知('剪贴板无内容')

    def 新建蓝图(self):
        if self.当前类型 == None:
            self.通知("未选择蓝图类型")
            return
        蓝图列表 = self.获取数据(self.当前类型)
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

        self.添加数据(self.当前类型, 新数据, 索引)
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
            self.添加数据(self.当前类型, 新数据)
            self.当前蓝图索引 = len(self.获取数据(self.当前类型)) -1
        else:
            self.更改数据(self.当前类型, 新数据, self.当前蓝图索引)
       
        self.刷新蓝图列表()
        self.通知(f'{新数据["name"]} 已保存')

    def 删除蓝图(self,快速删除=False):
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

        self.列表写入(新类名, [])
        self.刷新页面()
        self.选择蓝图类型(新类名)
        self.通知(f'已添加 {新类名} 分类')

    def 删除蓝图分类(self):
        if len(self.获取类表()) <= 1:
            messagebox.showwarning("警告", "不能删除最后一个分类")
            return
        if not self.当前类型:
            messagebox.showwarning("警告", "请先选分类")
            return
        if not messagebox.askyesno("确认", f"确定删除 ‘{self.当前类型}’ 吗？"):
            return
        self.移出数据(self.当前类型)
        self.通知(f'已删除 {self.当前类型} 分类')
        self.刷新页面()

    def 更名分类(self):
        if self.当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        
        新类名 = simpledialog.askstring("输入", "请输入2~8个字符：", initialvalue=self.当前类型)
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
        self.列表写入(新类名, self.移出数据(self.当前类型), '修改')
        self.通知(f'已将 {self.当前类型} 更名为 {新类名}')
        self.刷新页面()
        self.选择蓝图类型(新类名)

    

    def 导入JSON(self):
        if self._数据是否未保存:
            if not messagebox.askyesno("确认", "当前蓝图库未保存，确定载入新蓝图库吗？"):
                return
        try:
            路径 = filedialog.askopenfilename(initialdir=".",filetypes=[("*.json","*.json")],title="导入JSON文件")
            if not 路径: return
            with open(路径,"r",encoding="utf-8") as f:
                导入的数据 = json.load(f)
            if not self.检查蓝图库格式(导入的数据):
                messagebox.showwarning("警告","JSON格式错误")
                return
            self.蓝图库 = 导入的数据
            self._数据是否未保存 = False
            self.刷新页面()
            self.选择蓝图类型(self.获取类表()[0])
            messagebox.showinfo("成功", "导入完成")
            self.通知('导入JSON')
        except Exception as e:
            messagebox.showerror("错误",f"文件导入失败：\n{str(e)}")

    def 导出JSON(self):
        try:
            路径 = filedialog.asksaveasfilename(initialdir=".",defaultextension=".json", filetypes=[("*.json","*.json")],title="导出JSON文件")
            if not 路径: return
            with open(路径,"w",encoding="utf-8") as f:
                json.dump(self.蓝图库, f, ensure_ascii=False, indent=4)
            self._数据是否未保存 = False
            messagebox.showinfo("成功", "导出完成")
            self.通知('导出JSON')
        except Exception as e:
            messagebox.showerror("错误",f"文件导出失败：\n{str(e)}")

    def 导出HTML(self):
        try:
            路径 = filedialog.asksaveasfilename(initialdir=".",defaultextension=".html", filetypes=[("HTML","*.html")],title="导出为HTML")
            if not 路径: return
            
            with open(self.HTML模板路径, "r", encoding="utf-8") as f:
                html = f.read()

            json字符串 = json.dumps(self.蓝图库, ensure_ascii=False).replace("\\", "\\\\").replace("\n", "\\n")
            html = self.匹配HM蓝图库.sub(
                rf"\1{json字符串}",
                html,
                re.DOTALL
            )
            html = self.匹配HMname.sub(
                rf'\1{self.name}\3',
                html
            )

            with open(路径, "w", encoding="utf-8") as f:
                f.write(html)
            if messagebox.askyesno("导出完成", "导出完成，是否打开HTML文件？"):
                os.startfile(路径)
        except Exception as e:
            messagebox.showerror("错误",f"文件导出失败：\n{str(e)}")
    
    def 导入HTML(self):
        try:
            路径 = filedialog.askopenfilename(initialdir=".",filetypes=[("HTML","*.html")],title="导入HTML文件")
            if not 路径: return
            with open(路径, "r", encoding="utf-8") as f:
                html = f.read()

            匹配数据 = self.匹配HM蓝图库.search(html, re.DOTALL)
            if not 匹配数据:
                return messagebox.showwarning("警告","这不是有效的HTML")
            导入的数据 = json.loads(匹配数据.group(2))
            if not self.检查蓝图库格式(导入的数据):
                return messagebox.showwarning("警告","该HTML蓝图库格式不正确")

            self.蓝图库 = 导入的数据
            self.刷新页面()
            self.选择蓝图类型(self.获取类表()[0])
            messagebox.showinfo("成功", "导入完成")
            self.通知('导入成功')

        except Exception as e:
            messagebox.showerror("错误",f"文件入失败：\n{str(e)}")

    def 批量操作窗口(self,操作类型):
        允许值 = {'移动', '删除','导入'}
        蓝图数据列表 = []
        # 初始校验
        if 操作类型 not in 允许值:
            raise ValueError(f"操作类型只能是：{允许值}")
        if 操作类型 in ('移动','删除') and self.当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        if 操作类型 == '导入':
            try:
                文件夹路径 = filedialog.askdirectory(initialdir=".",title="请选择蓝图文件夹")
                if not 文件夹路径:return
                for 文件名 in os.listdir(文件夹路径):
                    if 文件名.lower().endswith(".txt"):
                        文件完整路径 = os.path.join(文件夹路径, 文件名)
                        with open(文件完整路径, "r", encoding="utf-8") as f:
                            文件内容 = f.read()
                        if self.校验蓝图代码(文件内容):
                            蓝图数据列表.append({
                            "name": self.检查名字(os.path.splitext(文件名)[0],'规范'),
                            "data": 文件内容
                            })
            except Exception as e:
                messagebox.showerror("错误", f"文件夹读取失败：\n{str(e)}")
            if not 蓝图数据列表:
                messagebox.showinfo("提示", "该文件夹下未找到蓝图.txt文件！")
                return

        def 确认操作():
            nonlocal 蓝图数据列表
            # 操作前校验
            if not 列表框.curselection() and 操作类型 in ('移动','删除'):
                messagebox.showwarning("警告", "请至少选择一个蓝图")
                return
            if 操作类型 == '移动' and not 选中项.get():
                messagebox.showwarning("警告", "请选择移动的目标目录")
                return
            if 操作类型 == '删除' and not messagebox.askyesno("确认", "确定删除选中的蓝图吗？"):
                return
            
            # 操作数据
            if 操作类型 == '导入':
                if 导入同名图片.get():
                    nonlocal 文件夹路径
                    for 索引, 蓝图 in enumerate(蓝图数据列表):
                        for 文件名 in os.listdir(文件夹路径):
                            名字, 后缀 = os.path.splitext(文件名)
                            if 名字 == 蓝图['name'] and 后缀.lower() in ('.jpg', '.jpeg', '.png'):
                                结果,信息 = self.处理图片(os.path.join(文件夹路径, 文件名))
                                if 结果:
                                    蓝图数据列表[索引].update({"img": 信息})
                类型列表 = self.获取类表()
                类名 = self.检查名字(os.path.basename(文件夹路径),'规范')
                if 导入当前分类.get() and self.当前类型 != None:
                    目标 = self.当前类型
                elif 类名 in 类型列表:
                    目标 = self.添加序号(类名,类型列表)
                else:
                    目标 = 类名
            elif 操作类型 in ('移动','删除'):
                索引列表 = [展示列表[i][0] for i in 列表框.curselection()]
                # 逆序删除，避免索引错乱
                for 索引 in sorted(索引列表, reverse=True):
                    蓝图数据列表.append(self.移出数据(self.当前类型, 索引))
            if 操作类型 == '移动':
                蓝图数据列表.reverse()  # 恢复原顺序
                原类型 = self.当前类型
                目标 = 选中项.get()
            if 操作类型 in ('移动','导入'):
                self.列表写入(目标,蓝图数据列表)
                选择 = 目标

            # 生成消息
            if 操作类型 == '移动':
                消息 =f'将{len(蓝图数据列表)}个蓝图从 {原类型} 移动到 {选中项.get()}'
            elif 操作类型 == '导入':
                消息 =f'已将{len(蓝图数据列表)}个蓝图导入到 {目标}'
            elif 操作类型 == '删除':
                选择 = self.当前类型
                消息 =f'已删除{len(蓝图数据列表)}个蓝图'
            
            # 刷新界面
            self.刷新页面()
            self.选择蓝图类型(选择)
            self.通知(消息)
            窗口.destroy()
            

        窗口 = tk.Toplevel()
        窗口.title("批量操作")
        窗口.geometry(f"500x350+{(窗口.winfo_screenwidth()-500)//2}+{(窗口.winfo_screenheight()-350)//2}")
        窗口.resizable(False, False)  # 禁止缩放

        # 初始化界面
        if 操作类型 == '移动':
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

        elif 操作类型 == '删除':
            窗口.title("删除蓝图")

        elif 操作类型 == '导入':
            窗口.title("批量导入")
            导入同名图片 = tk.IntVar(value=1)
            导入当前分类 = tk.IntVar(value=0)
            ttk.Checkbutton(窗口, text="导入同名图片", variable=导入同名图片).pack(padx=15, fill=tk.X)
            ttk.Checkbutton(窗口, text="导入到当前分类，如果已选择的话；否则创建新分类", variable=导入当前分类).pack(padx=15, fill=tk.X)

        if 操作类型 in ('移动','删除'):
            tk.Label(窗口, text="鼠标拖动或按住Ctrl/Shift多选", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        
        列表框架 = ttk.Frame(窗口)
        列表框架.pack(padx=15, fill=tk.BOTH,expand=True)
        滚动条 = tk.Scrollbar(列表框架)
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        列表框 = tk.Listbox(列表框架, yscrollcommand=滚动条.set)
        列表框.pack(fill=tk.BOTH, expand=True)
        滚动条.config(command=列表框.yview)

        if 操作类型 in ('移动','导入'):
            tk.Label(窗口, text="如果重名将会自动添加序号", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)

        按钮框架 = ttk.Frame(窗口)
        按钮框架.pack(pady=15,fill=tk.Y)
        ttk.Button(按钮框架, text="确认", command=确认操作).pack(side=tk.LEFT, padx=10)
        ttk.Button(按钮框架, text="取消", command=窗口.destroy).pack(side=tk.LEFT, padx=10)

        # 填入内容
        if 操作类型 in ('移动','删除'):
            列表框.config(selectmode=tk.EXTENDED,exportselection=False)
            展示列表 = [[索引, 蓝图['name']] for 索引, 蓝图 in enumerate(self.获取数据(self.当前类型)) if not (蓝图.get('lock') == 1)]
            for 蓝图 in 展示列表:
                列表框.insert(tk.END,蓝图[1])
        elif 操作类型 == '导入':
            for 文件数据 in 蓝图数据列表:
                列表框.insert(tk.END, 文件数据["name"])
            列表框.config(state=tk.DISABLED)

        窗口.grab_set()
        窗口.wait_window()

    def 导出文件夹(self):
        try:
            根目录 = filedialog.askdirectory(initialdir=".", title="选择蓝图导出根目录")
            if not 根目录:
                return
            
            计数 = 0
            for 分类名 in self.获取类表():
                分类路径 = os.path.join(根目录, 分类名)
                if not os.path.exists(分类路径):
                    os.makedirs(分类路径)
                
                for 蓝图数据 in self.获取数据(分类名):
                    名字 = f"{蓝图数据['name']}"
                    蓝图文件路径 = os.path.join(分类路径, 名字 + ".txt")
                    
                    with open(蓝图文件路径, "w", encoding="utf-8") as f:
                        f.write(蓝图数据["data"].strip())
                        计数 += 1
                    try:
                        if "img" in 蓝图数据 and 蓝图数据["img"].strip():
                            img_prefix,img_base64 = 蓝图数据["img"].split(",")
                            img_ext = "png"
                            if "image/jpeg" in img_prefix or "image/jpg" in img_prefix:
                                img_ext = "jpg"
                            elif "image/png" in img_prefix:
                                img_ext = "png"
                            elif "image/svg+xml" in img_prefix:
                                img_ext = "svg"
                            图片路径 = os.path.join(分类路径, f"{名字}.{img_ext}")

                            img_data = base64.b64decode(img_base64)
                            with open(图片路径, "wb") as img_file:
                                img_file.write(img_data)
                    except:
                        continue

            messagebox.showinfo("成功", f"{计数}个蓝图已导出到：\n{根目录}")
            self.通知(f'导出文件夹完成：{根目录}')
        except Exception as e:
            messagebox.showerror("错误", f"导出异常中止，已导出了{计数}个蓝图：\n{str(e)}")

if __name__ == "__main__":
    app = 蓝图库编辑器()
    app.mainloop()