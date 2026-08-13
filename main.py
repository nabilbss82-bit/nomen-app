import os
import random
import sqlite3
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager

# قاعدة البيانات المحدثة مع التوليد الذكي للكلمات
AI_GENERATIVE_POOL = {
    "Secondaria": [
        ("Amic", "izia", "الصداقة (اسم مشتق)"),
        ("Giorn", "ata", "اليوم / طوال اليوم"),
        ("Scritt", "ore", "كاتب / مؤلف"),
        ("Lavor", "atore", "عامل / شغول"),
        ("Felici", "tà", "السعادة (نواة اسمية)"),
        ("Bambin", "o", "طفل / صبي"),
    ],
    "Universitaria": [
        ("Cogn", "izione", "الإدراك والعمليات المعرفية"),
        ("Epistem", "ologia", "الإبستمولوجيا وفلسفة العلوم"),
        ("Glottodi", "attica", "الغلوتوديداكتيك وتعليمية اللغات"),
        ("Morfolog", "ia", "المورفولوجيا وعلم الصرف"),
        ("Sintatt", "ico", "تركيبعي / نحوي متقدم"),
        ("Neuroscienz", "a", "العلوم العصبية اللغوية"),
    ],
}


class DatabaseManager:

  @staticmethod
  def init_db():
    conn = sqlite3.connect("Nomen_AI_Database.db")
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS Logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_level TEXT,
                word TEXT,
                reaction_time_ms REAL,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()


class RoundedButton(Button):

  def __init__(self, **kwargs):
    super(RoundedButton, self).__init__(**kwargs)
    self.background_color = (0, 0, 0, 0)
    self.background_normal = ""
    self.bind(pos=self.update_canvas, size=self.update_canvas)

  def update_canvas(self, *args):
    self.canvas.before.clear()
    with self.canvas.before:
      Color(
          self.bg_color[0], self.bg_color[1], self.bg_color[2], self.bg_color[3]
      )
      self.rect = RoundedRectangle(
          pos=self.pos, size=self.size, radius=[15]
      )


class StartupScreen(Screen):

  def __init__(self, **kwargs):
    super(StartupScreen, self).__init__(**kwargs)
    layout = BoxLayout(orientation="vertical", padding=40, spacing=25)

    # الهوية والعنوان الرئيسي المخصص باسمك
    layout.add_widget(
        Label(
            text="PROGETTO NOMEN",
            font_size=26,
            bold=True,
            color=(0.12, 0.16, 0.22, 1),
            size_hint=(1, 0.15),
        )
    )
    layout.add_widget(
        Label(
            text="Ricercatore: Nabil Boussalem\nGlottodidattica & IA Adattiva",
            font_size=15,
            color=(0.25, 0.52, 0.96, 1),
            size_hint=(1, 0.15),
        )
    )

    layout.add_widget(
        Label(
            text="Seleziona il target accademico per la sessione:",
            font_size=14,
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(1, 0.1),
        )
    )

    # أزرار جذابة واحترافية
    btn_sec = RoundedButton(
        text="Scuola Secondaria", font_size=16, bg_color=(0.16, 0.5, 0.72, 1)
    )
    btn_sec.bind(on_press=lambda x: self.go_to_experiment("Secondaria"))
    layout.add_widget(btn_sec)

    btn_uni = RoundedButton(
        text="Università", font_size=16, bg_color=(0.55, 0.27, 0.67, 1)
    )
    btn_uni.bind(on_press=lambda x: self.go_to_experiment("Universitaria"))
    layout.add_widget(btn_uni)

    self.add_widget(layout)

  def go_to_experiment(self, level):
    app = App.get_running_app()
    app.user_level = level
    app.root.current = "experiment"
    app.experiment_screen.load_ai_stimulus()


