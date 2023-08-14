# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EnerniteUploaderDockWidget
                                 A QGIS plugin
 This plugins allow uploading of maps to Enernite Cloud
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-08-09
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Enernite
        email                : marius@enernite.com
 ***************************************************************************/


"""

import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl
from qgis.core import Qgis



from qgis.core import QgsCredentials

from qgis.core import QgsProject, QgsVectorLayer, QgsJsonUtils

import json

from .uploader.layer_prepare import LayerExporter

import requests

from .enernite_dockwidget_base import Ui_EnerniteUploaderDockWidgetBase


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'enernite_dockwidget_base.ui'))


class EnerniteUploaderDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(EnerniteUploaderDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.active_workspace = None
        self.uid = None
        self.bearer_token = None 
        self.error_message = None
        
        self.ui = Ui_EnerniteUploaderDockWidgetBase()

        self.ui.setupUi(self)
        print("INIT UI")

        self.ui.signInButton.clicked.connect(self.on_sign_in_clicked)
        self.ui.uploadToProjectButton.clicked.connect(self.on_upload_to_project_clicked)

        self.ui.usernameLoggedIn.hide()
        self.ui.loaderProgressBar.hide()
        self.ui.projectUploadedButton.hide() 


    def on_sign_in_clicked(self):
        username = self.ui.usernameField.text()
        password = self.ui.passwordField.text()

        print(username)

        url = 'https://api.enernite.com/auth/login'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'username': username,
            'password': password,
        }

        response = requests.post(url, headers=headers, data=data)

        # We need to store the token.

        if response.status_code == 200:
            # Successfully logged in

            # We need to store the bearer token to a variable 
            self.bearer_token = response.json()["access_token"]

            # We set the UploadToProject to be enabled
            self.ui.uploadToProjectButton.setEnabled(True)
            self.ui.passwordField.hide()
            self.ui.signInButton.hide()
            self.ui.passwordLabel.hide()
            self.ui.usernameField.hide()
            self.ui.usernameLabel.hide()

            self.ui.usernameLoggedIn.setText(f"Logged in as {username}")
            self.ui.usernameLoggedIn.show()

            

        else:
            # Handle the error
            # You may want to display an error message to the user
            print("Password was not correct")

    def open_url(self):
        url = f"https://go.enernite.com/projects/{self.project_id}"
        QDesktopServices.openUrl(QUrl(url))
        return None

    
    def on_upload_to_project_clicked(self):
        print("Initiates the uploading sequence")

        # We need to retrieve the workspace and userID of the user, it is OK if this is done each time the user clicks "UploadToPorject"

        try:
            url = 'https://api.enernite.com/auth/user/'
            headers = {
                        'accept': 'application/json',
                        'Authorization': "Bearer " + str(self.bearer_token)
                        }
            # Make the GET request
            response = requests.get(url, headers=headers)

            # Print the response (optional)
            resp_info = response.json()
            self.active_workspace = resp_info["metadata"]["active_workspace"]
            self.uid = resp_info["metadata"]["uid"]

            print("Recieved the following information")
            print(self.active_workspace)
            print(self.uid)
            print("_____")

        except Exception as E:
            print(E)
            self.error_message = E 
            print("Issue with the authentification")

        # Create a project that is shared with everyone, and where the UserToken of the logged in user is the creator 

        url = "https://enernite-odin.duckdns.org/nocode/qgis_project_initiation"
        headers = {}
        payload = {
                'jwt': str(self.bearer_token),
                'name': 'Trial',
                'shared_in_workspace': 'True', 
                'workspace_id': str(self.active_workspace),
                'user_id': str(self.uid)
                }

        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            response = json.loads(response.text)
            project_id = response[0]["project_id"]
            self.project_id = project_id
            print(f"Project initiated successfully with ID: {project_id}")
            # projectUploadedTextLabel EDIT THE ProjectUploadedTextLabel

            self.ui.projectUploadedButton.setEnabled(True)
            self.ui.projectUploadedButton.show()
            self.ui.projectUploadedButton.clicked.connect(self.open_url)



            # Access all the files in the QGIS project
            project = QgsProject.instance()
            transform_context = project.transformContext()

            exporter = LayerExporter(transform_context)


            self.ui.loaderProgressBar.show()
            length_of_project = len(project.mapLayers().items()) 

            try:

                # Iterate through the layers in the project
                for layer_id, layer in project.mapLayers().items():
                    if exporter.can_export_layer(layer):
                        try:
                            # Export the vector layer using the export_vector_layer method
                            result = exporter.export_vector_layer(layer)
                            # Here you can handle the result as needed
                            new_layer_uri, dest_file = result
                            print("Export successful:", new_layer_uri)

                        except Exception as e:
                            print("Export failed for layer:", layer_id)
                            print("Error:", str(e))
                            continue
                        
                        try:
                            # Get the source file path of the layer
                            # style = LayerExporter.representative_layer_style(layer)
                            

                            url = "https://api.enernite.com/assets/dataset/project/upload"
                            params = {
                                "project_id": project_id,
                                "crs": 4326, # TODO: Should be correct CRS
                                "refresh_user": "true"
                            }
                            headers = {
                                "accept": "application/json",
                                "Authorization": f"Bearer {self.bearer_token}",
                            }
                            

                            with open(new_layer_uri, 'rb') as file:
                                content = file.read()
                                files = {'geo_file': (str(layer.name()) + ".gpkg", content)}
                                response = requests.post(url, params=params, headers=headers, files=files)

                            if response.status_code == 200:
                                print(f"File {dest_file} uploaded successfully")

                                dataset_id = json.loads(response.content)["dataset_ids"]
                                style = LayerExporter.representative_layer_style(layer)

                                print(style)

                                if style != {}:
                                    # Add the styling 
                                    url = f"https://api.enernite.com/assets/dataset/project/"
                                    json_body = {"id": dataset_id, "style": style, "project_id": project_id}
                                    print(style)
                                    response = requests.post(url, params=json_body, headers=headers)
                                
                            else:
                                print(f"Failed to upload file {new_layer_uri}: {response.text}")
                        except Exception as E:
                            print(E)



                # exporter.__del__()
            except Exception as E:
                print(E)
                # exporter.__del__()


        else:
            print(f"Failed to initiate project: {response.text}")



    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
