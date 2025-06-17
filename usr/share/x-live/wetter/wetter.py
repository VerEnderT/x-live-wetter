#!/usr/bin/python3

import about 
import xupdates
import sys, os, json, requests, locale
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox, QInputDialog,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDesktopWidget 
)
from PyQt5.QtGui import QIcon, QPixmap

from PyQt5.QtCore import QTimer, QSize, Qt, QProcess


CONFIG_DIR = os.path.expanduser("~/.config/x-live/wetter_tray")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
AUTOSTART_FILE = os.path.expanduser("~/.config/autostart/wetter_tray.desktop")

# Pfad zum gewünschten Arbeitsverzeichnis # Das Arbeitsverzeichnis festlegen
arbeitsverzeichnis = os.path.expanduser('/usr/share/x-live/wetter')

os.chdir(arbeitsverzeichnis)


class WeatherTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        QApplication.setQuitOnLastWindowClosed(False) 
        self.process = None
        self.app_name = "x-live-wetter"
        self.day_win = None
        self.tray = QSystemTrayIcon()
        self.buttonStyle="""    QPushButton {
                                    border: none;
                                    background-color: transparent;
                                    padding: 0px;
                                    /*color: inherit;   Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                }
                                QPushButton:hover {
                                    background-color: transparent;
                                }
                                QPushButton:pressed {
                                    background-color: transparent;
                                }
                            """
        self.buttonStyleDay="""    QPushButton {
                                    border: none;
                                    background-color: transparent;
                                    padding: 0px;
                                    /*color: inherit;   Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                }
                                QPushButton:hover {
                                    border-radius: 5px;
                                    background-color: #50a0a0a0;
                                }
                                QPushButton:pressed {
                                    background-color: transparent;
                                }
                            """
        self.buttonTitleStyle="""QPushButton {
                                    border: none;
                                    background-color: transparent;
                                    padding: 0px;
                                    /*color: inherit;   Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                    font-size: 45px;
                                }
                                QPushButton:hover {
                                    background-color: transparent;
                                }
                                QPushButton:pressed {
                                    background-color: transparent;
                                }
                            """
        self.buttonTitleStyle1="""QPushButton {
                                    border: none;
                                    background-color: transparent;
                                    padding: 0px;
                                    /*color: inherit;   Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                    font-size: 25px;
                                }
                                QPushButton:hover {
                                    background-color: transparent;
                                }
                                QPushButton:pressed {
                                    background-color: transparent;
                                }
                            """

        self.buttonStyle1="""   QPushButton {
                                    border: 3px;
                                    border-radius: 5px;
                                    background-color: black;
                                    padding: 0px;
                                    color: white;  /* Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                }
                                QPushButton:hover {
                                    background-color: grey;
                                }
                                QPushButton:pressed {
                                    background-color: yellow;
                                    color: black; 
                                }
                            """
        self.buttonStyle2="""   QPushButton {
                                    border: 3px;
                                    border-radius: 5px;
                                    background-color: green;
                                    padding: 0px;
                                    color: white;  /* Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                }
                                QPushButton:hover {
                                    background-color: grey;
                                }
                                QPushButton:pressed {
                                    background-color: yellow;
                                    color: black; 
                                }
                            """
        self.Style1="""         QWidget {
                                    border: none;
                                    background-color: #11334455;
                                    padding: 0px;
                                    color: white;  /* Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                    
                                }
                                QPushButton {
                                    border: none;
                                    background-color: transparent;
                                    padding: 0px;
                                    color: white;  /* Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                }
                                QPushButton:hover {
                                    background-color: transparent;
                                }
                                QPushButton:pressed {
                                    background-color: transparent;
                                }
                                QLabel {
                                    border: none;
                                    background-color: transparent;
                                    padding: 0px;
                                    color: white;  /* Optional: Textfarbe */
                                    font: inherit; /* Optional: Schrift vom Eltern-Widget übernehmen */
                                }
                            """
        self.load_config()

        self.menu = QMenu()
        self.autostart_action = QAction("Autostart aktivieren" if not self.autostart_enabled() else "Autostart deaktivieren")
        self.autostart_action.triggered.connect(self.toggle_autostart)
        self.menu.addAction(self.autostart_action)

        change_location = QAction("Ort ändern")
        change_location.triggered.connect(self.change_location)
        self.menu.addAction(change_location)
        
        
        self.update_action = QAction("Update verfügbar !!")
        self.update_action.triggered.connect(self.start_updating)
        self.menu.addAction(self.update_action)
        self.update_action.setVisible(False)  # Versteckt die Aktion im Menü


        quit_action = QAction("Beenden")
        quit_action.triggered.connect(self.app.quit)
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.icon_clicked)

        self.tray.setToolTip("Wetter wird geladen...")
        self.update_weather()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_weather)
        self.timer.start(60 * 60 * 1000)  # jede Stunde

        self.tray.setVisible(True)
        self.weather_win = None
        self.check_updates()
        sys.exit(self.app.exec_())

    # {"location": "Berlin", "lat": 52.52437, "lon": 13.41053}
    def load_config(self):
        self.location = "Berlin"
        self.lat = 52.52437
        self.lon = 13.41053
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                self.location = data.get("location", "Berlin")
                self.lat = data.get("lat", 52.52437)
                self.lon = data.get("lon", 13.41053)
        else:
            self.save_config()

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"location": self.location, "lat": self.lat, "lon": self.lon}, f)

    def autostart_enabled(self):
        return os.path.exists(AUTOSTART_FILE)

    def toggle_autostart(self):
        if self.autostart_enabled():
            os.remove(AUTOSTART_FILE)
            self.autostart_action.setText("Autostart aktivieren")
        else:
            with open(AUTOSTART_FILE, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Exec=python3 {os.path.abspath(__file__)}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=WetterTray
Comment=Wetter Tray App
""")
            self.autostart_action.setText("Autostart deaktivieren")

    def get_icon_for_code(self, code):
        icon_name = self.get_icon_name_for_code(code)
        icon_path = os.path.join("icons", icon_name)
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            return QIcon.fromTheme("weather-clear")  # Fallback

    def get_coordinates(self, location):
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=de&format=json"
        r = requests.get(url).json()
        if r.get("results"):
            result = r["results"][0]
            return result["latitude"], result["longitude"], result["name"]
        return None, None, None

    def get_weather_description(self, code):
        codes = {
            0: "Klar", 1: "Überwiegend klar", 2: "Teilweise bewölkt", 3: "Bewölkt",
            45: "Nebel", 48: "Nebel mit Reif", 51: "Leichter Nieselregen", 53: "Mäßiger Nieselregen",
            55: "Starker Nieselregen", 61: "Leichter Regen", 63: "Mäßiger Regen", 65: "Starker Regen",
            66: "Gefrierender Regen", 67: "Starker gefr. Regen", 71: "Leichter Schneefall", 73: "Mäßiger Schneefall",
            75: "Starker Schneefall", 77: "Schneekörner", 80: "Leichter Regenschauer", 81: "Regenschauer",
            82: "Starker Regenschauer", 85: "Leichte Schneeschauer", 86: "Starke Schneeschauer",
            95: "Gewitter", 96: "Gewitter mit leichtem Hagel", 99: "Gewitter mit starkem Hagel"
        }
        return codes.get(code, "Unbekannt")

    def get_icon_name_for_code(self, code):
        code_map = {
            0: "Sun.png",                        # Klar
            1: "PartlySunny.png",                # Überwiegend klar
            2: "Cloud.png",                      # Teilweise bewölkt
            3: "Cloud.png",                      # Bewölkt
            45: "Haze.png",                      # Nebel
            48: "Haze.png",                      # Reif-Nebel
            51: "Rain.png",                      # leichter Niesel
            53: "Rain.png",                      # mäßiger Niesel
            55: "Rain.png",                      # dichter Niesel
            56: "Rain.png",                      # leichter gefrierender Niesel
            57: "Rain.png",                      # dichter gefrierender Niesel
            61: "Rain.png",                      # leichter Regen
            63: "Rain.png",                      # mäßiger Regen
            65: "Rain.png",                      # starker Regen
            66: "Hail.png",                      # leichter gefrierender Regen
            67: "Hail.png",                      # starker gefrierender Regen
            71: "Snow.png",                      # leichter Schnee
            73: "Snow.png",                      # mäßiger Schnee
            75: "Snow.png",                      # starker Schneefall
            77: "Snow.png",                      # Schneekörner
            80: "Rain.png",                      # leichter Schauer
            81: "Rain.png",                      # mäßiger Schauer
            82: "Rain.png",                      # heftiger Schauer
            85: "Snow.png",                      # leichter Schneeschauer
            86: "Snow.png",                      # starker Schneeschauer
            95: "Storm.png",                     # Gewitter
            96: "Storm.png",                     # Gewitter mit leichtem Hagel
            99: "Storm.png",                     # Gewitter mit starkem Hagel
        }
        return code_map.get(code, "Sun.png")  # Fallback ist Sonne


    def update_weather(self):
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}"
            f"&current_weather=true&hourly=temperature_2m,weathercode&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&timezone=Europe%2FBerlin"
        )
        #print(url)
        try:
            r = requests.get(url).json()
            current = r["current_weather"]
            self.current_weather = {
                "temp": current["temperature"],
                "wind": current["windspeed"],
                "desc": self.get_weather_description(current["weathercode"]),
                "time": current["time"],
                "code": current["weathercode"]
            }
            self.hourly = r["hourly"]
            self.daily = r["daily"]
            #print(self.current_weather["code"])
            #print(self.get_icon_for_code(self.current_weather["code"]))
            self.tray.setIcon(self.get_icon_for_code(self.current_weather["code"]))

            tooltip = f"️🏠 {self.location} "
            tooltip += f"🌡️ {self.current_weather['temp']} °C\n"
            #tooltip += f"🪁 {self.current_weather['wind']} km/h \n"
            tooltip += f"🌤️ {self.current_weather['desc']}"

            self.tray.setToolTip(tooltip)
        except Exception as e:
            self.tray.setToolTip("Fehler beim Abrufen des Wetters")



    def icon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_weather_window()
        

    def weekday(self, datum_str):
        #print(datum_str)
        try:
            # Deutsches Locale für Wochentag-Namen setzen
            locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
            
            # Datum im Format yy-mm-dd einlesen
            dt = datetime.strptime(datum_str, "%Y-%m-%d")
            
            # Wochentag als deutscher Name
            return dt.strftime("%A")
        
        except ValueError:
            return "Ungültiges Datum"




    def show_weather_window(self):
        if self.weather_win == None:
            self.show_weather_window_new()
        else:
            self.weather_win.close()
            self.weather_win = None
            if self.day_win != None:
                self.day_win.close()
        
        
    def show_weather_window_new(self):
        self.weather_win = QWidget()
        self.weather_win.setStyleSheet(self.Style1)
        self.weather_win.setWindowTitle(f"Wetter für {self.location}")
        
        
        # Hintergrundbild-Label
        self.background = QLabel(self.weather_win)
        self.background.setPixmap(QPixmap("hintergrund.jpg").scaled(self.weather_win.size()))
        self.background.setScaledContents(True)  # <-- Wichtig!
        self.background.setGeometry(0, 0, 900, 600)
        self.background.move(0,0)
        self.background.lower()  # Nach ganz hinten

        layout = QVBoxLayout()
        #browser = QTextBrowser()
        date_time = self.current_weather['time'].split("T")
        date = date_time[0].split("-")
        text = f"<h5>Aktuell {date[2]}.{date[1]}.{date[0]} um {date_time[1]} Uhr</h5><br>"
        hourNow = int(date_time[1].split(":")[0])
        titleLabel=QLabel(text)
        layout.addWidget(titleLabel)
        
        weatherNowLayout=QHBoxLayout()
        weatherNowLayout.addStretch(3)
        text = f"️🏠 {self.location}"
        #text += f"Breitengrad: {self.lat}  "
        #text += f"Längengrad: {self.lon}"
        weatherNowLocation=QPushButton(text)
        weatherNowLocation.setStyleSheet(self.buttonTitleStyle)
        weatherNowLayout.addWidget(weatherNowLocation, alignment=Qt.AlignCenter)
        
        weatherNowLayout.addStretch(2)
        
        weatherNowIcon=QPushButton()
        weatherNowIcon.setIconSize(QSize(100, 100))
        weatherNowIcon.setFixedWidth(110)
        weatherNowIcon.setStyleSheet(self.buttonStyle)
        weatherNowIcon.setIcon(self.get_icon_for_code(self.current_weather["code"]))
        self.weather_win.setWindowIcon(self.get_icon_for_code(self.current_weather["code"]))
        weatherNowLayout.addWidget(weatherNowIcon, alignment=Qt.AlignCenter)
        
        weatherNowLayout.addStretch(2)
        
        text = f"🌡️ {self.current_weather['temp']} °C    "
        text += f"🪁 {self.current_weather['wind']} km/h\n"
        text += f"🌤️ {self.current_weather['desc']}"
        weatherNowText = QPushButton(text)
        weatherNowText.setStyleSheet(self.buttonTitleStyle1)
        
        weatherNowLayout.addWidget(weatherNowText, alignment=Qt.AlignCenter)
        weatherNowLayout.addStretch(3)
        
        layout.addLayout(weatherNowLayout)
        
        text = "<h3>⏳ Stündliche Vorhersage</h3><ul>"
        titleHourly=QLabel(text)
        titleHourlyLayout = QHBoxLayout()
        titleHourlyLayout.addWidget(titleHourly)
        titleHourlyLayout.addStretch(20)
        todayHourlyAll= QPushButton("Kompletter Tag")
        todayHourlyAll.clicked.connect(lambda: self.day_hour_temp(0))
        todayHourlyAll.setStyleSheet(self.buttonStyleDay)
        titleHourlyLayout.addWidget(todayHourlyAll)
        titleHourlyLayout.addStretch(1)
        layout.addLayout(titleHourlyLayout)
        text = ""
        hourlyLayout = QHBoxLayout()
        for t in range(6):
            i = t + 1 + hourNow
            hourlyLayoutDay = QVBoxLayout()
            time = self.hourly["time"][i].split("T")[1]
            temp = self.hourly["temperature_2m"][i]
            code = self.hourly["weathercode"][i]
            hourlyDayTime = QPushButton(time)
            hourlyDayTime.setStyleSheet(self.buttonStyle)
            hourlyLayoutDay.addWidget(hourlyDayTime, alignment=Qt.AlignCenter)
            
            hourlyDayCode = QPushButton()
            hourlyDayCode.setIconSize(QSize(50, 50))
            hourlyDayCode.setFixedWidth(60)
            hourlyDayCode.setStyleSheet(self.buttonStyle)
            hourlyDayCode.setIcon(self.get_icon_for_code(code))
            hourlyLayoutDay.addWidget(hourlyDayCode, alignment=Qt.AlignCenter)
            
            
            hourlyDayDesc=QPushButton(f"{temp} °C \n{self.get_weather_description(code)}\n")
            hourlyDayDesc.setStyleSheet(self.buttonStyle)
            hourlyDayDesc.setFixedWidth(150)
            
            hourlyLayoutDay.addWidget(hourlyDayDesc, alignment=Qt.AlignCenter)
            hourlyLayout.addLayout(hourlyLayoutDay)
            
        layout.addLayout(hourlyLayout)

        
        text = "<h3>📅📅 5-tage vorhersage</h3><ul>"
        titleDayly=QLabel(text)
        layout.addWidget(titleDayly)
        
        text = ""
        daylyLayout = QHBoxLayout()
        for t in range(5):
            i = t + 1
            daylyLayoutDay = QVBoxLayout()
            date_raw = self.daily["time"][i].split("-")
            date=date_raw[2]+"."+date_raw[1]+"."
            tmax = self.daily["temperature_2m_max"][i]
            tmin = self.daily["temperature_2m_min"][i]
            code = self.daily["weathercode"][i]
            if i == 0:
                date=f"Heute\n {date}"
            elif i == 1:
                date=f"Morgen\n {date}"
            else:
                date=self.weekday(self.daily["time"][i])+f"\n {date}"     


            daylyDayTime = QPushButton(date)
            daylyDayTime.setStyleSheet(self.buttonStyle)
            daylyLayoutDay.addWidget(daylyDayTime, alignment=Qt.AlignCenter)
            
            daylyDayCode = QPushButton()
            daylyDayCode.setIconSize(QSize(50, 50))
            daylyDayCode.setFixedWidth(60)
            daylyDayCode.setStyleSheet(self.buttonStyleDay)
            daylyDayCode.setIcon(self.get_icon_for_code(code))
            daylyDayCode.clicked.connect(lambda checked, x=i: self.day_hour_temp(x))
            daylyLayoutDay.addWidget(daylyDayCode, alignment=Qt.AlignCenter)
            
            
            daylyDayDesc=QPushButton(f"🌡️ {tmin}–{tmax} °C \n{self.get_weather_description(code)}")
            daylyDayDesc.setStyleSheet(self.buttonStyle)
            daylyDayDesc.setFixedWidth(150)
            
            daylyLayoutDay.addWidget(daylyDayDesc, alignment=Qt.AlignCenter)
            
            daylyLayout.addLayout(daylyLayoutDay)
        #text += "</ul>"
        layout.addLayout(daylyLayout)
        #browser.setHtml(text)
        #layout.addWidget(browser)
        
        bottomLayout = QHBoxLayout()
        aboutButton = QPushButton()
        aboutButton.setIcon(QIcon("about.png"))
        aboutButton.setIconSize(QSize(34,34))
        aboutButton.setFixedSize(34,34)
        aboutButton.setStyleSheet(self.buttonStyle1)
        aboutButton.clicked.connect(self.open_about)
        bottomLayout.addWidget(aboutButton)

        #text = "<h4>© 2025 by F.Maczollek aka. VerEnderT</h4><ul>"
        #copyLabel=QLabel(text)
        #bottomLayout.addWidget(copyLabel)
        
        bottomLayout.addStretch()
        
        text = "Meteorologische Daten von open-meteo.com"
        dataLabel=QPushButton()
        dataLabel.setText(text)
        bottomLayout.addWidget(dataLabel)
        layout.addStretch()
        layout.addLayout(bottomLayout)
        
        self.weather_win.setLayout(layout)
        self.weather_win.resize(400, 600)
        self.weather_win.setFixedSize(900, 600)
        self.weather_win.show()
        self.center_on_screen(self.weather_win)
    
    def center_on_screen(self, fenster):
        screen = QDesktopWidget().availableGeometry().center()
        
        frame_geom = fenster.frameGeometry()
        frame_geom.moveCenter(screen)
        fenster.move(frame_geom.topLeft())
        
    def open_about(self):
        about.show_about_dialog("x-live-wetter","X-Live Wetter")
    
    def day_hour_temp(self, day):
        #print(len(self.daily["time"]))
        date_raw = self.daily["time"][day].split("-")
        date = date_raw[2]+"."+date_raw[1]+"."
        self.day_win = QWidget()
        self.day_win.setStyleSheet(self.Style1)
        self.day_win.setWindowTitle(f"Tagesübersicht für den {date}")
        self.day_win.setWindowIcon(self.get_icon_for_code(self.current_weather["code"]))
        
        text = ""
        dayWinLayout= QVBoxLayout()
        hourlyLayoutDay = QVBoxLayout()
        for t in range(0, 24, 2):
            tempLayout = None
            tempLayout=QHBoxLayout()
            i = t + (int(day)*24)
            time = self.hourly["time"][i].split("T")[1]
            temp = self.hourly["temperature_2m"][i]
            code = self.hourly["weathercode"][i]
            #print(f"⌛{time} - ️🌡️ ️{temp} °C - 🌤️ {self.get_weather_description(code)}")
            text += (f"\n\t⌛ {time}   \t🌡️ ️{temp} °C    \t 🌤️ {self.get_weather_description(code)}\t")
            tempLabel = QLabel(f"    ⌛ {time}      🌡️ ️{temp} °C")
            tempLabel.setFixedWidth(150)
            tempLayout.addWidget(tempLabel)
            tempCode = QPushButton()
            tempCode.setStyleSheet(self.buttonStyle)
            tempCode.setIcon(self.get_icon_for_code(code))
            tempLayout.addWidget(tempCode)
            tempLabel1 = QLabel(self.get_weather_description(code))
            tempLabel1.setFixedWidth(150)
            tempLayout.addWidget(tempLabel1)
            dayWinLayout.addLayout(tempLayout)
        text_label = QLabel(text)
        self.day_win.setLayout(dayWinLayout)

        # Hintergrundbild-Label
        self.day_background = QLabel(self.day_win)
        self.day_background.setPixmap(QPixmap("hintergrund.jpg").scaled(self.day_win.size()))
        self.day_background.setScaledContents(True)  # <-- Wichtig!
        self.day_background.setGeometry(0, 0, 900, 600)
        self.day_background.move(0,0)
        self.day_background.lower()  # Nach ganz hinten

        self.day_win.show()
        self.day_win.setFixedSize(self.day_win.size())
        self.center_on_screen(self.day_win)


    def change_location(self):
        city, ok = QInputDialog.getText(None, "Ort ändern", "Neuen Ort eingeben:")
        if ok and city:
            lat, lon, name = self.get_coordinates(city)
            if lat and lon:
                self.lat, self.lon = lat, lon
                self.location = name
                self.save_config()
                self.update_weather()
            else:
                QMessageBox.warning(None, "Fehler", f"Konnte Ort nicht finden: {city}")

    ### updates abrufen
    def check_updates(self):
        app_name  = self.app_name
        self.xcheck = xupdates.update_info("verendert", app_name)
        print(self.xcheck)
        if self.xcheck["update"] == "u":
            self.update_action.setVisible(True)  


    def start_updating(self, url):
        url = self.xcheck["url"]
        self.update_win = QWidget()
        self.update_win.setStyleSheet(self.Style1)
        self.update_win.setWindowTitle(f"Update verfügbar")
        self.update_win.setWindowIcon(self.get_icon_for_code(self.current_weather["code"]))
        

        update_layout=QVBoxLayout()
        self.updateLabel = QPushButton("Eine neue Version ist verfügbar. \nSoll die neue Version herunterladen und installiert werden?")
        self.updateLabel.setMaximumWidth(600)
        update_layout.addWidget(self.updateLabel)
        button_layout=QHBoxLayout()
        self.yesButton = QPushButton("Ja, Aktuallisieren")
        self.noButton = QPushButton("Nein, Alles bleibt wie es ist !")
        self.yesButton.setStyleSheet(self.buttonStyle2)
        self.noButton.setStyleSheet(self.buttonStyle1)
        self.yesButton.clicked.connect(lambda: self.start_download(url))
        self.noButton.clicked.connect(self.update_win.close)


        button_layout.addWidget(self.yesButton)
        button_layout.addWidget(self.noButton)
        update_layout.addLayout(button_layout)

        # Hintergrundbild-Label
        self.update_background = QLabel(self.update_win)
        self.update_background.setPixmap(QPixmap("hintergrund.jpg").scaled(self.update_win.size()))
        self.update_background.setScaledContents(True)  # <-- Wichtig!
        self.update_background.setGeometry(0, 0, self.update_win.size().width(), self.update_win.size().height())
        self.update_background.move(0,0)
        self.update_background.lower()  # Nach ganz hinten

        self.update_win.setLayout(update_layout)
        self.update_win.show()
        self.update_win.adjustSize()        
        self.updateLabel.setMaximumWidth(self.updateLabel.size().width())
        self.update_win.setMaximumSize(self.update_win.size())
        self.center_on_screen(self.update_win)


    # Download update
    def start_download(self, url):
        self.yesButton.hide()
        self.noButton.hide()
        os.system("rm /tmp/x-live/debs/*")
        filename = url.split("/")[-1]
        self.updateLabel.setText(f"Start downloading: {filename}")
        save_directory = '/tmp/x-live/debs/'

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        self.filename = os.path.join(save_directory, filename)

        if not self.process:
            self.process = QProcess()

        # Setup QProcess for wget command
        self.process.setProgram('wget')
        self.process.setArguments(['--progress=bar:force', '-O', self.filename, url])
        self.process.setWorkingDirectory(save_directory)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.read_output)
        self.process.finished.connect(self.handle_finished)
        self.process.start()

    
    def read_output(self):
        if self.process:
            output = self.process.readAll().data().decode()
            output = output.replace('\r\n', '\n').replace('\r', '\n')
            self.updateLabel.setText(output)
            print(output)

    def handle_finished(self):
        self.updateLabel.setText(f"Finished downloading: {self.filename}")
        self.install_update()

    def install_update(self):
        self.updateLabel.setText("\nStarte Paket Installation...\n")
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        
        # Prepare the command    
        command = "apt update && apt install -y /tmp/x-live/debs/*.deb" 
        self.updateLabel.setText("Bitte Passwort zum installieren eingeben !")
        self.process.start('pkexec', ['sh', '-c', command])

    def process_finished(self, exit_code, exit_status):
        if exit_status == QProcess.NormalExit and exit_code == 0:
            self.updateLabel.setText("\nInstallation erfolgreich beendet!")
        else:
            self.updateLabel.setText("\nInstallation fehlgeschlagen.")


if __name__ == "__main__":
    WeatherTrayApp()
