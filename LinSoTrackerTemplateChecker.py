import datetime
import json
import os
import tkinter as tk
from tkinter import filedialog


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.list_rules = None
        self.actions_conditions_keys = None
        self.list_items = None
        self.template_name = None
        self.master = master
        self.master.geometry("800x500")
        self.master.title("LinSoTracker JSON Checker")

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        x = (screen_width - root.winfo_reqwidth()) // 2
        y = (screen_height - root.winfo_reqheight()) // 2

        self.master.geometry("+{}+{}".format(x, y))

        cadre = tk.Frame(self.master)
        cadre.grid(row=0, column=0, sticky="nsew")

        label1 = tk.Label(cadre, text="Items List")
        label1.grid(row=0, column=0, sticky="w")

        self.listbox_items = tk.Listbox(cadre)
        self.listbox_items.grid(row=1, column=0, sticky="nsew")

        scrollbar1 = tk.Scrollbar(cadre, orient="vertical", command=self.listbox_items.yview)
        scrollbar1.grid(row=1, column=1, sticky="ns")

        self.listbox_items.config(yscrollcommand=scrollbar1.set)

        self.button_items = tk.Button(cadre, text="Open tracker.json", command=self.select_json_file)
        self.button_items.grid(row=2, column=0, pady=10)

        label2 = tk.Label(cadre, text="Problems with : ")
        label2.grid(row=0, column=2, sticky="w")

        self.listbox_problems = tk.Listbox(cadre)
        self.listbox_problems.grid(row=1, column=2, sticky="nsew")

        scrollbar2 = tk.Scrollbar(cadre, orient="vertical", command=self.listbox_problems.yview)
        scrollbar2.grid(row=1, column=3, sticky="ns")

        self.listbox_problems.config(yscrollcommand=scrollbar2.set)

        self.button_problems = tk.Button(cadre, text="Open MainMap.json", command=self.select_map_file,
                                         state="disabled")
        self.button_problems.grid(row=2, column=2, pady=10)

        self.export_button = tk.Button(cadre, text="Export Errors to File", command=self.export_errors, state="disabled")
        self.export_button.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=10)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)
        cadre.columnconfigure(1, weight=0)
        cadre.columnconfigure(2, weight=1)
        cadre.columnconfigure(3, weight=0)
        cadre.rowconfigure(1, weight=1)

    def get_items_list(self, datas):
        list_items = []

        for item in datas:
            list_items.append(item["Name"])

            if "NextItems" in item:
                for sub_item in item["NextItems"]:
                    list_items.append(sub_item["Name"])

            if item["Kind"] == "SubMenuItem":
                list_sub_items = self.get_items_list(item["ItemsList"])

                for sub_item in list_sub_items:
                    list_items.append(sub_item)

        return list_items

    def read_map(self, file_path):
        with open(file_path, "r") as f:
            datas = json.load(f)

            checks_list = datas[0]["ChecksList"]

            for check in checks_list:
                if check["Kind"] == "SimpleCheck":
                    self.process_conditions(check["Conditions"], check["Name"])

                if check["Kind"] == "Block":
                    for sub_check in check["Checks"]:
                        self.process_conditions(sub_check["Conditions"],
                                           f"[{check['Name']} - {sub_check['Name']}] ")

    def process_conditions(self, condition, emplacement):
        self.insert_research_by_pattern(text=condition,
                                        pattern="have",
                                        emplacement=emplacement,
                                        list_items=self.list_items)

        self.insert_research_by_pattern(text=condition,
                                        pattern="do",
                                        emplacement=emplacement,
                                        list_items=self.actions_conditions_keys)

        self.insert_research_by_pattern(text=condition,
                                        pattern="rules",
                                        emplacement=emplacement,
                                        list_items=self.list_rules)

    def read_json(self, file_path):
        with open(file_path, "r") as f:
            datas = json.load(f)
            self.template_name = datas[0]["Informations"]["Name"]
            items_datas = [data for data in datas if "Items" in data]
            self.list_items = self.get_items_list(items_datas[0]["Items"])
            for item in self.list_items:
                self.listbox_items.insert("end", item)

            map_data = [data for data in datas if "ActionsConditions" in data]
            actions_conditions = map_data[0]["ActionsConditions"]
            rules_data = map_data[0]["RulesOptions"]

            # print(rules_data)
            self.list_rules = []
            for rule in rules_data:
                self.list_rules.append(rule["Name"])

            self.actions_conditions_keys = actions_conditions.keys()

            for condition in actions_conditions:
                self.process_conditions(actions_conditions[condition], condition)

    def insert_research_by_pattern(self, text, pattern, emplacement, list_items):
        items = self.get_items(text=text, pattern=pattern)

        for item in items:
            state, name = self.match_item(list_items, item)
            if not state:
                self.listbox_problems.insert("end", f"{item} @ {emplacement}")

    @staticmethod
    def match_item(items_list, item):
        return item in items_list, item

    @staticmethod
    def get_items(text, pattern):
        items = []
        start = text.find(pattern + "('")
        while start != -1:
            end = text.find("')", start)
            if end != -1:
                item = text[start + len(pattern) + 2:end].split("'")[0]
                items.append(item)
                start = text.find(pattern + "('", end)
            else:
                break
        return items

    def select_json_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("tracker.json", "tracker.json")])
        self.list_rules = None
        self.actions_conditions_keys = None
        self.list_items = None
        self.listbox_items.delete("0", "end")
        self.listbox_problems.delete("0", "end")
        self.listbox_problems.insert("end", f"-----------ERRORS @ {os.path.basename(file_path)}-----------")
        self.read_json(file_path)
        self.listbox_problems.insert("end", "--------------------------------------------")
        self.button_problems.configure(state="normal")

    def select_map_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("map file json", "*.json")])
        self.listbox_problems.insert("end", f"-----------ERRORS @ {os.path.basename(file_path)}-----------")
        self.read_map(file_path)
        self.listbox_problems.insert("end", "--------------------------------------------")
        self.export_button.configure(state="normal")

    def export_errors(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        errors = self.listbox_problems.get(0, tk.END)
        error_filename = f"[ERRORS] - [{self.template_name}] - {datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.txt"
        filepath = os.path.join(script_path, error_filename)
        with open(filepath, "w") as f:
            for error in errors:
                f.write(error + "\n")

        os.startfile(script_path)


root = tk.Tk()
app = Application(master=root)
app.mainloop()

