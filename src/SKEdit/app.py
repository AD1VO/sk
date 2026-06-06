import os
import re
import plistlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

class SKEditApp(toga.App):
    def startup(self):
        self.tabs = toga.OptionContainer()

        # ВКЛАДКА 1
        tab1_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_full = toga.Button('Фулл аккаунт (в разработке)', style=Pack(padding_bottom=10))
        tab1_box.add(self.btn_full)

        # ВКЛАДКА 2 (РЕДАКТОР)
        tab2_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # Строка с полем для ID
        plist_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        self.btn_plist = toga.Button('1. Выбрать .plist (Авто-Разблокировка)', on_press=self.parse_plist, style=Pack(padding_right=10))
        self.id_input = toga.TextInput(placeholder='Сюда скрипт вставит ID сам', style=Pack(flex=1))
        plist_box.add(self.btn_plist)
        plist_box.add(self.id_input)

        # Строка с вводом самоцветов
        self.gems_input = toga.TextInput(placeholder='Введите кол-во самоцветов (например: 99999)', style=Pack(padding_bottom=10))

        # Строка с заготовкой
        self.new_input = toga.TextInput(placeholder='2. Вставьте новую заготовку для DATA', style=Pack(padding_bottom=10))
        self.btn_data = toga.Button('3. Обработать .data файлы (временно отключено)', on_press=self.process_data, style=Pack(padding_bottom=10))
        
        self.log = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
        self.log.value = "Готово!\n1. Введите желаемое количество самоцветов.\n2. Нажмите «Выбрать .plist» — скрипт сам найдет ID, накрутит гемы и разблокирует всё остальное."
        
        tab2_box.add(self.gems_input)
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
                with open(filepath, 'rb') as f: 
                    plist_data = plistlib.load(f)
                
                # Поиск ID
                found_id = None
                for k in plist_data.keys():
                    m1 = re.match(r'^(\d{6,})_', k)
                    if m1: found_id = m1.group(1); break
                    m2 = re.match(r'^OpenRijTest_(\d{6,})', k, re.IGNORECASE)
                    if m2: found_id = m2.group(1); break
                
                if found_id:
                    self.id_input.value = str(found_id)
                    log_msg = f"[+] Найден ID: {found_id}\n"
                    
                    # 1. Отключаем OpenRijTest
                    target_key_lower = f"openrijtest_{found_id}".lower()
                    for k in list(plist_data.keys()):
                        if k.lower() == target_key_lower and plist_data[k] == 1:
                            plist_data[k] = 0
                            log_msg += f"[+] Защита {k} отключена!\n"
                            
                    # 2. НАКРУТКА САМОЦВЕТОВ
                    # Проверяем, ввел ли пользователь число
                    gems_value = self.gems_input.value.strip()
                    if gems_value.isdigit():
                        gems_count = int(gems_value)
                        # Ищем все ключи, содержащие ID и слово 'gem' (например: 128924619_gem или 128924619_last_gems)
                        for k in list(plist_data.keys()):
                            if str(found_id) in k and 'gem' in k.lower():
                                plist_data[k] = gems_count
                                log_msg += f"[+] Значение {k} установлено на {gems_count}!\n"
                    else:
                        log_msg += "[!] Количество самоцветов не введено или введено неверно. Пропущено.\n"

                    # 3. АВТО-РАЗБЛОКИРОВКА ПЕРСОНАЖЕЙ И НАВЫКОВ
                    for c in range(35):
                        plist_data[f"{found_id}_c{c}_unlock"] = 1
                        for s in range(45):
                            plist_data[f"{found_id}_c{c}_skin{s}"] = 1
                            
                    for s in range(30):
                        plist_data[f"{found_id}_skill_{s}"] = 1
                    for p in range(65):
                        plist_data[f"{found_id}_pet{p}_unlock"] = 1
                        
                    log_msg += "[+] Персонажи, скины, питомцы и навыки успешно разблокированы!\n"

                    # Сохраняем обновленный файл
                    with open(filepath, 'wb') as f: 
                        plistlib.dump(plist_data, f)
                    log_msg += "[+] Файл .plist успешно перезаписан!"
                        
                    self.log.value = log_msg
                else:
                    self.log.value = "[-] Не удалось найти ID в файле .plist"
        except ValueError: 
            pass

    async def process_data(self, widget):
        self.log.value = "Шифрование .data в iOS-версии временно отключено."

def main():
    return SKEditApp('SKEdit', 'com.diablo.funpay')