import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json,os,io,base64,re

from PIL import Image, ImageTk
import pyperclip

class 蓝图库编辑器(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("戴森球蓝图库编辑器：by氢碳钾")
        self.geometry("900x600")
        
        self._蓝图库 = {}
        self._当前类型 = None
        self._当前蓝图索引 = None
        self._输入的图片 = None
        self._预览图片缓存 = None
        self._数据是否未保存 = False

        ttk.Button(self, takefocus=0)
        self.样式 = ttk.Style()
        self.样式.configure("Category.TButton", padding=5)
        self.样式.configure("Selected.TButton", background="#4a86e8", padding=5)
        
        self.顶部框架 = ttk.Frame(self)
        self.顶部框架.pack(fill=tk.X, padx=10, pady=10)
        
        self.导入JSON按钮 = ttk.Button(self.顶部框架, text="导入JSON", command=self.导入JSON)
        self.导入JSON按钮.pack(side=tk.LEFT, padx=5)
        self.导出JSON按钮 = ttk.Button(self.顶部框架, text="导出JSON", command=self.导出JSON)
        self.导出JSON按钮.pack(side=tk.LEFT, padx=5)
        self.导出HTML按钮 = ttk.Button(self.顶部框架, text="导出为HTML", command=self.导出HTML)
        self.导出HTML按钮.pack(side=tk.LEFT, padx=5)
        self.新建蓝图按钮 = ttk.Button(self.顶部框架, text="新建空蓝图", command=self.新建蓝图)
        self.新建蓝图按钮.pack(side=tk.LEFT, padx=5)
        self.移动蓝图按钮 = ttk.Button(self.顶部框架, text="移动蓝图", command=self.移动蓝图)
        self.移动蓝图按钮.pack(side=tk.LEFT, padx=5)
        self.批量导入按钮 = ttk.Button(self.顶部框架, text="批量导入", command=self.批量导入蓝图)
        self.批量导入按钮.pack(side=tk.LEFT, padx=5)
        self.通知窗 = ttk.Entry(self.顶部框架, width=50)
        self.通知窗.config(state="disabled")
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
        
        self.蓝图列表 = tk.Listbox(self.蓝图列表框架, width=20, height=20, exportselection=False)
        self.蓝图列表.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.蓝图列表.bind('<<ListboxSelect>>', self.选中蓝图)
        
        self.编辑区框架 = ttk.LabelFrame(self.主框架, text="蓝图编辑")
        self.编辑区框架.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, ipadx=8, ipady=5)

        self.编号显示标签 = ttk.Label(self.编辑区框架, text="新建蓝图：")
        self.编号显示标签.grid(row=0, column=0, columnspan=3, padx=8, pady=8, sticky="n")
        self.上移 = ttk.Button(self.编辑区框架, text="⬆️", width=3, command=lambda: self.排序蓝图(-1))
        self.上移.grid(row=0, column=2, padx=2)
        self.下移 = ttk.Button(self.编辑区框架, text="⬇️", width=3, command=lambda: self.排序蓝图(1))
        self.下移.grid(row=0, column=3, padx=2)


        self.名称标签 = ttk.Label(self.编辑区框架, text="*蓝图名:")
        self.名称标签.grid(row=1, column=0, padx=8, pady=8, sticky=tk.W)
        self.名称输入框 = ttk.Entry(self.编辑区框架, width=30)
        self.名称输入框.grid(row=1, column=1, padx=8, pady=8, sticky=tk.W)
        self.导入蓝图按钮 = ttk.Button(self.编辑区框架, text="导入蓝图文件", command=self.导入蓝图文件)
        self.导入蓝图按钮.grid(row=1, column=2, columnspan=2, padx=2, sticky=tk.W)

        self.蓝图代码标签 = ttk.Label(self.编辑区框架, text="*蓝图代码:")
        self.蓝图代码标签.grid(row=2, column=0, padx=8, pady=8, sticky=tk.NW)
        self.代码输入框 = tk.Text(self.编辑区框架, width=30, height=1, wrap="none")
        self.代码输入框.grid(row=2, column=1, sticky="nsew",padx=8, pady=8)
        self.代码输入框.bind("<ButtonRelease-1>", self.自动全选)
        for key in ["<Return>", "<Up>", "<Down>", "<Left>", "<Right>"]:
            self.代码输入框.bind(key, self.禁止按键)
        self.复制按钮 = ttk.Button(self.编辑区框架, text="复制代码", command=self.复制蓝图代码)
        self.复制按钮.grid(row=2, column=2, columnspan=2, padx=2, sticky=tk.W)

        self.图片预览标签 = ttk.Label(self.编辑区框架, text="蓝图图片:")
        self.图片预览标签.grid(row=3, column=0, padx=8, pady=8, sticky=tk.NW)
        self.预览画布 = tk.Canvas(self.编辑区框架, width=160, height=160, bg="#f5f5f5", bd=1, relief="solid")
        self.预览画布.grid(row=3, column=1, padx=8, pady=8)
        self.图片编辑框架 = ttk.Frame(self.编辑区框架)
        self.图片编辑框架.grid(row=3, column=2, columnspan=2, pady=5)
        self.导入图片按钮 = ttk.Button(self.图片编辑框架, text="导入图片", command=self.导入图片)
        self.导入图片按钮.grid(padx=2, sticky=tk.W)
        self.删除图片按钮 = ttk.Button(self.图片编辑框架, text="删除图片", command=self.删除图片)
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

    
    def 关闭窗口(self):
        if self._数据是否未保存:
            result = messagebox.askyesnocancel(
            title="保存提示",
            message="蓝图库未保存，是否保存为JSON？",
            #detail="选择“是”保存，“否”不保存，“取消”取消关闭"
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

    def 加载默认数据(self):
        self._蓝图库 = {"实用":[{"name":"演示1","data":""},{"name":"演示2","data":""}],"观赏":[{"name":"演示3","data":""}]}
        self.刷新页面()
        self.选择蓝图类型(next(iter(self._蓝图库)))

    def 刷新页面(self):
        self._当前类型 = None
        self._当前蓝图索引 = None
        self.刷新蓝图列表()

        for 控件 in self.分类项框架.winfo_children(): 控件.destroy()
        类型列表 = self._蓝图库.keys()
        for 蓝图类型 in 类型列表:
            按钮 = ttk.Button(self.分类项框架, text=蓝图类型, style="Category.TButton",command=lambda c=蓝图类型: self.选择蓝图类型(c))
            按钮.pack(fill=tk.X, padx=5, pady=3)
        
        #self.选择蓝图类型(list(类型列表)[0])
    
    def 选择蓝图类型(self, 蓝图类型):
        self._当前类型 = 蓝图类型
        self._当前蓝图索引 = None
        
        for 按钮 in self.分类项框架.winfo_children():
            if 按钮["text"] == 蓝图类型:
                按钮.config(style="Selected.TButton")
            else:按钮.config(style="Category.TButton")

        self.刷新蓝图列表()
        
    def 刷新蓝图列表(self):
        self.蓝图列表.delete(0, tk.END)
        if self._当前类型 != None:
            self.蓝图列表框架.config(text=f"蓝图列表 - {self._当前类型} -")
            for 蓝图数据 in self._蓝图库[self._当前类型]:
                self.蓝图列表.insert(tk.END, f"{蓝图数据['name']}")
        else:
            self.蓝图列表框架.config(text=f"蓝图列表 - 未选择分类 -")
        if self._当前蓝图索引 != None:
            self.蓝图列表.selection_set(self._当前蓝图索引)
        self.刷新编辑区()

    def 刷新编辑区(self):
        self.编号显示标签.config(text="新建蓝图：")
        self.名称输入框.delete(0, tk.END)
        self.代码输入框.delete("1.0", tk.END)
        self.备注输入框.delete(0, tk.END)
        self._输入的图片 = None
        self.加载图片预览()

        if self._当前蓝图索引 == None:
            return
        
        蓝图数据 =self._蓝图库[self._当前类型][self._当前蓝图索引]
        self.编号显示标签.config(text=f"修改蓝图：{self._当前类型} -- {蓝图数据["name"]}")
        self.名称输入框.insert(0, 蓝图数据['name'])
        self.代码输入框.insert("1.0", 蓝图数据['data'])
        备注 = 蓝图数据.get('memo', '')
        if 备注.strip():
            self.备注输入框.insert(0, 备注)
        self._输入的图片 = 蓝图数据.get("img","")
        self.加载图片预览()

    def 加载图片预览(self):
        try:
            if not self._输入的图片:
                self.预览画布.delete("all")
                self.预览画布.create_text(80, 80, text="暂无图片", fill="#999")
                self._预览图片缓存 = None
                return

            base64_str = self._输入的图片.split(",")[1]
            img_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_data))

            self._预览图片缓存 = ImageTk.PhotoImage(img)
            w = self.预览画布.winfo_width()
            h = self.预览画布.winfo_height()
            x = w / 2  
            y = h / 2  
            self.预览画布.delete("all")
            self.预览画布.create_image(x, y, image=self._预览图片缓存, anchor="center")
    
        except Exception:
            self.预览画布.delete("all")
            self.预览画布.create_text(80, 80, text="预览失败", fill="red")

    def 选中蓝图(self, event):
        选中 = self.蓝图列表.curselection()
        if not 选中: return
        
        self._当前蓝图索引 = 选中[0] if self._当前蓝图索引 != 选中[0] else None
        if self._当前蓝图索引 == None:
            self.蓝图列表.selection_clear(0, tk.END)
        self.刷新编辑区()
    
    def 通知(self,消息):
        self.通知窗.config(state="normal")
        self.通知窗.delete(0, tk.END)
        self.通知窗.insert(0, 消息)
        self.通知窗.config(state="disabled")

    @staticmethod
    def 校验蓝图代码(蓝图代码):
        return bool(re.match(r'^DYBP:.*"[0-9A-F]{32}$', 蓝图代码.strip()))

    @staticmethod
    def 检查名字(名字, 模式='检测'):
        非法字符 = {' ', '"', "'", '#', '.', '<', '>', '=', '/', '\\'}
        if 模式 == '检测':
            return 名字 and not any(c in 非法字符 for c in 名字)
        if 模式 == '规范':
            return ''.join([char for char in 名字 if char not in 非法字符])

    def 蓝图重名检测(self, 蓝图名, 蓝图分类,排除项索引=None):
        名字列表 = [名["name"] for 名 in self._蓝图库[蓝图分类]]
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
    def 打开图片(文件路径):
        try:
            with Image.open(文件路径) as 图片:
                # 自动转为RGB，避免透明/模式问题
                图片 = 图片.convert("RGB")
    
                宽度, 高度 = 图片.size
                最小边 = min(宽度, 高度)
                左 = (宽度 - 最小边) / 2
                上 = (高度 - 最小边) / 2
                右 = (宽度 + 最小边) / 2
                下 = (高度 + 最小边) / 2
                图片_裁剪 = 图片.crop((左, 上, 右, 下))
    
                图片_缩放 = 图片_裁剪.resize((150, 150), Image.Resampling.LANCZOS)

                # 压缩保存到内存，控制质量
                内存缓冲区 = io.BytesIO()
                图片_缩放.save(内存缓冲区, format="JPEG", quality=85)
                内存缓冲区.seek(0)
                # 转Base64
                base64数据 = base64.b64encode(内存缓冲区.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{base64数据}"
        except Exception:
            return None

    def 写入数据(self,蓝图类型,蓝图列表):
        名字列表 = [名["name"] for 名 in self._蓝图库[蓝图类型]]
        for 蓝图数据 in 蓝图列表:
            if 蓝图数据['name'] in 名字列表:
                蓝图数据['name'] = self.添加序号(蓝图数据['name'],名字列表)
            self._蓝图库[蓝图类型].append(蓝图数据)



    def 导入图片(self):
        文件路径 = filedialog.askopenfilename(initialdir=".", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not 文件路径:
            return
        图片数据 = self.打开图片(文件路径)
        if not 图片数据:
            messagebox.showerror("错误", "图片导入失败")
        self._输入的图片 = 图片数据
        self.加载图片预览()
        self.通知('成功导入图片')

    def 导入蓝图文件(self):
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
        except Exception:
            messagebox.showerror("错误","蓝图导入失败")

    def 删除图片(self):
        self._输入的图片 = None
        self.加载图片预览()
        self.通知('图片已删除')

    def 复制蓝图代码(self):
        try:
            文本 = self.代码输入框.get("1.0", tk.END).strip()
            if 文本:
                pyperclip.copy(文本)
                self.通知('蓝图已复制到剪贴板')
            else:
                self.通知('输入框无内容')
                
        except Exception:
            messagebox.showerror("错误","文件导入失败")
    
    def 新建蓝图(self):
        if self._当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        名字列表 = [名["name"] for 名 in self._蓝图库[self._当前类型]]
        新数据 = {
            "name": self.添加序号("新蓝图",名字列表),
            "data": ""
        }
        self._蓝图库[self._当前类型].append(新数据)
        self._当前蓝图索引 = len(self._蓝图库[self._当前类型]) -1
        self.刷新蓝图列表()
        self.通知(f'已添加 {新数据["name"]}')


    def 保存蓝图(self):
        if self._当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        
        新数据 = {
            "name": self.名称输入框.get().strip(),
            "data": self.代码输入框.get("1.0", tk.END).strip(),
            "memo": self.备注输入框.get().strip(),
        }

        if not self.检查名字(新数据["name"]):
            messagebox.showwarning("警告", '蓝图名包含"空格\'"#.<>=/\\')
            return
        
        if not self.蓝图重名检测(新数据["name"], self._当前类型, self._当前蓝图索引):
            messagebox.showwarning("警告", "蓝图名重复")
            return

        if not self.校验蓝图代码(新数据["data"]):
            messagebox.showwarning("警告", "蓝图格式不正确")
            return
        
        if self._输入的图片:
            新数据.update({"img": self._输入的图片})

        # 如果没有选中蓝图则新增 没有则更改
        if self._当前蓝图索引 == None:
            self._蓝图库[self._当前类型].append(新数据)
            self._当前蓝图索引 = len(self._蓝图库[self._当前类型]) -1
        else:
            self._蓝图库[self._当前类型][self._当前蓝图索引] = 新数据
            self._数据是否未保存 = True
       
        self.刷新蓝图列表()
        self.通知(f'{新数据["name"]} 已保存')

    def 删除蓝图(self):
        if self._当前类型 == None or self._当前蓝图索引 == None:
            messagebox.showwarning("警告", "请先选择蓝图")
            return
        if not messagebox.askyesno("确认", "确定删除？"):
            return
        垃圾 = self._蓝图库[self._当前类型].pop(self._当前蓝图索引)
        self._当前蓝图索引 = None
        self._数据是否未保存 = True

        self.刷新蓝图列表()
        self.通知(f'{垃圾['name']} 已删除')
        
    def 排序蓝图(self,步):
        if self._当前类型 == None or self._当前蓝图索引 == None:
            return
        目标 = self._当前蓝图索引 + 步
        if 目标 < 0 or 目标 == len(self._蓝图库[self._当前类型]):
            return
        
        蓝图数据 = self._蓝图库[self._当前类型].pop(self._当前蓝图索引)
        self._蓝图库[self._当前类型].insert(目标, 蓝图数据)
        self._当前蓝图索引 = 目标
        self._数据是否未保存 = True

        self.刷新蓝图列表()
        self.通知('排序蓝图')

    def 添加蓝图分类(self):
        新类名 = simpledialog.askstring("输入", "请输入2~6个字符：")
        if not 新类名: return
        新类名 = 新类名.strip()
        if not self.检查名字(新类名):
            messagebox.showwarning("警告", '蓝图名包含"空格\'"#.<>=/\\')
            return
        if len(新类名) < 2 or len(新类名) > 6:
            messagebox.showwarning("警告","请输入2~6个字符")
            return
        if 新类名 in self._蓝图库:
            messagebox.showwarning("警告","不可输入相同的类名")
            return

        self._蓝图库[新类名] = []
        self._数据是否未保存 = True
        self.刷新页面()
        self.选择蓝图类型(新类名)
        self.通知(f'已添加 {新类名} 分类')

    def 删除蓝图分类(self):
        if len(self._蓝图库) <= 1:
            messagebox.showwarning("警告", "不能删除最后一个分类")
            return
        if not self._当前类型:
            messagebox.showwarning("警告", "请先选分类")
            return
        if not messagebox.askyesno("确认", f"确定删除 ‘{self._当前类型}’ 吗？"):
            return
        self._蓝图库.pop(self._当前类型)
        self._数据是否未保存 = True
        self.通知(f'已删除 {self._当前类型} 分类')
        self.刷新页面()

    def 更名分类(self):
        if self._当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        
        新类名 = simpledialog.askstring("输入", "请输入2~6个字符：", initialvalue=self._当前类型)
        if not 新类名: return
        新类名 = 新类名.strip()
        if not self.检查名字(新类名):
            messagebox.showwarning("警告", '蓝图名包含"空格\'"#.<>=/\\')
            return
        if len(新类名) < 2 or len(新类名) > 6:
            messagebox.showwarning("警告","请输入2~6个字符")
            return
        if 新类名 in self._蓝图库:
            messagebox.showwarning("警告","不可输入相同的类名")
            return
        self._蓝图库[新类名] = self._蓝图库.pop(self._当前类型)
        self._数据是否未保存 = True
        self.通知(f'已将 {self._当前类型} 更名为 {新类名}')
        self.刷新页面()
        self.选择蓝图类型(新类名)

    
    def 排序分类(self, 步):
        类型 = self._当前类型
        if 类型 == None:
            return
        
        蓝图列表 = list(self._蓝图库.items())
        索引 = [k[0] for k in 蓝图列表].index(类型)
        目标 = 索引 + 步

        if 目标 < 0 or 目标 == len(蓝图列表):
            return
        蓝图列表.insert(目标, 蓝图列表.pop(索引))
        self._蓝图库 = dict(蓝图列表)
        self._数据是否未保存 = True

        self.刷新页面()
        self.选择蓝图类型(类型)
        self.通知('排序蓝图类型')

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
            self._蓝图库 = 导入的数据
            self._数据是否未保存 = False
            self.刷新页面()
            self.选择蓝图类型(next(iter(self._蓝图库)))
            messagebox.showinfo("成功", "导入完成")
            self.通知('导入JSON')
        except Exception:
            messagebox.showerror("错误","文件导入失败")

    def 导出JSON(self):
        try:
            路径 = filedialog.asksaveasfilename(initialdir=".",defaultextension=".json", filetypes=[("*.json","*.json")],title="导出JSON文件")
            if not 路径: return
            with open(路径,"w",encoding="utf-8") as f:
                json.dump(self._蓝图库, f, ensure_ascii=False, indent=4)
            self._数据是否未保存 = False
            messagebox.showinfo("成功", "导出完成")
            self.通知('导出JSON')
        except Exception:
            messagebox.showerror("错误","文件导出失败")
    
    def 导出HTML(self):
        try:
            路径 = filedialog.asksaveasfilename(initialdir=".",defaultextension=".html", filetypes=[("HTML","*.html")],title="导出为HTML")
            if not 路径: return

            name=""
            HTML1=r"""<!doctype html><html lang="zh-cn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>戴森球(云)蓝图</title><style>.page{display:flex;justify-content:center}.card,.card_title,#标题{padding:0 5px;background:#e6e6e6;border-radius:5px;border:1px solid #5a5a5a;text-align:center}.card{padding:5px;width:100%;display:grid;gap:5px;grid-template-columns:150px 1fr;grid-template-rows:1fr 150px}.card_title{width:100%;height:auto;grid-column:1/-1}.card_data{resize:none;grid-column:2/3;grid-row:1/-1}.Memo{width:100%;height:15px;margin:0;padding:0;line-height:1;font-size:12px;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;grid-column:1/-1}body{overflow-y:scroll;margin:auto;position:relative;background-image:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIj4NCiAgICA8dGV4dCB4PSIxMDAiIHk9IjEwMCIgZmlsbD0icmdiYSgwLDAsMCwwLjEpIiBmb250LXNpemU9IjE1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBhbGlnbm1lbnQtYmFzZWxpbmU9Im1pZGRsZSIgdHJhbnNmb3JtPSJyb3RhdGUoLTMwLDEwMCwxMDApIj7msKLnorPpkr54djwvdGV4dD4NCjwvc3ZnPg==);background-repeat:repeat;background-attachment:fixed}#蓝图{width:max(320px,60%);padding-top:55px;padding-bottom:80px;display:grid;gap:5px 17px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));grid-auto-rows:min-content;justify-items:center}#标题{width:max(320px,60%);position:fixed;top:10px;z-index:99}</style></head><body><div class="page"><div id="标题"></div><div id="蓝图"></div></div><script>const BPlist="""
            HTML2=r""",NoneImg="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNTAiIGhlaWdodD0iMTUwIj4NCiAgPGRlZnM+DQogICAgPHN0eWxlPg0KICAgICAgLmNscy0xIHsNCiAgICAgICAgZm9udC1zaXplOiA3MHB4Ow0KICAgICAgICBmaWxsOiAjZmZmOw0KICAgICAgICB0ZXh0LWFuY2hvcjogbWlkZGxlOw0KICAgICAgICBmb250LWZhbWlseTogU1RIdXBvOw0KICAgICAgfQ0KICAgIDwvc3R5bGU+DQogIDwvZGVmcz4NCiAgPHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzAwMCIvPg0KICA8dGV4dCBjbGFzcz0iY2xzLTEiIHg9Ijc1IiB5PSI1OSI+5rKh5pyJPC90ZXh0Pg0KICA8dGV4dCBjbGFzcz0iY2xzLTEiIHg9Ijc1IiB5PSIxMzIuMyI+5Zu+54mHPC90ZXh0Pg0KPC9zdmc+DQo=";function initUI(){const e=Object.keys(BPlist);let t="";for(let n=0;n<e.length;n++)t+=`<button style="margin: 5px;" onclick="loadBP('${e[n]}')">${e[n]}</button>`;document.getElementById("标题").innerHTML=t,loadBP(e[0])}function loadBP(e){let t=`<div class="card_title">${e}戴森球蓝图</div>`;const n=BPlist[e];n.forEach(e=>{const{name:n,data:o,img:i,memo:s}=e;t+=`<div class="card"><div style="margin:auto;">${n} <button onclick="cvBP('${n}')">复制</button></div><img src="${i||NoneImg}" width="150" height="150"><textarea class="card_data" id="${n}" readonly>${o}</textarea>`,s&&(t+=`<div class="Memo">${s}</div>`),t+="</div>"}),t+='<div class="Memo">"""
            HTML3=r"""</div>',document.getElementById("蓝图").innerHTML=t}async function cvBP(e){try{const t=document.getElementById(e).value;await navigator.clipboard.writeText(t),alert("蓝图已复制到剪贴板")}catch(e){alert(`复制失败，请手动复制：\n`+e.message)}}initUI()</script></body></html>"""
            html = HTML1 + json.dumps(self._蓝图库) + HTML2 + name + HTML3

            with open(路径, "w", encoding="utf-8") as f:
                f.write(html)
            messagebox.showinfo("成功", "导出完成")
            self.通知('导出HTML')
        except Exception:
            messagebox.showerror("错误","文件导出失败")

    def 移动蓝图(self):
        if self._当前类型 == None:
            messagebox.showwarning("警告", "未选择蓝图类型")
            return
        
        def 确认操作():
            if not 选中项.get():
                messagebox.showwarning("警告", "请选择蓝图类型")
                return
            索引列表 = [i for i in 列表框.curselection()]

            蓝图列表 = [self._蓝图库[self._当前类型][索引] for 索引 in sorted(索引列表)]
            for 索引 in sorted(索引列表, reverse=True):
                self._蓝图库[self._当前类型].pop(索引)
            
            原类型 = self._当前类型
            self.写入数据(选中项.get(),蓝图列表)
            self._数据是否未保存 = True
            self.刷新页面()
            self.选择蓝图类型(选中项.get())
            self.通知(f'将蓝图从 {原类型} 移动到 {选中项.get()}')
            窗口.destroy()
        
        def 取消操作():
            窗口.destroy()
        

        窗口 = tk.Toplevel()
        窗口.title("移动蓝图")
        窗口.geometry("500x350")
        窗口.resizable(False, False)  # 禁止缩放

        选项框架 = ttk.Frame(窗口)
        选项框架.pack(padx=15, fill=tk.X)
        tk.Label(选项框架, text=f"从 {self._当前类型} 移动到：").pack(side=tk.LEFT)
        选中项 = tk.StringVar()
        选项 = ttk.Combobox(
            选项框架,
            textvariable=选中项,
            values=list([key for key in self._蓝图库 if key != self._当前类型]),
            state="readonly",
        )
        选项.pack(side=tk.LEFT,)
        选项.configure(height=5)

        tk.Label(窗口, text="鼠标拖动或按住Ctrl/Shift多选", anchor="w").pack(padx=15, fill=tk.X, anchor=tk.W)
        列表框架 = ttk.Frame(窗口)
        列表框架.pack(padx=15, fill=tk.BOTH,expand=True)
        滚动条 = tk.Scrollbar(列表框架)
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        列表框 = tk.Listbox(列表框架, yscrollcommand=滚动条.set, selectmode=tk.EXTENDED, exportselection=False)
        名字列表 = [蓝图['name'] for 蓝图 in self._蓝图库[self._当前类型]]
        for 名字 in 名字列表:
            列表框.insert(tk.END,名字)
        列表框.pack(fill=tk.BOTH, expand=True)
        滚动条.config(command=列表框.yview)

        按钮框架 = ttk.Frame(窗口)
        按钮框架.pack(pady=15,fill=tk.Y)
        ttk.Button(按钮框架, text="确认", command=确认操作).pack(side=tk.LEFT, padx=10)
        ttk.Button(按钮框架, text="取消", command=取消操作).pack(side=tk.LEFT, padx=10)

        窗口.grab_set()
        窗口.wait_window()


    def 批量导入蓝图(self):
        蓝图数据列表 = []
    
        def 加载所有蓝图文件数据(文件夹路径):
            nonlocal 蓝图数据列表
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

        def 确认操作():
            nonlocal 蓝图数据列表
            if 导入同名图片.get():
                nonlocal 文件夹路径
                for 索引, 蓝图 in enumerate(蓝图数据列表):
                    for 文件名 in os.listdir(文件夹路径):
                        名字, 后缀 = os.path.splitext(文件名)
                        if 名字 == 蓝图['name'] and 后缀.lower() in ('.jpg', '.jpeg', '.png'):
                            蓝图数据列表[索引].update({"img": self.打开图片(os.path.join(文件夹路径, 文件名))})
            
            类型列表 = self._蓝图库.keys()
            类名 = self.检查名字(os.path.basename(文件夹路径),'规范')
            if 导入当前分类.get() and self._当前类型:
                目标 = self._当前类型
            elif 类名 in 类型列表:
                目标 = self.添加序号(类名,类型列表)
            else:
                目标 = 类名
            self._蓝图库.setdefault(目标,[])

            self.写入数据(目标,蓝图数据列表)
            self._数据是否未保存 = True
            self.刷新页面()
            self.选择蓝图类型(目标)
            self.通知(f'已将蓝图批量导入到 {目标}')
            窗口.destroy()

        def 取消操作():
            窗口.destroy()
    
        文件夹路径 = filedialog.askdirectory(initialdir=".",title="请选择蓝图文件夹")
        if not 文件夹路径:
            return
    
        加载所有蓝图文件数据(文件夹路径)
        if not 蓝图数据列表:
            messagebox.showinfo("提示", "该文件夹下未找到蓝图文件！")
            return []
    
        窗口 = tk.Toplevel()
        窗口.title("批量导入")
        窗口.geometry("500x350")
        窗口.resizable(False, False)  # 禁止缩放

        导入同名图片 = tk.IntVar()
        导入当前分类 = tk.IntVar()
        ttk.Checkbutton(窗口, text="导入同名图片", variable=导入同名图片).pack(padx=15, fill=tk.X)
        ttk.Checkbutton(窗口, text="导入到当前分类，如果已选择分类的话", variable=导入当前分类).pack(padx=15, fill=tk.X)

        列表框架 = ttk.Frame(窗口)
        列表框架.pack(padx=15, fill=tk.BOTH,expand=True)
        滚动条 = tk.Scrollbar(列表框架)
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        列表框 = tk.Listbox(列表框架, yscrollcommand=滚动条.set)
        列表框.pack(fill=tk.BOTH, expand=True)
        滚动条.config(command=列表框.yview)
    
        按钮框架 = ttk.Frame(窗口)
        按钮框架.pack(pady=15)
        ttk.Button(按钮框架, text="确认", command=确认操作).pack(side=tk.LEFT, padx=10)
        ttk.Button(按钮框架, text="取消", command=取消操作).pack(side=tk.LEFT, padx=10)
    
        for 文件数据 in 蓝图数据列表:
            列表框.insert(tk.END, 文件数据["name"])
        窗口.grab_set()
        窗口.wait_window()


if __name__ == "__main__":
    app = 蓝图库编辑器()
    app.mainloop()