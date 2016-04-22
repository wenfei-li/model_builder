"""Convert all-atom to coarse-grain representation



"""

# TODO: 
# - Finish CACB mapping.


import numpy as np

import mdtraj as md

import mdtraj as md
from mdtraj.core.topology import Topology

import contacts as cts
import atom_types

class CalphaMapping(object):
    r"""Calpha representation mapping"""

    def __init__(self, topology):
        r"""Calpha representation mapping

        Maps an all-atom representation to just the C-alpha's of the backbone.

        Holds default assignment of .

        Parameters
        ----------
        topology : mdtraj.Topology object

        """


        self._ref_topology = topology.copy()

        # Build new topology
        newTopology = Topology()
        prev_ca = None
        ca_idxs = []
        atm_idx = 0 
        for chain in topology._chains:
            newChain = newTopology.add_chain()
            for residue in chain._residues:
                resSeq = getattr(residue, 'resSeq', None) or residue.index
                newResidue = newTopology.add_residue(residue.name, newChain, resSeq)
                # map CA
                new_ca = newTopology.add_atom('CA', md.core.element.get_by_symbol('C'), 
                                    newResidue, serial=atm_idx)

                ca_idxs.append([[ atm.index for atm in residue.atoms if \
                            (atm.name == "CA") ][0], atm_idx ])
                if prev_ca is None:
                    prev_ca = new_ca
                else:
                    if prev_ca.residue.chain.index == new_ca.residue.chain.index:
                        # Only bond atoms in same chain 
                        newTopology.add_bond(prev_ca, new_ca)
                    prev_ca = new_ca
                atm_idx += 1

        self._ca_idxs = np.array(ca_idxs)
        self.topology = newTopology

    @property
    def top(self):
        return self.topology

    def map_traj(self, traj):
        """Create new trajectory"""
        ca_xyz = traj.xyz[:,self._ca_idxs[:,0],:]
        return md.Trajectory(ca_xyz, self.topology)

    @property
    def n_atomtypes(self):
        return len(self.atomtypes)

    def add_atoms(self, mass=1, radius=0.4, charge=0):
        name = "CA"
        mass = mass # amu
        radius = radius # nm
        charge = charge  # units??
        self.atoms = []
        self.atomtypes = []
        for atom in self.top.atoms:
            cg_atom = atom_types.CoarseGrainAtom(atom.index, name, 
                    atom.residue.index, atom.residue.name, radius, mass, charge)
            self.atoms.append(cg_atom)

            # Unique list of atom types.
            if cg_atom.name not in [ atm.name for atm in self.atomtypes ]:
                self.atomtypes.append(cg_atom)

    def _residue_to_atom_contacts(self, residue_contacts):
        atm_contacts = []
        for n,k in residue_contacts: 
            nres = self.topology.residue(n)
            kres = self.topology.residue(k)
            # Calpha-Calpha contact
            ca_n = nres.atom(0)
            ca_k = kres.atom(0)
            atm_contacts.append((ca_n, ca_k))
        return atm_contacts

    def _assign_sbm_angles(self):
        self._angles = []
        for chain in self.topology.chains:
            for i in range(chain.n_atoms - 2):
                self._angles.append(( chain.atom(i), chain.atom(i + 1), chain.atom(i + 2)))
        
    def _assign_sbm_dihedrals(self):
        self._improper_dihedrals = []
        self._dihedrals = []
        for chain in self.topology.chains:
            for i in range(chain.n_atoms - 3):
                self._dihedrals.append(( chain.atom(i), chain.atom(i + 1),\
                                   chain.atom(i + 2), chain.atom(i + 3)))

    def _assign_sbm_contacts(self, ref_traj_aa):
        residue_contacts = cts.residue_contacts(ref_traj_aa)
        self._contact_pairs = self._residue_to_atom_contacts(residue_contacts)
    
    def _add_pairs(self, pairs):
        self._contact_pairs = []
        for n, k in pairs:
            natom = self.top.atom(n)
            katom = self.top.atom(k)
            self._contact_pairs.append([natom, katom])
    
    def add_disulfides(self, disulfides):
        """ Add disulfide bonded interactions.
        
        Adds appropriate bond, angle and dihedral interactions.
        
        Args:
            disulfides (list): List of disulfide pairs between the 
                residues of the disulfides.
                
        """
        
        for pair in disulfides:
            res1 = self.top.residue(pair[0])
            res2 = self.top.residue(pair[1])
            respre = self.top.residue(pair[0]-1)
            respost = self.top.residue(pair[1]-1)
            
            #add c-alpha atoms
            cys1 = res1.atom(0)
            cys2 = res2.atom(0)
            #add c-beta
            ca1 = respre.atom(0)
            ca2 = respost.atom(0)
            
            #add bond between c-alpha of the Cys residues
            self.top.add_bond(cys1, cys2)
            
            #add angular constraints between CYS;s and previous c-alphas
            self._angles.append((ca1, cys1, cys2))
            self._angles.append((cys1, cys2, ca2))
            
            #add dihedral constraints between CYS's and previous c-alphas
            self._dihedrals.append((ca1, cys1, cys2, ca2))

