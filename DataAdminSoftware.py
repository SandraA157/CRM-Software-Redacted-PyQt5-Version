# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import re
import csv 
import pymysql #pip instal pymsql PyQt5
import pandas as pd # pip install pandas
import calendar

from sqlalchemy import create_engine #pip install sqlalchemy
from menu import Menu #pip install menu
from datetime import datetime, date #pip install datetime

from PyQt5 import QtCore, QtGui, QtWidgets #pip intall PyQt5
from PyQt5.QtWidgets import (QApplication, QShortcut, QMainWindow, QVBoxLayout, QWidget,
     QScrollArea, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextBrowser,
     QFileDialog, QMessageBox, QComboBox, QLineEdit,  QDialog, QTextEdit,
     QMenuBar, QAction, QPlainTextEdit, QSpinBox, QDateEdit, QHeaderView, QHBoxLayout)
from PyQt5.QtGui import (QKeySequence, QRegularExpressionValidator,  QTextDocument,
     QTextCursor, QFont)
from PyQt5.QtCore import (QRegularExpression, pyqtSignal, QSize, QSizeF, QDate)
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog

font = QFont('Arial',16)

#Replace with your database details
dbhost= "localhost" 
dbusername="root"
dbpassword="password"
dbdatabase="database"

#-----------Mysql Connection --------------#

class DatabaseManager:
    def __init__(self):
        self.db_connection = None

    def connect_to_database(self):
        global dbhost, dbusername, dbpassword, dbdatabase
        
        try:
            self.db_connection = pymysql.connect(
                host=dbhost,
                user=dbusername,
                password=dbpassword,
                database=dbdatabase,
                charset='utf8mb4'
            )
            if not self.db_connection:
                self.show_warning("Cannot Connect to Database")

        except pymysql.Error as err:
            self.show_warning(f"Database Connection Error: {err}")

    def close_connection(self):
        if self.db_connection:
            self.db_connection.close()

    def show_warning(self, message):
        QMessageBox.warning(None, "Error", message)



#-------------Check User Credential from Database (User Authentication Dialog)--------------------#
def check_credentials(entered_username, entered_password):
    try:
        db_manager = DatabaseManager()  
        db_manager.connect_to_database()         
        cursor = db_manager.db_connection.cursor()

        query = f"SELECT Username, Password FROM User WHERE Username = '{entered_username}'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result and result[1] == entered_password:
            return True  # Return authentication result
        else:
            return False  # Return authentication result (False)
    finally:
        if db_manager:
            db_manager.close_connection()

#---------- Check User in Database (User Creation Dialog) Function-----------------#
def check_existed_user(new_username):
    db_manager = DatabaseManager()
    db_manager.connect_to_database()
    cursor = db_manager.db_connection.cursor()

    query_username = "SELECT Username FROM User WHERE Username = %s"
    cursor.execute(query_username, (new_username,))
    result_username = cursor.fetchone()

    if result_username:
        cursor.close()
        return 1
    else:
        cursor.close()
        return 0  # username are available

#-----------Change Database Dialog Class--------------#
#------------ init Section------------------#
class ChangeDatabase(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Change Database")
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.setGeometry(100, 100, 300, 150)

        self.host_label = QLabel("Host:", self)
        layout.addWidget(self.host_label)
        self.host_edit = QLineEdit(self)
        layout.addWidget(self.host_edit)

        self.database_label = QLabel("Database:", self)
        layout.addWidget(self.database_label)
        self.database_edit = QLineEdit(self)
        layout.addWidget(self.database_edit)

        self.user_label = QLabel("User:", self)
        layout.addWidget(self.user_label)
        self.user_edit = QLineEdit(self)
        layout.addWidget(self.user_edit)

        self.password_label = QLabel("Password:", self)
        layout.addWidget(self.password_label)
        self.password_edit = QLineEdit(self)
        layout.addWidget(self.password_edit)

        self.change_button = QPushButton("Change", self)
        self.change_button.clicked.connect(self.change_database)
        layout.addWidget(self.change_button)

        self.change_cancel_button = QPushButton("Cancel", self)
        self.change_cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.change_cancel_button)

        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def change_database(self):
        global dbhost, dbusername, dbpassword, dbdatabase
        
        dbhost = self.host_edit.text().strip()
        dbusername = self.user_edit.text().strip()
        dbpassword = self.password_edit.text().strip()
        dbdatabase = self.database_edit.text().strip()

        if not dbhost or not dbusername or not dbdatabase:
            QMessageBox.warning(self, "Error", "Please fill out all fields.")
            return
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()

            QMessageBox.information(self, "Success", "Database connection updated successfully.")
            self.accept()
        except pymysql.Error as err:
            QMessageBox.warning(self, "Error", f"Database Connection Error: {err}")

