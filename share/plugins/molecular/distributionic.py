# Zeobuilder is an extensible GUI-toolkit for molecular model construction.
# Copyright (C) 2005 Toon Verstraelen
#
# This file is part of Zeobuilder.
#
# Zeobuilder is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# --


from zeobuilder import context
from zeobuilder.actions.composed import ImmediateWithMemory, Parameters, UserError
from zeobuilder.actions.collections.menu import MenuInfo
from zeobuilder.nodes.parent_mixin import ContainerMixin
from zeobuilder.gui.fields_dialogs import FieldsDialogSimple
from zeobuilder.gui.glade_wrapper import GladeWrapper
from zeobuilder.gui.simple import ask_save_filename
from zeobuilder.gui import load_image
from zeobuilder.expressions import Expression
from zeobuilder.conversion import express_measure
import zeobuilder.gui.fields as fields

from molmod.units import to_unit

import gtk, numpy, pylab, matplotlib

import math, os


# UGLY HACK: TODO report this as a bug to the matplotlib project
gtk.window_set_default_icon(load_image("zeobuilder.svg"))
# END UGLY HACK

# UGLY HACK TODO: this should be in zeobuilder.__init__
matplotlib.rcParams["backend"] = "GTKAgg"
matplotlib.rcParams["numerix"] = "numpy"
matplotlib.rcParams["font.size"] = 9
matplotlib.rcParams["legend.fontsize"] = 8
matplotlib.rcParams["axes.titlesize"] = 9
matplotlib.rcParams["axes.labelsize"] = 9
matplotlib.rcParams["xtick.labelsize"] = 9
matplotlib.rcParams["ytick.labelsize"] = 9
matplotlib.rcParams["figure.facecolor"] = "w"
# END UGLY HACK

class DistributionDialog(GladeWrapper):
    def __init__(self):
        GladeWrapper.__init__(self, "plugins/molecular/gui.glade", "di_distribution", "dialog")
        self.dialog.hide()
        self.init_callbacks(DistributionDialog)
        self.init_proxies(["hb_images", "tv_properties"])

        figure = pylab.figure(0, figsize=(4, 4), dpi=100)
        mpl_widget = matplotlib.backends.backend_gtkagg.FigureCanvasGTKAgg(figure)
        mpl_widget.set_size_request(400, 400)
        self.hb_images.pack_start(mpl_widget, expand=False, fill=True)

        self.property_store = gtk.ListStore(str, str)
        self.tv_properties.set_model(self.property_store)

        column = gtk.TreeViewColumn()
        renderer_text = gtk.CellRendererText()
        column.pack_start(renderer_text, expand=False)
        column.add_attribute(renderer_text, "text", 0)
        self.tv_properties.append_column(column)

        column = gtk.TreeViewColumn()
        renderer_text = gtk.CellRendererText()
        column.pack_start(renderer_text, expand=True)
        column.add_attribute(renderer_text, "text", 1)
        self.tv_properties.append_column(column)


    def run(self, data, measure, label, comments):
        self.data = data
        self.data.sort()
        self.measure = measure
        self.unit = context.application.configuration.default_units[self.measure]
        self.label = label
        self.comments = comments

        self.dialog.set_title("%s distribution" % label)
        self.calculate_properties()
        self.create_images()

        for name, value in self.property_store:
            self.comments.append("%s: %s" % (name, value))
        self.comments.append("%s data in unit [%s]" % (self.label, self.unit))
        self.comments.append("model filename: %s" % context.application.model.filename)

        self.dialog.show_all()
        result = self.dialog.run()
        self.dialog.hide()
        return result

    def calculate_properties(self):
        self.average = self.data.mean()
        self.median = numpy.median(self.data)
        self.stdev = math.sqrt(sum((self.data - self.data.mean())**2) / (len(self.data) - 1))

        self.property_store.clear()
        self.property_store.append([
            "Samples",
            str(len(self.data))
        ])
        self.property_store.append([
            "Average",
            express_measure(self.average, self.measure)
        ])
        self.property_store.append([
            "Median",
            express_measure(self.median, self.measure)
        ])
        self.property_store.append([
            "Stdev (N-1)",
            express_measure(self.stdev, self.measure)
        ])

    def create_images(self):
        figure = pylab.figure(0)
        pylab.clf()
        pylab.axes([0.15, 0.1, 0.8, 0.85])
        patches = []
        labels = []

        patch_average = pylab.plot([to_unit[self.unit](self.average)]*2, [48, 52], "g-")
        patches.append(patch_average)
        labels.append("Average")

        xtmp = to_unit[self.unit](numpy.array([self.average - self.stdev, self.average + self.stdev]))
        patch_stdev = pylab.plot(xtmp, [50, 50], "m-")
        patches.append(patch_stdev)
        labels.append("+- Stdev")

        patch_line = pylab.plot(
            to_unit[self.unit](self.data),
            100*numpy.arange(len(self.data), dtype=float)/(len(self.data)-1),
            color="r",
        )
        patches.append(patch_line)
        labels.append("Cumulative")

        probs, bins = numpy.histogram(
            to_unit[self.unit](self.data),
            bins=int(math.sqrt(len(self.data))),
            normed=False,
        )
        delta = bins[1] - bins[0]
        probs = probs*(100.0/len(self.data))
        args = zip(bins, numpy.zeros(len(bins)), numpy.ones(len(bins))*delta, probs)
        for l, b, w, h in args:
            patch_hist = matplotlib.patches.Rectangle((l, b), w, h, facecolor="w", edgecolor="#AAAAAA")
            pylab.gca().add_patch(patch_hist)
        pylab.xlim([bins[0]-delta, bins[-1]+delta])
        pylab.ylim([0, 100])
        pylab.xlabel("%s [%s]" % (self.label, self.unit))
        pylab.ylabel("Probability [%]")
        patches.append([patch_hist])
        labels.append("Histogram")

        pylab.legend(patches, labels, 0)

    def save_figure(self, filename):
        old_backend = matplotlib.rcParams["backend"]
        matplotlib.rcParams["backend"] = "SVG"
        pylab.figure(0)
        pylab.savefig(filename, dpi=100)
        matplotlib.rcParams["backend"] = old_backend

    def save_data(self, filename):
        f = file(filename, "w")
        for line in self.comments:
            print >> f, "#", line
        for value in self.data:
            print >> f, value
        f.close()

    def on_bu_save_clicked(self, button):
        filename = self.label.lower().replace(" ", "_")
        filename = ask_save_filename("Save distribution data", filename)
        if filename is not None:
            self.save_data("%s.txt" % filename)
            self.save_figure("%s.svg" % filename)