class CalphaCbetaMapping(object):
    """Calpha Cbeta center-of-mass representation mapping"""

    def __init__(self, topology):
        self._ref_topology = topology.copy()

        # Build new topology
        newTopology = Topology()
        new_atm_idx = 0 
        res_idx = 1
        prev_ca = None
        ca_idxs = []
        self._sidechain_idxs = []
        self._sidechain_mass = []
        for chain in topology._chains:
            newChain = newTopology.add_chain()
            for residue in chain._residues:
                #resSeq = getattr(residue, 'resSeq', None) or residue.index
                newResidue = newTopology.add_residue(residue.name, newChain, res_idx)
                # map CA
                new_ca = newTopology.add_atom('CA', md.core.element.get_by_symbol('C'), 
                                    newResidue, serial=new_atm_idx)
                if prev_ca is None:
                    prev_ca = new_ca
                else:
                    # only bond atoms in the same chain.
                    if new_ca.residue.chain.index == prev_ca.residue.chain.index:
                        newTopology.add_bond(prev_ca, new_ca)
                    prev_ca = new_ca

                ca_idxs.append([[ atm.index for atm in residue.atoms if \
                            (atm.name == "CA") ][0], new_atm_idx ])
                new_atm_idx += 1

                if residue.name == 'GLY':
                    self._sidechain_idxs.append([])
                    self._sidechain_mass.append([])
                else:
                    # map CB
                    cb_name = "CB%s" % atom_types.residue_code[residue.name]
                    new_cb = newTopology.add_atom(cb_name, md.core.element.get_by_symbol('C'), 
                                        newResidue, serial=new_atm_idx)

                    newTopology.add_bond(new_cb, new_ca)

                    self._sidechain_idxs.append([[ atm.index for atm in residue.atoms if \
                                (atm.is_sidechain) and (atm.element.symbol != "H") ], new_atm_idx ])
                    self._sidechain_mass.append(np.array([ atm.element.mass for atm in residue.atoms if \
                                (atm.is_sidechain) and (atm.element.symbol != "H") ]))
                    new_atm_idx += 1
                res_idx += 1

        self._ca_idxs = np.array(ca_idxs)
        self.topology = newTopology
    
    @property
    def top(self):
        return self.topology

    def map_traj(self, traj):
        """Return new Trajectory object with cacb topology and xyz"""
        cacb_xyz = np.zeros((traj.n_frames, self.topology.n_atoms, 3))

        for res in self.topology.residues:
            cacb_xyz[:,self._ca_idxs[res.index,1],:] = \
                    traj.xyz[:,self._ca_idxs[res.index,0],:]
            # Map sidechain atoms to their center of mass
            if res.name != 'GLY': 
                old_idxs = self._sidechain_idxs[res.index][0]
                new_idx = self._sidechain_idxs[res.index][1]
                sc_mass = self._sidechain_mass[res.index]
                tot_mass = np.sum(sc_mass)

                res_frms = traj.xyz[:,old_idxs,:]
                sc_com_xyz = np.array(map(lambda frm: \
                        np.sum(frm.T*sc_mass/tot_mass, axis=1), res_frms))

                cacb_xyz[:,new_idx,:] = sc_com_xyz

        return md.Trajectory(cacb_xyz, self.topology)

    def _residue_to_atom_contacts(self, residue_contacts):
        atm_contacts = []
        for n,k in residue_contacts: 
            nres = self.topology.residue(n)
            kres = self.topology.residue(k)
            # Calpha-Calpha contact
            ca_n = nres.atom(0)
            ca_k = kres.atom(0)
            atm_contacts.append([ca_n, ca_k])
            if (nres.name != "GLY") and (kres.name != "GLY"): 
                # Cbeta-Cbeta contact
                cb_n = nres.atom(1)
                cb_k = kres.atom(1)
                atm_contacts.append([cb_n, cb_k])
        return atm_contacts

    def _assign_sbm_angles(self):

        self._angles = []
        for chain in self.topology.chains:
            # CA-CA-CA angles first
            ca_atoms = [ atom for atom in chain.atoms if atom.name == "CA" ]
            for i in range(len(ca_atoms) - 2):
                self._angles.append((ca_atoms[i], ca_atoms[i + 1], ca_atoms[i + 2]))

            # CA-CA-CB and CB-CA-CA angles next
            for res in chain.residues:
                if res.name != "GLY":
                    ca = res.atom(0)
                    cb = res.atom(1)
                    if res.index == 0:
                        # if terminal
                        next_ca = chain.residue(res.index + 1).atom(0)
                        self._angles.append((cb, ca, next_ca))
                    elif (res.index + 1) == chain.n_residues:
                        # if terminal
                        prev_ca = chain.residue(res.index - 1).atom(0)
                        self._angles.append((prev_ca, ca, cb))
                    else:
                        prev_ca = chain.residue(res.index - 1).atom(0)
                        next_ca = chain.residue(res.index + 1).atom(0)
                        self._angles.append((prev_ca, ca, cb))
                        self._angles.append((cb, ca, next_ca))

    def _assign_sbm_dihedrals(self):
        
        self._improper_dihedrals = []
        self._dihedrals = []
        for chain in self.topology.chains:
            #add the proper ca-ca-ca-ca dihedrals
            ca_atoms = [ atom for atom in chain.atoms if atom.name == "CA" ]
            for i in range(len(ca_atoms)-3):
                self._dihedrals.append((ca_atoms[i], ca_atoms[i+1], ca_atoms[i+2], ca_atoms[i+3]))
            #add improper dihedrals
            num_residues = chain.residue(-1).index
            for res in chain.residues:
                check = res.index == 0 #not first residue 
                check = check or res.index == num_residues #last residue 
                check = check or res.name == "GLY" #GLY
                if not check:
                    idx = res.index
                    cj = chain.residue(idx-1).atom(0)
                    ck = chain.residue(idx+1).atom(0)
                    dih = (res.atom(0), cj, ck, res.atom(1))
                    self._improper_dihedrals.append(dih)
                    
    def add_disulfides(self, disulfides):
        """ Add disulfide bonded interactions.
        
        Adds appropriate bond, angle and dihedral interactions.
        
        Args:
            disulfides (list): List of disulfide pairs between the 
                residues of the disulfides.
                
        """
        
        for pair in disulfides:
            res1 = self.top.residue(pair[0])
            res2 = self.top.residue(pair[1])
            
            #add c-alpha atoms
            ca1 = res1.atom(0)
            ca2 = res2.atom(0)
            #add c-beta
            cb1 = res1.atom(1)
            cb2 = res2.atom(1)
            
            #add bond between c-beta
            self.top.add_bond(cb1, cb2)
            
            #add angular constraints
            self._angles.append((ca1, cb1, cb2))
            self._angles.append((cb1, cb2, ca2))
            
            #add dihedral constraints
            self._dihedrals.append((ca1, cb1, cb2, ca2))

    @property
    def n_atomtypes(self):
        return len(self.atomtypes)
                                        
    def add_atoms(self):
        self.atoms = []
        self.atomtypes = []
        for chain in self.top._chains:
            for res in chain._residues:
                if res.name == "GLY":
                    cg_atom = atom_types.CoarseGrainAtom(res.atom(0).index, "CA", 
                            res.index, res.name, 0.266, 1, 0)
                    self.atoms.append(cg_atom)
                else:
                    cg_atom = atom_types.CoarseGrainAtom(res.atom(0).index, "CA", 
                            res.index, res.name, 0.266, 1, 0)  
                    self.atoms.append(cg_atom)
                    radii = atom_types.residue_cacb_effective_interaction[res.name]
                    name = "CB%s" % atom_types.residue_code[res.name]
                    cg_atom = atom_types.CoarseGrainAtom(res.atom(1).index, name, 
                            res.index, res.name, radii, 1, 0)
                    self.atoms.append(cg_atom)   
        
        for cg_atom in self.atoms:
            # Unique list of atom types.
            if cg_atom.name not in [ atm.name for atm in self.atomtypes ]:
                self.atomtypes.append(cg_atom)
    
    def _atomidx_to_atom_contacts(self, pairs):
        atm_contacts = []
        for n,k in pairs:
            natom = self.top.atom(n)
            katom = self.top.atom(k)
            atm_contacts.append([natom, katom])
        return atm_contacts
        
    def _add_pairs(self, pairs):
        self._contact_pairs = self._atomidx_to_atom_contacts(pairs)

    def _add_atomtypes(self):
        pass
        

