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

        # --- ТАБ 2: ПЕРСОНАЖИ ---
        tab_chars = toga.Box(style=Pack(direction=COLUMN, padding=10))
        tab_chars.add(toga.Label('Разблокировка персонажей:', style=Pack(padding_bottom=10)))
        self.input_char_id = toga.TextInput(placeholder='Номер персонажа (например: 0)', style=Pack(padding_bottom=10))
        self.btn_unlock_char = toga.Button('Разблокировать одного', on_press=self.unlock_one_char, style=Pack(padding_bottom=20))
        self.btn_unlock_all_chars = toga.Button('Разблокировать ВСЕХ персонажей', on_press=self.unlock_all_chars, style=Pack(padding_bottom=10))
        
        tab_chars.add(self.input_char_id)
        tab_chars.add(self.btn_unlock_char)
        tab_chars.add(self.btn_unlock_all_chars)

        # --- ТАБ 3: СКИНЫ ---
        tab_skins = toga.Box(style=Pack(direction=COLUMN, padding=10))
        tab_skins.add(toga.Label('Разблокировка скинов:', style=Pack(padding_bottom=10)))
        self.input_skin_char = toga.TextInput(placeholder='Номер персонажа (например: 0)', style=Pack(padding_bottom=5))
        self.input_skin_id = toga.TextInput(placeholder='Номер скина (например: 2)', style=Pack(padding_bottom=10))
        self.btn_unlock_skin = toga.Button('Разблокировать один скин', on_press=self.unlock_one_skin, style=Pack(padding_bottom=20))
        self.btn_unlock_all_skins = toga.Button('Разблокировать ВСЕ скины', on_press=self.unlock_all_skins, style=Pack(padding_bottom=10))
        
        tab_skins.add(self.input_skin_char)
        tab_skins.add(self.input_skin_id)
        tab_skins.add(self.btn_unlock_skin)
        tab_skins.add(self.btn_unlock_all_skins)

        # --- ТАБ 4: НАВЫКИ ---
        tab_skills = toga.Box(style=Pack(direction=COLUMN, padding=10))
        tab_skills.add(toga.Label('Разблокировка навыков:', style=Pack(padding_bottom=10)))
        self.input_skill_id = toga.TextInput(placeholder='Номер навыка (например: 1)', style=Pack(padding_bottom=10))
        self.btn_unlock_skill = toga.Button('Разблокировать один навык', on_press=self.unlock_one_skill, style=Pack(padding_bottom=20))
        self.btn_unlock_all_skills = toga.Button('Разблокировать ВСЕ навыки', on_press=self.unlock_all_skills, style=Pack(padding_bottom=10))
        
        tab_skills.add(self.input_skill_id)
        tab_skills.add(self.btn_unlock_skill)
        tab_skills.add(self.btn_unlock_all_skills)

        # --- ТАБ 5: АККАУНТЫ ---
        tab_accounts = toga.Box(style=Pack(direction=COLUMN, padding=10))
        tab_accounts.add(toga.Label('Здесь будут готовые аккаунты', style=Pack(padding_bottom=10)))
        tab_accounts.add(toga.Button('Загрузить фулл аккаунт (в разработке)', style=Pack(padding_bottom=10)))

        # Добавляем табы в нижнее меню в нужном порядке
        self.tabs.content.append('Главная', tab_main)
        self.tabs.content.append('Персы', tab_chars)
        self.tabs.content.append('Скины', tab_skins)
        self.tabs.content.append('Навыки', tab_skills)
        self.tabs.content.append('Аккаунты', tab_accounts)

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
                    self.save_file()
                    await self.main_window.dialog(toga.InfoDialog('Успех', f'Файл загружен!\nВаш ID: {self.found_id}\nСамоцветов: {current_gems}'))
                else:
                    await self.main_window.dialog(toga.InfoDialog('Ошибка', 'ID не найден в файле.'))
        except Exception as e:
            print(e)

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

    async def unlock_one_char(self, widget):
        if not self.found_id: return await self.show_error()
        val = self.input_char_id.value.strip()
        if val.isdigit():
            self.plist_data[f"{self.found_id}_c{val}_unlock"] = 1
            self.save_file()
            await self.main_window.dialog(toga.InfoDialog('Успех', f'Персонаж {val} разблокирован!'))

    async def unlock_all_chars(self, widget):
        if not self.found_id: return await self.show_error()
        for c in range(35):
            self.plist_data[f"{self.found_id}_c{c}_unlock"] = 1
        self.save_file()
        await self.main_window.dialog(toga.InfoDialog('Успех', 'Все персонажи разблокированы!'))

    async def unlock_one_skin(self, widget):
        if not self.found_id: return await self.show_error()
        c = self.input_skin_char.value.strip()
        s = self.input_skin_id.value.strip()
        if c.isdigit() and s.isdigit():
            self.plist_data[f"{self.found_id}_c{c}_skin{s}"] = 1
            self.save_file()
            await self.main_window.dialog(toga.InfoDialog('Успех', f'Скин {s} для персонажа {c} разблокирован!'))

    async def unlock_all_skins(self, widget):
        if not self.found_id: return await self.show_error()
        for c in range(35):
            for s in range(45):
                self.plist_data[f"{self.found_id}_c{c}_skin{s}"] = 1
        self.save_file()
        await self.main_window.dialog(toga.InfoDialog('Успех', 'Все скины разблокированы!'))

    async def unlock_one_skill(self, widget):
        if not self.found_id: return await self.show_error()
        val = self.input_skill_id.value.strip()
        if val.isdigit():
            self.plist_data[f"{self.found_id}_skill_{val}"] = 1
            self.save_file()
            await self.main_window.dialog(toga.InfoDialog('Успех', f'Навык {val} разблокирован!'))

    async def unlock_all_skills(self, widget):
        if not self.found_id: return await self.show_error()
        for s in range(30):
            self.plist_data[f"{self.found_id}_skill_{s}"] = 1
        self.save_file()
        await self.main_window.dialog(toga.InfoDialog('Успех', 'Все навыки разблокированы!'))

    async def show_error(self):
        await self.main_window.dialog(toga.InfoDialog('Ошибка', 'Сначала выберите файл .plist на вкладке "Главная"'))

def main():
    return SKEditApp('SKEdit', 'com.diablo.funpay')
