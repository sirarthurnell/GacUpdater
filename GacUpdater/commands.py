# -*- coding: latin-1 -*-

import os
import gridcontroller
import gacdesc
from gacdesc import asmdesc
import clr
clr.AddReference("PresentationFramework")
from System.Windows import MessageBox

class Update(object):
    """
    Comando para actualizar aquellos ensamblados que han sido
    seleccionados para ser actualizados.
    """
    
    def __init__(self, mainwindow, gac, gridcontroller, info):
        """
        El parámetro gac es el objeto que representa la gac.
        El parámetro gridcontroller es el controlador del grid.
        El parámetro info es una función que acepta una cadena y sirve
        para describir la operación que se está realizando actualmente.
        """
        self._gac = gac
        self._gridcontroller = gridcontroller
        self._info = info
        self._mainwindow = mainwindow
        
    def execute(self):
        """
        Provoca la actualización de los ensamblados seleccionados.
        """
        if self._gridcontroller.haserrors():
            MessageBox.Show(self._mainwindow, "Corrija los errores introducidos antes de continuar.", "Actualizar ensamblados")
            return None
        
        selecteddescriptors = self._gridcontroller.get_selected_descriptors()
        for descriptorstuple in selecteddescriptors:
            descriptorindir = descriptorstuple[0]
            descriptoringac = descriptorstuple[1]
            
            #Quitamos el ensamblado antiguo de la gac.
            if descriptoringac:
                self._info("Eliminando ensamblado antiguo %s de la GAC..." % (descriptoringac.name,))
                self._gac.unregister(descriptoringac)
            
            #Metemos el ensamblado nuevo en la gac y actualizamos sus directivas de enlace.
            self._info("Instalando ensamblado antiguo %s de la GAC..." % (descriptorindir.name,))
            self._gac.register(descriptorindir)
            self._info("Actualizando directivas de enlace del ensamblado %s..." % (descriptorindir.name,))
            self._gac.updatebindings(descriptorindir)
            self._info("Ensamblado %s actualizado" % (descriptorindir.name,))
            
            #Eliminamos del grid el ensamblado actualizado.
            self._gridcontroller.removedescriptor(descriptorindir)

class SelectAll(object):
    """
    Comando para seleccionar todos los ensamblados
    a ser actualizados.
    El parámetro gridcontroller es el controlador del grid.
    """
    
    def __init__(self, gridcontroller):
        self._gridcontroller = gridcontroller
        
    def execute(self):
        """
        Selecciona todos los ensamblados en el grid.
        """
        self._gridcontroller.selectall(True)
            
class SelectNone(object):
    """
    Comando para deseleccionar todos los ensamblados
    a ser actualizados.
    """
    
    def __init__(self, gridcontroller):
        """
        El parámetro gridcontroller es el controlador del grid.
        """
        self._gridcontroller = gridcontroller
        
    def execute(self):
        """
        Deselecciona todos los ensamblados en el grid.
        """
        self._gridcontroller.selectall(False)

