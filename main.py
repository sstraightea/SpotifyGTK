import logging
import os
import sys
from os.path import exists
from threading import Thread
from time import sleep

import auth_controller
from playback_info import PlaybackInfo
from web_controller import WebController
from main_ui import SpotifyGtkUI
from server.webserver import Webserver


class SpotifyGTK:
	server: Webserver = None
	controller: WebController = None
	window: SpotifyGtkUI = None
	callbacks: dict[str, ()] = None

	def __init__(self):
		self.log_level = logging.DEBUG
		log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
		self.log = logging.getLogger(__name__)
		self.log.setLevel(self.log_level)
		# writing to stdout
		handler = logging.StreamHandler(sys.stdout)
		handler.setLevel(self.log_level)
		handler.setFormatter(log_format)
		self.log.addHandler(handler)

		self.log.log(logging.INFO, "Starting SpotifyGTK")
		self.callbacks = {"backend_ready": lambda: self.backend_ready(), "toggle_play": lambda d: self.toggle_play(d),
		                  "report_state": lambda info: self.report_state(info), "set_volume": lambda volume:
		                  self.set_volume(volume), "set_position": lambda pos: self.set_position(pos)}

	def run_server(self):
		"""
		This method starts the webserver, should be run in a thread
		:param serv: A initialized Webserver
		"""
		self.server.run()

	def run_web_controller(self):
		"""
		This method starts the selenium web controller with the callbacks variable
		:param ctrl: A initialized WebController
		"""
		self.controller.run_controller(self.callbacks)

	def run_ui(self):
		"""
		This method runs the GTK/Libadwaita UI with the callbacks variable
		:param ui: A initialized SpotifyGtkUI
		"""
		self.window.run_ui(self.callbacks)

	def toggle_play(self, d):
		"""
		This callback is called from the ui, and tells the controller to press play
		:param d: is given by the button connect event
		"""
		self.controller.togglePlay(d)

	def backend_ready(self):
		"""
		Is called from the controller, when the webpage finished loading and is ready to play music
		"""
		self.window.backend_ready_callback()

	def report_state(self, info: PlaybackInfo):
		self.window.report_state_callback(info)

	def set_volume(self, volume: int):
		self.controller.set_volume(volume)

	def set_position(self, position: int):
		self.controller.set_position(position)

	def run(self):
		path = os.getcwd()
		os.environ["PATH"] += os.pathsep + path
		# mail = input("\nEmail: ")
		# passw = input("\nPassword: ")
		# if not os.path.exists("server/token.txt"):
		#     # need to authenticate
		#     auth_browser = AuthController()
		#     auth_browser
		if not exists("server/token.txt"):
			auth = Thread(target=auth_controller.run_auth, args=[])
			auth.start()
			while auth.is_alive():
				sleep(0.5)
		print("Auth done.")
		os.chdir(path)
		if not exists("server/token.txt"):
			print("Token not found, can't continue.")
			return 1
		self.server = Webserver()
		self.controller = WebController()
		self.window = SpotifyGtkUI()
		srv = Thread(target=self.run_server, args=[])
		ctl = Thread(target=self.run_web_controller, args=[])
		uiw = Thread(target=self.run_ui, args=[])

		srv.start()
		ctl.start()
		uiw.start()

		while True:
			sleep(0.5)
			if not uiw.is_alive():
				if self.controller is not None:
					self.controller.dead = True
					self.controller.stop()
					del self.controller
				if self.server is not None:
					self.server.web_server.shutdown()
					self.server.stop()
					del self.server
				break
		return 0


if __name__ == "__main__":
	app = SpotifyGTK()
	app.run()