class HeavyAtomMapping(object):

    def __init__(self, topology):
        r"""Calpha representation mapping

        Maps an all-atom representation to the heavy (non-hydrogen) atoms.

        Parameters
        ----------
        topology : mdtraj.Topology object

        """
        newTopology = md.Topology()     
        
        atom_mapping = {}

        atm_idx = 0
        res_idx = 1
        heavy_atom_idxs = []
        for chain in topology.chains:
            newChain = newTopology.add_chain()
            for residue in chain.residues:
                newResidue = newTopology.add_residue(residue.name, newChain, res_idx)
                for atom in residue.atoms:  
                    if "H" != atom.element.symbol:
                        new_atom = newTopology.add_atom(atom.name, 
                                            md.core.element.get_by_symbol(atom.element.symbol),
                                            newResidue, serial=atm_idx)
                        atom_mapping[atom] = new_atom
                        heavy_atom_idxs.append([atom.index, new_atom.index])
                        atm_idx += 1
                res_idx += 1
        
        # Add new bonds
        for atm1, atm2 in topology.bonds:
            if (atm1 in atom_mapping) and (atm2 in atom_mapping):
                new_atm1 = atom_mapping[atm1]
                new_atm2 = atom_mapping[atm2]
                newTopology.add_bond(new_atm1, new_atm2)

        self._heavy_atom_idxs = np.array(heavy_atom_idxs)
        self.topology = newTopology

    @property
    def top(self):
        return self.topology

    def map_traj(self, traj):
        """Create new trajectory"""
        hvy_xyz = traj.xyz[:,self._heavy_atom_idxs[:,0],:]
        return md.Trajectory(hvy_xyz, self.topology)

