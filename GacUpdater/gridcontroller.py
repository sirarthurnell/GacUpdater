# -*- coding: latin-1 -*-

import gacdesc
from gacdesc import asmdesc
import clr
clr.AddReference("PresentationFramework")
from System.Windows.Controls import DataGrid, Validation
from System.Windows.Media import VisualTreeHelper

class GridController(object):
    """
    Mantiene una sincronización con el grid
    y el modelo.
    """
    def __init__(self, grid):
        self._grid = grid
        self._descriptorslist = []
        
    def haserrors(self):
        """
        Devuelve True si hay datos erróneos introducidos en el grid.
        Devuelve False si todos los datos introducidos son correctos.
        """         
        return not self._isvalid(self._grid)
        
    def descriptorscount(self):
        """
        Obtiene el número de ensamblados que se están mostrando en el grid.
        """
        return len(self._descriptorslist)
        
    def fill(self, descriptors):
        """
        Carga los ensamblados de la GAC y los muestra en el grid.
        """
        descriptoritem = None
        self._descriptorslist = []
        for i, descriptorstuple in enumerate(descriptors):
            descriptoritem = DescriptorItem(descriptorstuple[0], descriptorstuple[1], False)
            self._descriptorslist.append(descriptoritem)
            
        self._grid.ItemsSource = self._descriptorslist
        
    def selectall(self, selectuselect):
        """
        Selecciona o deselecciona todos los ensamblados
        a ser actualizados.
        """
        for descriptoritem in self._descriptorslist:
            descriptoritem.update = selectuselect
            
        #Refrescamos la vista.
        self._grid.Items.Refresh()
            
    def removedescriptor(self, descriptortoremove):
        """
        Elimina el descriptor especificado del grid.
        """
        descriptorslistcopy = self._descriptorslist[:]
        for descriptoritem in descriptorslistcopy:
            if (descriptortoremove == descriptoritem.descriptorindir 
            or descriptortoremove == descriptoritem.descriptoringac):
                #Tras la eliminación, actualizamos la lista de descriptorsitems.
                self._descriptorslist.remove(descriptoritem)
        
        #Refrescamos la vista.
        self._grid.Items.Refresh()
            
    def get_selected_descriptors(self):
        """
        Obtiene los descriptores de ensamblado que han sido
        seleccionados para ser actualizados.
        """
        descriptorstoupdate = []
        for descriptoritem in self._descriptorslist:
            if descriptoritem.update:
                descriptorstoupdate.append((descriptoritem.descriptorindir,
                descriptoritem.descriptoringac))
                
        return tuple(descriptorstoupdate)
    
    #Comprueba si un control WPF contiene errores de datos.
    def _isvalid(self, parent):
        if Validation.GetHasError(parent):
            return False
        
        child = None
        childrencount = VisualTreeHelper.GetChildrenCount(parent)
        i = 0
        while i < childrencount:
            child = VisualTreeHelper.GetChild(parent, i)
            if not self._isvalid(child):
                return False
            i += 1
        
        return True
        

class DescriptorItem(object):
    """
    Wrapper para mostrar un descriptor de ensamblado en el grid.
    """    
    def __init__(self, descriptorindir, descriptoringac, update):
        self.descriptorindir = descriptorindir
        self.descriptoringac = descriptoringac
        self.name = self.descriptorindir.name
        self.token = self.descriptorindir.token
        self.culture = self.descriptorindir.culture
        self.version = self.descriptorindir.version
        self._newdirective = self.descriptorindir.bindings[-1].interval
        self.update = update
        
    def __get_newdirective(self):
        return self._newdirective
    
    def __set_newdirective(self, directive):        
        newbindings = []
        newbinding = asmdesc.BindingDirective(directive, self.descriptorindir.version)
        newbindings.append(newbinding)
        self.descriptorindir.bindings = newbindings
        
    newdirective = property(fget=__get_newdirective, fset=__set_newdirective, doc="Directiva de enlace a aplicar")