#-----------Create New User Dialog Class--------------#
#------------ init Section------------------#
class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Create New User")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setGeometry(100, 100, 300, 120)

        self.create_username_label = QLabel("Username:", self)
        self.create_username_label.setGeometry(10, 10, 280, 20)

        self.create_password_label = QLabel("Password:", self)
        self.create_password_label.setGeometry(10, 40, 280, 20)

        self.create_username_edit = QLineEdit(self)
        self.create_username_edit.setGeometry(100, 10, 190, 20)

        self.create_password_edit = QLineEdit(self)
        self.create_password_edit.setGeometry(100, 40, 190, 20)

        self.create_login_button = QPushButton("Create", self)
        self.create_login_button.setGeometry(50, 70, 90, 30)
        self.create_login_button.clicked.connect(self.register_new_user)

        self.create_cancel_button = QPushButton("Cancel", self)
        self.create_cancel_button.setGeometry(160, 70, 90, 30)
        self.create_cancel_button.clicked.connect(self.reject)

        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

#-------------New User Creation Functions---------------#
    def register_new_user(self):
        new_username = self.create_username_edit.text()
        new_password = self.create_password_edit.text()
        db_manager = DatabaseManager()
        db_manager.connect_to_database()
        if not new_username or not new_password:
            error = 2
        else:
            error = check_existed_user(new_username)

            if error == 0:
                self.accept()
                cursor = db_manager.db_connection.cursor()
                
                cursor.execute("SELECT MAX(ID) FROM User")
                result = cursor.fetchone()
                latest_id = result[0]

                if latest_id:
                    numeric_part = latest_id  # Extract the numeric part if ID start with a letter (numeric_part = int(latest_id[1:]) ) 
                    new_id_number = numeric_part + 1 # if ID start with a letter (new_id_number = numeric_part + 1)
                    new_id = f'{new_id_number}'  # Format the new ID. If ID start with a letter (new_id = f'D{new_id_number:04d}')
                else:
                    new_id = '1'  # If no previous IDs exist, start from 1

                query = f"INSERT INTO User (ID, Username, Password) " \
                        f"VALUES ('{new_id}', '{new_username}', '{new_password}')"
                cursor.execute(query)
                db_manager.db_connection.commit()
                db_manager.close_connection()
    
                return True  # User registration was successful
            
            elif error == 1:
                QMessageBox.warning(self, "Username already exists", "Please choose a different username.")
            elif error == 2:
                QMessageBox.warning(self, "Empty Fields", "Please fill in all the required fields.")
            
        return False
            
#-----------Login Dialog Class--------------#
#------------ init Section------------------#

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 300, 170)
        entered_username = None

        self.username_label = QLabel("Username:", self)
        self.username_label.setGeometry(10, 10, 280, 20)

        self.password_label = QLabel("Password:", self)
        self.password_label.setGeometry(10, 40, 280, 20)

        self.username_edit = QLineEdit(self)
        self.username_edit.setGeometry(100, 10, 190, 20)

        self.password_edit = QLineEdit(self)
        self.password_edit.setGeometry(100, 40, 190, 20)
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login", self)
        self.login_button.setGeometry(50, 75, 90, 30)
        self.login_button.clicked.connect(self.authenticate)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setGeometry(160, 75, 90, 30)
        self.cancel_button.clicked.connect(self.reject)

        self.create_new_user_label = QLabel('<a href="create_new_user">Create User</a>', self)
        self.create_new_user_label.setOpenExternalLinks(False)  # Prevent opening links in a web browser
        self.create_new_user_label.linkActivated.connect(self.open_create_user_dialog)
        self.create_new_user_label.move(110, 105)  # Set the label's position

        self.create_new_user_label = QLabel('<a href="change_database">Change Database</a>', self)
        self.create_new_user_label.setOpenExternalLinks(False)  # Prevent opening links in a web browser
        self.create_new_user_label.linkActivated.connect(self.open_change_database_dialog)
        self.create_new_user_label.setGeometry(90, 125, 120, 30)
        
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.setLayout(layout)
        
#----------------User Authentication and Creation (redirect) Function-----------#
    def authenticate(self):
        global login_username

        entered_username = self.username_edit.text()
        entered_password = self.password_edit.text()
        db_manager = DatabaseManager()

        login_username = entered_username        
        authentication_result, Type = check_credentials(entered_username, entered_password)

        if authentication_result:
            self.accept()
        else:
            QMessageBox.warning(self, "Authentication Failed", "Invalid username or password. Please try again.")
            self.username_edit.clear()
            self.password_edit.clear()
            self.username_edit.setFocus()

    def open_create_user_dialog(self, link):
        db_manager = DatabaseManager()
        if link == "create_new_user":
            create_user_dialog = CreateUserDialog(db_manager)
            create_user_dialog.exec_()
            
    def open_change_database_dialog(self, link):
        db_manager = DatabaseManager()
        if link == "change_database":
            change_database_dialog = ChangeDatabase(db_manager)
            change_database_dialog.exec_()
            
