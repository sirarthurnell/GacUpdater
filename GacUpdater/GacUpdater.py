# -*- coding: latin-1 -*-

import wpf
import gacdesc
import gridcontroller
import commands
from gacdesc import gac, asmexp, asmdesc
from System.Windows import Application, Window
from System.Windows.Threading import Dispatcher, DispatcherPriority
import clr
clr.AddReference("Ironpython")
from IronPython.Compiler import CallTarget0

class MyWindow(Window):
	def __init__(self):
		wpf.LoadComponent(self, 'GacUpdater.xaml')
		self._gac = gac.Gac(r"c:\windows\assembly\gac_msil", r"C:\WINDOWS\Microsoft.NET\Framework\v2.0.50727\CONFIG\machine.config")
		self._asmexplorer = asmexp.AssemblyExplorer(r"C:\Archivos de programa\Archivos comunes\Mityc\Sigetel\Assemblies\Frmwk2", r"C:\WINDOWS\Microsoft.NET\Framework\v2.0.50727\CONFIG\machine.config")
		self._gridcontroller = gridcontroller.GridController(self.grid)
		self._createcommands()
	
	def btnExplore_Click(self, sender, e):
		self._explorecmd.execute()
		
	def btnSelectAll_Click(self, sender, e):
		self._selectallcmd.execute()
		
	def btnSelectNone_Click(self, sender, e):
		self._selectnonecmd.execute()
		
	def btnApplyChanges_Click(self, sender, e):
		self._updatecmd.execute()
		
	#Crea los comandos de la aplicación.
	def _createcommands(self):
		self._explorecmd = commands.Explore(self._gac, self._asmexplorer, self._gridcontroller, self._infowithdoevents)
		self._selectallcmd = commands.SelectAll(self._gridcontroller)
		self._selectnonecmd = commands.SelectNone(self._gridcontroller)
		self._updatecmd = commands.Update(self, self._gac, self._gridcontroller, self._infowithdoevents)
		
	#Muestra un mensaje en la barra de estado.      
	def _infowithdoevents(self, message):
		#Función de retrollamada.
		def setmessage():
			self.txtStatus.Text = message
			
		#La siguiente línea es necesaria para sustituir en WPF la funcionalidad
		#que daba en Windows.Forms el método DoEvents. En otras palabras, esto
		#se asegura de que se vayan mostrando los mensajes conforme se producen.
		Dispatcher.CurrentDispatcher.Invoke(DispatcherPriority.Background, CallTarget0(setmessage))

#Punto de entrada.
if __name__ == '__main__':
	Application().Run(MyWindow())
