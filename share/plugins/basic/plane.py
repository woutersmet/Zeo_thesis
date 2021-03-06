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
from zeobuilder.actions.collections.menu import MenuInfo
from zeobuilder.nodes.meta import Property
from zeobuilder.nodes.model_object import ModelObjectInfo
from zeobuilder.nodes.reference import SpatialReference
from zeobuilder.nodes.elementary import GLReferentBase
from zeobuilder.nodes.color_mixin import ColorMixin
from zeobuilder.gui.fields_dialogs import DialogFieldInfo
import zeobuilder.gui.fields as fields
import zeobuilder.authors as authors
import zeobuilder.actions.primitive as primitive

import numpy

import math


class Plane(GLReferentBase, ColorMixin):
    info = ModelObjectInfo("plugins/basic/plane.svg")
    authors = [authors.toon_verstraelen]

    #
    # State
    #

    def set_targets(self, targets, init=False):
        self.set_children([SpatialReference("Point") for target in targets])
        GLReferentBase.set_targets(self, targets, init)

    #
    # Properties
    #

    def set_margin(self, margin, init=False):
        self.margin = margin
        if not init:
            self.invalidate_draw_list()
            self.invalidate_boundingbox_list()

    properties = [
        Property("margin", 1.0, lambda self: self.margin, set_margin),
    ]

    #
    # Dialog fields (see action EditProperties)
    #

    dialog_fields = set([
        DialogFieldInfo("Geometry", (2, 10), fields.faulty.Length(
            label_text="Margin",
            attribute_name="margin",
            low=0.0,
            low_inclusive=True,
        )),
    ])

    #
    # Draw
    #

    def update_normal(self):
        self.points = numpy.array([child.target.get_frame_relative_to(self.parent).t for child in self.children if child.target is not None], float)

        self.center = sum(self.points)/len(self.points)
        tmp = self.points - self.center
        tensor = (tmp.ravel()**2).sum()*numpy.identity(3) - numpy.dot(tmp.transpose(), tmp)
        evals, evecs = numpy.linalg.eigh(tensor)
        indices = evals.argsort()
        self.x = evecs[:,indices[0]]
        self.y = evecs[:,indices[1]]
        if numpy.linalg.det(evecs) < 0:
            self.normal = evecs[:,indices[2]]
        else:
            self.normal = -evecs[:,indices[2]]
        px = numpy.dot(tmp, self.x)
        py = numpy.dot(tmp, self.y)

        px_low = px.min() - self.margin
        px_high = px.max() + self.margin
        py_low = py.min() - self.margin
        py_high = py.max() + self.margin

        self.l_l = self.x*px_low + self.y*py_low + self.center
        self.l_h = self.x*px_low + self.y*py_high + self.center
        self.h_l = self.x*px_high + self.y*py_low + self.center
        self.h_h = self.x*px_high + self.y*py_high + self.center


    def draw(self):
        GLReferentBase.draw(self)
        ColorMixin.draw(self)
        self.update_normal()
        vb = context.application.vis_backend
        vb.draw_quads((
            self.normal,
            [
                self.l_l + 0.001*self.normal,
                self.l_h + 0.001*self.normal,
                self.h_h + 0.001*self.normal,
                self.h_l + 0.001*self.normal,
            ],
        ), (
            - self.normal,
            [
                self.h_l - 0.001*self.normal,
                self.h_h - 0.001*self.normal,
                self.l_h - 0.001*self.normal,
                self.l_l - 0.001*self.normal,
            ],
        ))

    #
    # Revalidation
    #

    def revalidate_bounding_box(self):
        GLReferentBase.revalidate_bounding_box(self)
        self.update_normal()
        self.bounding_box.extend_with_point(self.l_l)
        self.bounding_box.extend_with_point(self.l_h)
        self.bounding_box.extend_with_point(self.h_l)
        self.bounding_box.extend_with_point(self.h_h)

    #
    # Vector
    #


    def define_target(self, reference, new_target):
        GLReferentBase.define_target(self, reference, new_target)
        self.invalidate_boundingbox_list()
        self.invalidate_draw_list()

    def target_moved(self, reference, target):
        GLReferentBase.target_moved(self, reference, target)
        self.invalidate_boundingbox_list()
        self.invalidate_draw_list()



class AddPlane(Immediate):
    description = "Add plane"
    menu_info = MenuInfo("default/_Object:tools/_Add:3d", "_Plane", image_name="plugins/basic/plane.svg", order=(0, 4, 1, 0, 0, 5))
    authors = [authors.toon_verstraelen]

    @staticmethod
    def analyze_selection():
        # A) calling ancestor
        if not Immediate.analyze_selection(): return False
        # B) validating
        cache = context.application.cache
        if len(cache.nodes) < 3: return False
        if len(cache.translations) < 3: return False
        if cache.common_parent is None: return False
        # C) passed all tests:
        return True

    def do(self):
        cache = context.application.cache
        nodes = cache.nodes
        primitive.Add(
            Plane(targets=nodes),
            cache.common_parent,
            index=cache.highest_index + 1
        )


nodes = {
    "Plane": Plane
}

actions = {
    "AddPlane": AddPlane,
}


