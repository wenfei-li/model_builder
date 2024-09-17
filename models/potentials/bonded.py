"""Utilities for bonded potential terms"""

import numpy as np

#############################################################################
# Bond potentials
#############################################################################
class BondPotential(object):

    def __init__(self, atmi, atmj):
        self.atmi = atmi
        self.atmj = atmj

    def describe(self):
        """interaction description"""
        return "{}:{:>12}{:>12}".format(self.prefix_label, self.atmi, self.atmj)

    def __hash__(self):
        hash_value = hash(self.prefix_label)
        hash_value ^= hash(self.atmi)
        hash_value ^= hash(self.atmj)
        return hash_value

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class HarmonicBondPotential(BondPotential):

    def __init__(self, atmi, atmj, kb, r0):
        BondPotential.__init__(self, atmi, atmj)
        self.prefix_label = "HARMONIC_BOND"
        self.kb = kb
        self.r0 = r0
    
    def V(self, r):
        return self.kb*self.dVdkb(r)

    def dVdr(self, r): 
        return self.kb*self.d2Vdrdkb(r)

    def dVdkb(self, r):
        return 0.5*(r - self.r0)**2

    def d2Vdrdkb(self, r): 
        return (r - self.r0)

    def __hash__(self):
        return hash(frozenset(self.__dict__.items()))

############################################################################
# Angle potentials
############################################################################
class AnglePotential(object):

    def __init__(self, atmi, atmj, atmk):
        self.atmi = atmi
        self.atmj = atmj
        self.atmk = atmk

    def describe(self):
        """interaction description"""
        return "{}:{:>12}{:>12}{:>12}".format(
                self.prefix_label, self.atmi, self.atmj, self.atmk)

    def __hash__(self):
        hash_value = hash(self.prefix_label)
        hash_value ^= hash(self.atmi)
        hash_value ^= hash(self.atmj)
        hash_value ^= hash(self.atmk)
        return hash_value

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

class HarmonicAnglePotential(AnglePotential):

    def __init__(self, atmi, atmj, atmk, ka, theta0):
        AnglePotential.__init__(self, atmi, atmj, atmk)
        self.prefix_label = "HARMONIC_ANGLE"
        self.ka = ka
        self.theta0 = theta0

    def V(self, theta):
        return self.ka*self.dVdka(theta)

    def dVdtheta(self, theta): 
        return self.ka*self.d2Vdthetadka(theta)

    def dVdka(self, theta):
        return 0.5*(theta - self.theta0)**2

    def d2Vdthetadka(self, theta): 
        return (theta - self.theta0)

    def __hash__(self):
        hash_value = AnglePotential.__hash__(self)
        hash_value ^= hash(self.ka)
        hash_value ^= hash(self.theta0)
        return hash_value

############################################################################
# Dihedral potentials
############################################################################
class DihedralPotential(object):

    def __init__(self, atmi, atmj, atmk, atml):
        self.atmi = atmi
        self.atmj = atmj
        self.atmk = atmk
        self.atml = atml

    def describe(self):
        """interaction description"""
        return "{}:{:>12}{:>12}{:>12}{:>12}".format(
                self.prefix_label, self.atmi, self.atmj, self.atmk, self.atml)

    def __hash__(self):
        hash_value = hash(self.prefix_label)
        hash_value ^= hash(self.atmi)
        hash_value ^= hash(self.atmj)
        hash_value ^= hash(self.atmk)
        hash_value ^= hash(self.atml)
        return hash_value

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

class HarmonicDihedralPotential(DihedralPotential):

    def __init__(self, atmi, atmj, atmk, atml, kd, phi0):
        DihedralPotential.__init__(self, atmi, atmj, atmk, atml)
        self.prefix_label = "HARMONIC_DIHEDRAL"
        self.kd = kd
        self.phi0 = phi0

    def V(self, phi):
        return self.kd*self.dVdkd(phi)

    def dVdphi(self, phi): 
        return self.kd*self.d2Vdphidkd(phi)

    def dVdkd(self, phi):
        return 0.5*(phi - self.phi0)**2

    def d2Vdphidkd(self, phi): 
        return (phi - self.phi0)

    def __hash__(self):
        hash_value = DihedralPotential.__hash__(self)
        hash_value ^= hash(self.prefix_label) 
        hash_value ^= hash(self.kd)
        hash_value ^= hash(self.phi0)
        return hash_value

class CosineDihedralPotential(DihedralPotential):

    def __init__(self, atmi, atmj, atmk, atml, kd, phi0, mult):
        DihedralPotential.__init__(self, atmi, atmj, atmk, atml)
        self.prefix_label = "COSINE_DIHEDRAL"
        self.kd = kd
        self.phi0 = phi0
        self.mult = mult

    def V(self, phi):
        return self.kd*self.dVdkd(phi)

    def dVdphi(self, phi): 
        return self.kd*self.d2Vdphidkd(phi)

    def dVdkd(self, phi):
        return 1. - np.cos(self.mult*(phi - self.phi0))

    def d2Vdphidkd(self, phi): 
        return self.mult*np.sin(self.mult*(phi - self.phi0))

    def __hash__(self):
        hash_value = DihedralPotential.__hash__(self)
        hash_value ^= hash(self.prefix_label) 
        hash_value ^= hash(self.kd)
        hash_value ^= hash(self.phi0)
        hash_value ^= hash(self.mult)
        return hash_value


BOND_POTENTIALS = {"HARMONIC_BOND":HarmonicBondPotential}

ANGLE_POTENTIALS = {"HARMONIC_ANGLE":HarmonicAnglePotential}

DIHEDRAL_POTENTIALS = {"HARMONIC_DIHEDRAL":HarmonicDihedralPotential,
                        "COSINE_DIHEDRAL":CosineDihedralPotential}
