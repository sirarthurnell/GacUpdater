# -*- coding: latin-1 -*-

import os
import clr
clr.AddReference("Mono.Cecil")
from System import Version
from Mono.Cecil import (
	AssemblyDefinition, AssemblyNameDefinition	
)

def version_to_tuple(version):
	"""Comprueba que el n�mero de versi�n pasado como par�metro
	sea un n�mero de versi�n de ensamblado v�lido. De serlo
	devuelve una tupla con el n�mero de versi�n. De no ser un
	n�mero v�lido, devuelve una tupla vac�a.
	
	"""

	#Si se nos suministr� una cadena o lista,
	#los transformamos en una tupla.
	if isinstance(version, str):
		vsplitted = tuple(version.split("."))
	else:
		vsplitted = tuple(version)		
	
	versionresult = []	
	try:
		for element in vsplitted:
			versionresult.append(int(element))
	except ValueError:
		raise ValueError("Debe suministrar un enumerable o cadena con formato x.x.x.x donde x es un n�mero entero.")
		
	#Si todo ha ido bien, devolvemos la tupla con el n�mero
	#de versi�n.
	return tuple(versionresult)

def compareversions(version_a, version_b):
	"""Compara las versiones de dos ensamblados y devuelve
	si la primera es mayor que la segunda con un -1, si son
	iguales, con un 0, o si es la segunda mayor que la primera,
	con un 1.
	
	Los par�metros pueden ser una tupla o lista de enteros entre
	0 y 65535, o una cadena con el formato x.x.x.x siendo x un
	n�mero entero comprendido entre 0 y 65535.
	
	"""
	
	version_a_splitted = version_to_tuple(version_a)
	version_b_splitted = version_to_tuple(version_b)
	
	if len(version_a_splitted) > len(version_b_splitted):
		shorter = version_b_splitted
		longer = version_a_splitted
		factor = -1
	else:
		shorter = version_a_splitted
		longer = version_b_splitted
		factor = 1
		
	i = 0
	while i < len(shorter):
		if shorter[i] == longer[i]:
			pass
		else:
			return cmp(shorter[i], longer[i]) * factor
		i += 1
	else:
		if len(shorter) < len(longer):
			return factor
	
	return 0
	
class BindingDirective(object):
	"""Representa una directiva de enlace a aplicar a un
	ensamblado.
	
	"""
	
	def __init__(self, interval, target):
		"""El par�metro interval es el intervalo de versiones
		que comprende la directiva de enlace. Es una cadena con
		el formato x.x.x.x-x.x.x.x (donde x son n�meros enteros)
		
		El par�metro target es la versi�n que ser� devuelta.
		Es una cadena con el formato x.x.x.x (donde x son n�mero
		enteros)
		
		"""
		
		#Comprobamos que el intervalo de versiones es v�lido.
		self._validateinterval(interval)
		self._interval = interval
			
		#La versi�n de destino tambi�n tiene que ser v�lida.
		self._validatetarget(target)
		self._target = target
		
	def __str__(self):
		return "Interval=%s, Target=%s" % (self._interval, self._target)
		
	def __repr__(self):
		return "BindingDirective('%s','%s')" % (self._interval, self._target)
		
	def __getinterval(self):
		return self._interval
		
	def __setinterval(self, interval):
		self._interval = interval
		
	def __gettarget(self):
		return self._target
		
	def __settarget(self, target):
		self._target = target
	
	interval = property(fget=__getinterval, fset=__setinterval, doc="Intervalo de versiones")
	target = property(fget=__gettarget, fset=__settarget, doc="Versi�n de destino")
		
	#Valida si el n�mero de versi�n de destino es correcto.
	def _validatetarget(self, target):
		if not version_to_tuple(target):
			raise ValueError("La versi�n de destino no es un n�mero de versi�n v�lido.")
	
	#Valida si un intervalo de versiones tiene el formato
	#correcto.
	def _validateinterval(self, interval):
		if not interval:
			raise ValueError("Debe especificar un intervalo de versiones en la directiva de enlace.")
			
		intervalsplitted = interval.split("-")
		if len(intervalsplitted) < 2:
			raise ValueError("La directiva de enlace especificada no tiene el formato correcto.")
		else:
			minorversion = intervalsplitted[0]
			majorversion = intervalsplitted[1]
			if (not version_to_tuple(minorversion)
				or not version_to_tuple(majorversion)):
				raise ValueError("El intervalo de versiones especificado no es v�lido.")
	
