# -*- coding: utf-8 -*-
import os
import stripe
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
    def _init_(self, app):
        self.db_connection = None
        self.app = app

    def connect_to_database(self):
        try:
            self.db_connection = pymysql.connect(
                host= dbhost, 
                user= dbusername,
                password= dbpassword,
                database= dbdatabase,
                charset='utf8mb4'
            ) 
            if not self.db_connection:
                self.show_warning("Cannot Connect to Database")

        except pymysql.Error as err:
            self.show_warning("Database Connection Error: {}".format(err))

    def close_connection(self):
        if self.db_connection:
            self.db_connection.close()

    def show_warning(self, message):
        QMessageBox.warning(None, "Error", message)


#-------------Check User Credential from Database (User Authentication Dialog)--------------------#
def check_credentials(entered_username, entered_password):
    Type = None
    try:
        db_manager = DatabaseManager()  
        db_manager.connect_to_database()         
        cursor = db_manager.db_connection.cursor()

        query = f"SELECT Username, Password, Type FROM User WHERE Username = '{entered_username}'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result and result[1] == entered_password:
            Type = result[2]
            return True, Type  # Return authentication result
        else:
            return False, Type  # Return authentication result (False)
    finally:
        if db_manager:
            db_manager.close_connection()

#---------- Check User in Database (User Creation Dialog) Function-----------------#
def check_existed_user(new_username, new_email):
    db_manager = DatabaseManager()
    db_manager.connect_to_database()
    cursor = db_manager.db_connection.cursor()

    query_username = "SELECT Username FROM User WHERE Username = %s"
    cursor.execute(query_username, (new_username,))
    result_username = cursor.fetchone()

    query_email = "SELECT Email FROM User WHERE Email = %s"
    cursor.execute(query_email, (new_email,))
    result_email = cursor.fetchone()

    if result_username:
        cursor.close()
        return 1
    elif result_email:
        cursor.close()
        return 2
    else:
        cursor.close()
        return 0  # Both username and email are available

#-----------Create New User Dialog Class--------------#
#------------ init Section------------------#
class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Create New User")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setGeometry(100, 100, 300, 150)

        self.create_username_label = QLabel("Username:", self)
        self.create_username_label.setGeometry(10, 10, 280, 20)

        self.create_password_label = QLabel("Password:", self)
        self.create_password_label.setGeometry(10, 70, 280, 20)

        self.create_email_label = QLabel("Email:", self)
        self.create_email_label.setGeometry(10, 40, 280, 20)

        self.create_username_edit = QLineEdit(self)
        self.create_username_edit.setGeometry(100, 10, 190, 20)

        self.create_password_edit = QLineEdit(self)
        self.create_password_edit.setGeometry(100, 70, 190, 20)
        
        self.create_email_edit = QLineEdit(self)
        self.create_email_edit.setGeometry(100, 40, 190, 20)

        self.create_login_button = QPushButton("Create", self)
        self.create_login_button.setGeometry(50, 100, 90, 30)
        self.create_login_button.clicked.connect(self.register_new_user)

        self.create_cancel_button = QPushButton("Cancel", self)
        self.create_cancel_button.setGeometry(160, 100, 90, 30)
        self.create_cancel_button.clicked.connect(self.reject)

        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

#-------------New User Creation Functions---------------#
    def register_new_user(self):
        new_username = self.create_username_edit.text()
        new_email = self.create_email_edit.text()
        new_password = self.create_password_edit.text()
        db_manager = DatabaseManager()
        db_manager.connect_to_database()
        if not new_username or not new_email or not new_password:
            error = 3
        else:
            error = check_existed_user(new_username, new_email)

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

                query = f"INSERT INTO User (ID, Username, Email, Password, Type) " \
                        f"VALUES ('{new_id}', '{new_username}', '{new_email}', '{new_password}', 'admin')"
                cursor.execute(query)
                db_manager.db_connection.commit()
                db_manager.close_connection()
    
                return True  # User registration was successful
            
            elif error == 1:
                QMessageBox.warning(self, "Username already exists", "Please choose a different username.")
            elif error == 2:
                QMessageBox.warning(self, "Email already exists", "Please choose a different email address.")
            elif error == 3:
                QMessageBox.warning(self, "Empty Fields", "Please fill in all the required fields.")
            
        return False
            