#-----------Main Window UI Class--------------#
#------------ init Section------------------#
class Ui_MainWindow(object): # Set UI for MainWindow
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.SearchBox = QtWidgets.QLineEdit(self.centralwidget)
        self.SearchBox.setGeometry(QtCore.QRect(980, 5, 298, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.SearchBox.setFont(font)
        self.SearchBox.setText("")
        self.SearchBox.setObjectName("SearchBox")
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(2, 30, 978, 653))
        self.tableWidget.setRowCount(100)
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Set edit triggers
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)


        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(980, 30, 301, 720))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(200)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.ResetPushButton = QtWidgets.QPushButton(self.frame)
        self.ResetPushButton.setGeometry(QtCore.QRect(105, 620, 89, 25))
        self.ResetPushButton.setObjectName("ResetPushButton")
        self.SavePushButton = QtWidgets.QPushButton(self.frame)
        self.SavePushButton.setGeometry(QtCore.QRect(200, 620, 89, 25))
        self.SavePushButton.setObjectName("SavePushButton")
        self.ClearPushButton = QtWidgets.QPushButton(self.frame)
        self.ClearPushButton.setGeometry(QtCore.QRect(10, 620, 89, 25))
        self.ClearPushButton.setObjectName("ClearPushButton")
        self.AddPushButton = QtWidgets.QPushButton(self.frame)
        self.AddPushButton.setGeometry(QtCore.QRect(105, 6, 89, 25))
        self.AddPushButton.setObjectName("AddPushButton")
        self.EditPushButton = QtWidgets.QPushButton(self.frame)
        self.EditPushButton.setGeometry(QtCore.QRect(200, 6, 89, 25))
        self.EditPushButton.setObjectName("EditPushButton")
        self.CancelPushButton = QtWidgets.QPushButton(self.frame)
        self.CancelPushButton.setGeometry(QtCore.QRect(200, 6, 89, 25))
        self.CancelPushButton.setObjectName("CancelPushButton")
        self.CancelPushButton.setVisible(False)
        self.DeletePushButton = QtWidgets.QPushButton(self.frame)
        self.DeletePushButton.setGeometry(QtCore.QRect(10, 6, 89, 25))
        self.DeletePushButton.setObjectName("DeletePushButton")
        self.ClearTablePushButton = QtWidgets.QPushButton(self.frame)
        self.ClearTablePushButton.setGeometry(QtCore.QRect(105, 6, 89, 25))
        self.ClearTablePushButton.setObjectName("ClearTablePushButton")
        self.ClearTablePushButton.setVisible(False)

        self.ResetPushButton.setEnabled(False)
        self.SavePushButton.setEnabled(False)
        self.ClearPushButton.setEnabled(False)
        self.AddPushButton.setEnabled(False)
        self.EditPushButton.setEnabled(False)
        self.DeletePushButton.setEnabled(False)    

        self.scrollArea = QtWidgets.QScrollArea(self.frame)
        self.scrollArea.setEnabled(True)
        self.scrollArea.setGeometry(QtCore.QRect(0, 40, 301, 571))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setEnabled(False)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, -338, 285, 930))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow): # Set UI text
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.SearchBox.setPlaceholderText(_translate("MainWindow", "Search..."))
        self.ResetPushButton.setText(_translate("MainWindow", "Reset"))
        self.SavePushButton.setText(_translate("MainWindow", "OK"))
        self.ClearPushButton.setText(_translate("MainWindow", "Clear"))
        self.AddPushButton.setText(_translate("MainWindow", "Add Row"))
        self.EditPushButton.setText(_translate("MainWindow", "Edit Row"))
        self.CancelPushButton.setText(_translate("MainWindow", "Cancel"))
        self.DeletePushButton.setText(_translate("MainWindow", "Delete Row"))
        self.ClearTablePushButton.setText(_translate("MainWindow", "Clear Table"))

#-----------Table Selection Dialog Class--------------#
#------------ init Section------------------#
        
class TableSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        db_manager = DatabaseManager()
        self.setWindowTitle("Select Table")
        self.setGeometry(100, 100, 300, 100)

        self.combo_box = QComboBox(self)
        self.combo_box.setGeometry(10, 10, 280, 30)

        self.populate_table_names()

        ok_button = QPushButton("Open", self)
        ok_button.setGeometry(10, 50, 90, 30)
        ok_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.setGeometry(110, 50, 90, 30)
        cancel_button.clicked.connect(self.reject)

#--------------Table Selection Function-----------------#
        
    def populate_table_names(self):
        try:  
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.execute("SHOW TABLES")
            table_names = [row[0] for row in cursor.fetchall()]
            self.combo_box.addItems(table_names)

        finally:
            if db_manager:
                db_manager.close_connection()

    def get_selected_table(self):
        return self.combo_box.currentText()

