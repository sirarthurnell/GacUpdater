# -*- coding: latin-1 -*-

import os
import bisect
import asmdesc
import clr
clr.AddReference("System.Xml")
from System.Xml import (
	XmlDocument, XmlNodeList, XmlAttribute,
	XmlNode, XmlElement
)

class AssemblyExplorer(object):
    """Clase encargada de explorar un directorio en busca de ensamblados.
    """
    
    def __init__(self, pathtodir, pathtomachineconfig):
		self._pathtodir = pathtodir
		self._pathtomachineconfig = pathtomachineconfig
		self._descriptors = []
		self._names = []
		self._bindings = {}
        
    def __iter__(self):		
		return self._descriptors.__iter__()
		
    def __len__(self):
		return len(self._descriptors)
		
    def __getitem__(self, index):
		return self._descriptors[index]
		
    def __str__(self):
		return "Directorio cargado desde %s" % self._pathtodir
		
    def __repr__(self):
		return "AssemblyExplorer(r'%s', r'%s')" % (self._pathtodir, self._pathtomachineconfig)
	
    def load(self, onlydirs=False, progress=None):
		"""Carga los ensamblados de la GAC.
		
		progress es una función a la que llamar cada vez
		que se acaba de explorar un subdirectorio de la GAC.
		Dicha función acepta un parámetro que es el porcentaje
		de exploración de la GAC completado.
		
		"""		
				
		if len(self._descriptors) > 0:
			del self._descriptors
			del self._names
			self._descriptors = []
			self._names = []
			
		#Cargamos las directivas de enlace.
		self._loadbindings()
			
		#Exploramos la GAC cargando los descriptores de cada uno de sus ensamblados.
		currentassemblypath = ""
		currentdescriptor = None
		toplevelpaths = []
		toplevelpaths = os.listdir(self._pathtodir) if onlydirs else (self._pathtodir,)
		toplevelpathscount = len(toplevelpaths)
		toplevelpathselapsed = 0
		bindingdirective = None
		
		for toplevelpath in toplevelpaths:
			for dirpath, dirnames, filenames in os.walk(os.path.join(self._pathtodir, toplevelpath)):
				for filename in filenames:
					if filename.endswith(".dll"):
						currentassemblypath = os.path.join(dirpath, filename)
						currentdescriptor = self._create_descriptor(currentassemblypath)
						
						#Le asociamos al descriptor su directiva de enlace, si es que
						#la tiene.
						descriptorkey = currentdescriptor.name + "_" + currentdescriptor.token.lower()
						if self._bindings.has_key(descriptorkey):
							bindingdirective = self._bindings[descriptorkey]
							currentdescriptor.bindings = bindingdirective
						
						self._descriptors.append(currentdescriptor)
						
			if progress != None:
				toplevelpathselapsed += 1
				progress(toplevelpathselapsed / toplevelpathscount * 100)
	
		self._descriptors.sort()
		self._names = [currentdescriptor.name.lower() for currentdescriptor in self._descriptors]


    def index(self, descriptor):
		"""Obtiene el índice que ocupa un descriptor de ensamblado
		dentro del objeto Gac.
		
		"""
		
		i = bisect.bisect_left(self._descriptors, descriptor)
		if i != len(self._descriptors) and self._descriptors[i] == descriptor:
			return i
		else:
			return -1
			
    def find(self, name):
		"""Obtiene una lista de descriptores de ensamblado cuyo
		nombre coincide con el especificado.
		
		"""
		
		found = []
		lowername = name.lower()
		startpos = bisect.bisect_left(self._names, lowername)
		if startpos >= len(self._names):
			return []
		else:
			i = startpos
			while self._names[i] == lowername:
				found.append(self._descriptors[i])
				i += 1
			
			return found
			
	#Carga las directivas de enlace establecidas para los
	#ensamblados de la GAC.
    def _loadbindings(self):
		doc = XmlDocument()
		doc.Load(self._pathtomachineconfig)
		assemblybindingnode = doc.SelectSingleNode('/configuration/runtime//*[local-name()="assemblyBinding"]')
		dependentlist = assemblybindingnode.GetElementsByTagName("dependentAssembly")
		
		if len(self._bindings) > 0:
			del self._bindings
			self._bindings = {}
		
		identity = None
		bindingslist = None
		assemblyname = ""
		token = ""
		interval = ""
		target = ""
		currentdirective = None
		for dependentnode in dependentlist:
			assemblybindings = []
		
			identity = dependentnode.GetElementsByTagName("assemblyIdentity")[0]
			assemblyname = identity.GetAttribute("name")
			token = identity.GetAttribute("publicKeyToken").lower()
			
			bindingslist = dependentnode.GetElementsByTagName("bindingRedirect")
			for bindingnode in bindingslist:
				interval = bindingnode.GetAttribute("oldVersion")
				target = bindingnode.GetAttribute("newVersion")
				currentdirective = asmdesc.BindingDirective(interval, target)
				assemblybindings.append(currentdirective)
			
			self._bindings[assemblyname + "_" + token] = assemblybindings
	
	#Comprueba si la ruta especificada (por cadena o como descriptor)
	#pertenece a un ensamblado existente en disco. De ser así, devuelve
	#el descriptor al ensamblado.
    def _getdescriptor(self, assembly):
		if isinstance(assembly, asmdesc.AssemblyDescriptor):
			return assembly
		else:
			return asmdesc.AssemblyDescriptor(assembly)
        
    #Crea un descriptor de ensamblado a partir de la
	#ruta hacia el mismo.
    def _create_descriptor(self, path):
		#Creamos el ensamblado y lo devolvemos.
		descriptor = asmdesc.AssemblyDescriptor(path)
		return descriptor