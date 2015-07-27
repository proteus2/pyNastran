# coding: utf-8
from __future__ import print_function#, unicode_literals
from six import iteritems
#from struct import pack

from pyNastran.bdf.bdf import BDF
from pyNastran.op2.op2 import OP2
from numpy import zeros, array, searchsorted

#def pack_nodes(fmt, data):
    #return ''

def pack_int_array(fmt, data):
    return ' '.join([str(val) for val in data]) + '\n\n'

def pack_float_3d_array(fmt, data):
    msg = ''
    for datai in data[0, :, :]:
        msgi = ''
        for dataii in datai:
            #print(dataii)
            msgi += '%s ' % dataii
        msg += msgi[:-1] + '\n'
    return msg + '\n\n'

def pack_float_2d_array(fmt, data):
    msg = ''
    for datai in data:
        msgi = ''
        for dataii in datai:
            print(dataii)
            msgi += '%s ' % dataii
        msg += msgi[:-1] + '\n'
    print(data.shape)
    return msg + '\n'

#def pack(fmt, data):
#    return ''

def export_to_vtk(model):
    bdf_filename = model + '.bdf'
    op2_filename = model + '.op2'
    vtk_filename = model + '.vtu'
    export_to_vtk_filename(bdf_filename, op2_filename, vtk_filename)

