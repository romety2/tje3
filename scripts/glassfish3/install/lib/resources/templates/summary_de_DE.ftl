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
<title>${summary.productname} Sitzungsübersicht</title></head>

<body topmargin="12" leftmargin="12" rightmargin="12" bgcolor="#ffffff" marginheight="12" marginwidth="12">

  <#if (summary.totalinstallcount > 0)>
  <h2><a name="section-InstallationSummary"> Installationsübersicht für ${summary.productname}</a></h2>
  </#if>
  <#if (summary.totalrepaircount > 0)>
  <h2><a name="section-InstallationSummary"> Behebungsübersicht für ${summary.productname}</a></h2>
  </#if>
  <#if (summary.totaluninstallcount > 0)>
<h2><a name="section-InstallationSummary"> Deinstallationsübersicht für ${summary.productname}</a></h2>
  </#if>


  <hr>

<h4>Eine Zusammenfassung Ihrer ${summary.productname}-Sitzung finden Sie weiter unten.
<#if (summary.totalinstallcount > 0)>  <b>${summary.fullyinstalledcount} von ${summary.totalinstallcount} Komponenten wurde vollständig installiert.</b>. </#if>
<#if (summary.totalrepaircount > 0)>  <b>${summary.fullyrepairedcount} von ${summary.totalrepaircount} Komponenten wurde vollständig repariert.</b>. </#if>
<#if (summary.totalconfigcount > 0)>  <b>${summary.fullyconfiguredcount} von ${summary.totalconfigcount} Komponenten wurden vollständig konfiguriert</b>. </#if>
<#if (summary.totaluninstallcount > 0)>  <b>${summary.fullyuninstalledcount} von ${summary.totaluninstallcount} Komponenten wurde vollständig entfernt.</b>. </#if>
<#if (summary.totalunconfigcount > 0)>  <b>${summary.fullyunconfiguredcount} von ${summary.totalunconfigcount} Komponenten wurden vollständig dekonfiguriert</b>. </#if>
Um alle Teilinstallationen oder Teildeinstallationen von jeder Komponente abzuschließen , führen Sie die folgenden Anweisungen aus.  </a></h4>
<h4>${summary.introtext?default("")}</h4>
<p>
<i>Sitzung Abgeschlossen: ${summary.date}</i>
</p>

<#if (summary.componentstoinstall?size > 0)>
<h3><a name="section-ComponentsToInstall">Zu installierende Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th></tr>
<#list summary.componentstoinstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyInstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstorepair?size > 0)>
<h3><a name="section-ComponentsToRepair">Zu reparierende Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th></tr>
<#list summary.componentstorepair as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyRepairedComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstouninstall?size > 0)>
<h3><a name="section-ComponentsToUninstall">Zu entfernende Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th></tr>
<#list summary.componentstouninstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyUninstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ComponentsToConfigure">Zu konfigurierende Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-ComponentsToUnConfigure">Zu dekonfigurierende Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.installedcomponents?size > 0)>
<h3><a name="section-CompletelyInstalledComponents"> Vollständig installierte Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Protokolldatei</th><th>Weitere Schritte</th><th>Dokumentation und andere Quellen</th></tr>
<#list summary.installedcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Protokolldatei</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.repairedcomponents?size > 0)>
<h3><a name="section-CompletelyRepairedComponents"> Vollständig reparierte Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Protokolldatei</th><th>Weitere Schritte</th><th>Dokumentation und andere Quellen</th></tr>
<#list summary.repairedcomponents as component>
<tr>
  <td><a name="section-CompletelyRepairedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Protokolldatei</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.uninstalledcomponents?size > 0)>
<h3><a name="section-CompletelyUninstalledComponents"> Vollständig entfernte Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Protokolldatei</th><th>Weitere Schritte</th><th>Dokumentation und andere Quellen</th></tr>
<#list summary.uninstalledcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Protokolldatei</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.failedcomponents?size > 0)>
<h3><a name="section-FailedComponents"> Fehlgeschlagene Komponenten</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Protokolldatei</th><th>Systemfehler</th><th>Produktfehler</th><th>Weitere Schritte</th><th>Dokumentation und andere Quellen</th></tr>
<#list summary.failedcomponents as component>
<tr>
  <td><a name="section-FailedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Protokolldatei</a></td>
  <td>${component.install.errormsg.system?default("")}<p>${component.install.errormsg.other?default("None")}</td>
  <td>${component.install.errormsg.product?default("None")}</td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ConfigurationReport"> Konfigurationsbericht</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th><th>Protokolldatei</th><th>Systemfehler</th><th>Produktfehler</th><th>Weitere Schritte</th><th>Dokumentation und andere Quellen</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">Protokolldatei</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-UnConfigurationReport"> Dekonfigurationsbericht</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Status</th><th>Protokolldatei</th><th>Systemfehler</th><th>Produktfehler</th><th>Weitere Schritte</th><th>Dokumentation und andere Quellen</th></tr>
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
<h3><a name="section-NextStepsReport">Weitere Schritte für die Verwendung von ${summary.productname}</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Weitere Schritte</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-NextStepsReport">Weitere Schritte zum Abschließen der Dekonfiguration von ${summary.productname}</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Komponente</th><th>Weitere Schritte</th></tr>
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
