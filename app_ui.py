import re
import threading
import websocket
import requests
from tkinter import *
from tkinter import messagebox
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

        self.frame_system_buttons = Frame(self.master, pady=10)
        self.login_frame = Frame(self.master)
        self.register_frame = Frame(self.master)
        self.chat_frame = Frame(self.master)  # NEW

        self.create_widgets()


    '''Виджеты'''

    def create_widgets(self):

        self.frame_system_buttons.pack(fill=X)

        # Кнопка создать чат
        btn_create_chat = Button(self.frame_system_buttons, text="Создать чат", command=self.start_server_thread)
        btn_create_chat.pack(side=LEFT, padx=10)

        # Кнопка подключиться к чату
        btn_connect_chat = Button(self.frame_system_buttons, text='Подключиться к чату', command=self.connect_to_chat)
        btn_connect_chat.pack(side=LEFT, padx=10)

        # Кнопка авторизации
        btn_login = Button(self.frame_system_buttons, text='Авторизоваться', command=self.show_log_frame)
        btn_login.pack(side=LEFT, padx=10)

        # авторизация

        Label(self.login_frame, text='Имя пользователя:').pack()
        self.login_username = Entry(self.login_frame)
        self.login_username.pack()

        Label(self.login_frame, text='Пароль:').pack()
        self.login_password = Entry(self.login_frame, show='*')
        self.login_password.pack()

        Button(self.login_frame, text="Войти", command=self.login).pack()
        Button(self.login_frame, text="Зарегистрироваться", command=self.show_reg_frame).pack()
        Button(self.login_frame, text='Назад', command=self.show_general_frame).pack()

        # регистрация

        Label(self.register_frame, text="Имя пользователя:").pack()
        self.register_username = Entry(self.register_frame)
        self.register_username.pack()

        Label(self.register_frame, text="Пароль:").pack()
        self.register_password = Entry(self.register_frame, show="*")
        self.register_password.pack()

        Label(self.register_frame, text="Эл.Почта").pack()
        self.register_email = Entry(self.register_frame)
        self.register_email.pack()

        Button(self.register_frame, text='Зарегистрироваться', command=self.register).pack()
        Button(self.register_frame, text="Авторизоваться", command=self.show_log_frame).pack()
        Button(self.register_frame, text='Назад', command=self.show_general_frame).pack()

        # Окно чата
        self.text_box = Text(self.chat_frame, height=20, width=50)
        self.text_box.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(self.chat_frame, command=self.text_box.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.text_box.config(yscrollcommand=scrollbar.set, state=DISABLED)

        self.entry = Entry(self.chat_frame, width=50)
        self.entry.pack(padx=10, pady=5)

        send_button = Button(self.chat_frame, text="Отправить", command=self.send_message_to_server)
        send_button.pack(pady=5)

        back_button = Button(self.chat_frame, text='Выйти', command=self.stop_client)
        back_button.pack(pady=5)

    '''Сообщение о запуске сервера'''

    def custom_message_box_server_start(self):
        message_window = Toplevel(self.master)
        message_window.title('Сервер запущен')

        ip_message = self.server_instance.get_local_ip()

        msg_label = Label(message_window, text=f'Ваш сервер запущен! Теперь к вам в чат могут зайти\n'
                                               f'Ваш ip для подключения {ip_message}')
        msg_label.pack(padx=20, pady=20)

        def _copy_text():
            message_window.clipboard_clear()
            message_window.clipboard_append(ip_message)

        copy_btn = Button(message_window, text='Скопировать IP', command=_copy_text)
        copy_btn.pack(pady=10)

        close_button = Button(message_window, text="Закрыть", command=message_window.destroy)
        close_button.pack(pady=10)

        message_window.grab_set()
        message_window.wait_window()

    def check_ip_wrapper(self):
        ip = self.ent_ip.get()
        threading.Thread(target=self.check_ip, args=(ip,)).start()

    '''Проверка на корректность данных для подключения'''

    def check_ip(self, ip):
        ip_regex = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'  # ip
        if re.match(ip_regex, ip):
            try:
                messagebox.showinfo(title='Подключение', message='Подключаемся... Ожидайте')
                self.btn_complete['state'] = 'disable'
                ws = websocket.create_connection(f"ws://{ip}:8765")
                ws.close()
                self.master.after(0, lambda: self.on_success_check_ip(ip))
            except Exception:
                self.btn_complete['state'] = 'normal'
                self.master.after(0, lambda: self.on_error(
                    'Подключение не установлено, т.к. конечный компьютер отверг запрос на подключение'))
        else:
            self.master.after(0, lambda: self.on_error('Введите корректный ip адрес'))

    def on_error(self, message):
        messagebox.showerror(title='Ошибка', message=message)

    def on_success_check_ip(self, ip):
        self.start_client(ip)
        messagebox.showinfo(title='Успех', message=f'Вы подключились к {self.ent_ip.get()}')
        self.show_chat_frame()

    def connect_to_chat(self):
        self.stop_client()  # Останавливаем предыдущий клиент перед созданием нового
        self.message_window = Toplevel(self.master)
        self.message_window.title('Подключиться')

        msg_label = Label(self.message_window, text='Введите ip чтобы подключиться к чату')
        msg_label.pack(padx=20, pady=3)

        self.ent_ip = Entry(self.message_window, width=30)
        self.ent_ip.pack()

        self.btn_complete = Button(self.message_window, text='Подключиться', command=self.check_ip_wrapper)
        self.btn_complete.pack(pady=10)

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

            self.hide_all_frames()
            self.frame_system_buttons.pack(fill=X)

    '''Создания экземпляра клиента при подключении к серверу'''

    def start_client(self, ip):
        self.client_instance = Client(ip, app)
        self.client_instance.start_client_thread()

    def send_message_to_server(self):
        message = self.entry.get()
        if message.strip():  # Проверяем, что сообщение не пустое
            self.client_instance.send_message(message)
            self.entry.delete(0, END)

    def login(self):
        username = self.login_username.get()
        password = self.login_password.get()

        response = requests.post('http://localhost:5000/login', json={'username': username, 'password': password})

        if response.status_code == 200:
            messagebox.showinfo("Info", "Login successful")
            self.hide_all_frames()
            self.show_general_frame() # основное окно чата

        else:
            messagebox.showerror("Ошибка", 'Вы ввели неверные данные!')
    def register(self):
        username = self.register_username.get()
        password = self.register_password.get()
        mail = self.register_email.get()

        response = requests.post('http://localhost:5000/register', json={'username': username, 'password': password, 'mail': mail})

        if response.status_code == 200:
            messagebox.showinfo("Info", "Registration successful")
            self.hide_all_frames()
            self.show_log_frame()
        else:
            messagebox.showerror("Ошибка", 'Пользователь не был зарегистрирован. Проверьте корректность данных!')

    '''Сокрытие всех фреймов'''

    def hide_all_frames(self):
        self.frame_system_buttons.pack_forget()
        self.register_frame.pack_forget()
        self.login_frame.pack_forget()
        self.chat_frame.pack_forget()

    '''Окно авторизации'''

    def show_log_frame(self):
        self.hide_all_frames()
        self.login_frame.pack(fill='both', expand=True)

    '''Окно регистрации'''

    def show_reg_frame(self):
        self.hide_all_frames()
        self.register_frame.pack(fill='both', expand=True)

    '''Стартовое окно'''

    def show_general_frame(self):
        self.hide_all_frames()
        self.frame_system_buttons.pack(fill=X)

    '''Создания окна с текстовым полем чата'''

    def show_chat_frame(self):
        self.message_window.destroy()
        self.hide_all_frames()
        self.chat_frame.pack(fill=BOTH, expand=True)


if __name__ == "__main__":
    window = Tk()
    app = ChatApp(window)
    window.mainloop()
