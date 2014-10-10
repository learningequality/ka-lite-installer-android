from kivy.uix.progressbar import ProgressBar
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
Window.clearcolor = (1, 1, 1, 1)

class _BoxLayout(BoxLayout):
	def __init__(self, **kwargs):
		super(_BoxLayout, self).__init__(**kwargs)
		with self.canvas.before:
		    Color(0.878, 0.941, 0.784)
		    self.rect = Rectangle(size=self.size, pos=self.pos)
		self.bind(size=self._update_rect, pos=self._update_rect)

	def _update_rect(self, instance, value):
		self.rect.pos = instance.pos
		self.rect.size = instance.size

class KaliteUI(object):
	def constructor(self, appLayout, kaliteApp):
		logohoulder = _BoxLayout(orientation='horizontal')
		log_img = Image(source='horizontal-logo.png')
		#log_img.pos_hint={'center_x': 0.1, 'center_y': .5}
		logohoulder.padding = [20,10,Window.width-250,0]
		logohoulder.add_widget(log_img)

		appLayout.add_widget(logohoulder)

		#create BubbleButtons
		btn1= Button(text='OpenBrowser', font_size=30
		    , color=(0.14, 0.23, 0.25, 1), bold=True)
		btn1.background_normal='green_button_up.png'
		#btn1.background_down='button_down.png'
		btn1.bind(on_press=kaliteApp.start_webview_bubblebutton)

		btn2= Button(text='Exit', font_size=30
		    , color=(0.14, 0.23, 0.25, 1), bold=True)
		btn2.background_normal='green_button_up.png'
		#btn2.background_down='button_down.png'
		btn2.bind(on_press=kaliteApp.quit_app)

		btn3= Button(text='thread', font_size=30
		    , color=(0.14, 0.23, 0.25, 1), bold=True)
		btn3.background_normal='green_button_up.png'
		#btn3.background_down='button_down.png'
		btn3.bind(on_press=kaliteApp.getThreadNum)

		btn4= Button(text='StopServer', font_size=30
		    , color=(0.14, 0.23, 0.25, 1), bold=True)
		btn4.background_normal='green_button_up.png'
		btn4.bind(on_press=kaliteApp.stop_server)

		btn5= Button(text='StartServer', font_size=30
		    , color=(0.14, 0.23, 0.25, 1), bold=True)
		btn5.background_normal='green_button_up.png'
		btn5.bind(on_press=kaliteApp.start_server)

		#Add items to bubble
		buttonsholder = _BoxLayout(orientation='horizontal')
		buttonsholder.padding = [10,0,10,0]
		buttonsholder.add_widget(btn1)
		buttonsholder.add_widget(btn2)
		buttonsholder.add_widget(btn3)
		buttonsholder.add_widget(btn4)
		buttonsholder.add_widget(btn5)

		appLayout.add_widget(buttonsholder)

		#image stuff
		self.img_holder = BoxLayout(orientation='vertical', size=(200,200), size_hint=(1, None))
		self.img_holder.padding = [0,80,0,10]
		appLayout.add_widget(self.img_holder)

		#thread input box
		textinputholder = BoxLayout(orientation='horizontal')
		textinputholder.padding = [200,10,200,10]

		self.textinput = TextInput(multiline=False, 
		    hint_text="Enter number of threads here:")
		self.textinput.padding = [10,10,10,10]
		textinputholder.add_widget(self.textinput)

		self.progress_bar = ProgressBar()

		self.server_box = BoxLayout(orientation='horizontal')
		self.messages = BoxLayout(orientation='vertical')

		appLayout.add_widget(self.messages)
		appLayout.add_widget(self.server_box)
		appLayout.add_widget(textinputholder)
		appLayout.add_widget(self.progress_bar)

	def addMessages(self, message):
		self.messages.add_widget(message)

	def removeMessages(self, message):
		self.messages.remove_widget(message)

	def addLoadingGif(self):
		self.gif_img = Image(source='loading.zip',  anim_delay = 0.15)
		#self.gif_img = Image(source='horizontal-logo.png')
		self.img_holder.add_widget(self.gif_img)

	def removeLoadingGif(self):
		self.img_holder.remove_widget(self.gif_img)

	def getThreadNum(self):
		return 'threads=' + self.textinput.text

	def startProgressBar(self, anim_value):
		self.anim = Animation(value = anim_value, duration = 1)
		self.anim.start(self.progress_bar)

	def animationBind(self, bindFunction):
		self.anim.bind(on_complete = bindFunction)