def export_to_vtk_filename(bdf_filename, op2_filename, vtk_filename):
    with open(vtk_filename, 'w') as vtk_file:
        vtk_file.write('# vtk DataFile Version 3.1\n')
        vtk_file.write('created by pyNastran\n')
        #vtk_file.write('BINARY\n')
        vtk_file.write('ASCII\n')
        vtk_file.write('DATASET UNSTRUCTURED_GRID\n')

        etype_map = {
            # line
            'CDAMP1' : 3,
            'CDAMP2' : 3,
            'CDAMP3' : 3,
            'CDAMP4' : 3,
            'CELAS1' : 3,
            'CELAS2' : 3,
            'CELAS3' : 3,
            'CELAS4' : 3,
            'CBAR' : 3,
            'CBEAM' : 3,
            'CROD' : 3,
            'CONROD' : 3,
            'CTUBE' : 3,

            'CTRIA3' : 5, # triangle
            'CQUAD4' : 9,  # quad

            # quadratic
            'CTRIA6' : 22,  # quadratic triangle
            #'CQUAD8' : 23/28/30,

            'CTETRA' : 10,
            'CPENTA' : 13, # wedge
            'CPYRAM' : 14,
            'CHEXA' : 12, # hex

            # quadratic solids
            #'CTETRA' : 64,
            #'CPENTA' : 65, # wedge
            #'CPYRAM' : 66,
            #'CHEXA' : 67, # hex
        }

        bdf = BDF()
        bdf.read_bdf(bdf_filename)
        op2 = OP2()
        op2.read_op2(op2_filename)

        out = bdf.get_card_ids_by_card_types()
        print(out.keys())
        grids = sorted(out['GRID'])
        spoint = sorted(out['SPOINT'])
        epoint = sorted(out['EPOINT'])
        ngrid = len(grids)
        nspoint = len(spoint)
        nepoint = len(epoint)
        nnodes = ngrid + nspoint + nepoint

        ncrod = len(out['CROD'])
        nconrod = len(out['CONROD'])
        nctube = len(out['CTUBE'])
        nline = ncrod + nconrod + nctube

        nctria3 = len(out['CTRIA3'])
        ncquad4 = len(out['CQUAD4'])
        nctria6 = len(out['CTRIA6'])
        ncquad8 = len(out['CQUAD8'])
        nshell = nctria3 + ncquad4 + nctria6 + ncquad8

        nctetra4 = len(out['CTETRA'])
        ncpyram5 = len(out['CPYRAM'])
        ncpenta6 = len(out['CPENTA'])
        nchexa8 = len(out['CHEXA'])
        nctetra10 = 0
        ncpyram8 = 0
        ncpenta15 = 0
        nchexa20 = 0
        nsolid = (nctetra4 + ncpyram5 + ncpenta6 + nchexa8 +
                  nctetra10 + ncpyram8 + ncpenta15 + nchexa20)

        nelements = nline + nshell + nsolid
        nproperties = nelements
        etypes = [
            'CELAS1', 'CELAS2', 'CELAS3', 'CELAS4',
            'CDAMP', 'CDAMP', 'CDAMP', 'CDAMP',
            'CROD', 'CONROD', 'CBAR', 'CBEAM',
            'CFAST',

            'CTRIA3', 'CQUAD4', 'CTRIA3', 'CQUAD8',

            'CTETRA', 'CPENTA', 'CPYRAM', 'CHEXA',
        ]
        for etype in etypes:
            if etype in out:
                ne = len(out[etype])
                nelements += ne

        # SPOINT & EPOINT are implicitly defined
        xyz_cid0 = zeros((nnodes, 3), dtype='float32')
        nids = zeros(nnodes, dtype='float32')
        for i, nid in enumerate(grids):
            xyz_cid0[i, :] = bdf.nodes[nid].get_position()
        nids[:ngrid] = grids
        if nspoint:
            nids[i:i+nspoint] = spoint
        if nepoint:
            nids[i+nspoint:] = epoint

        nid_fmt = '%ii' % nnodes
        xyz_fmt = '%ii' % (nnodes * 3)
        vtk_file.write('POINTS %i float\n' % nnodes)
        vtk_file.write(pack_float_2d_array(xyz_fmt, xyz_cid0))

        nelements = nline + nshell + nsolid
        nmaterials = nelements

        eid_fmt = '%ii' % nelements
        eids = zeros(nelements, dtype='int32')
        cell_types = zeros(nelements, dtype='int32')
        pids = zeros(nelements, dtype='int32')
        mids = zeros(nelements, dtype='int32')

        # we'll add 1 to the slot count of each
        # so for a single CROD, it has 2 nodes and 1 extra value (to indicate it's a line)
        # for a total of 3
        nline_slots = nline * 3
        nshell_slots = 4 * nctria3 + 5 * ncquad4 + 7 * nctria6 + 9 * ncquad8
        nsolid_slots = 5 * nctetra4 + 6 * ncpyram5 + 7 * ncpenta6 + 9 * nchexa8
        nelements_slots = nline_slots + nshell_slots + nsolid_slots

        i = 0
        vtk_file.write('CELLS %i %i\n' % (nelements, nelements_slots))
        for eid, elem in sorted(iteritems(bdf.elements)):
            etype = etype_map[elem.type]
            nids2 = searchsorted(nids, elem.node_ids)
            print(elem.type)
            #print(elem.node_ids, nids2)
            nnodesi = len(nids2)
            vtk_file.write('%i %s\n' % (nnodesi, str(nids2)[1:-1]))
            pid = elem.Pid()
            mid = elem.Mid()
            eids[i] = eid
            pids[i] = pid
            mids[i] = mid
            cell_types[i] = etype
            i += 1
        #vtk_file.write('\n')
        vtk_file.write('CELL_TYPES %i\n' % nelements)
        vtk_file.write(pack_int_array(eid_fmt, cell_types))

        vtk_file.write('NodeID %i float\n' % nnodes)
        vtk_file.write(pack_int_array(nid_fmt, nids))

        fmt = b'%si' % nelements
        if nelements:
            vtk_file.write('ElementID %i float\n' % nelements)
            vtk_file.write(pack_int_array(eid_fmt, eids))
        if nproperties:
            vtk_file.write('PropertyID %i float\n' % nproperties)
            vtk_file.write(pack_int_array(eid_fmt, pids))
        if nmaterials:
            vtk_file.write('MaterialID %i float\n' % nmaterials)
            vtk_file.write(pack_int_array(eid_fmt, mids))

        nodal_cases = [op2.eigenvectors, op2.displacements, op2.velocities, op2.accelerations]
        fmt = '%sf' % (nnodes * 6)
        for cases in nodal_cases:
            keys = cases.keys()#[0]
            if not keys:
                continue
            key0 = keys[0]
            print(key0)
            node_ids = cases[key0].node_gridtype[:, 0]

            if nnodes == len(node_ids):
                # every node exists
                i = None
                ni = nnodes
            else:
                # node_ids is a subset of nids
                i = searchsorted(nids, node_ids)
                ni = len(i)

            for isubcase, case in sorted(iteritems(cases)):
                if case.is_real:
                    if i is None:
                        #data = case.data
                        ni = nnodes
                    else:
                        data = zeros((nnodes, 6), dtype='float32')
                        #data[:, i, :] = case.data

                    ntimes = case.data.shape[0]
                    case_type = case.__class__.__name__
                    for itime in range(ntimes):
                        name = '%s_isubcase=%s_itime=%s' % (case_type, isubcase, itime)
                        vtk_file.write('%s %i float\n' % (name, ni))
                        vtk_file.write(pack_float_3d_array(fmt, case.data[itime, i, :]))

        #CELLS 217 1039

def main():
    export_to_vtk('solid_bending')

if __name__ == '__main__':
    main()