class AwsemMapping(object):
    """Calpha Cbeta center-of-mass representation mapping"""

    def __init__(self, topology):
        self._ref_topology = topology.copy()

        # weights for creating glycine hydrogens (H-Beta, HB).
        self.HB_coeff_N = -0.946747
        self.HB_coeff_CA = 2.50352
        self.HB_coeff_O = -0.620388

        # Build new topology
        newTopology = Topology()
        CACBO_idxs = []
        HB_idxs = []
        chain_idx = 1
        res_idx = 1
        atm_idx = 0
        prev_ca = None
        prev_o = None
        for chain in topology._chains:
            newChain = newTopology.add_chain()
            for residue in chain._residues:
                newResidue = newTopology.add_residue(residue.name, newChain, res_idx)

                # Add atoms for residue 
                new_ca = newTopology.add_atom('CA', md.core.element.get_by_symbol('C'), 
                                            newResidue, serial=atm_idx)
                CA_idx = [ atm.index for atm in residue.atoms if (atm.name == "CA") ][0]
                CACBO_idxs.append([CA_idx, new_ca.index])
                atm_idx += 1

                new_o = newTopology.add_atom('O', md.core.element.get_by_symbol('O'), 
                                            newResidue, serial=atm_idx)
                O_idx = [ atm.index for atm in residue.atoms if (atm.name == "O") ][0]
                CACBO_idxs.append([O_idx, new_o.index])

                newTopology.add_bond(new_ca, new_o)

                atm_idx += 1
                
                if residue.name == 'GLY':
                    new_hb = newTopology.add_atom('HB', md.core.element.get_by_symbol('H'), 
                                                newResidue, serial=atm_idx)
                    N_idx = [ atm.index for atm in residue.atoms if (atm.name == "N") ][0]
                    HB_idxs.append([N_idx, CA_idx, O_idx, new_hb.index])
                    newTopology.add_bond(new_ca, new_hb)
                else:
                    new_cb = newTopology.add_atom('CB', md.core.element.get_by_symbol('C'), 
                                                newResidue, serial=atm_idx)
                    CB_idx = [ atm.index for atm in residue.atoms if (atm.name == "CB") ][0]
                    CACBO_idxs.append([CB_idx, new_cb.index])
                    newTopology.add_bond(new_ca, new_cb)

                # Add bonds to previous CA and O
                if (prev_ca is None) and (prev_o is None):
                    prev_ca = new_ca
                    prev_o = new_o
                else:
                    newTopology.add_bond(prev_ca, new_ca)
                    newTopology.add_bond(prev_o, new_ca)
                    prev_ca = new_ca
                    prev_o = new_o

                atm_idx += 1
                res_idx += 1
            chain_idx += 1


        self._HB_idxs = np.array(HB_idxs)
        self._CACBO_idxs = np.array(CACBO_idxs)
        self.topology = newTopology

    @property
    def top(self):
        return self.topology

    def map_traj(self, traj):
        """Return new Trajectory object with AWSEM topology and xyz"""
        # Direct slicing for CA, CB, O. HB is interpolated from other atoms
        cacbo_xyz = np.zeros((traj.n_frames, self.topology.n_atoms, 3))
        cacbo_xyz[:, self._CACBO_idxs[:,1], :] = traj.xyz[:, self._CACBO_idxs[:,0], :]
        cacbo_xyz[:, self._HB_idxs[:,3], :] = self.HB_coeff_N*traj.xyz[:, self._HB_idxs[:,0], :] +\
                                              self.HB_coeff_CA*traj.xyz[:, self._HB_idxs[:,1], :] +\
                                              self.HB_coeff_O*traj.xyz[:, self._HB_idxs[:,2], :]
        return md.Trajectory(cacbo_xyz, self.top)

    def set_atom(self):
        pass
        

