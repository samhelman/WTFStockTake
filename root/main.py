import kivymd
from kivymd.app import MDApp
from kivymd.uix.navigationdrawer import NavigationLayout, MDNavigationDrawer
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast
from kivy.storage.jsonstore import JsonStore

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MainApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"

        self.storage = JsonStore('../store.json')
        self.emails = JsonStore('../emails.json')

        self.view_stock_widgets = []
        self.manage_items_widgets = []
        self.add_remove_stock_widgets = []
        self.edit_item_widgets = []
        self.send_data_widgets = []
        self.low_stock_widgets = []

    def add_item(self, name, stock_type, stock_level, stock_units, low_threshold, pop_weighting):
        inputs = [name, stock_type, stock_level, stock_units, low_threshold, pop_weighting]
        if '' not in inputs:
            self.storage.put(
                name, 
                name=name, 
                stock_type=stock_type,
                stock_level=int(stock_level),
                stock_units=stock_units,
                low_threshold=int(low_threshold),
                pop_weighting=int(pop_weighting)
                )
        else:
            toast('Some fields were left blank...')

    def remove_item(self, name):
        self.storage.delete(name)

    def remove_email(self, email):
        self.emails.delete(email)

    def update_stock_level(self, name, stock_level_change):
        item = self.storage.get(name)
        item['stock_level'] += stock_level_change
        if item['stock_level'] < 0:
            item['stock_level'] = 0
        self.storage.put(
            name, 
            name=name, 
            stock_type=item['stock_type'],
            stock_level=item['stock_level'],
            stock_units=item['stock_units'],
            low_threshold=item['low_threshold'],
            pop_weighting=item['pop_weighting']
            )

    def apply_stock_changes(self):
        for widget in self.add_remove_stock_widgets:
            try:
                if widget.ids.plus_minus.active == True:
                    sign = '+'
                else:
                    sign = '-'
            except AttributeError:
                continue
            if len(widget.ids.stock.text) > 0:
                stock_change = sign + widget.ids.stock.text
                self.update_stock_level(widget.ids.name.text, int(stock_change))
                widget.ids.stock.text = ''
        self.load_add_remove_stock_screen()
        self.load_low_stock_screen()
        toast('Update Successful')

    def apply_edit_changes(self, name, stock_type, stock_level, stock_units, low_threshold, pop_weighting):
        self.storage.delete(self.editing_item)
        self.storage.put(
            name,
            name=name, 
            stock_type=stock_type, 
            stock_level=int(stock_level), 
            stock_units=stock_units, 
            low_threshold=int(low_threshold), 
            pop_weighting=int(pop_weighting)
            )
        self.load_manage_items_screen()
        self.load_view_stock_screen()
        self.load_add_remove_stock_screen()
        self.load_low_stock_screen()
        self.editing_item = None
        toast('Changes Applied')

    def delete_item(self, item):
        screen = self.root.ids.screen_manager.current
        if screen == 'manage_items':
            self.remove_item(item)
            self.root.ids.screen_manager.current = 'manage_items'
            self.load_manage_items_screen()
            self.load_view_stock_screen()
            self.load_add_remove_stock_screen()
            self.load_low_stock_screen()
        elif screen == 'send_data':
            self.remove_email(item)
            self.root.ids.screen_manager.current = 'send_data'
            self.load_send_data_screen()
        toast('Deleted')

    def load_manage_items_screen(self):
        for widget in self.manage_items_widgets:
            self.root.ids.manage_items_list.remove_widget(widget)
        keys = sorted(self.storage.keys())
        stock_types = []
        for key in self.storage:
            item = self.storage.get(key)
            if item['stock_type'] not in stock_types:
                stock_types.append(item['stock_type'])
        stock_types.sort()
        for stock_type in stock_types:
            widget = Subtitle_Widget(stock_type)
            self.root.ids.manage_items_list.add_widget(widget)
            self.manage_items_widgets.append(widget)
            for key in keys:
                item = self.storage.get(key)
                if item['stock_type'] == stock_type:
                    name = item['name']
                    widget = Manage_Items_Swipe_Card(name)
                    self.root.ids.manage_items_list.add_widget(widget)
                    self.manage_items_widgets.append(widget)

    def load_view_stock_screen(self):
        for widget in self.view_stock_widgets:
            self.root.ids.view_stock_list.remove_widget(widget)
        keys = sorted(self.storage.keys())
        stock_types = []
        for key in self.storage:
            item = self.storage.get(key)
            if item['stock_type'] not in stock_types:
                stock_types.append(item['stock_type'])
        stock_types.sort()
        for stock_type in stock_types:
            widget = Subtitle_Widget(stock_type)
            self.root.ids.view_stock_list.add_widget(widget)
            self.view_stock_widgets.append(widget)
            for key in keys:
                item = self.storage.get(key)
                if item['stock_type'] == stock_type:
                    name = item['name']
                    stock_level = item['stock_level']
                    units = item['stock_units']
                    low_threshold = item['low_threshold']
                    if stock_level <= low_threshold:
                        low = True
                    else:
                        low = False
                    stock_level_string = str(stock_level) + ' ' + str(units)
                    widget = View_Stock_Card(name, stock_level_string, low)
                    self.root.ids.view_stock_list.add_widget(widget)
                    self.view_stock_widgets.append(widget)

    def load_add_remove_stock_screen(self):
        for widget in self.add_remove_stock_widgets:
            self.root.ids.add_remove_stock_list.remove_widget(widget)
        self.add_remove_stock_widgets = []
        keys = sorted(self.storage.keys())
        stock_types = []
        for key in self.storage:
            item = self.storage.get(key)
            if item['stock_type'] not in stock_types:
                stock_types.append(item['stock_type'])
        stock_types.sort()
        for stock_type in stock_types:
            widget = Subtitle_Widget(stock_type)
            self.root.ids.add_remove_stock_list.add_widget(widget)
            self.add_remove_stock_widgets.append(widget)
            for key in keys:
                item = self.storage.get(key)
                if item['stock_type'] == stock_type:
                    name = item['name']
                    widget = Add_Remove_Stock_Card(name)
                    self.root.ids.add_remove_stock_list.add_widget(widget)
                    self.add_remove_stock_widgets.append(widget)
        widget = MDCard(size_hint_y=None,height='50dp')
        self.root.ids.add_remove_stock_list.add_widget(widget)
        self.add_remove_stock_widgets.append(widget)

    def load_edit_item_screen(self, key):
        for widget in self.edit_item_widgets:
            self.root.ids.edit_item_layout.remove_widget(widget)
        self.edit_item_widgets = []
        item = self.storage.get(key)
        widget = Edit_Item_Dialog_Content()
        widget.ids.item_name.text = str(item['name'])
        widget.ids.item_type.text = str(item['stock_type'])
        widget.ids.stock_level.text = str(item['stock_level'])
        widget.ids.stock_units.text = str(item['stock_units'])
        widget.ids.low_threshold.text = str(item['low_threshold'])
        widget.ids.pop_weighting.text = str(item['pop_weighting'])
        self.root.ids.edit_item_layout.add_widget(widget)
        self.edit_item_widgets.append(widget)
        self.editing_item = item['name']

    def load_send_data_screen(self):
        for widget in self.send_data_widgets:
            self.root.ids.emails_list.remove_widget(widget)
        self.send_data_widgets = []
        keys = sorted(self.emails.keys())
        for key in keys:
            email = self.emails.get(key)
            widget = Email_Contact_Card(email['email'])
            self.root.ids.emails_list.add_widget(widget)
            self.send_data_widgets.append(widget)

    def load_low_stock_screen(self):
        for widget in self.low_stock_widgets:
            self.root.ids.low_stock_layout.remove_widget(widget)
        self.low_stock_widgets = []
        keys = sorted(self.storage.keys())
        stock_types = []
        for key in self.storage:
            item = self.storage.get(key)
            if item['stock_type'] not in stock_types:
                stock_types.append(item['stock_type'])
        stock_types.sort()
        for stock_type in stock_types:
            widget = Subtitle_Widget(stock_type)
            self.root.ids.low_stock_layout.add_widget(widget)
            self.low_stock_widgets.append(widget)
            for key in keys:
                item = self.storage.get(key)
                if item['stock_type'] == stock_type and item['stock_level'] <= item['low_threshold']:
                    widget = Low_Stock_Item_Card(item['name'])
                    self.root.ids.low_stock_layout.add_widget(widget)
                    self.low_stock_widgets.append(widget)

    def open_add_item_popup(self):
        content = Add_Item_Dialog_Content()
        self.popup = MDDialog(
            type='custom',
            content_cls=content,
            auto_dismiss=False,
        )
        self.popup.open()

    def confirm_delete_dialog(self, item):
        content = Confirm_Delete_Dialog_Content(item)
        self.popup = MDDialog(
            type='custom',
            content_cls=content,
            auto_dismiss=False,
        )
        self.popup.open()

    def open_add_email_popup(self):
        content = Add_Email_Content()
        self.popup = MDDialog(
            type='custom',
            content_cls=content,
            auto_dismiss=False,
        )
        self.popup.open()

    def add_contact(self, email):
        self.emails.put(email, email=email, sent=False)
        self.load_send_data_screen()

    def send_email(self, email):

        address = self.emails.get(email)
        self.emails.put(
            email,
            email=email,
            sent=True
        )

        #customise frm and password to send emails from your account for testing purposes.
        frm = '07shelman@gmail.com'
        password = ''
        to = email
        subject = 'Stock Level Data'

        server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        server.starttls()
        server.login(frm, password)

        msg = MIMEMultipart()
        msg['From'] = frm
        msg['to'] = to
        msg['subject'] = subject

        body = ""

        keys = self.storage.keys()
        keys.sort()

        stock_types = []
        for key in keys:
            stock_type = self.storage.get(key)['stock_type']
            if stock_type not in stock_types:
                stock_types.append(stock_type)
        for stock_type in stock_types:
            body += '%s\n' % stock_type.upper()
            for key in keys:
                item = self.storage.get(key)
                if item['stock_type'] == stock_type:
                    body += '%s: %s %s\n' % (item['name'], item['stock_level'], item['stock_units'])
            body += '\n'

        msg.attach(MIMEText(body, 'plain'))

        server.sendmail(frm, to, msg.as_string())

        toast('Sent to: %s' % email)

    def set_screen(self, screen):
        self.root.ids.screen_manager.current = screen

    def build(self):
        self.title = 'WTF Stock Take'
        return MainLayout()

    def on_start(self):
        self.load_manage_items_screen()
        self.load_view_stock_screen()
        self.load_add_remove_stock_screen()
        self.load_send_data_screen()
        self.load_low_stock_screen()

