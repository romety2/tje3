'DO NOT ALTER OR REMOVE COPYRIGHT NOTICE OR THIS HEADER.
'
'Copyright 2006, 2007 Sun Microsystems, Inc. All rights reserved.
'Use is subject to license terms.
'
'The contents of this file are subject to the terms of the Common Development
'and Distribution License("CDDL") (the "License"). You may not use this file
'except in compliance with the License.
'
'You can obtain a copy of the License at https://openinstaller.dev.java.net/license.html
'or http://openinstaller.dev.java.net/license.txt . See the License for the
'specific language governing permissions and limitations under the License.
'
'When distributing the Covered Code, include this CDDL Header Notice in each
'file and include the License file at http://openinstaller.dev.java.net/license.txt .
'If applicable, add the following below this CDDL Header, with the fields
'enclosed by brackets [] replaced by your own identifying information:
'"Portions Copyrighted [year] [name of copyright owner]"
'
'ident "@(#)%Name% %Revision% %Date% SMI"
'
'Sun Install engine wrapper script


'default supported jdk version

ENGINE_BASEDIR=trim(Replace(Wscript.scriptFullName, "bin\" & Wscript.scriptName, ""))


set wshell=WScript.CreateObject("WScript.Shell")
Set gWshEnv = wshell.Environment("SYSTEM")
CURRENTCLASSPATH=wShell.ExpandEnvironmentStrings("%CLASSPATH%")
gReturnValue = wshell.Run("regsvr32 /s scrrun.dll", 0 ,True)
set gFileSystem = CreateObject("Scripting.FileSystemObject")

'parsing the options and assigning the values to the corresponding variables

Set args = WScript.Arguments
argumentCounter=0
do while argumentCounter < args.Length
argName=args.Item(argumentCounter)
select case argName

case "-a"
 if argumentCounter + 1 < args.Length Then
   ANSWERFILE=ANSWERFILE & "," & trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-R"
 if argumentCounter + 1 < args.Length Then
   ALTROOT=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
   if Not gFileSystem.FolderExists(ALTROOT) Then
     WScript.Echo ALTROOT+" is not a valid alternate root"
     WScript.Quit(1)
   end if
 Else
   usage
 End if

case "-l"
 if argumentCounter + 1 < args.Length Then
   DEBUGLEVEL=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-n"
 if argumentCounter + 1 < args.Length Then
   DRYRUN=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-p"
 if argumentCounter + 1 < args.Length Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & trim(args.Item(argumentCounter+1)) & chr(34)
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-c"
 if argumentCounter + 1 < args.Length Then
   INSTALLPROPS=INSTALLPROPS & " -c " & chr(34) & trim(args.Item(argumentCounter+1)) & chr(34)
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-s"
 if argumentCounter + 1 < args.Length Then
   CONFIGSTATE=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-V"
 VERSIONFLAG=true
 argumentCounter=argumentCounter+1

case "-m"
 if argumentCounter + 1 < args.Length Then
   MEDIALOC=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-i"
 if argumentCounter + 1 < args.Length Then
   INSTALLABLES=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-j"
 if argumentCounter + 1 < args.Length Then
   JAVA_HOME=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
     if Not gFileSystem.FolderExists(JAVA_HOME) Then
	WScript.Echo JAVA_HOME+" must be the root directory of a valid JVM installation"
        WScript.Quit(1)
     end if
 Else
   usage
 End if

case "-J"
 if argumentCounter + 1 < args.Length Then
   JAVA_OPTIONS=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case "-C"
 if argumentCounter + 1 < args.Length Then
   ADDITIONALCLASSPATHS=trim(args.Item(argumentCounter+1))
   argumentCounter=argumentCounter+2
 Else
   usage
 End if

case Else
 usage

end select

Loop


if VERSIONFLAG <> "" Then
  Wscript.Echo "openInstaller Install Framework 0.9.6"
  Wscript.Echo "Copyright 2006, 2007 Sun Microsystems, Inc. All rights reserved."
  Wscript.Echo "Use is subject to license terms."
  Wscript.Echo
  Wscript.Echo "Version      : 0.9.6"
  Wscript.Echo "Release      : 1.1"
  Wscript.Echo "Build        : 65d65b03c578"
  Wscript.Echo "Assembled on : Mon, Sep 29, 2008 04:35 AM PDT"
  Wscript.Quit(0)
' If its a dry-run and answer file is specified
' Verify if it already exists. if so, inform the user to choose a different
' answer file and quit.
elseif  DRYRUN <> "" Then
  if gFileSystem.FileExists(DRYRUN) Then
    Wscript.Echo "Dry Run file "+DRYRUN+" already exists. Please choose a different one"
    WScript.Quit(1)
  end if
end if



INSTALLCONFIG_PROPERTIES=ENGINE_BASEDIR & "install-config.properties"

INSTENGINE=ENGINE_BASEDIR & "lib\engine.jar;" & ENGINE_BASEDIR & "lib\sims.jar"
INSTENGINE=INSTENGINE & ";" & ENGINE_BASEDIR & "lib\config.jar"

 theCP=ENGINE_BASEDIR & "lib\bootstrap.jar;" & ENGINE_BASEDIR & "lib\bindings.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\beanshell\bsh.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\swixml\swixml.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\swixml\j2h.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\swixml\ui.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\jdom\jdom.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\jaxb\jaxb-impl.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\jaxb\jaxb-jsr173_1.0_api.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\jaxb\jaxb-api.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\jaxb\activation.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\freemarker\freemarker.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\chaxml\chaxml.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\charva\charva.jar"
 theCP=theCP & ";" & ENGINE_BASEDIR & "lib\external\apache\commons-logging.jar"
 if ADDITIONALCLASSPATHS <> "" Then
   theCP=theCP & ";" & ADDITIONALCLASSPATHS
 end if
 if CURRENTCLASSPATH <> "" Then
   theCP=theCP & ";" & CURRENTCLASSPATH
 end if

INSTALLPROPS=INSTALLPROPS & " -p ""Platform-Plugin-Path=" & ENGINE_BASEDIR & "lib\platforms"""
INSTALLPROPS=INSTALLPROPS & " -p ""Provider-Path=" & ENGINE_BASEDIR & "lib\providers"""

 if DRYRUN <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & "Dry-Run-File=" & DRYRUN & chr(34)
 end if

 if CONFIGSTATE <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & "Config-State=" & CONFIGSTATE & chr(34)
 end if

 if ANSWERFILE <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & "Answer-Files=" & ANSWERFILE & chr(34)
 end if

 if ALTROOT <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & "Alternate-Root=" & ALTROOT & chr(34)
 end if

 if DEBUGLEVEL <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p Log-Level=" & DEBUGLEVEL
 end if

 if MEDIALOC <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & "Media-Location=" & MEDIALOC & chr(34)
 end if

 if INSTALLABLES <> "" Then
   INSTALLPROPS=INSTALLPROPS & " -p " & chr(34) & "Installable-Unit-Path=" & INSTALLABLES & chr(34)
 end if

'starting the installer
mycmd = chr(34) & JAVA_HOME & "\bin\javaw.exe" & chr(34) & " -classpath " & chr(34) & theCP & chr(34) & " " & JAVA_OPTIONS & " " & chr(34) & "-Dinstall.engine=" & INSTENGINE & chr(34) & " " & chr(34) & "-Dinstaller.resources.url=" & MEDIALOC & chr(34) & " " & chr(34) & "-Ddefault.resources.url=file:///" & ENGINE_BASEDIR & "lib\resources" & chr(34) & " " & chr(34) & "-Dsims.native-file-dir=" & ENGINE_BASEDIR & "lib" & chr(34) & " org.openinstaller.core.EngineBootstrap " & INSTALLPROPS
'Wscript.echo mycmd
set oExec=Wshell.exec(mycmd)
Do While oExec.Status = 0
     WScript.Sleep 500
Loop

set wshell = nothing

'-------------------------------------------------------------------------------
' usage only: define what parameters are available here
' input(s):  exitCode
'-------------------------------------------------------------------------------
Function usage

WScript.echo "Options:"
WScript.Quit(1)
End Function
