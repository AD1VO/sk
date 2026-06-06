import os
import re
import plistlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

class SKEditApp(toga.App):
    def startup(self):
        self.plist_data = {}
        self.filepath = None
        self.found_id = None
        self.original_skin_values = {}

        self.tabs = toga.OptionContainer()

        # --- ТАБ 1: ГЛАВНАЯ (ПЛИСТ И САМОЦВЕТЫ) ---
        tab_main = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.lbl_status = toga.Label('Файл не выбран', style=Pack(padding_bottom=10))
        
        self.btn_load = toga.Button('1. Выбрать plist', on_press=self.load_plist, style=Pack(padding_bottom=20))
        
        self.lbl_gems = toga.Label('Текущие самоцветы: -', style=Pack(padding_bottom=5))
        self.input_gems = toga.TextInput(placeholder='Введите новое количество', style=Pack(padding_bottom=10))
        self.btn_save_gems = toga.Button('Сохранить самоцветы', on_press=self.save_gems, style=Pack(padding_bottom=10))
        
        # Кнопка для загрузки .data файлов
        self.btn_load_files = toga.Button('2. Выбрать файлы (.data)', on_press=self.load_data_files, style=Pack(padding_top=20, padding_bottom=10))
        
        tab_main.add(self.lbl_status)
        tab_main.add(self.btn_load)
        tab_main.add(self.lbl_gems)
        tab_main.add(self.input_gems)
        tab_main.add(self.btn_save_gems)
        tab_main.add(self.btn_load_files)

        # --- ТАБ 2, 3, 4: ПЕРСОНАЖИ, СКИНЫ, НАВЫКИ ---
        self.chars_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.chars_scroll = toga.ScrollContainer(content=self.chars_box, horizontal=False)
        self.char_switches = {}

        self.skins_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.skins_scroll = toga.ScrollContainer(content=self.skins_box, horizontal=False)
        self.skin_switches = {}

        self.skills_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.skills_scroll = toga.ScrollContainer(content=self.skills_box, horizontal=False)
        self.skill_switches = {}

        # --- ТАБ 5: ФАЙЛЫ ---
        self.data_files_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.data_files_scroll = toga.ScrollContainer(content=self.data_files_box, horizontal=False)

        # Добавляем табы
        self.tabs.content.append('Главная', tab_main)
        self.tabs.content.append('Персы', self.chars_scroll)
        self.tabs.content.append('Скины', self.skins_scroll)
        self.tabs.content.append('Навыки', self.skills_scroll)
        self.tabs.content.append('Файлы', self.data_files_scroll)

        self.main_window = toga.MainWindow(title="SKEdit Mod")
        self.main_window.content = self.tabs
        self.main_window.show()

    def get_base_dir(self):
        if os.name == 'nt':
            return "C:\\"
        
        base_dir = "/var/mobile/Containers/Data/Application/"
        if os.path.exists(base_dir):
            try:
                for app_dir in os.listdir(base_dir):
                    check_path = os.path.join(base_dir, app_dir, "Library", "Preferences")
                    if os.path.exists(os.path.join(check_path, "com.chillyroom.dungeonshooter.plist")):
                        return os.path.join(base_dir, app_dir)
            except Exception:
                pass
        return base_dir

    async def load_plist(self, widget):
        app_dir = self.get_base_dir()
        start_dir = os.path.join(app_dir, "Library", "Preferences") if app_dir != "C:\\" else app_dir
        
        try:
            filepath = await self.main_window.dialog(toga.OpenFileDialog("Выберите plist", initial_directory=start_dir))
            if filepath:
                self.filepath = filepath
                with open(filepath, 'rb') as f:
                    self.plist_data = plistlib.load(f)
                
                # Поиск ID
                self.found_id = None
                for k in self.plist_data.keys():
                    m1 = re.match(r'^(\d{6,})_', k)
                    if m1: self.found_id = m1.group(1); break
                    m2 = re.match(r'^OpenRijTest_(\d{6,})', k, re.IGNORECASE)
                    if m2: self.found_id = m2.group(1); break

                if self.found_id:
                    target_key_lower = f"openrijtest_{self.found_id}".lower()
                    for k in list(self.plist_data.keys()):
                        if k.lower() == target_key_lower:
                            self.plist_data[k] = 0

                    current_gems = 0
                    for k in self.plist_data.keys():
                        if str(self.found_id) in k and 'gem' in k.lower():
                            current_gems = self.plist_data[k]
                            break
                    
                    self.lbl_status.text = f"ID загружен: {self.found_id}"
                    self.lbl_gems.text = f"Текущие самоцветы: {current_gems}"
                    
                    self.populate_switches()
                    self.save_file()
                    await self.main_window.dialog(toga.InfoDialog('Успех', f'Файл загружен!\nВаш ID: {self.found_id}'))
                else:
                    await self.main_window.dialog(toga.InfoDialog('Ошибка', 'ID не найден в файле.'))
        except Exception as e:
            print(e)
            
    async def load_data_files(self, widget):
        if not self.found_id:
            return await self.main_window.dialog(toga.InfoDialog('Ошибка', 'Сначала выберите .plist файл (кнопка 1), чтобы узнать ваш ID!'))

        app_dir = self.get_base_dir()
        documents_dir = os.path.join(app_dir, "Documents") if app_dir != "C:\\" else app_dir

        self.data_files_box.clear()
        
        found_files = []
        if os.path.exists(documents_dir):
            try:
                for f in os.listdir(documents_dir):
                    # Ищем файлы, содержащие ID пользователя и заканчивающиеся на .data
                    if str(self.found_id) in f and f.endswith('.data'):
                        found_files.append(f)
            except Exception as e:
                print(e)

        if not found_files:
            self.data_files_box.add(toga.Label(f'Файлы .data для ID {self.found_id} не найдены.', style=Pack(padding=10)))
            self.tabs.current_tab = 'Файлы'
            return

        self.data_files_box.add(toga.Label(f'Найдены файлы для ID {self.found_id}:', style=Pack(padding_bottom=10, font_weight='bold')))

        for filename in sorted(found_files):
            file_box = toga.Box(style=Pack(direction=ROW, padding_bottom=5))
            lbl = toga.Label(filename, style=Pack(flex=1, padding_right=10))
            btn = toga.Button('Редактировать', on_press=lambda w, name=filename: self.edit_data_file(name, documents_dir))
            
            file_box.add(lbl)
            file_box.add(btn)
            self.data_files_box.add(file_box)

        self.data_files_box.refresh()
        
        # Переключаем пользователя на вкладку с файлами
        self.tabs.current_tab = 'Файлы'
        await self.main_window.dialog(toga.InfoDialog('Успех', f'Отфильтровано файлов: {len(found_files)}'))

    def edit_data_file(self, filename, folder):
        full_path = os.path.join(folder, filename)
        # TODO: Добавить парсинг .data файла
        print(f"Будем редактировать {full_path}")

    def populate_switches(self):
        self.chars_box.clear()
        self.skins_box.clear()
        self.skills_box.clear()
        self.char_switches.clear()
        self.skin_switches.clear()
        self.skill_switches.clear()
        self.original_skin_values.clear()

        self.chars_box.add(toga.Button('Разблокировать ВСЕХ персонажей', on_press=self.unlock_all_chars, style=Pack(padding=5)))
        self.skins_box.add(toga.Button('Разблокировать ВСЕ скины', on_press=self.unlock_all_skins, style=Pack(padding=5)))
        self.skills_box.add(toga.Button('Разблокировать ВСЕ навыки', on_press=self.unlock_all_skills, style=Pack(padding=5)))

        chars_found = set()
        skins_found = set()
        skills_found = set()

        for k in self.plist_data.keys():
            if not k.startswith(f"{self.found_id}_"):
                continue
                
            m_char = re.match(fr'^{self.found_id}_(c[a-zA-Z0-9_]+)_unlock$', k)
            if m_char:
                char_key = m_char.group(1)
                chars_found.add(char_key)
                
            m_skin = re.match(fr'^{self.found_id}_(c[a-zA-Z0-9_]+_skin[0-9]+)$', k)
            if m_skin:
                skin_key = m_skin.group(1)
                skins_found.add(skin_key)
                
            m_skill = re.match(fr'^{self.found_id}_(c[a-zA-Z0-9_]+_skill_[0-9]+)_unlock$', k)
            if m_skill:
                skill_key = m_skill.group(1)
                skills_found.add(skill_key)

        for char_key in sorted(chars_found):
            full_key = f"{self.found_id}_{char_key}_unlock"
            is_unlocked = str(self.plist_data.get(full_key, 'false')).lower() == 'true'
            
            switch = toga.Switch(f"Персонаж {char_key}", is_on=is_unlocked, 
                                 on_change=lambda w, k=full_key: self.toggle_char(w, k))
            self.char_switches[full_key] = switch
            self.chars_box.add(toga.Box(children=[switch], style=Pack(padding=5)))

        for skin_key in sorted(skins_found):
            full_key = f"{self.found_id}_{skin_key}"
            val = self.plist_data.get(full_key, 0)
            self.original_skin_values[full_key] = val
            is_unlocked = val == 1
            
            switch = toga.Switch(f"Скин {skin_key}", is_on=is_unlocked, 
                                 on_change=lambda w, k=full_key: self.toggle_skin(w, k))
            self.skin_switches[full_key] = switch
            self.skins_box.add(toga.Box(children=[switch], style=Pack(padding=5)))

        for skill_key in sorted(skills_found):
            full_key = f"{self.found_id}_{skill_key}_unlock"
            is_unlocked = self.plist_data.get(full_key, 0) == 1
            
            switch = toga.Switch(f"Навык {skill_key}", is_on=is_unlocked, 
                                 on_change=lambda w, k=full_key: self.toggle_skill(w, k))
            self.skill_switches[full_key] = switch
            self.skills_box.add(toga.Box(children=[switch], style=Pack(padding=5)))

        self.chars_box.refresh()
        self.skins_box.refresh()
        self.skills_box.refresh()

    def toggle_char(self, widget, key):
        self.plist_data[key] = 'true' if widget.value else 'false'
        self.save_file()

    def toggle_skin(self, widget, key):
        if widget.value:
            self.plist_data[key] = 1
        else:
            prev = self.original_skin_values.get(key, 0)
            self.plist_data[key] = prev if prev != 1 else 0
        self.save_file()

    def toggle_skill(self, widget, key):
        self.plist_data[key] = 1 if widget.value else 0
        self.save_file()

    def save_file(self):
        if self.filepath and self.plist_data:
            with open(self.filepath, 'wb') as f:
                plistlib.dump(self.plist_data, f)

    async def save_gems(self, widget):
        if not self.found_id: return await self.show_error()
        val = self.input_gems.value.strip()
        if val.isdigit():
            val_int = int(val)
            for k in list(self.plist_data.keys()):
                if str(self.found_id) in k and 'gem' in k.lower():
                    self.plist_data[k] = val_int
            self.lbl_gems.text = f"Текущие самоцветы: {val_int}"
            self.save_file()
            await self.main_window.dialog(toga.InfoDialog('Успех', f'Самоцветы изменены на {val_int}!'))
        else:
            await self.main_window.dialog(toga.InfoDialog('Ошибка', 'Введите число'))

    async def unlock_all_chars(self, widget):
        for key, switch in self.char_switches.items():
            switch.value = True
        await self.main_window.dialog(toga.InfoDialog('Успех', 'Все персонажи разблокированы!'))

    async def unlock_all_skins(self, widget):
        for key, switch in self.skin_switches.items():
            switch.value = True
        await self.main_window.dialog(toga.InfoDialog('Успех', 'Все скины разблокированы!'))

    async def unlock_all_skills(self, widget):
        for key, switch in self.skill_switches.items():
            switch.value = True
        await self.main_window.dialog(toga.InfoDialog('Успех', 'Все навыки разблокированы!'))

    async def show_error(self):
        await self.main_window.dialog(toga.InfoDialog('Ошибка', 'Сначала выберите файл plist на вкладке "Главная"'))

def main():
    return SKEditApp('SKEdit', 'com.diablo.funpay')
