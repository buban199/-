import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Функция для загрузки и обработки CSV
def load_and_process_csv(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8', delimiter=None)
        expected_columns = ["TIME", "Скорость автомобиля", "Число оборотов коленвала"]
        if not all(col in df.columns for col in expected_columns):
            messagebox.showerror("Ошибка", f"В файле отсутствуют нужные колонки. Найденные: {df.columns.tolist()}")
            return None
        df = df[expected_columns].apply(pd.to_numeric, errors='coerce')
        return df
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")
        return None

# Функция для расчета мощности и момента
def calculate_power_and_torque(df, mass, Cd, A, Crr, transmission_loss, power_correction_factor, torque_correction_factor):
    g = 9.81
    air_density = 1.225

    df["Скорость м/с"] = df["Скорость автомобиля"] * 1000 / 3600
    df["Ускорение м/с²"] = df["Скорость м/с"].diff() / df["TIME"].diff()
    df["Ускорение м/с²"] = df["Ускорение м/с²"].fillna(0)

    df["Сопротивление воздуха Н"] = 0.5 * air_density * Cd * A * df["Скорость м/с"] ** 2
    df["Сопротивление качению Н"] = mass * g * Crr
    df["Инерционная сила Н"] = mass * df["Ускорение м/с²"]
    df["Сила тяги Н"] = df["Сопротивление воздуха Н"] + df["Сопротивление качению Н"] + df["Инерционная сила Н"]

    df["Мощность Вт"] = df["Сила тяги Н"] * df["Скорость м/с"]
    df["Мощность л.с."] = df["Мощность Вт"] / 735.5
    df["Мощность л.с. на маховике"] = df["Мощность л.с."] / (1 - transmission_loss)
    df["Мощность л.с. на маховике"] *= power_correction_factor
    df["Мощность кВт на маховике"] = df["Мощность л.с. на маховике"] * 0.7355
    df["Крутящий момент Н·м"] = (df["Мощность кВт на маховике"] * 9550) / df["Число оборотов коленвала"]
    df["Крутящий момент Н·м"] *= torque_correction_factor

    return df

# Функция для построения графика в отдельном окне
def plot_results(df1, df2, plot_type, name1, name2):
    if df1 is None and df2 is None:
        return

    # Создаем новое окно для графика
    plot_window = tk.Toplevel()
    plot_window.title("График мощности и крутящего момента")
    plot_window.geometry("800x600")

    # Создаем фигуру и оси
    fig, ax = plt.subplots(figsize=(8, 6))

    # Построение первого графика
    if df1 is not None and plot_type in ["first", "both"]:
        df1 = df1.sort_values(by="Число оборотов коленвала")
        power_smoothed1 = gaussian_filter1d(df1["Мощность л.с. на маховике"], sigma=4)
        torque_smoothed1 = gaussian_filter1d(df1["Крутящий момент Н·м"], sigma=4)

        ax.plot(df1["Число оборотов коленвала"], power_smoothed1, label=f"Мощность (л.с.) - {name1}", color='blue')
        ax.plot(df1["Число оборотов коленвала"], torque_smoothed1, label=f"Крутящий момент (Н·м) - {name1}", color='red')

        # Находим пиковые значения для первого графика
        max_power_idx1 = np.argmax(power_smoothed1)
        max_power1 = power_smoothed1[max_power_idx1]
        max_power_rpm1 = df1["Число оборотов коленвала"].iloc[max_power_idx1]
        ax.plot(max_power_rpm1, max_power1, 'bo')  # Точка на графике

        max_torque_idx1 = np.argmax(torque_smoothed1)
        max_torque1 = torque_smoothed1[max_torque_idx1]
        max_torque_rpm1 = df1["Число оборотов коленвала"].iloc[max_torque_idx1]
        ax.plot(max_torque_rpm1, max_torque1, 'ro')  # Точка на графике

        # Добавляем плашку с пиковыми значениями для первого графика
        ax.text(0.02, 0.98, f"{name1}\nМакс. мощность: {max_power1:.2f} л.с. @ {max_power_rpm1:.0f} об/мин\nМакс. момент: {max_torque1:.2f} Н·м @ {max_torque_rpm1:.0f} об/мин",
                transform=ax.transAxes, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

    # Построение второго графика
    if df2 is not None and plot_type in ["second", "both"]:
        df2 = df2.sort_values(by="Число оборотов коленвала")
        power_smoothed2 = gaussian_filter1d(df2["Мощность л.с. на маховике"], sigma=4)
        torque_smoothed2 = gaussian_filter1d(df2["Крутящий момент Н·м"], sigma=4)

        ax.plot(df2["Число оборотов коленвала"], power_smoothed2, label=f"Мощность (л.с.) - {name2}", color='blue', linestyle='--')
        ax.plot(df2["Число оборотов коленвала"], torque_smoothed2, label=f"Крутящий момент (Н·м) - {name2}", color='red', linestyle='--')

        # Находим пиковые значения для второго графика
        max_power_idx2 = np.argmax(power_smoothed2)
        max_power2 = power_smoothed2[max_power_idx2]
        max_power_rpm2 = df2["Число оборотов коленвала"].iloc[max_power_idx2]
        ax.plot(max_power_rpm2, max_power2, 'bo')  # Точка на графике

        max_torque_idx2 = np.argmax(torque_smoothed2)
        max_torque2 = torque_smoothed2[max_torque_idx2]
        max_torque_rpm2 = df2["Число оборотов коленвала"].iloc[max_torque_idx2]
        ax.plot(max_torque_rpm2, max_torque2, 'ro')  # Точка на графике

        # Добавляем плашку с пиковыми значениями для второго графика
        ax.text(0.02, 0.88, f"{name2}\nМакс. мощность: {max_power2:.2f} л.с. @ {max_power_rpm2:.0f} об/мин\nМакс. момент: {max_torque2:.2f} Н·м @ {max_torque_rpm2:.0f} об/мин",
                transform=ax.transAxes, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

    # Настройка графика
    ax.set_xlabel("Обороты двигателя (об/мин)")
    ax.set_ylabel("Значение")
    ax.legend()
    ax.set_title("График мощности и крутящего момента на маховике")
    ax.grid(True)

    # Встраиваем график в окно Tkinter
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Кнопка для сохранения графика
    save_button = tk.Button(plot_window, text="Сохранить график", command=lambda: save_plot(fig))
    save_button.pack(side=tk.BOTTOM, pady=10)

# Функция для сохранения графика
def save_plot(fig):
    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if file_path:
        fig.savefig(file_path)
        messagebox.showinfo("Успех", f"График сохранен в {file_path}")

# Основное окно приложения
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчет мощности и момента")
        self.root.geometry("1200x600")

        # Переменные для ввода данных (первый график)
        self.file_path1 = tk.StringVar()
        self.mass1 = tk.DoubleVar(value=1500)
        self.Cd1 = tk.DoubleVar(value=0.3)
        self.A1 = tk.DoubleVar(value=2.2)
        self.Crr1 = tk.DoubleVar(value=0.01)
        self.transmission_loss1 = tk.DoubleVar(value=0.1)
        self.power_correction_factor1 = tk.DoubleVar(value=1.0)
        self.torque_correction_factor1 = tk.DoubleVar(value=1.0)
        self.name1 = tk.StringVar(value="График 1")

        # Переменные для ввода данных (второй график)
        self.file_path2 = tk.StringVar()
        self.mass2 = tk.DoubleVar(value=1500)
        self.Cd2 = tk.DoubleVar(value=0.3)
        self.A2 = tk.DoubleVar(value=2.2)
        self.Crr2 = tk.DoubleVar(value=0.01)
        self.transmission_loss2 = tk.DoubleVar(value=0.1)
        self.power_correction_factor2 = tk.DoubleVar(value=1.0)
        self.torque_correction_factor2 = tk.DoubleVar(value=1.0)
        self.name2 = tk.StringVar(value="График 2")

        self.plot_type = tk.StringVar(value="both")  # Тип графика: first, second, both

        # Элементы интерфейса (первый график)
        tk.Label(root, text="Первый график", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=10)
        tk.Label(root, text="Путь к CSV-файлу:").grid(row=1, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.file_path1, width=30).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(root, text="Загрузить CSV", command=lambda: self.load_csv(self.file_path1)).grid(row=1, column=2, padx=10, pady=10)

        tk.Label(root, text="Масса автомобиля (кг):").grid(row=2, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.mass1).grid(row=2, column=1, padx=10, pady=10)

        tk.Label(root, text="Коэффициент аэродинамического сопротивления (Cd):").grid(row=3, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.Cd1).grid(row=3, column=1, padx=10, pady=10)

        tk.Label(root, text="Лобовая площадь (м²):").grid(row=4, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.A1).grid(row=4, column=1, padx=10, pady=10)

        tk.Label(root, text="Коэффициент сопротивления качению (Crr):").grid(row=5, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.Crr1).grid(row=5, column=1, padx=10, pady=10)

        tk.Label(root, text="Потери в трансмиссии (доля):").grid(row=6, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.transmission_loss1).grid(row=6, column=1, padx=10, pady=10)

        tk.Label(root, text="Коэффициент коррекции мощности:").grid(row=7, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.power_correction_factor1).grid(row=7, column=1, padx=10, pady=10)

        tk.Label(root, text="Коэффициент коррекции момента:").grid(row=8, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.torque_correction_factor1).grid(row=8, column=1, padx=10, pady=10)

        tk.Label(root, text="Имя графика:").grid(row=9, column=0, padx=10, pady=10)
        tk.Entry(root, textvariable=self.name1).grid(row=9, column=1, padx=10, pady=10)

        # Элементы интерфейса (второй график)
        tk.Label(root, text="Второй график", font=("Arial", 12, "bold")).grid(row=0, column=3, columnspan=3, pady=10)
        tk.Label(root, text="Путь к CSV-файлу:").grid(row=1, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.file_path2, width=30).grid(row=1, column=4, padx=10, pady=10)
        tk.Button(root, text="Загрузить CSV", command=lambda: self.load_csv(self.file_path2)).grid(row=1, column=5, padx=10, pady=10)

        tk.Label(root, text="Масса автомобиля (кг):").grid(row=2, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.mass2).grid(row=2, column=4, padx=10, pady=10)

        tk.Label(root, text="Коэффициент аэродинамического сопротивления (Cd):").grid(row=3, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.Cd2).grid(row=3, column=4, padx=10, pady=10)

        tk.Label(root, text="Лобовая площадь (м²):").grid(row=4, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.A2).grid(row=4, column=4, padx=10, pady=10)

        tk.Label(root, text="Коэффициент сопротивления качению (Crr):").grid(row=5, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.Crr2).grid(row=5, column=4, padx=10, pady=10)

        tk.Label(root, text="Потери в трансмиссии (доля):").grid(row=6, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.transmission_loss2).grid(row=6, column=4, padx=10, pady=10)

        tk.Label(root, text="Коэффициент коррекции мощности:").grid(row=7, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.power_correction_factor2).grid(row=7, column=4, padx=10, pady=10)

        tk.Label(root, text="Коэффициент коррекции момента:").grid(row=8, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.torque_correction_factor2).grid(row=8, column=4, padx=10, pady=10)

        tk.Label(root, text="Имя графика:").grid(row=9, column=3, padx=10, pady=10)
        tk.Entry(root, textvariable=self.name2).grid(row=9, column=4, padx=10, pady=10)

        # Выбор типа графика
        tk.Label(root, text="Тип графика:").grid(row=10, column=0, padx=10, pady=10)
        tk.Radiobutton(root, text="Первый", variable=self.plot_type, value="first").grid(row=10, column=1, padx=10, pady=10)
        tk.Radiobutton(root, text="Второй", variable=self.plot_type, value="second").grid(row=10, column=2, padx=10, pady=10)
        tk.Radiobutton(root, text="Оба", variable=self.plot_type, value="both").grid(row=10, column=3, padx=10, pady=10)

        # Кнопка для построения графика
        tk.Button(root, text="Построить график", command=self.plot).grid(row=11, column=0, columnspan=6, padx=10, pady=10)

    # Загрузка CSV
    def load_csv(self, file_path_var):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            file_path_var.set(file_path)

    # Построение графика
    def plot(self):
        df1 = load_and_process_csv(self.file_path1.get())
        df2 = load_and_process_csv(self.file_path2.get())

        if df1 is not None:
            df1 = calculate_power_and_torque(
                df1,
                self.mass1.get(),
                self.Cd1.get(),
                self.A1.get(),
                self.Crr1.get(),
                self.transmission_loss1.get(),
                self.power_correction_factor1.get(),
                self.torque_correction_factor1.get()
            )

        if df2 is not None:
            df2 = calculate_power_and_torque(
                df2,
                self.mass2.get(),
                self.Cd2.get(),
                self.A2.get(),
                self.Crr2.get(),
                self.transmission_loss2.get(),
                self.power_correction_factor2.get(),
                self.torque_correction_factor2.get()
            )

        plot_results(df1, df2, self.plot_type.get(), self.name1.get(), self.name2.get())

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()