class AssemblyDescriptor(object):
	"""Esta clase representa, de una forma ligera, a un
	ensamblado. Tan s�lo contiene una serie de atributos
	propios de un ensamblado, pero en ning�n caso contiene
	c�digo ejecutable por reflexi�n como la clase Assembly
	de .NET
	
	"""
	
	def __init__(self, path=None, name=None, token=None, culture=None, version=None):
		"""Si se especifica s�lo la ruta del ensamblado, se tratar� de obtener
		el resto de los par�metros mediante la lectura del ensamblado.
		
		Si adem�s de la ruta se suministran el resto de los par�metros, no se
		realizar� carga alguna.
		
		"""
	
		#Comprobamos que la ruta al ensamblado es v�lida.
		if (not os.path.exists(path) 
			or not path.endswith(".dll")):
			raise ValueError("La ruta al ensamblado ha de ser una ruta v�lida.")
	
		self._path = path
		self._bindings = []
	
		#Debe especificarse s�lo la ruta al ensamblado, o bien,
		#todos los par�metros (inclu�da la ruta al ensamblado).
		if path and (not name and not token and not culture and not version):
			#Obtener los dem�s par�metros cargando el ensamblado.
			definition = AssemblyDefinition.ReadAssembly(path)
			self._name = definition.Name.Name
			self._culture = definition.Name.Culture.lower() if definition.Name.Culture else "neutral" 
			self._token = "%02x%02x%02x%02x%02x%02x%02x%02x" % tuple([element for element in definition.Name.PublicKeyToken])
			self._token = self._token.lower()
			defversion = definition.Name.Version
			self._version = "%s.%s.%s.%s" % (defversion.Major, defversion.Minor, defversion.Build, defversion.Revision)
		elif path and name and token and culture and version:
			#Guardamos los par�mtros suministrados.			
			self._name = name
			self._token = token.lower()
			self._culture = culture.lower()
			self._version = version
		else:
			raise ValueError("Se debe rellenar s�lo la ruta al ensamblado, o bien, todos los par�metros.")
		
	def __eq__(self, other):
		if not isinstance(other, AssemblyDescriptor):
			return False
		else:			
			if (self._name.lower() == other._name.lower()
				and self._token == other._token
				and self._culture == other._culture
				and self._version == other._version):
				return True
			else:
				return False
				
	def __ne__(self, other):
		return not self.__eq__(other)
				
	def __gt__(self, other):
		myname = self._name.lower()
		othername = other._name.lower()
		if myname != othername:
			return myname > othername
		else:
			return compareversions(self._version, other._version) == -1
			
	def __ge__(self, other):
		myname = self._name.lower()
		othername = other._name.lower()
		if myname != othername:
			return myname >= othername
		else:
			result = compareversions(self._version, other._version)
			return result == -1 or result == 0
			
	def __lt__(self, other):
		myname = self._name.lower()
		othername = other._name.lower()
		if myname != othername:
			return myname < othername
		else:
			return compareversions(self._version, other._version) == 1
			
	def __le__(self, other):
		myname = self._name.lower()
		othername = other._name.lower()
		if myname != othername:
			return myname <= othername
		else:
			result = compareversions(self._version, other._version)
			return result == 1 or result == 0
		
	def __str__(self):
		return "%s, Version=%s, Culture=%s, PublicKeyToken=%s" % (self.name, self.version, self.culture, self.token)
		
	def __repr__(self):
		return "AssemblyDescriptor(r'%s', '%s', '%s', '%s', '%s')" % (self.path, self.name, self.token, self.culture, self.version)
	
	def __get_path(self):
		return self._path
	
	def __get_name(self):
		return self._name
		
	def __get_token(self):
		return self._token
		
	def __get_culture(self):
		return self._culture
		
	def __get_version(self):
		return self._version
		
	def __get_bindings(self):
		return self._bindings
		
	def __set_bindings(self, bindings):
		try:		
			self._bindings = list(bindings)
		except ValueError:
			raise ValueError("Debe especificar una lista o tupla de objetos BindingDirective.")
		
	#Creamos las propiedades p�blicas de s�lo lectura.
	path = property(fget=__get_path, doc="Ruta al ensamblado")
	name = property(fget=__get_name, doc="Nombre")
	token = property(fget=__get_token, doc="Token")
	culture = property(fget=__get_culture, doc="Cultura")
	version = property(fget=__get_version, doc="Versi�n")
	bindings = property(fget=__get_bindings, fset=__set_bindings, doc="Directivas de enlace")