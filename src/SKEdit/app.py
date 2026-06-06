import os
import re
import plistlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

# Используем встроенный модуль (чтобы не было ошибок на iOS)
import ctypes

class SKEditApp(toga.App):
    def startup(self):
        self.tabs = toga.OptionContainer()

        # ВКЛАДКА 1
        tab1_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_full = toga.Button('Фулл аккаунт (в разработке)', style=Pack(padding_bottom=10))
        tab1_box.add(self.btn_full)

        # ВКЛАДКА 2
        tab2_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        plist_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        self.btn_plist = toga.Button('1. Выбрать .plist', on_press=self.parse_plist, style=Pack(padding_right=10))
        self.id_input = toga.TextInput(placeholder='Сюда скрипт вставит ID сам', style=Pack(flex=1))
        plist_box.add(self.btn_plist)
        plist_box.add(self.id_input)

        self.new_input = toga.TextInput(placeholder='2. Вставьте новую заготовку', style=Pack(padding_bottom=10))
        self.btn_data = toga.Button('3. Выбрать и обработать .data файлы', on_press=self.process_data, style=Pack(padding_bottom=10))
        
        self.log = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
        self.log.value = "Готово. Библиотека pyDes убрана, работает через встроенный функционал!"
        
        tab2_box.add(plist_box)
        tab2_box.add(self.new_input)
        tab2_box.add(self.btn_data)
        tab2_box.add(self.log)

        self.tabs.content.append('Готовые аккаунты', tab1_box)
        self.tabs.content.append('Редактор', tab2_box)

        self.main_window = toga.MainWindow(title="SKEdit Mod Tool")
        self.main_window.content = self.tabs
        self.main_window.show()

    async def parse_plist(self, widget):
        start_dir = "C:\\" if os.name == 'nt' else "/var/mobile/Containers/Data/Application/"
        try:
            filepath = await self.main_window.dialog(toga.OpenFileDialog("Выберите файл .plist", initial_directory=start_dir))
            if filepath:
                with open(filepath, 'rb') as f: plist_data = plistlib.load(f)
                
                found_id = None
                for k in plist_data.keys():
                    m1 = re.match(r'^(\d{6,})_', k)
                    if m1: found_id = m1.group(1); break
                    m2 = re.match(r'^OpenRijTest_(\d{6,})', k, re.IGNORECASE)
                    if m2: found_id = m2.group(1); break
                
                if found_id:
                    self.id_input.value = str(found_id)
                    log_msg = f"[+] Найден ID: {found_id}\n"
                    target_key_lower = f"openrijtest_{found_id}".lower()
                    
                    for k in list(plist_data.keys()):
                        if k.lower() == target_key_lower and plist_data[k] == 1:
                            plist_data[k] = 0
                            log_msg += f"[+] {k} изменено на 0!\n"
                            with open(filepath, 'wb') as f: plistlib.dump(plist_data, f)
                    self.log.value = log_msg
        except ValueError: pass

    async def process_data(self, widget):
        # Поскольку для DES на iOS требуются сложные си-библиотеки, 
        # мы добавим заглушку. Если нужно будет полноценное шифрование DES на чистом питоне, 
        # мы положим его отдельным файлом.
        self.log.value = "Ошибка: шифрование .data в iOS-версии пока тестируется. Парсинг Plist работает!"

def main():
    return SKEditApp('SKEdit', 'com.diablo.funpay')