#-----------Import Dialog Class--------------#
#------------ init Section------------------#
class ImportDialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.resize(560, 427)
        self.main_window = main_window
        self.setWindowTitle("Import")
        # Initialize csv_headers here if needed
        self.csv_headers = []

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(180, 380, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.label = QLabel(self)
        self.label.setGeometry(QtCore.QRect(40, 10, 81, 17))
        self.label.setObjectName("label")

        self.label2 = QLabel(self)
        self.label2.setGeometry(QtCore.QRect(390, 10, 111, 17))
        self.label2.setObjectName("label2")

        self.label3 = QLabel(self)
        self.label3.setGeometry(QtCore.QRect(390, 60, 111, 17))
        self.label3.setObjectName("label3")

        self.text = QLineEdit(self)
        self.text.setGeometry(QtCore.QRect(40, 30, 291, 25))
        self.text.setObjectName("text")
        self.text.setPlaceholderText("No File Selected")

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(QtCore.QRect(40, 90, 491, 271))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tableWidget.resizeColumnsToContents()

        self.button3 = QPushButton(self)
        self.button3.setGeometry(QtCore.QRect(40, 60, 89, 25))
        self.button3.setObjectName("button3")
        self.button3.setText("Choose File")

        # Replace with dynamic fetching
        self.combo_box = QComboBox(self)
        self.combo_box.setGeometry(390, 30, 111, 25)

        self.populate_table_names()

        self.label.setText("File Name:")
        self.label2.setText("Import to: ")

        self.buttonBox.accepted.connect(self.selecting_import_table)
        self.buttonBox.rejected.connect(self.reject)
        self.button3.clicked.connect(self.Openfile)

        self.file_name = None
        self.all_data = None

    def populate_table_names(self):
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.execute("SHOW TABLES")
            table_names = [row[0] for row in cursor.fetchall()]
            self.combo_box.addItems(table_names)

        except pymysql.Error as err:
            print(f"Error: {err}")
        finally:
            if db_manager:
                db_manager.close_connection()

    def get_selected_table(self):
        return self.combo_box.currentText()

    def Openfile(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV", os.getenv('HOME'), "CSV Files (*.csv);;All Files (*)", options=options)

        if file_name:
            self.text.setText(file_name)
            self.file_name = file_name
            self.all_data = pd.read_csv(file_name)
            num_rows = len(self.all_data)
            num_columns = len(self.all_data.columns)
            
            self.tableWidget.clear()
            self.tableWidget.setRowCount(num_rows)
            self.tableWidget.setColumnCount(num_columns)
            self.tableWidget.setHorizontalHeaderLabels(self.all_data.columns)
            
            for i in range(num_rows):
                for j in range(num_columns):
                    item = QTableWidgetItem(str(self.all_data.iat[i, j]))
                    self.tableWidget.setItem(i, j, item)
            self.csv_headers = list(self.all_data.columns)

    def selecting_import_table(self):
        if not self.file_name:
            QtWidgets.QMessageBox.critical(self, "Error", "No file selected.")
            return

        selected_table = self.get_selected_table()
        if selected_table:
            table_columns, table_columns_type = self.get_table_columns_from_database(selected_table)
            mapping_dialog = HeaderMappingDialog(self.csv_headers, table_columns, table_columns_type)
            if mapping_dialog.exec_() == QDialog.Accepted:
                mappings = mapping_dialog.selected_mapping()
                self.import_data_to_database(selected_table, mappings)
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No table selected.")

    def get_table_columns_from_database(self, table_name):
        selected_table = table_name
        column_names = []
        column_data_types = {}

        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}' ORDER BY ordinal_position")
            column_info = cursor.fetchall()

            column_names = [col[0] for col in column_info]
            column_data_types = {col[0]: col[1] for col in column_info}

            self.column_names = column_names  
            self.column_data_types = column_data_types
        except pymysql.Error as err:
            print(f"Error: {err}")
        finally:
            if db_manager:
                db_manager.close_connection()

        return column_names, column_data_types  
         
    def import_data_to_database(self, selected_table, mappings):
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            data = pd.read_csv(self.file_name)
            db_columns = ', '.join(mappings.values())

            for index, row in data.iterrows():
                values = []
                for csv_header, db_column in mappings.items():
                    if csv_header in data.columns:  
                        value = row[csv_header]
                        if pd.isnull(value): 
                            value = None
                        values.append(value)
                    else:
                        values.append(None)  

                placeholders = ', '.join(['%s'] * len(values))
                query = f"INSERT INTO {selected_table} ({db_columns}) VALUES ({placeholders})"
                cursor.execute(query, values)

            db_manager.db_connection.commit() 
            QtWidgets.QMessageBox.information(self, "Success", f"Imported file '{self.file_name}' to table '{selected_table}'.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error importing data: {str(e)}")

        finally:
            if db_manager:
                db_manager.close_connection()

            print(f"Importing file '{self.file_name}' to table '{selected_table}' with mappings:")
            for csv_header, db_column in mappings.items():
                print(f"- CSV Column '{csv_header}' maps to DB Column '{db_column}'")

            QtWidgets.QMessageBox.information(self, "Success", f"Imported file '{self.file_name}' to table '{selected_table}'.")

class HeaderMappingDialog(QDialog):
    def __init__(self, csv_headers, table_columns, table_columns_type):
        super().__init__()
        self.setWindowTitle("Map CSV Headers to Table Columns")

        self.csv_headers = csv_headers
        self.table_columns = table_columns
        self.column_data_types = table_columns_type

        scroll_area = QScrollArea(self)
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        layout = QVBoxLayout(content_widget)

        self.mapping_widgets = []

        for column in self.table_columns:
            if column in self.column_data_types:
                label_text = f"{column} ({self.column_data_types[column]}): "
            else:
                label_text = f"{column}: "

            label = QLabel(label_text, self)
            combo_box = QComboBox(self)
            combo_box.addItems([""] + self.csv_headers)
            layout.addWidget(label)
            layout.addWidget(combo_box)

            self.mapping_widgets.append((label, combo_box))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.resize(600, 400)  
         
    def populate_column_data_types(self):
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}' ORDER BY ordinal_position")
            column_info = cursor.fetchall()
            self.column_data_types = {col[0]: col[1] for col in column_info}

        except pymysql.Error as err:
            print(f"Error: {err}")
        finally:
            if db_manager:
                db_manager.close_connection()

    def selected_mapping(self):
        mapping = {}
        for label, combo_box in self.mapping_widgets:
            csv_header = combo_box.currentText()
            if csv_header:
                mapping[label.text().split()[0]] = csv_header 
        return mapping
    