distribution_dialog = DistributionDialog()


class DistributionBondLengths(ImmediateWithMemory):
    description = "Distribution of bond lengths"
    menu_info = MenuInfo("default/_Object:tools/_Molecular:info", "Distribution of bond _lengths", order=(0, 4, 1, 5, 2, 2))

    parameters_dialog = FieldsDialogSimple(
        "Bond length distribution parameters",
        fields.group.Table(fields=[
            fields.faulty.Expression(
                label_text="Filter expression: atom 1",
                attribute_name="filter_atom1",
                history_name="filter",
                width=250,
                height=60,
            ),
            fields.faulty.Expression(
                label_text="Filter expression: bond 1-2",
                attribute_name="filter_bond12",
                history_name="filter",
                width=250,
                height=60,
            ),
            fields.faulty.Expression(
                label_text="Filter expression: atom 2",
                attribute_name="filter_atom2",
                history_name="filter",
                width=250,
                height=60,
            ),
        ]),
        ((gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL), (gtk.STOCK_OK, gtk.RESPONSE_OK)),
    )

    @staticmethod
    def analyze_selection(parameters=None):
        # A) calling ancestor
        if not ImmediateWithMemory.analyze_selection(parameters): return False
        # B) validating
        cache = context.application.cache
        if len(cache.nodes) == 0: return False
        # C) passed all tests:
        return True

    @classmethod
    def default_parameters(cls):
        result = Parameters()
        result.filter_atom1 = Expression()
        result.filter_bond12 = Expression()
        result.filter_atom2 = Expression()
        return result

    def do(self):
        Bond = context.application.plugins.get_node("Bond")
        def yield_bonds(nodes):
            for node in nodes:
                if isinstance(node, Bond):
                    yield node
                elif isinstance(node, ContainerMixin):
                    for result in yield_bonds(node.children):
                        yield result

        bonds = {}
        for bond in yield_bonds(context.application.cache.nodes):
            key = frozenset([bond.children[0].target, bond.children[1].target])
            bonds[key] = bond

        lengths = []
        for (atom1, atom2), bond in bonds.iteritems():
            try:
                match_b12 = self.parameters.filter_bond12(bond)
            except Exception:
                raise UserError("An exception occured while evaluating the filter expression for 'bond 1-2'.")
            try:
                match_a1_1 = self.parameters.filter_atom1(atom1)
                match_a1_2 = self.parameters.filter_atom1(atom2)
            except Exception:
                raise UserError("An exception occured while evaluating the filter expression for 'atom 1'.")
            try:
                match_a2_1 = self.parameters.filter_atom2(atom1)
                match_a2_2 = self.parameters.filter_atom2(atom2)
            except Exception:
                raise UserError("An exception occured while evaluating the filter expression for 'atom 1'.")
            if match_b12 and ((match_a1_1 and match_a2_2) or (match_a1_2 and match_a2_1)):
                if not hasattr(bond, "length"):
                    bond.calc_vector_dimensions()
                lengths.append(bond.length)

        comments = [
            "atom 1 filter expression: %s" % self.parameters.filter_atom1.code,
            "bond 1-2 filter expression: %s" % self.parameters.filter_bond12.code,
            "atom 2 filter expression: %s" % self.parameters.filter_atom2.code,
        ]

        distribution_dialog.run(numpy.array(lengths), "Length", "Bond length", comments)


actions = {
    "DistributionBondLengths": DistributionBondLengths,
#    "DistributionBendingAngles": DistributionBendingAngles,
#    "DistributionDihedralAngles": DistributionDihedralAngles,
}
