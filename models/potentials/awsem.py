import numpy as np

def theta(r, nu, r_min, r_max):
    return 0.25*(1. + np.tanh(nu*(r - r_min)))*(1. + np.tanh(nu*(r_max - r)))


class DirectContact(object):

    def __init__(self, lambda_direct=1, nu=50., r_min=0.45, r_max=0.65):
        self.lambda_direct = lambda_direct
        self.nu = nu
        self.r_min = r_min
        self.r_max = r_max

    def V(self, r, gamma_direct): 
        return gamma_direct*self.theta_I(r)

    def dVdgamma_direct(self, r):
        return self.theta_I(r)

    def theta_I(self, r):
        return theta(r, self.nu, self.r_min, self.max)

class WaterMediatedContact(object):

    def __init__(self, lambda_water=1., nu=50., nu_sigma=70., r_min=0.65, r_max=0.95):
        self.lambda_water = lambda_water
        self.nu = nu
        self.nu_sigma = nu_sigma
        self.r_min = r_min
        self.r_max = r_max

    def V(self, r, rhoi, rhoj, gamma_water, gamma_protein): 
        return self.lambda_water*(gamma_water*self.dVdgamma_water(r, rhoi, rhoj) +\
                                gamma_protein*self.dVdgamma_protein(r, rhoi, rhoj))

    def dVdgamma_water(self, r, rhoi, rhoj):
        return self.theta_II(r)*self.sigma_water(rhoi, rhoj)

    def dVdgamma_protein(self, r, rhoi, rhoj):
        return self.theta_II(r)*(1. - self.sigma_water(rhoi, rhoj))

    def theta_II(self, r):
        return theta(r, self.nu, self.r_min, self.r_max)

    def sigma_water(self, rhoi, rhoj):
        return 0.25*(1. - np.tanh(self.nu_sigma*(rhoi - self.rho_0)))*(1. - np.tanh(self.nu_sigma*(rhoj - self.rho_0)))
    
class Burial(object):
    """One-body burial potential"""
    def __init__(self, lambda_burial=1., nu=40., rho1_lims=[0.0, 0.3], rho2_lims=[0.3, 0.6], rho3_lims=[0.6, 0.9]):
        self.lambda_burial = lambda_burial
        self.nu = nu
        self.rho_lims = [ rho1_lims, rho2_lims, rho3_lims ]

    def V(self, rhoi, gamma_burials):
        """Burial potential
        
        Parameters
        ----------
        rhoi : np.ndarray 
            Vector that contains the local protein density at site i.
        gamma_burials : list (3)
            Residue specific burial coefficients for residue type i.
    
        """
        V = np.zeros(rho.shape[0])
        for i in range(3):
            V += -self.lambda_burial*gamma_burials[i]*self.burial_theta(
                        rhoi, self.nu, self.rho_lims[i][0], self.rho_lims[i][1])
        return V

    def burial_theta(self, rhoi, nu, rho_min, rho_max):
        return  0.5*np.tanh(nu*(rhoi - rho_min))*np.tanh(nu*(rhoi- rho_max))

class Chi(object):

    def __init__(self, lambda_chi=1., chi_0=-0.83):
        self.lambda_chi
        self.chi_0

    def V(self, C_xyz, CA_xyz, CB_xyz, N_xyz):
        """
        Parameters
        ----------
        C_xyz : np.ndarray (3)
            Coordinates of the backbone C atom.
        CA_xyz : np.ndarray (3)
            Coordinates of the backbone CA atom.
        CB_xyz : np.ndarray (3)
            Coordinates of the CB atom.
        N_xyz : np.ndarray (3)
            Coordinates of the backbone N atom.
        """
        v1 = CA_xyz - C_xyz; v2 = N_xyz - CA_xyz; v3 = CA_xyz - CB_xyz
        chi = np.dot(np.cross(v1, v2), v3)
        return self.lambda_chi*((chi - chi_0)**2)

AWSEM_POTENTIALS = {"DIRECT":DirectContact,
                "WATER":WaterMediatedContact,
                "BURIAL":Burial, 
                "CHI":Chi}