import os
import re
import pyDes
import plistlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

def pad_key_iv(text):
    b = text.encode('utf-8')
    return (b + b'\0' * 8)[:8]

class SKEditApp(toga.App):
    def startup(self):
        self.tabs = toga.OptionContainer()

        # ВКЛАДКА 1: ГОТОВЫЕ АККАУНТЫ
        tab1_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_full = toga.Button('Фулл аккаунт (в разработке)', style=Pack(padding_bottom=10))
        tab1_box.add(self.btn_full)

        # ВКЛАДКА 2: РЕДАКТОР
        tab2_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        plist_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        self.btn_plist = toga.Button('1. Выбрать .plist', on_press=self.parse_plist, style=Pack(padding_right=10))
        self.id_input = toga.TextInput(placeholder='Сюда скрипт вставит ID сам', style=Pack(flex=1))
        plist_box.add(self.btn_plist)
        plist_box.add(self.id_input)

        self.new_input = toga.TextInput(placeholder='2. Вставьте новую заготовку (текст для замены)', style=Pack(padding_bottom=10))
        self.btn_data = toga.Button('3. Выбрать и обработать .data файлы', on_press=self.process_data, style=Pack(padding_bottom=10))
        
        self.log = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
        self.log.value = "Редактор готов.\nСначала выберите .plist, чтобы найти ID и отключить OpenRijTest."
        
        tab2_box.add(plist_box)
        tab2_box.add(self.new_input)
        tab2_box.add(self.btn_data)
        tab2_box.add(self.log)

        self.tabs.content.append('Готовые аккаунты', tab1_box)
        self.tabs.content.append('Редактор', tab2_box)

        self.main_window = toga.MainWindow(title="SKEdit Mod Tool")
        self.main_window.content = self.tabs
        self.main_window.show()

    # Умный парсинг Plist
    async def parse_plist(self, widget):
        # Настройка начального пути
        start_dir = "C:\\" if os.name == 'nt' else "/var/mobile/Containers/Data/Application/"
        
        try:
            filepath = await self.main_window.dialog(
                toga.OpenFileDialog("Выберите файл .plist", initial_directory=start_dir)
            )
            if filepath:
                with open(filepath, 'rb') as f:
                    plist_data = plistlib.load(f)
                
                found_id = None
                for k in plist_data.keys():
                    m1 = re.match(r'^(\d{6,})_', k)
                    if m1: 
                        found_id = m1.group(1)
                        break
                    m2 = re.match(r'^OpenRijTest_(\d{6,})', k, re.IGNORECASE)
                    if m2:
                        found_id = m2.group(1)
                        break
                
                if found_id:
                    self.id_input.value = str(found_id)
                    log_msg = f"[+] Найден ID: {found_id}\n"
                    
                    modified = False
                    target_key_lower = f"openrijtest_{found_id}".lower()
                    
                    for k in list(plist_data.keys()):
                        if k.lower() == target_key_lower:
                            if plist_data[k] == 1:
                                plist_data[k] = 0
                                modified = True
                                log_msg += f"[+] Значение {k} успешно изменено на 0!\n"
                            else:
                                log_msg += f"[i] Значение {k} уже равно 0.\n"
                                
                    if modified:
                        with open(filepath, 'wb') as f:
                            plistlib.dump(plist_data, f)
                        log_msg += "[+] Файл .plist перезаписан с новыми значениями!\n"
                        
                    self.log.value = log_msg + "\nТеперь вставьте текст и обработайте .data файлы."
                else:
                    self.log.value = "[-] Не удалось найти ID. Формат файла неизвестен."
        except ValueError:
            pass
        except Exception as e:
            self.log.value = f"[-] Ошибка обработки plist: {e}"

    # Обработка DATA файлов
    async def process_data(self, widget):
        if not self.id_input.value:
            self.log.value = "Ошибка: Сначала выберите Plist или введите ID вручную!\n"
            return
        if not self.new_input.value:
            self.log.value = "Ошибка: Вставьте текст новой заготовки!\n"
            return
            
        # Настройка начального пути
        start_dir = "C:\\" if os.name == 'nt' else "/var/mobile/Containers/Data/Application/"
            
        try:
            files = await self.main_window.dialog(
                toga.OpenFileDialog("Выберите файлы .data", multiple=True, initial_directory=start_dir)
            )
            if files:
                results = [self.do_replace(str(f)) for f in files]
                self.log.value = "\n".join(results)
        except ValueError:
            pass

    def do_replace(self, filepath):
        filename = os.path.basename(filepath).lower()
        key_mapping = {
            "iambo": ["item", "season", "task", "setting", "bp", "pvp", "weapon", "monsrise"],
            "crst1": ["statistic"],
            "_@sT0r3Cxnf19": ["fish"]
        }
        
        file_key = next((k for k, v in key_mapping.items() if any(w in filename for w in v)), None)
        if not file_key: return f"[-] Пропущен (неизвестный файл): {filename}"

        try:
            key = pad_key_iv(file_key)
            iv = pad_key_iv("Ahbool")
            cipher = pyDes.des(key, pyDes.CBC, iv, pad=None, padmode=pyDes.PAD_PKCS5)
            
            with open(filepath, 'rb') as f: enc = f.read()
            text = re.sub(str(self.id_input.value), str(self.new_input.value), cipher.decrypt(enc).decode('utf-8', 'ignore'))
            
            with open(filepath, 'wb') as f: f.write(cipher.encrypt(text.encode('utf-8')))
            return f"[+] Обновлен: {filename}"
        except Exception as e: return f"[-] Ошибка ({filename}): {e}"

def main():
    return SKEditApp('SKEdit', 'com.diablo.funpay')