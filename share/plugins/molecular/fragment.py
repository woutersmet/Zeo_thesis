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
        self.transformation = "BOE!"

    def set_name(self,name):
        self.name = name


    def getTransformation(self):
        print "getting transformation!"
        return self.fragment_frame.transformation.t[:]
        #return self.transformation #-> infinite recursion so that's not good

    def setTransformation(self,transformation):
        print "setting transformation!"

    #transformation property is more complicated than with point object nodes
    # so we override its getter and setter
    transformation = property(getTransformation,
                                setTransformation)

    def load_fragment(self): #read file from self.name into molecule object
        pass


    def addToModel(self,position=[0,0,0],parent=None):
        if parent is None:
            parent = context.application.model.universe

        fragmentdir = context.get_share_filename('fragments')
        filename = fragmentdir+'/'+self.name+'.cml'

        from molmod.io.cml import load_cml
        molecules = load_cml(filename)
        molecule = molecules[0] #we only look at first molecule in the list

        #load 'universe' from file trough cml load filter (stolen from models.py > file_open)
        load_filter = context.application.plugins.get_load_filter('cml')

        #create frame
        Frame = context.application.plugins.get_node("Frame")
        self.fragment_frame = Frame(name=self.name)

        #fill frame with molecule
        load_filter.load_molecule(self.fragment_frame,molecule)

        #apply transformation to frame
        self.fragment_frame.transformation.t[:] = position

        #add to model (note: should add to parent frame, not universe)
        primitive.Add(self.fragment_frame, parent)

class AddFragment(AddBase):
    description = "Add fragment"
    menu_info = MenuInfo("default/_Object:tools/_Add:3d", "_Fragment", image_name="plugins/basic/tetra.svg", order=(0, 4, 1, 0, 0, 7))
    authors = [authors.toon_verstraelen]

    @staticmethod
    def analyze_selection():
        # A) calling ancestor
        if not Immediate.analyze_selection(): return False
        # B) validating

        # C) passed all tests:
        return True

    def do(self):
        print "doing addfragment action.."
        fragment = context.application.plugins.get_node("Fragment")()
        fragment.set_name('ammonium')
        fragment.addToModel()


nodes = {
    "Fragment": Fragment,
}

actions = {
    "AddFragment": AddFragment

}


