import os
import unittest
from six import iteritems
from numpy import array, allclose, array_equal

import pyNastran
from pyNastran.bdf.bdf import BDF, BDFCard, DAREA, PLOAD4
from pyNastran.bdf.bdf import SET1, AESTAT, DMI, DMIG
from pyNastran.op2.op2 import OP2

bdf = BDF(debug=False)
test_path = pyNastran.__path__[0]


class TestLoads(unittest.TestCase):
    def test_darea_01(self):
        #
        #DAREA SID P1 C1 A1  P2 C2 A2
        #DAREA 3   6   2 8.2 15 1  10.1
        lines = ['DAREA,3,6,2,8.2,15,1,10.1']
        card = bdf.process_card(lines)
        card = BDFCard(card)

        size = 8
        card = DAREA(card)
        card.write_card(size, 'dummy')
        card.raw_fields()

    def test_pload4_01(self):
        lines = ['PLOAD4  1000    1       -60.    -60.    60.             1']
        card = bdf.process_card(lines)
        card = BDFCard(card)

        size = 8
        card = PLOAD4(card)
        card.write_card(size, 'dummy')
        card.raw_fields()

    def test_pload4_02(self):
        lines = ['PLOAD4  1       101     1.                              10000   10011']
        card = bdf.process_card(lines)
        card = BDFCard(card)

        size = 8
        card = PLOAD4(card)
        card.write_card(size, 'dummy')
        card.raw_fields()

    def test_pload4_03(self):
        bdf_filename = os.path.join(test_path, '..', 'models', 'pload4', 'cpenta.bdf')
        op2_filename = os.path.join(test_path, '..', 'models', 'pload4', 'cpenta.op2')
        make_geom = False
        write_bdf = False
        write_f06 = True
        debug = False
        op2 = OP2()
        op2.read_op2(op2_filename)

        #if os.path.exists(debug_file):
            #os.remove(debug_file)
        model_b = BDF()
        model_b.read_bdf(bdf_filename)
        p0 = model_b.nodes[21].xyz
        angles = [
            (23, 24), (24, 23),
            (21, 26), (26, 21),
        ]
        nx = [
            (23, 25), (25, 23),
            (22, 26), (26, 22),
        ]

        for isubcase, subcase in sorted(iteritems(model_b.subcases)):
            if isubcase == 0:
                continue
            loadcase_id = subcase.get_parameter('LOAD')[0]
            load = model_b.loads[loadcase_id][0]
            elem = load.eid
            g1 = load.g1.nid
            if load.g34 is None:
                #print(load)
                face, area, centroid, normal = elem.getFaceAreaCentroidNormal(g1)
                assert area == 0.5, area
                if g1 in [21, 22, 23]:
                    assert face == (2, 1, 0), 'g1=%s face=%s' % (g1, face)
                    assert array_equal(centroid, array([2/3., 1/3., 0.])),  'fore g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                    assert array_equal(normal, array([0., 0., -1.])), 'fore g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                else:
                    assert face == (3, 4, 5), 'g1=%s face=%s' % (g1, face)
                    assert array_equal(centroid, array([2/3., 1/3., 2.])),  'aft g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                    assert array_equal(normal, array([0., 0., 1.])), 'aft g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)

                f, m = model_b.sum_forces_moments(p0, loadcase_id, include_grav=False)
                case = op2.spc_forces[isubcase]
                fm = case.data[0, 0, :]#.ravel()
                if f[0] != fm[0]:
                    print('%i f=%s fexpected=%s' % (isubcase, f, fm))
            else:
                g34 = load.g34.nid
                face, area, centroid, normal = elem.getFaceAreaCentroidNormal(g1, g34)
                if (g1, g34) in angles:
                    self.assertAlmostEqual(area, 2 * 2**0.5,  msg='g1=%s g34=%s face=%s area=%s' % (g1, g34, face, area))
                elif (g1, g34) in nx:
                    self.assertEqual(area, 2.0, 'area=%s' % area)
                    msg = '%s%s%s%s\n' % (
                        elem.nodes[face[0]], elem.nodes[face[1]], elem.nodes[face[2]], elem.nodes[face[3]])
                    assert array_equal(centroid, array([1., .5, 1.])),  'Nx g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                    assert array_equal(normal, array([-1., 0., 0.])),  'Nx g1=%s g34=%s face=%s normal=%s\n%s' % (g1, g34, face, normal, msg)
                else:
                    msg = '%s%s%s%s\n' % (
                        elem.nodes[face[0]], elem.nodes[face[1]], elem.nodes[face[2]], elem.nodes[face[3]])

                    assert array_equal(centroid, array([0.5, .0, 1.])), 'Ny g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                    assert array_equal(normal, array([0., 1., 0.])),  'Ny g1=%s g34=%s face=%s normal=%s\n%s' % (g1, g34, face, normal, msg)
                    self.assertEqual(area, 2.0, 'area=%s' % area)
            #self.assertEqual(f[0], fm[0], 'f=%s fexpected=%s' % (f, fm[:3]))
            #self.assertEqual(f[1], fm[1], 'f=%s fexpected=%s' % (f, fm[:3]))
            #self.assertEqual(f[2], fm[2], 'f=%s fexpected=%s' % (f, fm[:3]))
            #self.assertEqual(m[0], fm[3], 'm=%s mexpected=%s' % (m, fm[3:]))
            #self.assertEqual(m[1], fm[4], 'm=%s mexpected=%s' % (m, fm[3:]))
            #self.assertEqual(m[2], fm[5], 'm=%s mexpected=%s' % (m, fm[3:]))

    def test_pload4_04(self):
        bdf_filename = os.path.join(test_path, '..', 'models', 'pload4', 'chexa.bdf')
        op2_filename = os.path.join(test_path, '..', 'models', 'pload4', 'chexa.op2')
        op2 = OP2()
        op2.read_op2(op2_filename)

        model_b = BDF()
        model_b.read_bdf(bdf_filename)
        p0 = model_b.nodes[21].xyz
        nx = [
            (22, 27), (27, 22),
            (23, 26), (26, 22),

            (24, 25), (25, 24),
            (21, 28), (28, 21),
            #(23, 25), (25, 23),
            #(22, 26), (26, 22),
        ]

        nz = [
            (25, 27), (27, 25),
            (26, 28), (28, 26),

            (21, 23), (23, 21),
            (24, 22), (22, 24),

        ]

        for isubcase, subcase in sorted(iteritems(model_b.subcases)):
            if isubcase == 0:
                continue
            loadcase_id = subcase.get_parameter('LOAD')[0]
            load = model_b.loads[loadcase_id][0]
            elem = load.eid
            g1 = load.g1.nid

            f, m = model_b.sum_forces_moments(p0, loadcase_id, include_grav=False)
            case = op2.spc_forces[isubcase]
            fm = case.data[0, 0, :]#.ravel()
            if f[0] != fm[0]:
                print('%i f=%s fexpected=%s' % (isubcase, f, fm))

            g34 = load.g34.nid
            face, area, centroid, normal = elem.getFaceAreaCentroidNormal(g1, g34)
            msg = '%s%s%s%s\n' % (
                elem.nodes[face[0]], elem.nodes[face[1]],
                elem.nodes[face[2]], elem.nodes[face[3]])

            if (g1, g34) in nx:
                self.assertEqual(area, 2.0, 'Nx area=%s' % area)
            elif (g1, g34) in nz:
                self.assertEqual(area, 1.0, 'Nz area=%s' % area)

                #print(nodes[n1i])
                #print(nodes[n2i])
                #print(nodes[n3i])
                #print(nodes[n4i])
                #assert array_equal(centroid, array([1., .5, 1.])),  'Nx g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                #assert array_equal(normal, array([-1., 0., 0.])),  'Nx g1=%s g34=%s face=%s normal=%s\n%s' % (g1, g34, face, normal, msg)
            else:
                #assert array_equal(centroid, array([0.5, .0, 1.])), 'Ny g1=%s g34=%s face=%s centroid=%s\n%s' % (g1, g34, face, centroid, msg)
                #assert array_equal(normal, array([0., 1., 0.])),  'Ny g1=%s g34=%s face=%s normal=%s\n%s' % (g1, g34, face, normal, msg)
                self.assertEqual(area, 2.0, 'area=%s' % area)
            #self.assertEqual(f[0], fm[0], 'f=%s fexpected=%s' % (f, fm[:3]))
            #self.assertEqual(f[1], fm[1], 'f=%s fexpected=%s' % (f, fm[:3]))
            #self.assertEqual(f[2], fm[2], 'f=%s fexpected=%s' % (f, fm[:3]))
            #self.assertEqual(m[0], fm[3], 'm=%s mexpected=%s' % (m, fm[3:]))
            #self.assertEqual(m[1], fm[4], 'm=%s mexpected=%s' % (m, fm[3:]))
            #self.assertEqual(m[2], fm[5], 'm=%s mexpected=%s' % (m, fm[3:]))


    def test_aestat_01(self):
        lines = ['AESTAT  502     PITCH']
        card = bdf.process_card(lines)
        card = BDFCard(card)

        size = 8
        card = AESTAT(card)
        card.write_card(size, 'dummy')
        card.raw_fields()

    def test_dmi_01(self):
        lines = ['DMI,Q,0,6,1,0,,4,4']
        card = bdf.process_card(lines)
        card = BDFCard(card)

        size = 8
        card = DMI(card)
        card.write_card(size, 'dummy')
        #card.rawFields()

    def test_set1_01(self):
        lines = ['SET1,    1100,    100,     101']
        card = bdf.process_card(lines)
        card = BDFCard(card)

        size = 8
        card = SET1(card)
        card.write_card(size, 'dummy')
        card.raw_fields()


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

