#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""radiative transfer module used in exospectral analysis.

"""
from jax import jit
from jax.lax import scan
from exojax.spec import lpf
import jax.numpy as jnp
from exojax.spec import planck
from functools import partial


__all__ = ['JaxRT']

class JaxRT(object):
    """Jax Radiative Transfer class
    
    """
    def __init__(self):
        self.nuarr = []
        self.numic = 0.5 # 0.5 micron for planck
        self.Sfix = []
        self.Parr = []

    @partial(jit, static_argnums=(0,))
    def run(self,nu0,sigmaD,gammaL):
        """Running RT by linear algebra radiative transfer (default)

        """
        gi = planck.nB(self.Tarr,self.numic)
        numatrix=lpf.make_numatrix(self.nuarr,self.hatnufix,nu0)
        xsv = 1.e-1*cross(numatrix,sigmaD,gammaL,self.Sfix)
        dParr = (1.0-self.k)*self.Parr
        dtauM=dParr[:,None]*xsv[None,:]
        TransM=(1.0-dtauM)*jnp.exp(-dtauM)

        #QN=jnp.ones(len(nuarr))*planck.nB(Tarr[0],numic)
        QN=jnp.zeros(len(self.nuarr))
        Qv=(1-TransM)*gi[:,None]
        Qv=jnp.vstack([Qv,QN])
    
        onev=jnp.ones(len(self.nuarr))
    
        TransM=jnp.vstack([onev,TransM])
        F=(jnp.sum(Qv*jnp.cumprod(TransM,axis=0),axis=0))
        F=F*3.e7
   
        return F
        
    @partial(jit, static_argnums=(0,))        
    def add_layer(self,carry,x):
        """adding an atmospheric layer

        Params:
           carry: F[i], P[i], nu0, sigmaD, gammaL
           x: free parameters, T
        
        Returns:
           carry: F[i+1], P[i+1]=k*P[i]
           dtaui: dtau of this layer

        """
        F,Pi,nu0,sigmaD,gammaL = carry        
        Ti = x
        gi = planck.nB(Ti,self.numic)
        numatrix=lpf.make_numatrix(self.nuarr,self.hatnufix,nu0)
        cs=cross(numatrix,sigmaD,gammaL,self.Sfix)
        dtaui = 1.e-1*cs*(1.0-self.k)*Pi # delta P = (1.0-k)*Pi
        Trans=(1.0-dtaui)*jnp.exp(-dtaui)
        F = F*Trans + gi*(1.0-Trans)
        carry=[F,self.k*Pi,nu0,sigmaD,gammaL] #carryover 
        return carry,dtaui

    @partial(jit, static_argnums=(0,))
    def layerscan(self,init):
        """Runnin RT by scanning layers

        Params: 
           init: initial parameters
           Tarr: temperature array        
        
        Returns:
           F: upward flux

        """
        FP,null=(scan(self.add_layer,init,self.Tarr,self.NP))
        return FP[0]*3.e4 #TODO: 

    
@jit
def cross(numatrix,sigmaD,gammaL,S):
    """cross section

    Params:
       numatrix: jnp array
                 wavenumber matrix
       sigmaD: float
               sigma parameter in Voigt profile
       gammaL: float
               gamma parameter in Voigt profile
       S: jnp array
          line strength array
    
    Returns:
       cs: cross section

    """
#    cs = jnp.dot(lpf.VoigtTc(numatrix,sigmaD,gammaL).T,S)
    cs = jnp.dot((lpf.VoigtHjert(numatrix.flatten(),sigmaD,gammaL)).reshape(jnp.shape(numatrix)).T,S)
    return cs

def const_p_layer(logPtop=-2.,logPbtm=2.,NP=17):
    """constructing the pressure layer
    
    Args: 
       logPtop: float
                log10(P[bar]) at the top layer
       logPbtm: float
                log10(P[bar]) at the bottom layer
       NP: int
                the number of the layers

    Returns: 
         Parr: jnp array
               pressure layer
         k: float
            k-factor, P[i+1] = k*P[i]
    
    """
    dlogP=(logPbtm-logPtop)/(NP-1)
    k=10**-dlogP
    Parr=jnp.logspace(logPtop,logPbtm,NP)
    Parr=Parr[::-1]
    return Parr, k

def tau_layer(nu,T):
    tau=jnp.dot((lpf.VoigtHjert(numatrix.flatten(),sigmaD,gammaL)).reshape(jnp.shape(numatrix)).T,S)
    lpf.VoigtHjert(nu,sigmaD,gammaL)
    dtau=lpf.VoigtHjert(nu,sigmaD,gammaL).T
    f=jnp.exp(-A*tau)
    return f
