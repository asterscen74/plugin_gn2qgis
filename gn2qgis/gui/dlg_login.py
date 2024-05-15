# -*- coding: utf-8 -*-

# PyQt libs
from PyQt5.QtCore import QJsonDocument, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton

# QGIS lib
from qgis.PyQt.Qt import QUrl
from qgis.PyQt.QtGui import QDesktopServices

from gn2qgis.__about__ import __geonature__, __geonature_login__, __geonature_domain__


class LoginDialog(QDialog):
    finished_dl = pyqtSignal()

    def __init__(self, network_manager=None):
        QDialog.__init__(self)

        # Login window parameters
        self.setWindowTitle("Login GeoNature")

        self.network_manager = network_manager

        self.cookies = None
        self.accepted = None

        self.resize(469, 204)
        # Create an account part
        self.service_label = QLabel(self)
        self.service_label.setText("Se connecter à " + __geonature_domain__)
        self.service_label.setGeometry(9, 20, 300, 20)
        self.create_account = QPushButton(self)
        self.create_account.setText(self.tr("Créer un compte"))
        self.create_account.setGeometry(300, 20, 150, 23)
        self.create_account.clicked.connect(self.open_url)
        # login with username and password part
        self.user_label = QLabel(self)
        self.user_label.setGeometry(9, 112, 123, 23)
        self.user_label.setText("Nom d'utilisateur :")
        self.password_label = QLabel(self)
        self.password_label.setGeometry(9, 141, 123, 23)
        self.password_label.setText("Mot de passe :")
        self.lne_user = QLineEdit(self)
        self.lne_user.setGeometry(138, 112, 322, 23)
        self.lne_user.setText("")
        self.lne_password = QLineEdit(self)
        self.lne_password.setEchoMode(QLineEdit.Password)
        self.lne_password.setText("")
        self.lne_password.setGeometry(138, 141, 322, 23)
        
        # Button to validate the login and password.
        ok_button = QPushButton("OK", self)
        # When the ok button is clicked the validation process start
        ok_button.clicked.connect(self.check_password)
        ok_button.resize(100, 25)
        ok_button.move(350, 170)
        
        # Label for the wrong password error message.
        self.wrongPasswordLabel = QLabel(self)
        self.wrongPasswordLabel.setText("")
        self.wrongPasswordLabel.move(20, 80)
        self.wrongPasswordLabel.resize(200, 30)

    def open_url(self):
        # Function to open the url of the buttons
        url = QUrl(__geonature__)
        QDesktopServices.openUrl(url)

    def check_password(self):
        # Validation of the user credentials informations
        if self.lne_password.text() != "":
            url = QUrl(__geonature_login__)
            request = QNetworkRequest(url)
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            # Add credentials to a json
            json_data = {
                "login": self.lne_user.text(),
                "password": self.lne_password.text(),
            }
            document = QJsonDocument(json_data)
            # Post request to test credentials
            reply = self.network_manager.post(request, document.toJson())
            # Once the asynchronous request is finished, we check the password
            reply.finished.connect(lambda: self.validate_password(reply))

    def validate_password(self, reply):
        # Only the password is validated, there is no information on the login
        # If there is an error the message WRONG PASSWORD appear.
        # Problem, if there is no connection, or the url is wrong or anything else, the same message appear
        # TO DO change error message depending on the error code
        if reply.error() != QNetworkReply.NoError:
            self.wrongPasswordLabel.setText("MAUVAIS MOT DE PASSE !!")
            self.lne_password.setText("")
            print(f"code: {reply.error()} message: {reply.errorString()}")
        else:
            # Create the token to connect to the API
            self.cookies = self.network_manager.cookieJar()
            # Delete password from the line
            del self.lne_password
            # Show login as accepted
            self.accepted = True
            # Set login as finished to launch the process
            self.close()
            self.finished_dl.emit()