class MainLayout(NavigationLayout):
    pass

class View_Stock_Card(MDCard):
    
    def __init__(self, item, stock, low, **kwargs):
        self.item = item
        self.stock = stock
        if low == True:
            self.low = 'Yes'
        else:
            self.low = 'No'
        super().__init__(**kwargs)

class Manage_Items_Swipe_Card(MDCard):

    def __init__(self, item, **kwargs):
        self.item = item
        super().__init__(**kwargs)

class Add_Remove_Stock_Card(MDCard):

    def __init__(self, name, **kwargs):
        self.name = name
        super().__init__(**kwargs)

class Edit_Item_Dialog_Content(BoxLayout):
    pass

class Add_Item_Dialog_Content(BoxLayout):
    pass

class Confirm_Delete_Dialog_Content(BoxLayout):
    
    def __init__(self, item, **kwargs):
        self.item = item
        super().__init__(**kwargs)

class Subtitle_Widget(MDCard):
    
    def __init__(self, stock_type, **kwargs):
        self.stock_type = stock_type
        super().__init__(**kwargs)

class Add_Email_Content(BoxLayout):
    pass

class Email_Contact_Card(MDCard):
    
    def __init__(self, address, **kwargs):
        self.address = address
        super().__init__(**kwargs)

class Low_Stock_Item_Card(MDCard):

    def __init__(self, item, **kwargs):
        self.item = item
        super().__init__(**kwargs)

MainApp().run()