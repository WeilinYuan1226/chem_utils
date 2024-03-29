import numpy as np
from rdkit import Chem


def structure_generator_based_on_r_group(main_molecules, fragment_molecules, chromosome):
    """
    k-nearest neighbor normalized error (k3n-error)

    When X1 is data of X-variables and X2 is data of Z-variables
    (low-dimensional data), this is k3n error in visualization (k3n-Z-error).
    When X1 is Z-variables (low-dimensional data) and X2 is data of data of
    X-variables, this is k3n error in reconstruction (k3n-X-error).

    k3n-error = k3n-Z-error + k3n-X-error

    Parameters
    ----------
    main_molecules: list of MOL
    fragment_molecules: list of MOL
    chromosome: numpy.array

    Returns
    -------
    smiles : str
    """

    bond_list = [Chem.rdchem.BondType.UNSPECIFIED, Chem.rdchem.BondType.SINGLE, Chem.rdchem.BondType.DOUBLE,
                 Chem.rdchem.BondType.TRIPLE, Chem.rdchem.BondType.QUADRUPLE, Chem.rdchem.BondType.QUINTUPLE,
                 Chem.rdchem.BondType.HEXTUPLE, Chem.rdchem.BondType.ONEANDAHALF, Chem.rdchem.BondType.TWOANDAHALF,
                 Chem.rdchem.BondType.THREEANDAHALF, Chem.rdchem.BondType.FOURANDAHALF,
                 Chem.rdchem.BondType.FIVEANDAHALF,
                 Chem.rdchem.BondType.AROMATIC, Chem.rdchem.BondType.IONIC, Chem.rdchem.BondType.HYDROGEN,
                 Chem.rdchem.BondType.THREECENTER, Chem.rdchem.BondType.DATIVEONE, Chem.rdchem.BondType.DATIVE,
                 Chem.rdchem.BondType.DATIVEL, Chem.rdchem.BondType.DATIVER, Chem.rdchem.BondType.OTHER,
                 Chem.rdchem.BondType.ZERO]

    selected_main_molecule_number = np.floor(chromosome[0] * len(main_molecules)).astype(int)
    if selected_main_molecule_number == len(main_molecules):
        selected_main_molecule_number = len(main_molecules) - 1
    main_molecule = main_molecules[selected_main_molecule_number]
    # make adjacency matrix and get atoms for main molecule
    main_adjacency_matrix = Chem.rdmolops.GetAdjacencyMatrix(main_molecule)
    for bond in main_molecule.GetBonds():
        main_adjacency_matrix[bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()] = bond_list.index(bond.GetBondType())
        main_adjacency_matrix[bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()] = bond_list.index(bond.GetBondType())
    main_atoms = []
    for atom in main_molecule.GetAtoms():
        main_atoms.append(atom.GetSymbol())

    r_index_in_main_molecule_old = [index for index, atom in enumerate(main_atoms) if atom == '*']
    for index, r_index in enumerate(r_index_in_main_molecule_old):
        modified_index = r_index - index
        atom = main_atoms.pop(modified_index)
        main_atoms.append(atom)
        tmp = main_adjacency_matrix[:, modified_index:modified_index + 1].copy()
        main_adjacency_matrix = np.delete(main_adjacency_matrix, modified_index, 1)
        main_adjacency_matrix = np.c_[main_adjacency_matrix, tmp]
        tmp = main_adjacency_matrix[modified_index:modified_index + 1, :].copy()
        main_adjacency_matrix = np.delete(main_adjacency_matrix, modified_index, 0)
        main_adjacency_matrix = np.r_[main_adjacency_matrix, tmp]
    r_index_in_main_molecule_new = [index for index, atom in enumerate(main_atoms) if atom == '*']

    r_bonded_atom_index_in_main_molecule = []
    for number in r_index_in_main_molecule_new:
        r_bonded_atom_index_in_main_molecule.append(np.where(main_adjacency_matrix[number, :] != 0)[0][0])
    r_bond_number_in_main_molecule = main_adjacency_matrix[
        r_index_in_main_molecule_new, r_bonded_atom_index_in_main_molecule]

    main_adjacency_matrix = np.delete(main_adjacency_matrix, r_index_in_main_molecule_new, 0)
    main_adjacency_matrix = np.delete(main_adjacency_matrix, r_index_in_main_molecule_new, 1)

    for i in range(len(r_index_in_main_molecule_new)):
        main_atoms.remove('*')
    main_size = main_adjacency_matrix.shape[0]

    fragment_chromosome = chromosome[1:]
    fragment_numbers = fragment_chromosome.argsort()[::-1]
    selected_fragment_numbers = fragment_numbers[:len(r_index_in_main_molecule_old)]

    generated_molecule_atoms = main_atoms[:]
    generated_adjacency_matrix = main_adjacency_matrix.copy()
    for r_number_in_molecule in range(len(r_index_in_main_molecule_new)):
        fragment_molecule = fragment_molecules[selected_fragment_numbers[r_number_in_molecule]]
        fragment_adjacency_matrix = Chem.rdmolops.GetAdjacencyMatrix(fragment_molecule)
        for bond in fragment_molecule.GetBonds():
            fragment_adjacency_matrix[bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()] = bond_list.index(
                bond.GetBondType())
            fragment_adjacency_matrix[bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()] = bond_list.index(
                bond.GetBondType())
        fragment_atoms = []
        for atom in fragment_molecule.GetAtoms():
            fragment_atoms.append(atom.GetSymbol())

        # integrate adjacency matrix
        r_index_in_fragment_molecule = fragment_atoms.index('*')

        r_bonded_atom_index_in_fragment_molecule = \
            np.where(fragment_adjacency_matrix[r_index_in_fragment_molecule, :] != 0)[0][0]
        if r_bonded_atom_index_in_fragment_molecule > r_index_in_fragment_molecule:
            r_bonded_atom_index_in_fragment_molecule -= 1

        fragment_atoms.remove('*')
        fragment_adjacency_matrix = np.delete(fragment_adjacency_matrix, r_index_in_fragment_molecule, 0)
        fragment_adjacency_matrix = np.delete(fragment_adjacency_matrix, r_index_in_fragment_molecule, 1)

        main_size = generated_adjacency_matrix.shape[0]
        generated_adjacency_matrix = np.c_[generated_adjacency_matrix, np.zeros(
            [generated_adjacency_matrix.shape[0], fragment_adjacency_matrix.shape[0]], dtype='int32')]
        generated_adjacency_matrix = np.r_[generated_adjacency_matrix, np.zeros(
            [fragment_adjacency_matrix.shape[0], generated_adjacency_matrix.shape[1]], dtype='int32')]

        generated_adjacency_matrix[r_bonded_atom_index_in_main_molecule[
                                       r_number_in_molecule], r_bonded_atom_index_in_fragment_molecule + main_size] = \
            r_bond_number_in_main_molecule[r_number_in_molecule]
        generated_adjacency_matrix[
            r_bonded_atom_index_in_fragment_molecule + main_size, r_bonded_atom_index_in_main_molecule[
                r_number_in_molecule]] = r_bond_number_in_main_molecule[r_number_in_molecule]
        generated_adjacency_matrix[main_size:, main_size:] = fragment_adjacency_matrix

        # integrate atoms
        generated_molecule_atoms += fragment_atoms

    # generate structures 
    generated_molecule = Chem.RWMol()
    atom_index = []
    for atom_number in range(len(generated_molecule_atoms)):
        atom = Chem.Atom(generated_molecule_atoms[atom_number])
        molecular_index = generated_molecule.AddAtom(atom)
        atom_index.append(molecular_index)
    for index_x, row_vector in enumerate(generated_adjacency_matrix):
        for index_y, bond in enumerate(row_vector):
            if index_y <= index_x:
                continue
            if bond == 0:
                continue
            else:
                generated_molecule.AddBond(atom_index[index_x], atom_index[index_y], bond_list[bond])

    generated_molecule = generated_molecule.GetMol()

    return Chem.MolToSmiles(generated_molecule)


