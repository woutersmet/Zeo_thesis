# Zeobuilder is an extensible GUI-toolkit for molecular model construction.
# Copyright (C) 2007 - 2009 Toon Verstraelen <Toon.Verstraelen@UGent.be>, Center
# for Molecular Modeling (CMM), Ghent University, Ghent, Belgium; all rights
# reserved unless otherwise stated.
#
# This file is part of Zeobuilder.
#
# Zeobuilder is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# In addition to the regulations of the GNU General Public License,
# publications and communications based in parts on this program or on
# parts of this program are required to cite the following article:
#
# "ZEOBUILDER: a GUI toolkit for the construction of complex molecules on the
# nanoscale with building blocks", Toon Verstraelen, Veronique Van Speybroeck
# and Michel Waroquier, Journal of Chemical Information and Modeling, Vol. 48
# (7), 1530-1541, 2008
# DOI:10.1021/ci8000748
#
# Zeobuilder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


from zeobuilder import context
from zeobuilder.actions.composed import Immediate
from zeobuilder.actions.abstract import AddBase
from zeobuilder.actions.collections.menu import MenuInfo
from zeobuilder.nodes.meta import Property
from zeobuilder.nodes.elementary import GLGeometricBase
from zeobuilder.nodes.color_mixin import UserColorMixin
from zeobuilder.nodes.model_object import ModelObjectInfo
from zeobuilder.nodes.glcontainermixin import GLContainerMixin
from zeobuilder.models import Model

import zeobuilder.actions.primitive as primitive
import zeobuilder.authors as authors

from molmod.transformations import Translation

import numpy

import math

import os, copy

class Fragment(GLGeometricBase, UserColorMixin):
    info = ModelObjectInfo("plugins/molecular/atom.svg")
    authors = [authors.toon_verstraelen]

    def __init__(self):
        print "new fragment object created"
        self.name = 'ammonium'

    #
    # State
    #

    def initnonstate(self):
        GLGeometricBase.initnonstate(self, Translation)

    def set_name(self,name):
        self.name = name

    def load_fragment(self): #read file from self.name into molecule object
        pass

class AddFragment(AddBase):
    description = "Add fragment"
    menu_info = MenuInfo("default/_Object:tools/_Add:3d", "_Fragment", image_name="plugins/basic/tetra.svg", order=(0, 4, 1, 0, 0, 7))
    authors = [authors.toon_verstraelen]

    def set_name(self,name):
        self.name = name

    @staticmethod
    def analyze_selection():
        # A) calling ancestor
        if not Immediate.analyze_selection(): return False
        # B) validating

        # C) passed all tests:
        return True

    def do(self):
        print "Adding fragment..."

        #FileImport = context.application.plugins.get_action("FileImport")()
        #print FileImport
        fragmentdir = context.get_share_filename('fragments')

        fragmentname = 'ammonium'
        filename = fragmentdir+'/'+fragmentname+'.cml'

        #stolen from file.py    def file_import(self,filename):
        tmp_model = Model()
        tmp_model.file_open(filename)

        #same precautions as import? remove all universe children and folder content before copying?
        if len(tmp_model.universe.children) > 0:
            Frame = context.application.plugins.get_node("Frame")
            root_frame = Frame(name=os.path.basename(filename))
            tmp = copy.copy(tmp_model.universe.children)
            while len(tmp_model.universe.children) > 0:
                tmp_model.universe.remove(tmp_model.universe.children[0])
            for node in tmp:
                root_frame.add(node)
            del tmp
            context.application.model.universe.add(root_frame)

        if len(tmp_model.folder.children) > 0:
            Folder = context.application.plugins.get_node("Folder")
            root_folder = Folder(name=os.path.basename(filename))
            tmp = copy.copy(tmp_model.folder.children)
            while len(tmp_model.folder.children) > 0:
                tmp_model.universe.remove(tmp_model.folder.children[0])
            for node in tmp:
                root_folder.add(node)
            del tmp
            context.application.model.folder.add(root_folder)
            tmp_model.file_close()

nodes = {
    "Fragment": Fragment,
}

actions = {
    "AddFragment": AddFragment

}