#-----------Print Preview Class--------------#
#------------ init Section------------------#

class PrintView(QTextEdit):
    dpi = 72
    doc_width = 8.5 * dpi
    doc_height = 6 * dpi

    def __init__(self):
        super().__init__(readOnly=True)
        self.setFixedSize(QSize(int(self.doc_width), int(self.doc_height)))

    def build_invoice(self, data):
        document = QTextDocument()
        self.setDocument(document)
        document.setPageSize(QSizeF(int(self.doc_width), int(self.doc_height)))
        document.setDefaultFont(font)
        cursor = QTextCursor(document)

        return document

class TableSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Table")
        self.setGeometry(100, 100, 300, 100)

        self.combo_box = QComboBox(self)
        self.combo_box.setGeometry(10, 10, 280, 30)

        self.populate_table_names()

        ok_button = QPushButton("Open", self)
        ok_button.setGeometry(10, 50, 90, 30)
        ok_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.setGeometry(110, 50, 90, 30)
        cancel_button.clicked.connect(self.reject)

    def populate_table_names(self):
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()
                    
            cursor.execute("SHOW TABLES")
            table_names = [row[0] for row in cursor.fetchall()]
            self.combo_box.addItems(table_names)

        except pymysql.Error as err:
            print(f"Error: {err}")
        finally:
            if db_manager:
                db_manager.close_connection()

    def get_selected_table(self):
        return self.combo_box.currentText()

