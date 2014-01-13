# -*- coding: latin-1 -*-

import os
import bisect
import asmdesc
import asmexp
import clr
clr.AddReference("System.Xml")
from System.Xml import (
	XmlDocument, XmlNodeList, XmlAttribute,
	XmlNode, XmlElement
)

class Gac(asmexp.AssemblyExplorer):
	"""Clase encargada de representar la GAC del sistema y
	encargada de registrar y desregistrar ensamblados en la
	misma.	
	"""
	
	def __init__(self, pathtogac, pathtomachineconfig, pathtogacutil=None):
		asmexp.AssemblyExplorer.__init__(self, pathtogac, pathtomachineconfig)
		self._pathtogacutil = pathtogacutil
		
	def __str__(self):
		return "Gac cargada desde %s" % self._pathtodir
	
	def __repr__(self):
		return "Gac(r'%s', r'%s')" % (self._pathtodir, self._pathtomachineconfig)
	
	def load(self, progress=None):
		asmexp.AssemblyExplorer.load(self, True, progress)

	def register(self, assembly, callback=None):
		"""Registra en la Gac un ensamblado representado por su descriptor
		o la ruta hacia el mismo.
		
		El parámetro assembly es una ruta hacia un ensamblado o un descriptor
		del mismo. Dicho parámetro puede ser un enumerable de de rutas o descriptores
		a desinstalar.
		
		El parámetro callback es una función a la que llamar cada vez que se
		instala un ensamblado. La función acepta como parámetro el descriptor
		del ensamblado que se acaba de instalar.
		
		"""
		
		if not hasattr(assembly, "__iter__"):
			try:
				
				assembliestoinstall = (assembly,)
			except ValueError:
				raise ValueError("Debe especificar un enumerable de rutas o descriptores de ensamblado.")
		else:
			assembliestoinstall = assembly
		
		#Por cada uno de los ensamblados a instalar.
		for assemblytoinstall in assembliestoinstall:
			#Obtenemos el descriptor del ensamblado, si nos
			#han pasado una ruta.
			descriptor = self._getdescriptor(assemblytoinstall)
			
			#Si el ensamblado existía en la GAC, lanzamos
			#una excepción.
			if self.index(descriptor) >= 0:
				raise ValueError("El ensamblado que está tratando de registrar ya se encuentra en la GAC.")
			
			#Ejecutamos el registro del ensamblado.
			gacutil = self._resolve_gacutil_path(True)
			command = gacutil + " /i " +  "\"" + descriptor.path + "\"" + " /silent"
			if os.system(command) <> 0:
				raise OSError("gacutil no ha podido registrar el ensamblado %s. ¿Especificó correctamente la ruta a gacutil.exe?" % descriptor.name)

			#Añadimos el ensamblado a la lista de ensamblados y el
			#nombre a la lista de nombres.
			bisect.insort(self._descriptors, descriptor)
			self._names.insert(self.index(descriptor), descriptor.name.lower())

			#Llamamos a la función de retrollamada pasándole el
			#descriptor de ensamblado que se acaba de añadir
			#a la GAC.
			if callback != None:
				callback(descriptor)			
		
	def unregister(self, assembly, callback=None):
		"""Desregistra de la Gac un ensamblado representado por su descriptor
		o la ruta hacia el mismo.
		
		El parámetro assembly es una ruta hacia un ensamblado o un descriptor
		del mismo. Dicho parámetro puede ser un enumerable de de rutas o descriptores
		a desinstalar.
		
		El parámetro callback es una función a la que llamar cada vez que se
		desinstala un ensamblado. La función acepta como parámetro el descriptor
		del ensamblado que se acaba de desinstalar.
		
		El o los ensamblados deben existir en la GAC antes de ser desinstalados.
		"""
		
		if not hasattr(assembly, "__iter__"):
			try:
				
				assembliestouninstall = (assembly,)
			except ValueError:
				raise ValueError("Debe especificar un enumerable de rutas o descriptores de ensamblado.")
		else:
			assembliestouninstall = assembly
			
		#Por cada uno de los ensamblados a desinstalar.
		for assemblytouninstall in assembliestouninstall:
			#Obtenemos el descriptor del ensamblado, si nos
			#han pasado una ruta.
			descriptor = self._getdescriptor(assemblytouninstall)
		
			#Si el ensamblado no existía en la GAC, lanzamos
			#una excepción.
			index = self.index(descriptor)
			if index < 0:
				raise ValueError("El ensamblado que está tratando de desrregistrar no se encuentra en la GAC.")
						
			#Ejecutamos el desregistro del ensamblado.
			gacutil = self._resolve_gacutil_path(False)		
			command = gacutil + " /u " + "\"" + descriptor.name + "\"" + " /silent"
			if os.system(command) <> 0:
				raise OSError("gacutil no ha podido desrregistrar el ensamblado %s. ¿Especificó correctamente la ruta a gacutil.exe?" % descriptor.name)
			
			#Eliminamos el ensamblado de la lista de ensamblados
			#y de la lista de nombres.
			del self._descriptors[index]
			del self._names[index]
			
			#Llamamos a la función de retrollamada pasándole el
			#descriptor de ensamblado que se acaba de eliminar
			#de la GAC.
			if callback != None:
				callback(descriptor)
		
	def updatebindings(self, descriptors):
		"""Actualiza la directiva de enlace en el archivo
		machine.config especificado.
		
		El parámetro descriptors puede ser un descriptor de ensamblado
		o un enumerable de ellos.
		"""
		
		#Los descriptores a actualizar no pueden ser nulos, ni estar vacíos.
		if not descriptors:
			raise ValueError("Debe especificar un descriptor o una colección de descriptores.")
		
		#Si se nos ha pasado una enumerable, entonces hacemos
		#esto por cada uno de los descriptores que haya en el
		#enumerable.
		descriptors_to_update = None		
		if not hasattr(descriptors, "__iter__"):
			try:
				
				descriptors_to_update = (descriptors,)
			except ValueError:
				raise ValueError("El parámetro debe ser un descriptor o un enumerable de descriptores.")
		else:
			descriptors_to_update = descriptors
		
		doc = XmlDocument()
		doc.Load(self._pathtomachineconfig)
		assemblybindingnode = doc.SelectSingleNode('/configuration/runtime//*[local-name()="assemblyBinding"]')
		dependentlist = assemblybindingnode.GetElementsByTagName("dependentAssembly")
	
		for descriptor in descriptors_to_update:		
			#Recuperamos el nodo de directiva de enlace
			#del elemento que queremos actualizar.
			dependent_node_to_edit = None
			for dependentnode in dependentlist:
				identitynode = dependentnode.GetElementsByTagName("assemblyIdentity")[0]
				assemblyname = identitynode.GetAttribute("name")
				token = identitynode.GetAttribute("publicKeyToken").lower()
							
				if (assemblyname == descriptor.name 
					and token == descriptor.token.lower()):
					dependent_node_to_edit = dependentnode
					break
					
			#Si hemos encontrado el nodo, lo eliminamos.
			if dependent_node_to_edit != None:
				assemblybindingnode.RemoveChild(dependent_node_to_edit)
			
			#Si el descriptor indica que no existen directivas
			#de enlace a aplicar al ensamblado, no hacemos nada
			#pero si sí que hay, creamos un nuevo nodo
			#dependentAssembly con la información del descriptor.
			if descriptor.bindings:
				dependentnode = doc.CreateElement("dependentAssembly")
				assemblybindingnode.AppendChild(dependentnode)
				identitynode = doc.CreateElement("assemblyIdentity")
				nameattribute = doc.CreateAttribute("name")
				nameattribute.Value = descriptor.name
				identitynode.Attributes.Append(nameattribute)
				tokenattribute = doc.CreateAttribute("publicKeyToken")
				tokenattribute.Value = descriptor.token
				identitynode.Attributes.Append(tokenattribute)
				dependentnode.AppendChild(identitynode)
				
				for binding in descriptor.bindings:
					bindingnode = doc.CreateElement("bindingRedirect")
					oldversionattribute = doc.CreateAttribute("oldVersion")
					oldversionattribute.Value = binding.interval
					bindingnode.Attributes.Append(oldversionattribute)
					newversionattribute = doc.CreateAttribute("newVersion")
					newversionattribute.Value = binding.target
					bindingnode.Attributes.Append(newversionattribute)
					dependentnode.AppendChild(bindingnode)
	
		#Guardamos los cambios en el archivo machine.config.
		doc.Save(self._pathtomachineconfig)
	
	#Resuelve la ruta hacia la utilidad de registro de ensamblados
	#del framework.
	def _resolve_gacutil_path(self, forRegister):
		#Si se nos especificó la ruta a la gacutil, usamos esa.
		if self._pathtogacutil:
			return self._pathtogacutil
		else:
			#Si no se especificó, comprobamos el uso que se
			#va a hacer del framework.
			pathtogacutil = ""
			if forRegister:
				pathtogacutil = self._resolve_gacutil_path_for_fwk("2")
			else:
				pathtogacutil = self._resolve_gacutil_path_for_fwk("4")
			return pathtogacutil
		
	#Resuelve la ruta hacia la utilidad de registro de ensamblados
	#de la versión del framework indicada.
	def _resolve_gacutil_path_for_fwk(self, version):
		parentdir = os.path.dirname(os.path.realpath(__file__))
		parentdir = os.path.dirname(parentdir)
		pathtogacutil = os.path.join(parentdir, os.path.join(r"gacutil_fwk" + version, r"gacutil.exe"))
		return pathtogacutil

	#Crea un descriptor de ensamblado a partir de la
	#ruta hacia el mismo.
	def _create_descriptor(self, path):
		#Del nombre del directorio donde se encuentra el ensamblado,
		#obtenemos su versión, cultura y token.
		dir_assembly_name, assembly_attributes = os.path.split(os.path.dirname(path))
		parts = assembly_attributes.split("_")
		version, culture, token = parts[0], parts[1], parts[2]
		if not culture:
			culture = "neutral"
		
		#El nombre del ensamblado lo obtenemos del nombre del
		#directorio que contiene el directorio que contiene el
		#ensamblado.
		name = os.path.basename(dir_assembly_name)
		
		#Creamos el ensamblado y lo devolvemos.
		descriptor = asmdesc.AssemblyDescriptor(path, name, token, culture, version)
		return descriptor