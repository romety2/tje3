'
' DO NOT ALTER OR REMOVE COPYRIGHT NOTICE OR THIS HEADER.
'
' Copyright 2006, 2007 Sun Microsystems, Inc. All rights reserved.
' Use is subject to license terms.
'
' The contents of this file are subject to the terms of the Common Development
' and Distribution License("CDDL") (the "License"). You may not use this file
' except in compliance with the License.
'
' You can obtain a copy of the License at https://openinstaller.dev.java.net/license.html
' or http://openinstaller.dev.java.net/license.txt . See the License for the
' specific language governing permissions and limitations under the License.
'
' When distributing the Covered Code, include this CDDL Header Notice in each
' file and include the License file at http://openinstaller.dev.java.net/license.txt .
' If applicable, add the following below this CDDL Header, with the fields
' enclosed by brackets [] replaced by your own identifying information:
' "Portions Copyrighted [year] [name of copyright owner]"
'
' ident "@(#)%Name% %Revision% %Date% SMI"
'
'

set gWshell = WScript.CreateObject("WScript.shell")

INSTALL_HOME=trim(Replace(Wscript.scriptFullName, "install\bin\"+Wscript.scriptName, ""))
'Wscript.Echo("Install Home ="&INSTALL_HOME)
ENGINE_DIR=INSTALL_HOME

'-------------------------------------------------------------------------------
' usage only: define what parameters are available here
' input(s):  exitCode
'-------------------------------------------------------------------------------
Function usage

WScript.Echo "Options:"
End Function

'-------------------------------------------------------------------------------
' perform actual operation for the script: install/uninstall
' input(s):  none
' output(s): instCode
'-------------------------------------------------------------------------------

Set args = WScript.Arguments
argumentCounter=0

Set wShell = CreateObject("WScript.Shell")
gReturnValue = wshell.Run("regsvr32 /s scrrun.dll", 0 ,True)
set gFileSystem = CreateObject("Scripting.FileSystemObject")

do while argumentCounter < args.Length
argName=args.Item(argumentCounter)

select case argName

case "-a"
  ANSWERFILE=trim(args.Item(argumentCounter+1))
  argumentCounter=argumentCounter+2

case "-l"
  LOGDIR=trim(args.Item(argumentCounter+1))
  argumentCounter=argumentCounter+2

	    if Not gFileSystem.FolderExists(LOGDIR) Or Not gFileSystem.FileExists(LOGDIR) Then
		WScript.Echo LOGDIR+" is not a directory or is not writable"
	    end if

case "-s"
 CONFIG_STATE_DIR=trim(args.Item(argumentCounter+1))
 argumentCounter=argumentCounter+2

case "-m"
  MEDIALOC=trim(args.Item(argumentCounter+1))
  argumentCounter=argumentCounter+2

case "-q"
 LOGLEVEL=WARNING

case "-v"
 LOGLEVEL=FINEST
case "-t"
 INSTALLPROPS=INSTALLPROPS + " -p Display-Mode=CUI"

case "-N"
  DRYRUN=trim(args.Item(argumentCounter+1))
  argumentCounter=argumentCounter+2

case "-j"
 JAVA_HOME=trim(args.Item(argumentCounter+1))
 argumentCounter=argumentCounter+2

	   if Not gFileSystem.FolderExists(JAVA_HOME) And Not gFileSystem.FileExists(JAVA_HOME) Then
		WScript.Echo JAVA_HOME+" must be the root directory of a valid JVM installation"
           end if

case "-J"
 JAVA_OPTIONS=trim(args.Item(argumentCounter+1))
 argumentCounter=argumentCounter+2

case "-C"
 ADDITIONALCLASSPATHS=trim(args.Item(argumentCounter+1))
 argumentCounter=argumentCounter+2

case "-p"
 INSTALLPROPS=INSTALLPROPS + " -p " + chr(34) + trim(args.Item(argumentCounter+1)) + chr(34)
  argumentCounter=argumentCounter+2

case "-h"
 usage

end select

Loop

if DRYRUN <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -n " + chr(34) + DRYRUN + chr(34)
end if

if CONFIG_STATE_DIR <> "" Then
  ENGINE_OPS=ENGINE_OPS + " -s " + chr(34) + CONFIG_STATE_DIR + chr(34)
end if

if MEDIALOC <> "" Then
  INSTALLPROPS=INSTALLPROPS + " -m " + chr(34) + MEDIALOC + chr(34)
end if

if ANSWERFILE <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -a " + chr(34) + ANSWERFILE + chr(34)
end if

if LOGLEVEL <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -l " + LOGLEVEL
end if


if LOGDIR <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -p Logs-Location=" + chr(34) + LOGDIR + chr(34)
end if

if JAVA_HOME <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -j " + chr(34) + JAVA_HOME + chr(34)
end if

if JAVA_OPTIONS <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -J " + chr(34) + JAVA_OPTIONS + chr(34)
end if

if ADDITIONALCLASSPATHS <> "" Then
    ENGINE_OPS=ENGINE_OPS + " -C " + chr(34) + ADDITIONALCLASSPATHS + chr(34)
end if

if INSTALLPROPS <> "" Then
    ENGINE_OPS=ENGINE_OPS+" "+INSTALLPROPS
end if

' adding the missing path install to the wrapper script

'wscript.echo("wscript //nologo """ & ENGINE_DIR + "install\bin\engine-wrapper.vbs""" + " " + ENGINE_OPS)
wshell.exec("wscript //nologo """ & ENGINE_DIR + "install\bin\engine-wrapper.vbs""" + " " + ENGINE_OPS)

