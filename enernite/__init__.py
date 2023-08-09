# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EnerniteUploader
                                 A QGIS plugin
 This plugins allow uploading of maps to Enernite Cloud
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-08-09
        copyright            : (C) 2023 by Enernite
        email                : marius@enernite.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load EnerniteUploader class from file EnerniteUploader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .enernite import EnerniteUploader
    return EnerniteUploader(iface)