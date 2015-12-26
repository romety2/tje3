<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<#--

   DO NOT ALTER OR REMOVE COPYRIGHT NOTICE OR THIS HEADER.

   Copyright 2006, 2007 Sun Microsystems, Inc. All rights reserved.
   Use is subject to license terms.

   The contents of this file are subject to the terms of the Common Development
   and Distribution License("CDDL") (the "License"). You may not use this file
   except in compliance with the License.

   You can obtain a copy of the License at https://openinstaller.dev.java.net/license.html
   or http://openinstaller.dev.java.net/license.txt . See the License for the
   specific language governing permissions and limitations under the License.

   When distributing the Covered Code, include this CDDL Header Notice in each
   file and include the License file at http://openinstaller.dev.java.net/license.txt .
   If applicable, add the following below this CDDL Header, with the fields
   enclosed by brackets [] replaced by your own identifying information:
   "Portions Copyrighted [year] [name of copyright owner]"

   ident "@(#)%Name% %Revision% %Date% SMI"

   This is a FreeMarker template used to generate the detailed summary information after an install
   session is complete.
-->

<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>${summary.productname} Resumen de la sesión</title></head>

<body topmargin="12" leftmargin="12" rightmargin="12" bgcolor="#ffffff" marginheight="12" marginwidth="12">

  <#if (summary.totalinstallcount > 0)>
  <h2><a name="section-InstallationSummary"> Resumen de la instalación de ${summary.productname}</a></h2>
  </#if>
  <#if (summary.totalrepaircount > 0)>
  <h2><a name="section-InstallationSummary"> Resumen de la reparación de ${summary.productname}</a></h2>
  </#if>
  <#if (summary.totaluninstallcount > 0)>
<h2><a name="section-InstallationSummary"> Resumen de la desinstalación de ${summary.productname}</a></h2>
  </#if>


  <hr>

<h4>A continuación se muestra el resumen de la sesión de ${summary.productname}.
<#if (summary.totalinstallcount > 0)>  <b>Se han instalado completamente ${summary.fullyinstalledcount} de ${summary.totalinstallcount} componentes.</b>. </#if>
<#if (summary.totalrepaircount > 0)>  <b>Se han reparado completamente ${summary.fullyinstalledcount} de ${summary.totalinstallcount} componentes.</b>. </#if>
<#if (summary.totalconfigcount > 0)>  <b>${summary.fullyconfiguredcount} de ${summary.totalconfigcount} componentes se han configurado por completo</b>. </#if>
<#if (summary.totaluninstallcount > 0)>  <b>Se han eliminado completamente ${summary.fullyinstalledcount} de ${summary.totalinstallcount} componentes.</b>. </#if>
<#if (summary.totalunconfigcount > 0)>  <b>${summary.fullyunconfiguredcount} de ${summary.totalunconfigcount} componentes se han desconfigurado por completo</b>. </#if>
Para completar cualquier instalación o eliminación parcial, siga las instrucciones que aparecen a continuación para cada componente.  </a></h4>
<h4>${summary.introtext?default("")}</h4>
<p>
<i>Sesión Completado: ${summary.date}</i>
</p>

<#if (summary.componentstoinstall?size > 0)>
<h3><a name="section-ComponentsToInstall">Componentes que se van a instalar</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th></tr>
<#list summary.componentstoinstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyInstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstorepair?size > 0)>
<h3><a name="section-ComponentsToRepair">Componentes para reparar</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th></tr>
<#list summary.componentstorepair as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyRepairedComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstouninstall?size > 0)>
<h3><a name="section-ComponentsToUninstall">Componentes para eliminar</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th></tr>
<#list summary.componentstouninstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyUninstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ComponentsToConfigure">Componentes para configurar</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-ComponentsToUnConfigure">Componentes para desconfigurar</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.installedcomponents?size > 0)>
<h3><a name="section-CompletelyInstalledComponents"> Componentes instalados por completo</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Archivo de registro</th><th>Pasos siguientes</th><th>Documentación y otras referencias</th></tr>
<#list summary.installedcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Archivo de registro</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.repairedcomponents?size > 0)>
<h3><a name="section-CompletelyRepairedComponents"> Componentes reparados por completo</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Archivo de registro</th><th>Pasos siguientes</th><th>Documentación y otras referencias</th></tr>
<#list summary.repairedcomponents as component>
<tr>
  <td><a name="section-CompletelyRepairedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Archivo de registro</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.uninstalledcomponents?size > 0)>
<h3><a name="section-CompletelyUninstalledComponents"> Componentes eliminados por completo</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Archivo de registro</th><th>Pasos siguientes</th><th>Documentación y otras referencias</th></tr>
<#list summary.uninstalledcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Archivo de registro</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.failedcomponents?size > 0)>
<h3><a name="section-FailedComponents"> Componentes no satisfactorios</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Archivo de registro</th><th>Error del sistema</th><th>Error del producto</th><th>Pasos siguientes</th><th>Documentación y otras referencias</th></tr>
<#list summary.failedcomponents as component>
<tr>
  <td><a name="section-FailedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Archivo de registro</a></td>
  <td>${component.install.errormsg.system?default("")}<p>${component.install.errormsg.other?default("None")}</td>
  <td>${component.install.errormsg.product?default("None")}</td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ConfigurationReport"> Informe de configuración</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th><th>Archivo de registro</th><th>Error del sistema</th><th>Error del producto</th><th>Pasos siguientes</th><th>Documentación y otras referencias</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">Archivo de registro</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-UnConfigurationReport"> Informe de desconfiguración</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Estado</th><th>Archivo de registro</th><th>Error del sistema</th><th>Error del producto</th><th>Pasos siguientes</th><th>Documentación y otras referencias</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
  <td><a name="section-UnConfiguration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">Log File</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-NextStepsReport">Pasos siguientes para usar ${summary.productname}</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Pasos siguientes</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-NextStepsReport">Pasos siguientes para completar la desconfiguración de ${summary.productname}</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Componente</th><th>Pasos siguientes</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<hr>

<div class="footer">

</div>


<br>


</body></html>
