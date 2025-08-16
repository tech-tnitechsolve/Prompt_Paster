# -*- coding: utf-8 -*-
# core.py

import os
import csv
import json
import time
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QSettings, pyqtSlot

from pynput import keyboard
from pynput.keyboard import Controller, Key

class CoreLogic(QObject):
    """
    Cải tiến v9.1:
    - Loại bỏ hoàn toàn tính năng tự động di chuyển file.
    - Đặt hotkey mặc định là ctrl+b.
    - Tinh giản logic và các cài đặt không cần thiết.
    """
    data_changed = pyqtSignal()
    stats_updated = pyqtSignal(dict)
    show_message = pyqtSignal(str, str)
    show_mini_controller_signal = pyqtSignal(str)
    hide_mini_controller_signal = pyqtSignal()
    update_mini_progress_signal = pyqtSignal(int, int)
    progress_reset = pyqtSignal()
    pause_state_changed = pyqtSignal(bool) 
    hotkey_triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.prompt_lists = {}
        self.current_folder = None
        self.current_list_name = None
        self.current_prompt_index = 0
        self.session_paste_count = 0 
        self.is_active = False
        self.is_paused = False
        self.is_pasting = False
        self.last_hotkey_time = 0
        self.last_paste_time = 0
        self.paste_in_progress = False
        
        self.settings = QSettings("PromptPaster", "App")
        
        default_data_path = os.path.join(os.path.expanduser("~"), "PromptPaster_Data")
        self.storage_path = self.settings.value("storage_path", default_data_path, type=str)
        
        # Yêu cầu 1: Đảm bảo hotkey mặc định là ctrl+b
        self.hotkey = self.settings.value("hotkey", "ctrl+b", type=str)

        self.log_file = os.path.join(self.storage_path, "activity_log.json")
        
        self.hotkey_listener = None
        self.key_listener = None 
        self.pressed_keys = set()
        self.keyboard_controller = Controller()
        
        self._create_directory_if_not_exists(self.storage_path)
            
        self.hotkey_triggered.connect(self.execute_paste_action)

    def _get_clipboard(self):
        clipboard = QApplication.clipboard()
        if not clipboard:
            self.show_message.emit("Lỗi Clipboard", "Không thể truy cập clipboard của hệ thống.")
        return clipboard

    def _get_clipboard_text(self):
        clipboard = self._get_clipboard()
        text = ""
        if clipboard:
            mime_data = clipboard.mimeData()
            if mime_data and mime_data.hasText():
                try: text = clipboard.text()
                except Exception as e: print(f"Lỗi khi đọc clipboard: {e}")
        return text

    def _set_clipboard_text(self, text):
        clipboard = self._get_clipboard()
        if not clipboard: return False
        try:
            clipboard.setText(text); return True
        except Exception as e:
            print(f"Lỗi khi ghi vào clipboard: {e}")
            self.show_message.emit("Lỗi Clipboard", "Không thể ghi dữ liệu vào clipboard.")
            return False
    
    def _on_press(self, key):
        self.pressed_keys.add(key)
        try:
            if (hasattr(key, 'char') and key.char.lower() == 'c' and 
                any(k in self.pressed_keys for k in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])):
                if self.is_active and not self.is_paused: self.toggle_pause_resume()
        except AttributeError: pass

    def _on_release(self, key):
        if key in self.pressed_keys: self.pressed_keys.remove(key)

    def _start_key_listener(self):
        self._stop_key_listener()
        try:
            self.key_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self.key_listener.start()
        except Exception as e: print(f"Không thể khởi động key listener: {e}")

    def _stop_key_listener(self):
        if self.key_listener:
            try: self.key_listener.stop()
            except Exception as e: print(f"Lỗi khi dừng key listener: {e}")
            finally: self.key_listener = None; self.pressed_keys.clear()
    
    def load_all_lists(self): self.data_changed.emit()

    def get_list_content(self, key):
        if not key or '/' not in key: return []
        if key in self.prompt_lists: return self.prompt_lists[key]
        folder_name, list_name = key.split('/', 1)
        list_path = os.path.join(self.storage_path, folder_name, f"{list_name}.json")
        if os.path.exists(list_path):
            try:
                with open(list_path, 'r', encoding='utf-8') as f:
                    content = [item for item in json.load(f) if item and str(item).strip()]
                    self.prompt_lists[key] = content
                    return content
            except (json.JSONDecodeError, Exception) as e: print(f"Lỗi tải danh sách {list_path}: {e}")
        return []

    def save_list_to_file(self, key, data):
        if not key or '/' not in key: return False
        cleaned_data = [str(item).strip() for item in data if item and str(item).strip()]
        folder_name, list_name = key.split('/', 1)
        folder_path = os.path.join(self.storage_path, folder_name)
        self._create_directory_if_not_exists(folder_path)
        file_path = os.path.join(folder_path, f"{list_name}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
            self.prompt_lists[key] = cleaned_data
            return True
        except Exception as e: print(f"Lỗi lưu danh sách {key}: {e}"); return False

    def toggle_active_state(self, is_checked):
        if is_checked:
            if not self.current_list_name or not self.current_folder:
                self.show_message.emit("Chưa chọn danh sách", "Vui lòng chọn danh sách trước khi bắt đầu.")
                return False
            self.is_active = True; self.is_paused = False
            self.pause_state_changed.emit(self.is_paused)
            self.session_paste_count = 0
            if not self.start_hotkey_listener(): self.is_active = False; return False
            self._start_key_listener()
            self.log_activity("start")
            self.show_mini_controller_signal.emit(self.current_list_name)
            self.update_stats()
        else:
            self.is_active = False; self.is_paused = False
            self.stop_hotkey_listener(); self._stop_key_listener()
            self.log_activity("stop")
            self.hide_mini_controller_signal.emit()
        return True

    def toggle_pause_resume(self):
        if not self.is_active: return
        self.is_paused = not self.is_paused
        self.pause_state_changed.emit(self.is_paused)

    def on_hotkey_activated(self):
        current_time = time.time()
        if current_time - self.last_hotkey_time < 0.5:
            return
        self.last_hotkey_time = current_time
        
        if not self.is_pasting: 
            self.hotkey_triggered.emit()

    def _format_hotkey_for_pynput(self, hotkey_str):
        parts = hotkey_str.lower().replace(" ", "").split('+')
        return "+".join([f"<{p}>" if p in ['ctrl', 'alt', 'shift', 'cmd'] else p for p in parts])

    def start_hotkey_listener(self):
        self.stop_hotkey_listener()
        try:
            formatted_hotkey = self._format_hotkey_for_pynput(self.hotkey)
            self.hotkey_listener = keyboard.GlobalHotKeys({formatted_hotkey: self.on_hotkey_activated})
            self.hotkey_listener.start()
            return True
        except Exception as e:
            self.show_message.emit("Lỗi Hotkey", f"Không thể đăng ký hotkey '{self.hotkey}': {e}"); return False

    def stop_hotkey_listener(self):
        if self.hotkey_listener:
            try: self.hotkey_listener.stop()
            except Exception as e: print(f"Lỗi khi dừng hotkey listener: {e}")
            finally: self.hotkey_listener = None

    @pyqtSlot()
    def execute_paste_action(self):
        if self.paste_in_progress:
            return
            
        if (self.is_pasting or not self.is_active or self.is_paused or not self.current_list_name or not self.current_folder): 
            return
        
        current_time = time.time()
        if hasattr(self, 'last_paste_time') and current_time - self.last_paste_time < 1.0:
            return
        self.last_paste_time = current_time
        
        self.is_pasting = True
        self.paste_in_progress = True
        try:
            key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
            current_list = self.get_list_content(key)
            if not current_list or self.current_prompt_index >= len(current_list):
                if self.is_active: self.toggle_active_state(False)
                return
            prompt_to_paste = current_list[self.current_prompt_index]
            
            original_text = self._get_clipboard_text()
            
            if not self._set_clipboard_text(prompt_to_paste): 
                self.is_pasting = False; return
                
            time.sleep(0.3)
            
            paste_key = Key.cmd if sys.platform == 'darwin' else Key.ctrl
            self.keyboard_controller.press(paste_key)
            self.keyboard_controller.press('v')
            self.keyboard_controller.release('v')
            self.keyboard_controller.release(paste_key)
            
            time.sleep(0.3)
            self._set_clipboard_text(original_text)

            self.current_prompt_index += 1; self.session_paste_count += 1
            self.update_stats(); self.save_state()
            if self.current_prompt_index >= len(current_list):
                self.show_message.emit("Hoàn tất", f"Đã paste hết prompt trong '{self.current_list_name}'.")
                self.log_activity("finished")
                if self.is_active: self.toggle_active_state(False)
        except Exception as e: print(f"Lỗi trong execute_paste_action: {e}")
        finally: 
            self.is_pasting = False
            self.paste_in_progress = False

    def save_state(self):
        try:
            self.settings.setValue("storage_path", self.storage_path)
            self.settings.setValue("hotkey", self.hotkey)
            list_states = self.settings.value("list_states", {})
            if not isinstance(list_states, dict): list_states = {}
            if self.current_folder and self.current_list_name:
                key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
                list_states[key] = {"index": self.current_prompt_index}
                self.settings.setValue("last_selected_path", os.path.join(self.current_folder, f"{self.current_list_name}.json"))
            else: self.settings.remove("last_selected_path")
            self.settings.setValue("list_states", list_states)
        except Exception as e: print(f"Lỗi lưu trạng thái: {e}")
        
    def load_state(self):
        try: return self.settings.value("last_selected_path")
        except Exception as e: print(f"Lỗi tải trạng thái: {e}"); return None

    def update_settings(self, new_settings):
        should_restart = False
        if new_settings.get("hotkey") != self.hotkey:
            self.hotkey = new_settings.get("hotkey", "ctrl+b")
            if self.is_active: self.stop_hotkey_listener(); self.start_hotkey_listener()
        if new_settings.get("storage_path") != self.storage_path:
            self.storage_path = new_settings.get("storage_path")
            self.log_file = os.path.join(self.storage_path, "activity_log.json")
            should_restart = True
        
        self.save_state()
        return should_restart

    def _create_directory_if_not_exists(self, path):
        try:
            if path and not os.path.exists(path): os.makedirs(path)
            return True
        except Exception as e: print(f"Không thể tạo thư mục {path}: {e}"); return False
    
    def create_new_folder(self, folder_name):
        if not folder_name or not folder_name.strip(): self.show_message.emit("Lỗi", "Tên thư mục không được để trống."); return
        folder_name = "".join(c for c in folder_name.strip() if c.isalnum() or c in (' ', '-', '_')).strip()
        if not folder_name: self.show_message.emit("Lỗi", "Tên thư mục không hợp lệ."); return
        folder_path = os.path.join(self.storage_path, folder_name)
        if os.path.exists(folder_path): self.show_message.emit("Lỗi", "Thư mục đã tồn tại."); return
        try: os.makedirs(folder_path); self.load_all_lists()
        except Exception as e: self.show_message.emit("Lỗi", f"Không thể tạo thư mục: {e}")

    def create_new_list(self, target_folder_path, list_name):
        if not list_name or not list_name.strip() or not target_folder_path: self.show_message.emit("Lỗi", "Tên danh sách không được để trống."); return
        list_name = "".join(c for c in list_name.strip() if c.isalnum() or c in (' ', '-', '_')).strip()
        if not list_name: self.show_message.emit("Lỗi", "Tên danh sách không hợp lệ."); return
        list_path = os.path.join(target_folder_path, f"{list_name}.json")
        if os.path.exists(list_path): self.show_message.emit("Lỗi", "Danh sách đã tồn tại."); return
        key = f"{os.path.basename(target_folder_path)}/{list_name}"
        if self.save_list_to_file(key, []): self.load_all_lists()
        else: self.show_message.emit("Lỗi", "Không thể tạo danh sách.")

    def delete_item(self, item_path):
        import shutil
        if not item_path or not os.path.exists(item_path): self.show_message.emit("Lỗi", "Item không tồn tại."); return
        try:
            if os.path.isdir(item_path): shutil.rmtree(item_path)
            elif os.path.isfile(item_path): os.remove(item_path)
            self.load_all_lists()
        except Exception as e: self.show_message.emit("Lỗi", f"Không thể xóa: {e}")

    def import_from_csv(self, file_path):
        if not self.current_list_name or not self.current_folder: 
            self.show_message.emit("Chưa chọn danh sách", "Vui lòng chọn danh sách để import."); return
        try:
            with open(file_path, 'r', encoding='utf-8') as f: 
                prompts_from_csv = [str(row[0]).strip() for row in csv.reader(f) if row and str(row[0]).strip()]
            
            if not prompts_from_csv: 
                self.show_message.emit("Lỗi", "File CSV rỗng hoặc không hợp lệ."); return

            key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
            current_content = self.get_list_content(key)
            existing_prompts = set(current_content)
            
            newly_added = [p for p in prompts_from_csv if p not in existing_prompts]

            if not newly_added:
                self.show_message.emit("Thông báo", "Không có prompt mới nào được thêm. Tất cả đã có trong danh sách."); return

            final_content = current_content + newly_added
            if self.save_list_to_file(key, final_content): 
                self.load_all_lists()
                self.update_stats()
                self.show_message.emit("Thành công", f"Đã import và thêm mới {len(newly_added)} prompt.")
            else: 
                self.show_message.emit("Lỗi", "Không thể lưu dữ liệu import.")
        except Exception as e: 
            self.show_message.emit("Lỗi Import", f"Đã xảy ra lỗi: {e}")

    def export_to_csv(self, file_path):
        if not self.current_folder or not self.current_list_name: self.show_message.emit("Chưa chọn danh sách", "Vui lòng chọn danh sách để export."); return
        key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
        current_list = self.get_list_content(key)
        if not current_list: self.show_message.emit("Danh sách rỗng", "Không có prompt để export."); return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for prompt in current_list: writer.writerow([prompt])
            self.show_message.emit("Thành công", f"Đã export {len(current_list)} prompt.")
        except Exception as e: self.show_message.emit("Lỗi Export", f"Đã xảy ra lỗi: {e}")

    def set_current_list(self, folder_path, list_name):
        if self.is_active: self.toggle_active_state(False)
        self.current_folder = folder_path
        self.current_list_name = list_name
        if folder_path and list_name:
            key = f"{os.path.basename(folder_path)}/{list_name}"
            list_states = self.settings.value("list_states", {})
            state = list_states.get(key, {}) if isinstance(list_states, dict) else {}
            self.current_prompt_index = max(0, state.get("index", 0))
        else:
            self.current_prompt_index = 0
        self.update_stats()

    def set_start_index(self, index):
        if not self.current_folder or not self.current_list_name: return
        key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
        if 0 <= index <= len(self.get_list_content(key)): self.current_prompt_index = index; self.save_state(); self.update_stats()
        else: self.show_message.emit("Lỗi", "Vị trí ghim không hợp lệ.")

    def reset_current_list_progress(self):
        if not self.current_folder or not self.current_list_name: self.show_message.emit("Lỗi", "Vui lòng chọn một danh sách."); return
        if self.is_active: self.toggle_active_state(False)
        self.current_prompt_index = 0; self.session_paste_count = 0
        self.save_state(); self.show_message.emit("Thành công", f"Đã reset tiến trình cho '{self.current_list_name}'.")
        self.update_stats(); self.progress_reset.emit(); self.load_all_lists()

    def update_stats(self):
        if self.current_folder and self.current_list_name:
            key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
            current_list = self.get_list_content(key)
            total = len(current_list)
            pasted = min(self.current_prompt_index, total)
            stats = { "total": total, "pasted": pasted, "session_pasted": self.session_paste_count }
            self.stats_updated.emit(stats)
            if self.is_active: self.update_mini_progress_signal.emit(pasted, total)
        else:
            self.stats_updated.emit({ "total": 0, "pasted": 0, "session_pasted": 0 })

    def get_list_state(self, key):
        if not key: return {"index": 0, "total": 0}
        list_states = self.settings.value("list_states", {})
        state = list_states.get(key, {"index": 0}) if isinstance(list_states, dict) else {"index": 0}
        total = len(self.get_list_content(key))
        return {"index": min(state.get("index", 0), total), "total": total}

    def log_activity(self, status):
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            key = "N/A"
            if self.current_folder and self.current_list_name:
                key = f"{os.path.basename(self.current_folder)}/{self.current_list_name}"
            
            entry = {
                "start_time": timestamp, "end_time": "", "list_key": key, 
                "paste_count": 0, "status": "Running"
            }

            if status == "start": 
                self.current_log_entry = entry
            else:
                if not hasattr(self, 'current_log_entry'): return
                self.current_log_entry.update({
                    "end_time": timestamp, 
                    "paste_count": self.session_paste_count, 
                    "status": "Finished" if status == "finished" else "Stopped"
                })
                logs = []
                if os.path.exists(self.log_file):
                    try:
                        with open(self.log_file, 'r', encoding='utf-8') as f: logs = json.load(f)
                    except (json.JSONDecodeError, Exception): logs = []
                if not isinstance(logs, list): logs = []
                logs.append(self.current_log_entry)
                with open(self.log_file, 'w', encoding='utf-8') as f: json.dump(logs, f, indent=4, ensure_ascii=False)
        except Exception as e: print(f"Lỗi ghi log: {e}")
