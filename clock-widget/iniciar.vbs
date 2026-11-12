Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
CreateObject("Wscript.Shell").Run "pythonw.exe """ & folder & "\widdeks.py""", 0, False