class ExperimentScreen(Screen):

  def __init__(self, **kwargs):
    super(ExperimentScreen, self).__init__(**kwargs)
    self.start_time = 0.0
    self.current_root = ""
    self.current_suffix = ""

    layout = BoxLayout(orientation="vertical", padding=25, spacing=15)

    self.lbl_status = Label(
        text="Sessione Sperimentale - Nabil Boussalem",
        font_size=14,
        bold=True,
        color=(0.2, 0.2, 0.2, 1),
        size_hint=(1, 0.1),
    )
    layout.add_widget(self.lbl_status)

    # إطار الكلمة البصري الثنائي
    word_box = BoxLayout(
        orientation="horizontal", size_hint=(1, 0.35), spacing=5
    )
    self.lbl_root = Label(
        text="", font_size=34, bold=True, color=(0.12, 0.4, 0.7, 1)
    )
    self.lbl_suffix = Label(
        text="", font_size=34, bold=True, color=(0.3, 0.3, 0.3, 1)
    )
    word_box.add_widget(self.lbl_root)
    word_box.add_widget(self.lbl_suffix)
    layout.add_widget(word_box)

    self.lbl_trans = Label(
        text="", font_size=15, color=(0.5, 0.5, 0.5, 1), size_hint=(1, 0.1)
    )
    layout.add_widget(self.lbl_trans)

    # أزرار الاستجابة بتصميم أنيق
    btn_box = BoxLayout(
        orientation="horizontal", spacing=15, size_hint=(1, 0.2)
    )
    btn_fam = RoundedButton(
        text="Familiare\n(Veloce)", font_size=15, bg_color=(0.15, 0.68, 0.37, 1)
    )
    btn_fam.bind(on_press=lambda x: self.record_response("Familiare"))
    btn_box.add_widget(btn_fam)

    btn_diff = RoundedButton(
        text="Difficile\n(Sovraccarico)",
        font_size=15,
        bg_color=(0.75, 0.22, 0.16, 1),
    )
    btn_diff.bind(on_press=lambda x: self.record_response("Non familiare"))
    btn_box.add_widget(btn_diff)
    layout.add_widget(btn_box)

    self.lbl_ai = Label(
        text="IA Adattiva: In attesa di risposta...",
        font_size=13,
        italic=True,
        color=(0.09, 0.63, 0.52, 1),
        size_hint=(1, 0.1),
    )
    layout.add_widget(self.lbl_ai)

    btn_back = RoundedButton(
        text="← Torna al Menu", font_size=14, bg_color=(0.6, 0.6, 0.6, 1)
    )
    btn_back.bind(on_press=self.go_back)
    layout.add_widget(btn_back)

    self.add_widget(layout)

  def load_ai_stimulus(self):
    app = App.get_running_app()
    pool = AI_GENERATIVE_POOL.get(app.user_level, AI_GENERATIVE_POOL["Secondaria"])
    self.current_root, self.current_suffix, self.current_trans = random.choice(
        pool
    )

    self.lbl_root.text = self.current_root
    self.lbl_suffix.text = self.current_suffix
    self.lbl_trans.text = f"[{self.current_trans}]"
    self.start_time = time.perf_counter()

  def record_response(self, status):
    end_time = time.perf_counter()
    rt_ms = (end_time - self.start_time) * 1000
    word_combined = self.current_root + self.current_suffix
    app = App.get_running_app()

    conn = sqlite3.connect("Nomen_AI_Database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Logs (user_level, word, reaction_time_ms, status) VALUES"
        " (?, ?, ?, ?)",
        (app.user_level, word_combined, rt_ms, status),
    )
    conn.commit()
    conn.close()

    threshold = 1800 if app.user_level == "Universitaria" else 2200
    if rt_ms > threshold or status == "Non familiare":
      self.lbl_ai.text = (
          f"⚠️ IA: RT critica ({rt_ms:.1f}ms). Attivazione Ritirata Tattica."
      )
      self.lbl_ai.color = (0.9, 0.2, 0.2, 1)
    else:
      self.lbl_ai.text = f"✅ IA: Stabile - RT: {rt_ms:.1f}ms"
      self.lbl_ai.color = (0.1, 0.6, 0.5, 1)

    Clock.schedule_once(lambda dt: self.load_ai_stimulus(), 1.0)

  def go_back(self, instance):
    app = App.get_running_app()
    app.root.current = "startup"


class NomenAppUI(App):
  user_level = "Secondaria"

  def build(self):
    DatabaseManager.init_db()
    manager = ScreenManager()
    self.startup_screen = StartupScreen(name="startup")
    self.experiment_screen = ExperimentScreen(name="experiment")
    manager.add_widget(self.startup_screen)
    manager.add_widget(self.experiment_screen)
    return manager


if __name__ == "__main__":
  NomenAppUI().run()