class Explore(object):
    """
    Comando explorar de la aplicación.
    """

    def __init__(self, gac, asmexplorer, gridcontroller, info):
        """
        El parámetro gac es el objeto que representa la gac.
        El parámetro asmexplorer representa el explorador de ensamblados
        que apunta al directorio que contiene los ensamblados supuestamente
        más recientes que se desean actualizar.
        El parámetro gridcontroller es el controlador del grid.
        El parámetro info es una función que acepta una cadena y sirve
        para describir la operación que se está realizando actualmente.
        """
        self._gac = gac
        self._asmexplorer = asmexplorer
        self._gridcontroller = gridcontroller
        self._info = info
        
    def execute(self):
        """
        Comienza la exploración y comparación de ensamblados, rellenando el grid
        con aquellos que deberían ser actualizados.
        """
        self._info("Explorando GAC...")
        self._gac.load()
        self._info("Explorando directorio donde se encuentran los ensamblados a actualizar...")
        self._asmexplorer.load()
        self._info("Determinando actualizaciones...")
        updatesfound = self._determineupdates()
        self._gridcontroller.fill(updatesfound)
        self._info("Se han encontrado %d posibles actualizaciones" % (len(updatesfound),))
        
    #Determina que ensamblados deben actualizarse y la nueva directiva
    #de enlace a aplicar.
    
    #Devuelve los descriptores de aquellos ensamblados que necesitan
    #actualización con la nueva directiva de enlace establecida
    #en ellos pero sin aplicar en la GAC. Concretamente se devuelve
    #una lista de tuplas, en cada una de las cuales, su primer elemento
    #es el ensamblado en directorio a instalar, y el segundo es el
    #ensamblado en la gac que sería sustituido (o None si no existía
    #dicho ensamblado).
    def _determineupdates(self):
        asmingac = None
        updatesfound = []
        matchedsingac = []
        for asmindir in self._asmexplorer:
            matchedsingac = self._gac.find(asmindir.name)
            if matchedsingac:
                #Si en la gac había varios ensamblados con el mismo nombre,
                #obtenemos el de mayor versión.
                asmingac = matchedsingac[-1]
                
                #Comprobamos si puede ser actualizado.
                if self._needsupdate(asmindir, asmingac):
                    self._attach_new_bindings(asmindir, asmingac)
                    updatesfound.append((asmindir, asmingac))
            else:
                #Si no está en la gac, directamente lo tomamos para ser
                #instalado.
                self._attach_new_bindings(asmindir)
                updatesfound.append((asmindir, None))
                
        #Devolvemos la lista de ensamblados a ser actualizados.
        return updatesfound
        
    #Determina si el ensamblado especificado necesita ser actualizado o no.
    
    #El parámetro descriptortoinstall es el descriptor del ensamblado que
    #se quiere actualizar.
    #El parámetro descriptoringac es el descriptor del ensamblado que
    #está instalado en la gac.
    
    #Devuelve True en el caso en el que el ensamblado a instalar sea
    #de mayor versión que su homólogo instalado en la gac. También
    #devolverá True si no se especificó descriptoringac. Devolverá
    #False en el caso en el que el ensamblado instalado en la gac sea
    #de versión igual o mayor que su posible reemplazo.    
    def _needsupdate(self, descriptortoinstall, descriptoringac=None):
        #Función auxiliar que pasada una cadena o enumerable de versión,
        #devuelve una tupla de versión sin el número de compilación.
        def supresscompilenum(version):
            versiontuple = asmdesc.version_to_tuple(version)
            if len(versiontuple) > 3:
                newversion = (versiontuple[0], versiontuple[1], versiontuple[2])
            else:
                newversion = versiontuple            
            return newversion
        
        if not descriptoringac:
            return True
        
        versiontoinstall = supresscompilenum(descriptortoinstall.version)
        versioningac = supresscompilenum(descriptoringac.version)
        if asmdesc.compareversions(versiontoinstall, versioningac) > 0:
            return True
        else:
            return False
    
    #Determina la nueva directiva de enlace a aplicar al ensamblado
    #que es candidato para actualización.
    
    #No devuelve nada, sólo actualiza las directivas en el descriptor
    #del ensamblado que es candidato a ser actualizado.
    #Actualmente el parámetro descriptoringac no se usa. Está presente
    #para un posible uso futuro en el que debiera tener en cuenta la versión
    #del ensamblado existente en la gac.
    def _attach_new_bindings(self, descriptortoinstall, descriptoringac=None):
        versiontoinstall = descriptortoinstall.version.split(".")
        newbinding = None
        upperbound = ".".join(versiontoinstall[0:-1]) + ".65535"
        #Si no hay descriptor, usamos el rango que va desde 1.0.0.0 hasta la versión
        #del ensamblado a instalar con el último número especificado a 65535.
        #if not descriptoringac:            
        #lowerbound = "%s.0.0.0" % (versiontoinstall[0],)
        lowerbound = "1.0.0.0"
        newbinding = asmdesc.BindingDirective("-".join((lowerbound, upperbound)), 
            descriptortoinstall.version)
            
        #Sustituimos todas las directivas de enlace que tenía el ensamblado por
        #la nueva construida.
        descriptortoinstall.bindings = (newbinding,)