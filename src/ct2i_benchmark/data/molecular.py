"""Molecular utilities for BACE: canonical SMILES, Morgan fingerprints,
Bemis-Murcko scaffold groups. RDKit version is pinned in the lockfile."""
from __future__ import annotations

import numpy as np


def canonical_smiles(smiles_list):
    from rdkit import Chem
    out = []
    for s in smiles_list:
        mol = Chem.MolFromSmiles(s)
        out.append(Chem.MolToSmiles(mol, canonical=True) if mol is not None else None)
    return out


def morgan_fingerprints(canon_smiles, n_bits=1024, radius=2) -> np.ndarray:
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    fps = np.zeros((len(canon_smiles), n_bits), dtype=np.uint8)
    for i, s in enumerate(canon_smiles):
        if s is None:
            continue  # left all-zero; caller decides policy (BACE source has no invalid rows)
        mol = Chem.MolFromSmiles(s)
        bv = gen.GetFingerprint(mol)
        for b in bv.GetOnBits():
            fps[i, b] = 1
    return fps


def scaffold_groups(canon_smiles) -> np.ndarray:
    """Integer group id per molecule from Bemis-Murcko scaffold SMILES."""
    from rdkit.Chem.Scaffolds import MurckoScaffold
    keys = []
    for s in canon_smiles:
        if s is None:
            keys.append("__INVALID__")
            continue
        scaf = MurckoScaffold.MurckoScaffoldSmiles(smiles=s, includeChirality=False)
        keys.append(scaf if scaf else "__ACYCLIC__")
    uniq = {k: i for i, k in enumerate(dict.fromkeys(keys))}
    return np.array([uniq[k] for k in keys], dtype=np.int64)
