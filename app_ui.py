import re
from tkinter import *
from tkinter import messagebox
import threading

from client import Client
from server import Server


class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title('Чат')
        self.master.geometry('640x720')

        self.server_instance = None
        self.client_instance = None
        self.server_thread = None

        self.create_widgets()

    def create_widgets(self):
        frame_system_buttons = Frame(self.master, pady=10)
        frame_system_buttons.pack(fill=X)

        # Кнопка создать чат
        btn_create_chat = Button(frame_system_buttons, text="Создать чат", command=self.start_server_thread)
        btn_create_chat.pack(side=LEFT, padx=10)

        # Кнопка выйти из чата
        btn_close_connection = Button(self.master, text='Выйти', command=self.stop_client)
        btn_close_connection.pack(side=LEFT, padx=10)

        # Кнопка подключиться к чату
        btn_connect_chat = Button(frame_system_buttons, text='Подключиться к чату', command=self.connect_to_chat)
        btn_connect_chat.pack(side=LEFT, padx=10)

    def custom_message_box_server_start(self):
        message_window = Toplevel(self.master)
        message_window.title('Сервер запущен')

        ip_message = self.server_instance.get_local_ip()

        msg_label = Label(message_window, text=f'Ваш сервер запущен! Теперь к вам в чат могут зайти\n'
                                               f'Ваш ip для подключения {ip_message}')
        msg_label.pack(padx=20, pady=20)

        def copy_text():
            message_window.clipboard_clear()
            message_window.clipboard_append(ip_message)

        copy_btn = Button(message_window, text='Скопировать IP', command=copy_text)
        copy_btn.pack(pady=10)

        close_button = Button(message_window, text="Закрыть", command=message_window.destroy)
        close_button.pack(pady=10)

        message_window.grab_set()
        message_window.wait_window()

    ''' '''

    def create_chat_window(self):

        self.chat_window = Toplevel(self.master)
        self.chat_window.title('Диалог')
        self.chat_window.geometry('640x720')
        self.message_window.destroy()

        text_frame = Frame(self.chat_window)
        text_frame.pack(padx=10, pady=10)

        self.text_box = Text(text_frame, height=20, width=50)
        self.text_box.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(text_frame, command=self.text_box.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.text_box.config(yscrollcommand=scrollbar.set, state=DISABLED)

        self.entry = Entry(self.chat_window, width=50)
        self.entry.pack(padx=10, pady=5)

        send_button = Button(self.chat_window, text="Отправить", command=self.send_message_to_server)
        send_button.pack(pady=5)

        back_button = Button(self.chat_window, text='Выйти', command=self.stop_client)
        back_button.pack(pady=5)

    def check_ip(ip):  # TODO добавить в использование перед btn_complete
        ip_regex = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        # соответствует ли строка IP
        if re.match(ip_regex, ip):
            return True
        else:
            return False

    def connect_to_chat(self):
        self.stop_client()  # Останавливаем предыдущий клиент перед созданием нового
        self.message_window = Toplevel(self.master)
        self.message_window.title('Подключиться')

        msg_label = Label(self.message_window, text='Введите ip чтобы подключиться к чату')
        msg_label.pack(padx=20, pady=3)

        ent_ip = Entry(self.message_window, width=30)
        ent_ip.pack()

        btn_complete = Button(self.message_window, text='Подключиться',  # create_chat_window
                              command=lambda: [self.master.after(0, self.start_client, ent_ip.get()),
                                               messagebox.showinfo(title='Успех',
                                                                   message=f'Вы подключились к {ent_ip.get()}'),
                                               self.create_chat_window()])

        btn_complete.pack(pady=10)
        btn_complete.pack(pady=10)

        self.message_window.grab_set()
        self.message_window.wait_window()

    '''Обновление окна чата'''

    def update_chat_window(self, message):
        self.text_box.config(state=NORMAL)  # редактирование текстового поля
        self.text_box.insert(END, message + '\n')  # Добавляем сообщение в конец
        self.text_box.config(state=DISABLED)  # Запрещаем редактирование

    '''Старт и стоп работы сервера'''

    def start_server_thread(self):
        if self.server_thread and self.server_thread.is_alive():
            messagebox.showerror(title='Сервер уже запущен',
                                 message=f'Ваш сервер уже запущен на ip {self.server_instance.get_local_ip()}')
        else:
            self.server_instance = Server(app)
            self.server_thread = threading.Thread(target=self.server_instance.run_server)
            self.server_thread.start()
            if self.server_instance.server_started.wait(timeout=10):
                print(f'Ваш сервер запущен на ip {self.server_instance.get_local_ip()}')
                self.custom_message_box_server_start()

                self.btn_stop_chat = Button(self.master, text='Остановить', command=self.stop_server)
                self.btn_stop_chat.pack(side=LEFT, padx=10)

    def stop_server(self):
        if self.server_thread and self.server_thread.is_alive():
            self.server_instance.stop_server()
            self.server_thread.join()
            messagebox.showinfo(title='Сервер был остановлен', message='Сервер был остановлен на вашем ip')
            self.btn_stop_chat.destroy()
            print('Сервер был остановлен')

    '''Выход из чата'''

    def stop_client(self):
        if self.client_instance:
            self.client_instance.stop_client_thread()
            self.client_instance = None  # Сбрасываем ссылку на экземпляр клиента
            self.chat_window.destroy()

    def start_client(self, ip):
        self.client_instance = Client(ip, app)
        self.client_instance.start_client_thread()

    def send_message_to_server(self):
        message = self.entry.get()
        if message.strip():  # Проверяем, что сообщение не пустое
            self.client_instance.send_message(message)
            self.entry.delete(0, END)


if __name__ == "__main__":
    window = Tk()
    app = ChatApp(window)
    window.mainloop()