MAPPINGS = {"CA":CalphaMapping, "CACB":CalphaCbetaMapping, "All-Atom":HeavyAtomMapping, "AWSEM":AwsemMapping}

def assign_mapping(code, topology):
    return MAPPINGS[code](topology)
    

if __name__ == "__main__":
    from model_builder.models.structure.viz_bonds import write_bonds_conect, write_bonds_tcl

    #name = "1JDP"
    name = "2KJV"
    traj = md.load(name+'.pdb')

    # test CA
    mapping = CalphaMapping(traj.top)
    #ca_traj = mapping.map_traj(traj)
    #ca_traj[0].save_pdb('ca_{}.pdb'.format(name))
    #ca_traj.save_xtc('ca_{}.xtc'.format(name))
    #write_bonds_tcl(mapping.topology, outfile="{}_cabonds.tcl".format(name))
    #write_bonds_conect(mapping.topology, outfile="{}_cabonds.conect".format(name))

    # Calculate contacts
    contacts = get_CA_contacts(mapping, traj)
    contacts2 = residue_contacts(mapping, traj)
    #C = np.zeros((traj.n_residues, traj.n_residues))
    #for p in contacts:
    #    C[p[3], p[1]] = 1
    #import matplotlib.pyplot as plt
    #plt.pcolormesh(C)
    #plt.show()

    # test CACB
    #mapping = CalphaCbetaMapping(traj.top)
    #cacb_traj = mapping.map_traj(traj)
    #cacb_traj[0].save_pdb('cacb_{}.pdb'.format(name))
    #cacb_traj.save_xtc('cacb_{}.xtc'.format(name))