#-----------Main Window Class--------------#
#------------ init Section------------------#
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()  
        self.ui.setupUi(self)  
        self.initUI()
        self.login_dialog = login_dialog
        
        self.selected_row = None  
        self.num_columns = 0
        self.adding_row_mode = False
        self.unsaved_changes = False
        self.column_names = None
        data = 0
        self.view_mode = False
        self.edited_rows_list = []
        self.selected_table = None

        self.layout = self.ui.verticalLayout
        self.labels = []
        self.lineedit = {}

        self.PrintView = PrintView()

        self.table_name = QtWidgets.QLabel(self)
        self.table_name.setGeometry(QtCore.QRect(10, 25, 300, 25))
        self.table_name.setVisible(False)

    def initUI(self):
        self.ui.SearchBox.textChanged.connect(self.search)
        self.ui.AddPushButton.clicked.connect(self.add_row)
        self.ui.DeletePushButton.clicked.connect(self.delete_row)
        self.ui.SavePushButton.clicked.connect(self.save_changes) 
        self.ui.ClearPushButton.clicked.connect(self.clear_data)
        self.ui.ResetPushButton.clicked.connect(self.reset_data)
        self.ui.EditPushButton.clicked.connect(self.edit_row)
        self.ui.CancelPushButton.clicked.connect(self.cancel_edit)
                                                                     
        # Create Menu Bar
        self.menubar = self.menuBar()

        # File Menu
        self.file_menu = self.menubar.addMenu('&File')

        self.open_action = QAction('Open', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.triggered.connect(self.open_table_window)

        self.save_action = QAction('Save', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self.save_table_to_database)
        self.save_action.setDisabled(True)  # Initially disabled

        self.importm_action = QAction('Import', self)
        self.importm_action.setShortcut('Ctrl+Shift+O')
        self.importm_action.triggered.connect(self.import_csv)
        self.importm_action.setDisabled(False)
        
        self.export_action = QAction('Export', self)
        self.export_action.setShortcut('Ctrl+Shift+S')
        self.export_action.triggered.connect(self.export_csv)
        self.export_action.setDisabled(True)  # Initially disabled
                
        self.print_action = QAction ('Print', self)
        self.print_action.setShortcut('Ctrl+P')
        self.print_action.triggered.connect(self.printpreviewDialog)
        self.print_action.setDisabled(True)  # Initially disabled
                
        self.exit_action = QAction ('Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(self.exit_window)

        self.refresh_action = QAction('Refresh', self)
        self.refresh_action.setShortcut('F5')
        self.refresh_action.triggered.connect(self.refresh_table)
        self.refresh_action.setDisabled(True)  # Initially disabled

        self.file_menu.addAction(self.open_action)       
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.importm_action)
        self.file_menu.addAction(self.export_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.print_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.refresh_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
                        
#----------Open, Save, Import, Export, Close, and Exit (File Menu) Function Section -----------------------#
        
    def open_table_window(self):
        dialog = TableSelectDialog(self)
        result = dialog.exec_()         

        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.labels.clear()

        for line_edit in self.lineedit.values():
            self.layout.removeWidget(line_edit)
            line_edit.deleteLater()
        self.lineedit.clear()
        
        if result == QDialog.Accepted: 
            self.selected_table = dialog.get_selected_table()     
            if self.selected_table:
                self.open_table_from_database(self.selected_table)
                self.enabled_function()  


    def enabled_function(self):
        selected_table = self.selected_table
        self.save_action.setEnabled(True)
        self.export_action.setEnabled(True)
        self.print_action.setEnabled(True)  
        self.ui.AddPushButton.setEnabled(True)
        self.ui.AddPushButton.setVisible(True)
        self.ui.DeletePushButton.setEnabled(True)
        self.ui.DeletePushButton.setVisible(True)
        self.ui.EditPushButton.setEnabled(False)
        self.ui.EditPushButton.setText("Edit")
     
    def open_table_from_database(self, selected_table):
        self.ui.tableWidget.clearContents()
        self.refresh_action.setEnabled(True)
        self.table_name.setVisible(True)
        self.table_name.setText(f"Currently Viewing: {selected_table}")
        self.cancel_edit()
        self.enabled_function()
        self.selected_table = selected_table
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            # Retrieve column information
            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}' ORDER BY ordinal_position")
            column_info = cursor.fetchall()

            column_names=[]
            column_names = [col_name for col_name, _ in column_info]
            
            column_data_types = {col_name: data_type for col_name, data_type in column_info}
            self.column_data_types = column_data_types

            query = f"SELECT * FROM {selected_table}"
            cursor.execute(query)
            data = cursor.fetchall()
        
            self.num_columns = len(column_names)  
            self.table_data = data
    
        finally:
            if db_manager:
                db_manager.close_connection()

            self.ui.tableWidget.setColumnCount(self.num_columns)
            self.ui.tableWidget.setHorizontalHeaderLabels(column_names)

            self.column_names = column_names 
            header_labels = column_names  
            self.load_data_to_table_widget(self.table_data, column_names)

            for col_num, column_name in enumerate(self.column_names):
                label = QLabel(header_labels[col_num])
                lineedit = QLineEdit()
                self.layout.addWidget(label)
                self.layout.addWidget(lineedit)
                self.labels.append(label)
                self.lineedit[column_name] = lineedit
                
            if self.ui.tableWidget.rowCount() > 0:
                self.ui.tableWidget.selectRow(0)
                self.ui.tableWidget.setFocus()

            selected_rows = self.ui.tableWidget.selectionModel().selectedRows()
            if selected_rows:
                self.ui.EditPushButton.setEnabled(True)

            self.ui.tableWidget.resizeColumnsToContents()

    def load_data_to_table_widget(self, data, header_labels):
        self.ui.tableWidget.setColumnCount(len(header_labels))
        self.ui.tableWidget.setRowCount(len(data))

        for row_num, row_data in enumerate(data):
            for col_num, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.ui.tableWidget.setItem(row_num, col_num, item)

    def import_csv(self): # import table from .csv file
        dialog = ImportDialog(self)    
        result = dialog.exec_()     

    def export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
        
        if file_path:
            # Check if the file has the .csv extension, and add it if not
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"

            try:
                db_manager = DatabaseManager()
                db_manager.connect_to_database()
                cursor = db_manager.db_connection.cursor()

                query = f"SELECT * FROM {self.selected_table}"
                cursor.execute(query)
                data = cursor.fetchall()

                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.selected_table}' ORDER BY ordinal_position")
                column_info = cursor.fetchall()
                column_names = [col_name for col_name, in column_info]

                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    writer.writerow(column_names)
                    
                    for row_data in data:
                        writer.writerow(row_data)
            finally:
                if db_manager:
                    db_manager.close_connection()
                    QMessageBox.information(self, "Success", "Data exported to CSV.")
                
    def convert_to_data_type(self, data, data_type):
        if data_type == "int":
            return int(data)
        elif data_type == "date":
            try:
                date_obj = datetime.strptime(data, "%Y/%m/%d") or datetime.strptime(data, "%Y-%m-%d")   # Date format "yyyy-mm-dd" 
                return date_obj
            except ValueError:
                return None
        else:
            return str(data)

    def save_table_to_database(self):
        if self.selected_table:
            try:
                db_manager = DatabaseManager()
                db_manager.connect_to_database()
                cursor = db_manager.db_connection.cursor()

                with db_manager.db_connection.cursor() as cursor:
                    cursor.execute(f"TRUNCATE TABLE {self.selected_table}")

                    insert_query = f"INSERT INTO {selected_table} (`{'`, `'.join([col.replace('`', '``') for col in column_names])}`) VALUES ({', '.join(['%s'] * len(column_names))})"
                    values_list = []

                    for row in range(self.ui.tableWidget.rowCount()):
                        row_data = [self.ui.tableWidget.item(row, col).text() for col in range(self.ui.tableWidget.columnCount())]

                        converted_data = [self.convert_to_data_type(data, self.column_data_types.get(column, "str")) for data, column in zip(row_data, self.column_names)]
                        values_list.append(converted_data)

                    cursor.executemany(insert_query, values_list)
                    db_manager.db_connection.commit()
            
                self.unsaved_changes = False
                self.record_changes()
            except Exception as e:
                db_manager.db_connection.rollback()

            finally:
                if db_manager:
                    db_manager.db_connection.commit()
                    db_manager.close_connection()
                    QMessageBox.information(self, "Success", "Data saved to the database.")
        else:
            None
        
    def printpreviewDialog(self, data):
        previewDialog = QPrintPreviewDialog()
        previewDialog.paintRequested.connect(self.printPreview)
        previewDialog.exec_()


    def printPreview(self, printer):
        data = self.table_data 
        document = self.PrintView.build_invoice(data)
        document.print_(printer)

        model = self.ui.tableWidget.model()

        doc = QtGui.QTextDocument()

        html = """
        <html>
        <head>
        <style>
        body {
          background-color: white;
        }
        table, th, td {
          border: 2px solid black;
          border-collapse: collapse;
        }
        </style>
        </head>"""
        html += "<body> <b>MASTER "
        html += "{}".format(self.selected_table)
        html += "</b> <br>"
        html += "<table><thead>"
        html += "<tr>"
        for c in range(model.columnCount()):
            html += "<th>| {}</th>".format(model.headerData(c, QtCore.Qt.Horizontal))

        html += "</tr></thead>"
        html += "<tbody>"
        for r in range(model.rowCount()):
            html += "<tr>"
            for c in range(model.columnCount()):
                html += "<td>| {}</td>".format(model.index(r, c).data() or "")
            html += "</tr>"
        html += "</tbody></table></body></html>"
        doc.setHtml(html)

        doc.setPageSize(QtCore.QSizeF(printer.pageRect().size()))
        doc.print_(printer)

            
    def refresh_table(self):    
        for label in self.labels: # Clear labels 
            self.layout.removeWidget(label) # Remove item
            label.deleteLater() # Delete item
        self.labels.clear()

        for line_edit in self.lineedit.values(): # Clear line edit
            self.layout.removeWidget(line_edit)
            line_edit.deleteLater()
        self.lineedit.clear()
        if hasattr(self, 'selected_table'):
            self.ui.tableWidget.clearContents()
    ##        self.ui.tableWidget.setRowCount(0)  # Clear all rows
            self.ui.tableWidget.setColumnCount(0)  # Clear all columns
            self.open_table_from_database(self.selected_table)

    def record_changes (self):
        if self.unsaved_changes == True:
            self.table_name.setText("Currently Viewing: {} (Not saved)".format(self.selected_table))
        else:
            self.table_name.setText("Currently Viewing: {}".format(self.selected_table))
            
    def exit_window(self):
        if self.unsaved_changes == True:
            reply = QMessageBox.question(
                self,
                "There are still some Unsaved Change(s)",
                "Are you sure you want to close the Table?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                unsaved_changes = False
                sys.exit(app.exec_())
            else:
                return
        else:
            sys.exit(app.exec_())

        
#--------------Search/Filter Row Function Section ---------------------#


    def search(self, text):
        keyword = text.strip().lower()

        if not keyword:
            for row in range(self.ui.tableWidget.rowCount()):
                self.ui.tableWidget.showRow(row)
                for col in range(self.ui.tableWidget.columnCount()):
                    item = self.ui.tableWidget.item(row, col)
                    if item is not None:
                        item.setSelected(False)
        else:
            for row in range(self.ui.tableWidget.rowCount()):
                self.ui.tableWidget.showRow(row)
                is_matching = False
                for col in range(self.ui.tableWidget.columnCount()):
                    item = self.ui.tableWidget.item(row, col)
                    if item is not None:
                        cell_data = item.text()
                        if keyword in cell_data.lower():
                            is_matching = True
                if not is_matching:
                    self.ui.tableWidget.hideRow(row)


#---------------Buttons Function Section--------------------#
                    
    def edit_row(self):
        today = date.today()
        date_obj = today.strftime("%Y/%m/%d")
        selected_rows = self.ui.tableWidget.selectionModel().selectedRows()
        self.ui.EditPushButton.setVisible(False)
        self.ui.CancelPushButton.setVisible(True)
        self.ui.AddPushButton.setEnabled(False)
        self.ui.DeletePushButton.setEnabled(False)
        
        if selected_rows:
            self.selected_row = selected_rows[0].row()  
            self.ui.ResetPushButton.setEnabled(True)
            self.ui.SavePushButton.setEnabled(True)
            self.ui.ClearPushButton.setEnabled(True)
            self.ui.scrollAreaWidgetContents.setEnabled(True)  # Enable the scroll area
            
            for column_name, line_edit in self.lineedit.items():
                item = self.ui.tableWidget.item(self.selected_row, self.column_names.index(column_name))
                if item is not None:
                    cell_data = item.text()
                    line_edit.setText(cell_data)    
                        
    def cancel_edit(self):        
        for line_edit in self.lineedit.values():
            line_edit.clear()

        self.ui.scrollAreaWidgetContents.setEnabled(False)  # Disable editing mode
        self.ui.ResetPushButton.setEnabled(False)
        self.ui.SavePushButton.setEnabled(False)
        self.ui.ClearPushButton.setEnabled(False)
        self.ui.CancelPushButton.setVisible(False)
        self.ui.EditPushButton.setVisible(True)
        self.ui.tableWidget.setEnabled(True)
        self.ui.AddPushButton.setEnabled(True)
        self.ui.DeletePushButton.setEnabled(True)
        self.enabled_function() 

        if self.adding_row_mode == True:
            self.delete_row()

    def validate_inputs(self, column_name, line_edit):
        if isinstance(line_edit, QLineEdit):
            user_input = line_edit.text()
            if not user_input.strip():
                QMessageBox.warning(self, "Validation Error", f"Column '{column_name}' should not be empty.")
                line_edit.setFocus()
                return False
        elif isinstance(line_edit, QComboBox):
            user_input = line_edit.currentText()
            if not user_input.strip():
                QMessageBox.warning(self, "Validation Error", f"Column '{column_name}' should not be empty.")
                line_edit.setFocus()
                return False

        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()
            query = f"SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.selected_table}' AND COLUMN_NAME = '{column_name}'"
            cursor.execute(query)
            is_nullable = cursor.fetchone()
            if is_nullable and is_nullable[0] == 'NO':
                if not user_input.strip():
                    QMessageBox.warning(self, "Validation Error", f"Column '{column_name}' should not be empty.")
                    line_edit.setFocus()
                    return False
        finally:
            db_manager.close_connection()

        return True

    def save_changes(self):
        selected_rows = self.ui.tableWidget.selectionModel().selectedRows()

        if not selected_rows:
            return

        for row in selected_rows:
            for col_num, column_name in enumerate(self.column_names):
                line_edit = self.lineedit.get(column_name)
                if line_edit is not None:
                    if isinstance(line_edit, QLineEdit):
                        if not self.validate_inputs(column_name, line_edit):
                            return  # Abort saving 
                        new_text = line_edit.text()
                        
                    item = QTableWidgetItem(new_text)
                    self.ui.tableWidget.setItem(row.row(), col_num, item)

        if isinstance(line_edit, QLineEdit):
            line_edit.clear()
            line_edit.setStyleSheet("")
        elif isinstance(line_edit, QComboBox):
            line_edit.setCurrentIndex(-1)

        self.ui.scrollAreaWidgetContents.setEnabled(False)  # Disable editing mode
        self.ui.ResetPushButton.setEnabled(False)
        self.ui.SavePushButton.setEnabled(False)
        self.ui.ClearPushButton.setEnabled(False)
        self.ui.CancelPushButton.setVisible(False)
        self.ui.EditPushButton.setVisible(True)
        self.ui.tableWidget.setEnabled(True)
        self.clear_data()
        self.unsaved_changes = False
        self.record_changes()
        self.enabled_function() 
        return True  

    def clear_data(self):   # Clear the data in line edits for the selected(edited) columns
        for column_name, line_edit in self.lineedit.items():
            if isinstance(line_edit, QLineEdit):
                line_edit.clear()
                line_edit.setStyleSheet("")
            elif isinstance(line_edit, QComboBox):
                line_edit.setCurrentIndex(-1)

    def reset_data(self):   # Reset line edits with the original data from the selected(edited) row
        selected_rows = self.ui.tableWidget.selectionModel().selectedRows()

        if selected_rows:
            for row in selected_rows:
                for col_num, line_edit in enumerate(self.lineedit.values()):
                    item = self.ui.tableWidget.item(row.row(), col_num)    
                    if item:
                        line_edit.setText(item.text())
                    else:
                        line_edit.clear()

    def add_row(self):
        self.adding_row_mode = True
        row = -1
        id_column = -1
        for column in range(self.ui.tableWidget.columnCount()):
            header = self.ui.tableWidget.horizontalHeaderItem(column)
            if header is not None and header.text() == 'ID':
                id_column = column
                break

        # If the 'ID' column is not found, use the first column
        if id_column == -1:
            id_column = 0

        # Calculate the new ID based on existing rows
        latest_id = 0
        for row in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(row, id_column)
            if item:
                id_value = int(item.text())
                latest_id = max(latest_id, id_value)

        new_id = latest_id + 1

        self.ui.tableWidget.insertRow(self.ui.tableWidget.rowCount())
        id_item = QTableWidgetItem(str(new_id))
        self.id_item = id_item
        
        self.ui.tableWidget.setItem(self.ui.tableWidget.rowCount() - 1, id_column, id_item)  # Use the determined ID column

        self.ui.tableWidget.selectRow(row + 1)
        self.edit_row()

    def delete_row(self): # Delete data(row) from table
        selected_rows = self.ui.tableWidget.selectionModel().selectedRows()

        if self.adding_row_mode == False:
            if selected_rows:
                reply = QMessageBox.question(
                    self,
                    "Delete Row",
                    "Are you sure you want to delete the selected row?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.unsaved_changes = True
                    self.record_changes()
                    selected_rows = sorted(selected_rows, key=lambda x: x.row(), reverse=True)
                    for row in selected_rows:
                        self.ui.tableWidget.removeRow(row.row())
        if self.adding_row_mode == True:
            selected_rows = sorted(selected_rows, key=lambda x: x.row(), reverse=True)
            for row in selected_rows:
                self.ui.tableWidget.removeRow(row.row())
                        
#-------------------------------------------------------------#

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    db_manager = DatabaseManager()

    if login_dialog.exec_() == QDialog.Accepted:
        main_window = MainWindow()
        main_window.show()
    sys.exit(app.exec_())