#-----------Login Dialog Class--------------#
#------------ init Section------------------#

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 300, 150)
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
            self.Type = Type
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
        try:  # Establish a database connection
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.execute("SHOW TABLES")
            table_names = [row[0] for row in cursor.fetchall()]
            self.combo_box.addItems(table_names)

        finally:        # Close the database connection
            if db_manager:
                db_manager.close_connection()

    def get_selected_table(self):
        return self.combo_box.currentText()

#-----------Import Dialog Class--------------#
#------------ init Section------------------#
class Import_Dialog(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.resize(560, 427)
        self.main_window = main_window
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(180, 380, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(40, 10, 81, 17))
        self.label.setObjectName("label")

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setGeometry(QtCore.QRect(390, 10, 111, 17))
        self.label2.setObjectName("label2")

        self.label3 = QtWidgets.QLabel(self)
        self.label3.setGeometry(QtCore.QRect(390, 60, 111, 17))
        self.label3.setObjectName("label3")

        self.text = QtWidgets.QLineEdit(self)
        self.text.setGeometry(QtCore.QRect(40, 30, 291, 25))
        self.text.setObjectName("text")
        self.text.setPlaceholderText("No File Selected")

        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setGeometry(QtCore.QRect(40, 90, 491, 271))
        self.tableWidget.setObjectName("table")
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tableWidget.resizeColumnsToContents()

        self.button3 = QtWidgets.QPushButton(self)
        self.button3.setGeometry(QtCore.QRect(40, 60, 89, 25))
        self.button3.setObjectName("button3")

        self.combo_box = QComboBox(self)
        self.combo_box.setGeometry(390, 30, 111, 25)

        table_names = ["Table1", "Table2", "Table3", "Table4", "Table5"]
        self.combo_box.addItems(table_names)

        self.setWindowTitle("Import")
        self.label.setText("File Name:")
        self.label2.setText("Import to: ")
        self.button3.setText("Choose File")

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.button3.clicked.connect(self.Openfile)

        self.buttonBox.accepted.connect(self.import_to_database)

        # Determine the selected table
        self.import_to_table = None
        self.newacc = None

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
                
    def determine_table(self, column_names):
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()
            col_name_set = None
            col_name2_set = None

            self.table_to_import = self.combo_box.currentText()

            if self.table_to_import == 'Table1':
                col_name = [] # Add Table possible column/header
                col_name = [item.lower().replace(" ", "") for item in col_name]
                col_name_set = set(col_name)
                
            elif self.table_to_import == 'Table2':   
                col_name = []
                col_name = [item.lower().replace(" ", "") for item in col_name]
                col_name_set = set(col_name)
                
            column_names = [item.lower().replace(" ", "") for item in column_names]
            column_names_set = set(column_names)

            if column_names_set == col_name_set:
                    return True
            else:
                QMessageBox.information(self, "Error",
                                        "CSV file format don't match with {}.".format(self.table_to_import))
                return False
        finally:
            if db_manager:
                db_manager.close_connection()

    def import_to_database(self):
        if not self.text.text():  # Check if the line edit is empty
            QMessageBox.information(self, "Error", "No CSV file selected.")
              # Exit the function if no file is selected
        cancel = self.determine_table(self.all_data.columns)
        if not cancel:
            return
        else:
            try:
                db_manager = DatabaseManager()
                db_manager.connect_to_database()
                cursor = db_manager.db_connection.cursor()

                selected_table = self.combo_box.currentText()
                pd.read_csv(self.file_name)
                                    
                row_count = 0
                rowcountcomp = 0

                if selected_table == "Table1":
                    cursor.execute("SELECT MAX(ID) FROM Table3")
                    ID_result = cursor.fetchone()
                    ID_ = ID_result[0] if (
                            ID_result is not None and ID_result[0] is not None) else 0

                    data = pd.read_csv(self.file_name)
                    df = pd.DataFrame(data)
                    df = df.fillna('')

                    # Get the directory of the current script
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_csv_path1 = os.path.join(script_dir, 'temp_data1.csv')

                    # Lists to store the rows for each table
                    data_rows = []

                    for index, row in df.iterrows():
                        ID = ID + 1
                        row_count += 1
                        column1 = row['column1']
                        column2 = row['column2']
                        
                        # Append data to lists
                        data_rows.append(
                            [column1, column2])

                    # Write data to temporary CSV files
                    pd.DataFrame(data_rows,
                                 columns=['column1', 'column2']).to_csv(temp_csv_path1, index=False)

                    # Create a MySQL connection
                    engine = create_engine(f'mysql+pymysql://{dbusername}:{dbpassword}@{dbhost}:3306/{dbdatabase}',
                                       connect_args={'ssl_disabled': True}) 

                    # Read CSV data
                    data = pd.read_csv(temp_csv_path1)

                    # Truncate both tables to remove existing data
                    cursor.execute("TRUNCATE TABLE Table3")

                    # Use sqlalchemy to load data into Table1 and Table2
                    data.to_sql('Table3', engine, if_exists='append', index=False)

                    # Commit changes
                    engine.dispose()  # Close the connection

                    os.remove(temp_csv_path1)
                    QMessageBox.information(self, "Success",
                                            "All {} row(s) data saved to the database.".format(row_count))
                        
            finally:
                if db_manager:
                    db_manager.close_connection()



#-----------Create Invoice Class--------------#
#------------ init Section------------------#
class CreateInvoice(QDialog):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.resize(319, 160)
        self.label_4 = QtWidgets.QLabel(self)
        self.label_4.setGeometry(QtCore.QRect(53, 53, 67, 17))
        self.label_4.setObjectName("label_4")
        self.dateEdit_2 = QtWidgets.QDateEdit(self)
        self.dateEdit_2.setGeometry(QtCore.QRect(123, 49, 121, 26))
        self.dateEdit_2.setDateTime(QtCore.QDateTime(QtCore.QDate(2023, 1, 1), QtCore.QTime(0, 0, 0)))
        self.dateEdit_2.setCalendarPopup(False)
        self.dateEdit_2.setObjectName("dateEdit_2")
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(-40, 110, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.buttonBox.accepted.connect(self.callprocedure)
        self.buttonBox.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.setWindowTitle("Invoice")
        self.label_4.setText("YY/MM :")
        self.dateEdit_2.setDisplayFormat("yyyy/MM")
        
    def callprocedure(self):                        
        # Get the date from the QDateEdit widget
        selected_date = self.dateEdit_2.date()

        # Extract year and month
        year = selected_date.year()
        month = selected_date.month()

        Username = login_username
        
        # Determine the number of days in the given month
        _, last_day = calendar.monthrange(year, month)

        Tgl1 = f"{year}-{month:02d}-01"
        Tgl2 = f"{year}-{month:02d}-{last_day}"
        self.Tgl1=Tgl1
        self.Tgl2=Tgl2
        
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.callproc('Procedure1', (Username, Tgl1, Tgl2))
            cursor.callproc('Procedure2', (Username, Tgl1, Tgl2))
            db_manager.db_connection.commit()
            
        finally:
            QMessageBox.information(self, "Success",
            "Finish Calling Stored Procedures")
            cursor.close()
            db_manager.close_connection()

        
#-----------Print Preview Class--------------#
#------------ init Section------------------#

class InvoiceView(QTextEdit):
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

#-----------Main Window Class--------------#
#------------ init Section------------------#
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()  
        self.ui.setupUi(self)  
        self.initUI()
        self.login_dialog = login_dialog
        self.selected_row = None  # Initialize selected_row attribute
        self.num_columns = 0
        self.adding_row_mode = False
        self.unsaved_changes = False
        self.column_names = None
        data = 0
        self.view_mode = False
        self.edited_rows_list = []

        self.layout = self.ui.verticalLayout
        self.labels = []
        self.lineedit = {}

        self.invoiceView = InvoiceView()

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
        self.ui.ClearTablePushButton.clicked.connect(self.clear_table)
                                                                     
        # Create Menu Bar
        self.menubar = self.menuBar()

        # File Menu
        self.file_menu = self.menubar.addMenu('&File')
        
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

        # Table Menu
        self.User = self.menubar.addAction('User')
        self.User.triggered.connect(self.user_table)
        
        self.Table1 = self.menubar.addAction('Table1')
        self.Table1.triggered.connect(self.Table1_table)

        self.Table2 = self.menubar.addAction('Table2')
        self.Table2.triggered.connect(self.Table2_table)

        self.Table3 = self.menubar.addAction('Table3')
        self.Table3.triggered.connect(self.Table3_table)        

#---------------------Table Menu-------------------------------#
    def user_table(self):
        self.selected_table = "User"
        self.open_table_window()

    def Table1_table(self):
        self.selected_table = "Table1"
        self.open_table_window()

    def Table2_table(self):
        self.selected_table = "Table2"
        self.open_table_window()

    def Table3_table(self):
        self.selected_table = "Table3"
        self.open_table_window()

#--------------------Clear Table Function(Table3)-------------------------#
    def clear_table (self):
        reply = QMessageBox.question(
            self,
            "Delete Table",
            "Are you sure you want to clear the table?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                db_manager = DatabaseManager()
                db_manager.connect_to_database()
                cursor = db_manager.db_connection.cursor()
                
                cursor.execute(f"TRUNCATE TABLE {self.selected_table}")
            finally:
                if db_manager:
                    db_manager.db_connection.commit()
                    db_manager.close_connection()
                    QMessageBox.information(self, "Success", "Data saved to the database.")
        else:
            None
                        
#----------Open, Save, Import, Export, Close, and Exit (File Menu) Function Section -----------------------#
        
    def open_table_window(self):         # Open Table Selection Dialog
        selected_table = self.selected_table

        for label in self.labels: # Clear labels 
            self.layout.removeWidget(label) # Remove item
            label.deleteLater() # Delete item
        self.labels.clear()

        for line_edit in self.lineedit.values(): # Clear line edit
            self.layout.removeWidget(line_edit)
            line_edit.deleteLater()
        self.lineedit.clear()
        
        if selected_table:
            self.open_table_from_database(selected_table)   # Open the selected table from the database
            self.enabled_function() # Enable/Disable button and action accoring to the table being opened

    def enabled_function(self):
        selected_table = self.selected_table
        if selected_table == "User": # Default (Add, Delete, Edit, Import, Export)
            self.save_action.setEnabled(True)
            self.export_action.setEnabled(True)
            self.print_action.setEnabled(True)  
            self.ui.AddPushButton.setEnabled(True)
            self.ui.AddPushButton.setVisible(True)
            self.ui.DeletePushButton.setEnabled(True)
            self.ui.DeletePushButton.setVisible(True)
            self.ui.EditPushButton.setEnabled(False)
            self.ui.EditPushButton.setText("Edit")
            self.view_mode = False
            self.ui.ClearTablePushButton.setVisible(False)
        if selected_table == "Table1": # Default (Add, Delete, Edit, Import, Export)
            self.save_action.setEnabled(True)
            self.export_action.setEnabled(True)
            self.print_action.setEnabled(True)  
            self.ui.AddPushButton.setEnabled(True)
            self.ui.AddPushButton.setVisible(True)
            self.ui.DeletePushButton.setEnabled(True)
            self.ui.DeletePushButton.setVisible(True)
            self.ui.EditPushButton.setEnabled(False)
            self.ui.EditPushButton.setText("Edit")
            self.view_mode = False
            self.ui.ClearTablePushButton.setVisible(False)
        if selected_table == "Table2": # Default (Add, Delete, Edit, Import, Export)
            self.save_action.setEnabled(True)
            self.export_action.setEnabled(True)
            self.print_action.setEnabled(True)  
            self.ui.AddPushButton.setEnabled(True)
            self.ui.AddPushButton.setVisible(True)
            self.ui.DeletePushButton.setEnabled(True)
            self.ui.DeletePushButton.setVisible(True)
            self.ui.EditPushButton.setEnabled(False)
            self.ui.EditPushButton.setText("Edit")
            self.view_mode = False
            self.ui.ClearTablePushButton.setVisible(False)
        if selected_table == "Table3": # Default (Add, Delete, Edit, Import, Export)
            self.save_action.setEnabled(True)
            self.export_action.setEnabled(True)
            self.print_action.setEnabled(True)  
            self.ui.AddPushButton.setEnabled(True)
            self.ui.AddPushButton.setVisible(True)
            self.ui.DeletePushButton.setEnabled(True)
            self.ui.DeletePushButton.setVisible(True)
            self.ui.EditPushButton.setEnabled(False)
            self.ui.EditPushButton.setText("Edit")
            self.view_mode = False
            self.ui.ClearTablePushButton.setVisible(False)
            
    def open_table_from_database(self, selected_table):
        self.ui.tableWidget.clearContents()
        self.refresh_action.setEnabled(True)
        self.table_name.setVisible(True)
        self.table_name.setText("Currently Viewing: {}".format(selected_table))
        self.cancel_edit()
        self.enabled_function()
                
        if not selected_table:
            return
        try:
            db_manager = DatabaseManager()
            db_manager.connect_to_database()
            cursor = db_manager.db_connection.cursor()

            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}' ORDER BY ordinal_position")
            column_info = cursor.fetchall()
            
            column_names=[]
            column_names = [col_name for col_name, _ in column_info]
            
            column_data_types = {col_name: data_type for col_name, data_type in column_info}
            self.column_data_types = column_data_types

            query = f"SELECT * FROM {selected_table}"
            cursor.execute(query)
            data = cursor.fetchall()
        
            self.num_columns = len(column_names)  # Use column_names
            self.table_data = data
            
        finally:
            if db_manager:
                db_manager.close_connection()

            self.ui.tableWidget.setColumnCount(self.num_columns)  # Use self.num_columns
            self.ui.tableWidget.setHorizontalHeaderLabels(column_names)  # Use column_names

            self.column_names = column_names  # Use column_names
            header_labels = column_names  # Use column_names
            self.load_data_to_table_widget(self.table_data, column_names)


            combo_box_columns = []

            # List of Header with 2 or 3 Default Data (changing line edit to combo box)
            if selected_table == "User":
                combo_box_columns = ["Type"]
                items = ["a", "b"]

            for col_num, column_name in enumerate(self.column_names):
                label = QLabel(header_labels[col_num])
                lineedit = QComboBox() if column_name in combo_box_columns else QLineEdit()
                self.layout.addWidget(label)
                self.layout.addWidget(lineedit)
                self.labels.append(label)
                self.lineedit[column_name] = lineedit
                if isinstance(lineedit, QComboBox): # Combo box section
                    for item in items:
                        lineedit.addItem(item)  # Add options to the combo box
                    lineedit.setCurrentIndex(-1)
                    
            if self.ui.tableWidget.rowCount() > 0: # Automatically select first row when opening new table
                self.ui.tableWidget.selectRow(0)
                self.ui.tableWidget.setFocus() # Set focus to tableWidget, so that up and down button can be use to move row selection (without clicking on the table first)

            selected_rows = self.ui.tableWidget.selectionModel().selectedRows()
            if selected_rows: # If there are row selected, enable EditPushButton (If there are no row, nothing can be edited)
                if self.view_mode == False:
                    self.ui.EditPushButton.setEnabled(True)

            self.ui.tableWidget.resizeColumnsToContents()
            
    def load_data_to_table_widget(self, data, header_labels): # Populate the QTableWidget with data
        self.ui.tableWidget.setColumnCount(len(header_labels))

        self.ui.tableWidget.setRowCount(len(data))

        for row_num, row_data in enumerate(data):
            for col_num, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.ui.tableWidget.setItem(row_num, col_num, item)

    def import_csv(self): # import table from .csv file
        dialog = Import_Dialog(self)    
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

    def import_temp(self):
        dialog = ImportToTemp(self)    
        result = dialog.exec_()     
 
    def invoice(self):
        dialog = CreateInvoice(self)    
        result = dialog.exec_()     
        
    def printpreviewDialog(self, data):
        previewDialog = QPrintPreviewDialog()
        previewDialog.paintRequested.connect(self.printPreview)
        previewDialog.exec_()


    def printPreview(self, printer):
        data = self.table_data  # You can create data here, such as customer name and other details
        document = self.invoiceView.build_invoice(data)
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

    def search(self):   # Search for rows in the table based on the keyword
        keyword = self.ui.SearchBox.text().strip().lower()

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
            self.selected_row = selected_rows[0].row()  # Store the selected row
            if self.view_mode == True:
                self.ui.tableWidget.setEnabled(True)
                self.ui.ResetPushButton.setEnabled(False)
                self.ui.SavePushButton.setEnabled(False)
                self.ui.ClearPushButton.setEnabled(False)
            else:
                self.ui.ResetPushButton.setEnabled(True)
                self.ui.SavePushButton.setEnabled(True)
                self.ui.ClearPushButton.setEnabled(True)
            self.ui.scrollAreaWidgetContents.setEnabled(True)  # Enable the scroll area
            
            for column_name, line_edit in self.lineedit.items():
                item = self.ui.tableWidget.item(self.selected_row, self.column_names.index(column_name))
                if item is not None:
                    cell_data = item.text()
                    if isinstance(line_edit, QComboBox):
                        index = line_edit.findText(cell_data)
                        if index != -1:
                            line_edit.setCurrentIndex(index)
                    else:
                        line_edit.setText(cell_data)
                if self.adding_row_mode == True:
                    if self.selected_table == "User":
                        if column_name == "Type":
                            line_edit.setCurrentIndex(0)
                        
    def cancel_edit(self):
        combo_box_columns = []
        if self.selected_table == "User":
            combo_box_columns = ["Type"]
            items = ["a", "b"]
        
        for line_edit in self.lineedit.values():
            line_edit.clear()
            if isinstance(line_edit, QComboBox):
                # Preserve the items in the combo box
                for item in items:
                    line_edit.addItem(item)
                line_edit.setCurrentIndex(-1)

        self.ui.scrollAreaWidgetContents.setEnabled(False)  # Disable editing mode
        self.ui.ResetPushButton.setEnabled(False)
        self.ui.SavePushButton.setEnabled(False)
        self.ui.ClearPushButton.setEnabled(False)
        self.ui.CancelPushButton.setVisible(False)
        self.ui.EditPushButton.setVisible(True)
        self.ui.tableWidget.setEnabled(True)
        self.ui.AddPushButton.setEnabled(True)
        self.ui.DeletePushButton.setEnabled(True)
        self.enabled_function() # Enable/Disable button and action accoring to the table being opened

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
                            return  # Abort saving if validation fails
                        new_text = line_edit.text()
                    elif isinstance(line_edit, QComboBox):
                        new_text = line_edit.currentText()

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
        self.unsaved_changes = True
        self.record_changes()
        self.enabled_function() # Enable/Disable button and action accoring to the table being opened

        return True  # Successful saving

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
