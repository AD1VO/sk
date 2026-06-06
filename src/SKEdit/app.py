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
        self.original_skin_values = {} # Для сохранения предыдущего значения скинов

        self.tabs = toga.OptionContainer()

        # --- ТАБ 1: ГЛАВНАЯ (ПЛИСТ И САМОЦВЕТЫ) ---
        tab_main = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.lbl_status = toga.Label('Файл не выбран', style=Pack(padding_bottom=10))
        self.btn_load = toga.Button('1. Выбрать .plist файл', on_press=self.load_plist, style=Pack(padding_bottom=20))
        
        self.lbl_gems = toga.Label('Текущие самоцветы: -', style=Pack(padding_bottom=5))
        self.input_gems = toga.TextInput(placeholder='Введите новое количество', style=Pack(padding_bottom=10))
        self.btn_save_gems = toga.Button('Сохранить самоцветы', on_press=self.save_gems, style=Pack(padding_bottom=10))
        
        tab_main.add(self.lbl_status)
        tab_main.add(self.btn_load)
        tab_main.add(self.lbl_gems)
        tab_main.add(self.input_gems)
        tab_main.add(self.btn_save_gems)

        # --- ТАБ 2: ПЕРСОНАЖИ (ТУМБЛЕРЫ) ---
        self.chars_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.chars_scroll = toga.ScrollContainer(content=self.chars_box, horizontal=False)
        self.char_switches = {}

        # --- ТАБ 3: СКИНЫ (ТУМБЛЕРЫ) ---
        self.skins_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.skins_scroll = toga.ScrollContainer(content=self.skins_box, horizontal=False)
        self.skin_switches = {}

        # --- ТАБ 4: НАВЫКИ (ТУМБЛЕРЫ) ---
        self.skills_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.skills_scroll = toga.ScrollContainer(content=self.skills_box, horizontal=False)
        self.skill_switches = {}

        # Добавляем табы в нижнее меню в нужном порядке
        self.tabs.content.append('Главная', tab_main)
        self.tabs.content.append('Персы', self.chars_scroll)
        self.tabs.content.append('Скины', self.skins_scroll)
        self.tabs.content.append('Навыки', self.skills_scroll)

        self.main_window = toga.MainWindow(title="SKEdit Mod")
        self.main_window.content = self.tabs
        self.main_window.show()

    async def load_plist(self, widget):
        start_dir = "C:\\" if os.name == 'nt' else "/var/mobile/Containers/Data/Application/"
        try:
            filepath = await self.main_window.dialog(toga.OpenFileDialog("Выберите .plist", initial_directory=start_dir))
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
                    # Сразу выключаем защиту
                    target_key_lower = f"openrijtest_{self.found_id}".lower()
                    for k in list(self.plist_data.keys()):
                        if k.lower() == target_key_lower:
                            self.plist_data[k] = 0

                    # Ищем текущие гемы
                    current_gems = 0
                    for k in self.plist_data.keys():
                        if str(self.found_id) in k and 'gem' in k.lower():
                            current_gems = self.plist_data[k]
                            break
                    
                    self.lbl_status.text = f"ID загружен: {self.found_id}"
                    self.lbl_gems.text = f"Текущие самоцветы: {current_gems}"
                    
                    self.populate_switches()
                    
                    self.save_file()
                    await self.main_window.dialog(toga.InfoDialog('Успех', f'Файл загружен!\nВаш ID: {self.found_id}\nСамоцветов: {current_gems}'))
                else:
                    await self.main_window.dialog(toga.InfoDialog('Ошибка', 'ID не найден в файле.'))
        except Exception as e:
            print(e)
            
    def populate_switches(self):
        # Очищаем старые тумблеры
        self.chars_box.clear()
        self.skins_box.clear()
        self.skills_box.clear()
        self.char_switches.clear()
        self.skin_switches.clear()
        self.skill_switches.clear()
        self.original_skin_values.clear()

        # Кнопки "Включить все"
        self.chars_box.add(toga.Button('Разблокировать ВСЕХ персонажей', on_press=self.unlock_all_chars, style=Pack(padding=5)))
        self.skins_box.add(toga.Button('Разблокировать ВСЕ скины', on_press=self.unlock_all_skins, style=Pack(padding=5)))
        self.skills_box.add(toga.Button('Разблокировать ВСЕ навыки', on_press=self.unlock_all_skills, style=Pack(padding=5)))

        chars_found = set()
        skins_found = set()
        skills_found = set()

        for k in self.plist_data.keys():
            if not k.startswith(f"{self.found_id}_"):
                continue
                
            # Парсим персонажей (c0_unlock, c_Knight_unlock и т.д.)
            m_char = re.match(fr'^{self.found_id}_(c[a-zA-Z0-9_]+)_unlock$', k)
            if m_char:
                char_key = m_char.group(1)
                chars_found.add(char_key)
                
            # Парсим скины (c0_skin1, c_Knight_skin_2)
            m_skin = re.match(fr'^{self.found_id}_(c[a-zA-Z0-9_]+_skin[0-9]+)$', k)
            if m_skin:
                skin_key = m_skin.group(1)
                skins_found.add(skin_key)
                
            # Парсим навыки (c_Knight_skill_0_unlock)
            m_skill = re.match(fr'^{self.found_id}_(c[a-zA-Z0-9_]+_skill_[0-9]+)_unlock$', k)
            if m_skill:
                skill_key = m_skill.group(1)
                skills_found.add(skill_key)

        # Создаем тумблеры для персонажей
        for char_key in sorted(chars_found):
            full_key = f"{self.found_id}_{char_key}_unlock"
            is_unlocked = str(self.plist_data.get(full_key, 'false')).lower() == 'true'
            
            switch = toga.Switch(f"Персонаж {char_key}", is_on=is_unlocked, 
                                 on_change=lambda w, k=full_key: self.toggle_char(w, k))
            self.char_switches[full_key] = switch
            self.chars_box.add(toga.Box(children=[switch], style=Pack(padding=5)))

        # Создаем тумблеры для скинов
        for skin_key in sorted(skins_found):
            full_key = f"{self.found_id}_{skin_key}"
            val = self.plist_data.get(full_key, 0)
            self.original_skin_values[full_key] = val
            is_unlocked = val == 1
            
            switch = toga.Switch(f"Скин {skin_key}", is_on=is_unlocked, 
                                 on_change=lambda w, k=full_key: self.toggle_skin(w, k))
            self.skin_switches[full_key] = switch
            self.skins_box.add(toga.Box(children=[switch], style=Pack(padding=5)))

        # Создаем тумблеры для навыков
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
        await self.main_window.dialog(toga.InfoDialog('Ошибка', 'Сначала выберите файл .plist на вкладке "Главная"'))

def main():
    return SKEditApp('SKEdit', 'com.diablo.funpay')