def structure_generator_abc(main_mol, fragment1, fragment2, r_position=1):

    """

    parameters
    ----------
    main_mol : RDkit Mol object
        主骨格（A）の構造（フラグメント）
    fragment1 : RDkit Mol object
        * の数が二つのフラグメント（Bにあたる）
    fragment2 : RDkit Mol object
        * の数が一つのフラグメント(Bにあたる）
    r_position : int (1 or 2) 
        fragment1 中の * のどちらに、main_mol, fragment1を結合させるか。

    Returns
    ----------
    generated_molecule : RDkit Mol object
        各フラグメントを結合させて生成したA-B-C型の分子


    """
    bond_list = [Chem.rdchem.BondType.UNSPECIFIED, Chem.rdchem.BondType.SINGLE, Chem.rdchem.BondType.DOUBLE,
             Chem.rdchem.BondType.TRIPLE, Chem.rdchem.BondType.QUADRUPLE, Chem.rdchem.BondType.QUINTUPLE,
             Chem.rdchem.BondType.HEXTUPLE, Chem.rdchem.BondType.ONEANDAHALF, Chem.rdchem.BondType.TWOANDAHALF,
             Chem.rdchem.BondType.THREEANDAHALF, Chem.rdchem.BondType.FOURANDAHALF, Chem.rdchem.BondType.FIVEANDAHALF,
             Chem.rdchem.BondType.AROMATIC, Chem.rdchem.BondType.IONIC, Chem.rdchem.BondType.HYDROGEN,
             Chem.rdchem.BondType.THREECENTER, Chem.rdchem.BondType.DATIVEONE, Chem.rdchem.BondType.DATIVE,
             Chem.rdchem.BondType.DATIVEL, Chem.rdchem.BondType.DATIVER, Chem.rdchem.BondType.OTHER,
             Chem.rdchem.BondType.ZERO]

    # make adjacency matrix and get atoms for main molecule
    level1_adjacency_matrix = Chem.rdmolops.GetAdjacencyMatrix(fragment1)

    for bond in fragment1.GetBonds():
        level1_adjacency_matrix[bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()] = bond_list.index(bond.GetBondType())
        level1_adjacency_matrix[bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()] = bond_list.index(bond.GetBondType())
    level1_atoms = []
    for atom in fragment1.GetAtoms():
        level1_atoms.append(atom.GetSymbol())

    # * の位置を検索
    r_index_in_level1_molecule_old = [index for index, atom in enumerate(level1_atoms) if atom == '*']

    # matrix,atom の並び替え
    for index, r_index in enumerate(r_index_in_level1_molecule_old):
        modified_index = r_index - index
        atom = level1_atoms.pop(modified_index)
        level1_atoms.append(atom)
        tmp = level1_adjacency_matrix[:, modified_index:modified_index + 1].copy()
        level1_adjacency_matrix = np.delete(level1_adjacency_matrix, modified_index, 1)
        level1_adjacency_matrix = np.c_[level1_adjacency_matrix, tmp]
        tmp = level1_adjacency_matrix[modified_index:modified_index + 1, :].copy()
        level1_adjacency_matrix = np.delete(level1_adjacency_matrix, modified_index, 0)
        level1_adjacency_matrix = np.r_[level1_adjacency_matrix, tmp]

    r_index_in_level1_molecule_new = [index for index, atom in enumerate(level1_atoms) if atom == '*']

    # *がどの原子と結合しているか調べる。
    r_bonded_atom_index_in_level1_molecule = []
    for number in r_index_in_level1_molecule_new:
        r_bonded_atom_index_in_level1_molecule.append(np.where(level1_adjacency_matrix[number, :] != 0)[0][0])

    #結合のタイプを調べる
    r_bond_number_in_level1_molecule = level1_adjacency_matrix[
        r_index_in_level1_molecule_new, r_bonded_atom_index_in_level1_molecule]

    # *原子を削除
    level1_adjacency_matrix = np.delete(level1_adjacency_matrix, r_index_in_level1_molecule_new, 0)
    level1_adjacency_matrix = np.delete(level1_adjacency_matrix, r_index_in_level1_molecule_new, 1)

    for i in range(len(r_index_in_level1_molecule_new)):
        level1_atoms.remove('*')
    level1_size = level1_adjacency_matrix.shape[0]

    # level1フラグメントの ２つの* に残りのフラグメントを結合する
    generated_molecule_atoms = level1_atoms[:]
    generated_adjacency_matrix = level1_adjacency_matrix.copy()

    frag_permutations = list(itertools.permutations([main_mol, fragment2]))
    fragment_list = frag_permutations[r_position]

    for r_number_in_molecule, fragment_molecule in enumerate(fragment_list):  

        #ここから、主骨格の処理と同じ
        fragment_adjacency_matrix = Chem.rdmolops.GetAdjacencyMatrix(fragment_molecule)

        for bond in fragment_molecule.GetBonds():
            fragment_adjacency_matrix[bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()] = bond_list.index(
                bond.GetBondType())
            fragment_adjacency_matrix[bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()] = bond_list.index(
                bond.GetBondType())
        fragment_atoms = []
        for atom in fragment_molecule.GetAtoms():
            fragment_atoms.append(atom.GetSymbol())

        # integrate adjacency matrix
        r_index_in_fragment_molecule = fragment_atoms.index('*')

        r_bonded_atom_index_in_fragment_molecule = \
            np.where(fragment_adjacency_matrix[r_index_in_fragment_molecule, :] != 0)[0][0]

        # 後で * を削除するのでそのための調整（たぶん）
        if r_bonded_atom_index_in_fragment_molecule > r_index_in_fragment_molecule:
            r_bonded_atom_index_in_fragment_molecule -= 1

        fragment_atoms.remove('*')
        fragment_adjacency_matrix = np.delete(fragment_adjacency_matrix, r_index_in_fragment_molecule, 0)
        fragment_adjacency_matrix = np.delete(fragment_adjacency_matrix, r_index_in_fragment_molecule, 1)

        #新たに生成する分子用のマトリックス作成
        main_size = generated_adjacency_matrix.shape[0]
        generated_adjacency_matrix = np.c_[generated_adjacency_matrix, np.zeros(
            [generated_adjacency_matrix.shape[0], fragment_adjacency_matrix.shape[0]], dtype='int32')]
        generated_adjacency_matrix = np.r_[generated_adjacency_matrix, np.zeros(
            [fragment_adjacency_matrix.shape[0], generated_adjacency_matrix.shape[1]], dtype='int32')]

        #マトリックスに結合のタイプを記述
        generated_adjacency_matrix[r_bonded_atom_index_in_level1_molecule[r_number_in_molecule], 
                                   r_bonded_atom_index_in_fragment_molecule + main_size] = \
            r_bond_number_in_level1_molecule[r_number_in_molecule]

        generated_adjacency_matrix[r_bonded_atom_index_in_fragment_molecule + main_size, 
                                   r_bonded_atom_index_in_level1_molecule[r_number_in_molecule]] = \
            r_bond_number_in_level1_molecule[r_number_in_molecule]

        generated_adjacency_matrix[main_size:, main_size:] = fragment_adjacency_matrix

        generated_molecule_atoms += fragment_atoms

    # generate structures 
    generated_molecule = Chem.RWMol()
    atom_index = []

    for atom_number in range(len(generated_molecule_atoms)):
        atom = Chem.Atom(generated_molecule_atoms[atom_number])
        molecular_index = generated_molecule.AddAtom(atom)
        atom_index.append(molecular_index)

    for index_x, row_vector in enumerate(generated_adjacency_matrix):    
        for index_y, bond in enumerate(row_vector):      
            if index_y <= index_x:
                continue
            if bond == 0:
                continue
            else:
                generated_molecule.AddBond(atom_index[index_x], atom_index[index_y], bond_list[bond])

    generated_molecule = generated_molecule.GetMol()

    return generated_molecule
