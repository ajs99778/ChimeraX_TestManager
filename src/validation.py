def rmsd_tol(struc, superTight=False, superLoose=False):
    """
    Automatically determine a reasonable rmsd tolerance for the input
    AtomicStructure based on its size and number of atoms
    """
    import numpy as np
    tolerance = struc.num_atoms ** (
        2 - int(superTight) + int(superLoose)
    ) * np.sqrt(np.finfo(float).eps)

    com = np.mean(struc.active_coordset.xyzs, axis=0)
    max_d = None
    for atom in struc.atoms:
        d = np.linalg.norm(atom.coord - com)
        if max_d is None or d > max_d:
            max_d = d

    tolerance *= max_d * (2 - int(superTight) + int(superLoose))
    tolerance = tolerance ** (2 / (4 - int(superTight) + int(superLoose)))
    return tolerance


def check_atom_list(ref, comp):
    rv = True
    for i, j in zip(ref, comp):
        rv &= i.__repr__() == j.__repr__()
    return rv


def validate_elements(test, ref, debug=False):
    """
    Validates `test` atomic structure against `ref` atomic structure
    Returns: True if validation passed, False if failed
    
    checks if elements match
    """

    # elements should all be the same
    t_el = test.atoms.elements.names.tolist()
    r_el = ref.atoms.elements.names.tolist()
    if len(t_el) != len(r_el):
        if debug:
            print(
                "wrong number of atoms: {} (test) vs. {} (ref)".format(
                    len(t_el), len(r_el)
                )
            )
        return False

    for t, r in zip(t_el, r_el):
        if t != r:
            if debug:
                print("elements don't match")
            return False
    
    return True
    

def validate_connectivity(test, ref, debug=False):
    """
    Validates `test` atomic structure against `ref` atomic structure
    Returns: True if validation passed, False if failed
    
    checks if bonding matches (does not check pseudo bonds)
    """
    import numpy as np

    test_con = np.zeros((test.num_atoms, test.num_atoms), dtype=int)
    ref_con = np.zeros((ref.num_atoms, ref.num_atoms), dtype=int)
    for i, (test_atom, ref_atom) in enumerate(zip(test.atoms, ref.atoms)):
        for test_neighbor in test_atom.neighbors:
            j = test.atoms.index(test_neighbor)
            test_con[i,j] = 1
            test_con[j,i] = 1
        for ref_neighbor in ref_atom.neighbors:
            j = ref.atoms.index(ref_neighbor)
            ref_con[i,j] = 1
            ref_con[j,i] = 1
    
    if np.any(ref_con - test_con) != 0:
        if debug:
            con_diff = ref_con - test_con
            print("connectivity differs")
            for i in range(0, test.num_atoms):
                for j in range(0, i):
                    if con_diff[i,j] != 0:
                        print("%s-%s" % (ref.atoms[i].atomspec, ref.atoms[j].atomspec))
        return False
    
    return True


def validate_atomic_structures(test, ref, thresh=None, debug=False):
    """
    Validates `test` atomic structure against `ref` atomic structure
    Returns: True if validation passed, False if failed
    
    checks number of atoms, elements, connectivity (not pseudo bonds), and RMSD

    :test: the atomic structure to validate
    :ref: the reference atomic structure
    :thresh: the RMSD threshold
        if thresh is a number: use that as threshold
        if thresh is None: use rmsd_tol() to determine
        if thresh is "tight": use rmsd_tol(superTight=True)
        if thresh is "loose": use rmsd_tol(superLoose=True)
    :debug: print info useful for debugging
    """
    import numpy as np

    if debug:
        print("ref and test:")
        for mol in [ref, test]:
            print(mol.num_atoms)
            for atom in mol.atoms:
                print(" %-10s    %6.3f    %6.3f    %6.3f" % (atom.atomspec, atom.coord[0], atom.coord[1], atom.coord[2]))

    if thresh is None:
        thresh = rmsd_tol(ref)
    try:
        thresh = float(thresh)
    except ValueError:
        if thresh.lower() == "tight":
            thresh = rmsd_tol(ref, superTight=True)
        elif thresh.lower() == "loose":
            thresh = rmsd_tol(ref, superLoose=True)
        else:
            raise ValueError("Bad threshold provided")

    elements_valid = validate_elements(test, ref, debug=debug)
    if not elements_valid:
        if debug:
            print("bad elements")
        return elements_valid

    connectivity_valid = validate_connectivity(test, ref, debug=debug)
    if not connectivity_valid:
        if debug:
            print("bad connectivity")
        return connectivity_valid
    
    # and RMSD should be below a threshold
    ref_coords = ref.active_coordset.xyzs
    ref_coords -= np.mean(ref_coords, axis=0)
    test_coords = test.active_coordset.xyzs
    test_coords -= np.mean(test_coords, axis=0)
    
    if debug:
        print("ref centered:")
        for atom, coord in zip(ref.atoms, ref_coords):
                print(" %-10s    %6.3f    %6.3f    %6.3f" % (atom.atomspec, coord[0], coord[1], coord[2]))
        print("test centered:")
        for atom, coord in zip(test.atoms, test_coords):
                print(" %-10s    %6.3f    %6.3f    %6.3f" % (atom.atomspec, coord[0], coord[1], coord[2]))

    H = np.dot(ref_coords.T, test_coords)
    u, s, vh = np.linalg.svd(H, compute_uv=True)
    d = 1.
    if np.linalg.det(np.matmul(vh.T, u.T)) < 0:
        d = -1.
    m = np.diag([1., 1., d])
    R = np.matmul(vh.T, m)
    R = np.matmul(R, u.T)

    aligned_coords = np.dot(test_coords, R)
    
    diff = ref_coords - aligned_coords
    rmsd = 0
    for coord in diff:
        rmsd += np.dot(coord, coord)
    
    rmsd /= test.num_atoms
    rmsd = np.sqrt(rmsd)
    
    if debug:
        print("RMSD:", rmsd, "\tTHRESH:", thresh)
        print(test.num_atoms)
        for atom, new_coord in zip(test.atoms, aligned_coords):
            print(" %-10s    %6.3f    %6.3f    %6.3f" % (atom.atomspec, new_coord[0], new_coord[1], new_coord[2]))

    return rmsd < thresh
