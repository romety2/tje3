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
<title>${summary.productname} Résumé de la session</title></head>

<body topmargin="12" leftmargin="12" rightmargin="12" bgcolor="#ffffff" marginheight="12" marginwidth="12">

  <#if (summary.totalinstallcount > 0)>
  <h2><a name="section-InstallationSummary"> Résumé de l'installation de ${summary.productname}</a></h2>
  </#if>
  <#if (summary.totalrepaircount > 0)>
  <h2><a name="section-InstallationSummary"> Résumé de la réparation de ${summary.productname}</a></h2>
  </#if>
  <#if (summary.totaluninstallcount > 0)>
<h2><a name="section-InstallationSummary"> Résumé de la désinstallation de ${summary.productname}</a></h2>
  </#if>


  <hr>

<h4>Le résumé de votre session ${summary.productname} est disponible ci-dessous.
<#if (summary.totalinstallcount > 0)>  <b>${summary.fullyinstalledcount} sur ${summary.totalinstallcount} composants ont été installés avec succès</b>. </#if>
<#if (summary.totalrepaircount > 0)>  <b>${summary.fullyrepairedcount} sur ${summary.totalrepaircount} composants ont été réparés avec succès</b>. </#if>
<#if (summary.totalconfigcount > 0)>  <b>${summary.fullyconfiguredcount} sur ${summary.totalconfigcount} composants sont complètement configurés</b>. </#if>
<#if (summary.totaluninstallcount > 0)>  <b>${summary.fullyuninstalledcount} sur ${summary.totaluninstallcount} composants ont été supprimés avec succès</b>. </#if>
<#if (summary.totalunconfigcount > 0)>  <b>La configuration de ${summary.fullyunconfiguredcount} sur ${summary.totalunconfigcount} composants a été annulée</b>. </#if>
Pour terminer des installations ou suppressions partielles, suivez les instructions ci-dessous pour chaque composant.  </a></h4>
<h4>${summary.introtext?default("")}</h4>
<p>
<i>Session Terminée : ${summary.date}</i>
</p>

<#if (summary.componentstoinstall?size > 0)>
<h3><a name="section-ComponentsToInstall">Composants à installer</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th></tr>
<#list summary.componentstoinstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyInstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstorepair?size > 0)>
<h3><a name="section-ComponentsToRepair">Composants à réparer</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th></tr>
<#list summary.componentstorepair as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyRepairedComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstouninstall?size > 0)>
<h3><a name="section-ComponentsToUninstall">Composants à supprimer</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th></tr>
<#list summary.componentstouninstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyUninstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ComponentsToConfigure">Composants à configurer</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-ComponentsToUnConfigure">Composants à déconfigurer</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.installedcomponents?size > 0)>
<h3><a name="section-CompletelyInstalledComponents"> Composants complètement installés</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>Fichier journal</th><th>Étapes suivantes</th><th>Documentation et autres références</th></tr>
<#list summary.installedcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Fichier journal</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.repairedcomponents?size > 0)>
<h3><a name="section-CompletelyRepairedComponents"> Composants complètement réparés</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>Fichier journal</th><th>Étapes suivantes</th><th>Documentation et autres références</th></tr>
<#list summary.repairedcomponents as component>
<tr>
  <td><a name="section-CompletelyRepairedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Fichier journal</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.uninstalledcomponents?size > 0)>
<h3><a name="section-CompletelyUninstalledComponents"> Composants complètement supprimés</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>Fichier journal</th><th>Étapes suivantes</th><th>Documentation et autres références</th></tr>
<#list summary.uninstalledcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Fichier journal</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.failedcomponents?size > 0)>
<h3><a name="section-FailedComponents"> Composants ayant échoué</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>Fichier journal</th><th>Erreur système</th><th>Erreur produit</th><th>Étapes suivantes</th><th>Documentation et autres références</th></tr>
<#list summary.failedcomponents as component>
<tr>
  <td><a name="section-FailedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">Fichier journal</a></td>
  <td>${component.install.errormsg.system?default("")}<p>${component.install.errormsg.other?default("None")}</td>
  <td>${component.install.errormsg.product?default("None")}</td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ConfigurationReport"> Rapport de configuration</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th><th>Fichier journal</th><th>Erreur système</th><th>Erreur produit</th><th>Étapes suivantes</th><th>Documentation et autres références</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">Fichier journal</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-UnConfigurationReport"> Rapport sur l'annulation de la configuration</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>État</th><th>Fichier journal</th><th>Erreur système</th><th>Erreur produit</th><th>Étapes suivantes</th><th>Documentation et autres références</th></tr>
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
<h3><a name="section-NextStepsReport">Étapes suivantes pour utiliser ${summary.productname}</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>Étapes suivantes</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-NextStepsReport">Prochaines étapes d'annulation de la configuration de ${summary.productname}</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>Composant</th><th>Étapes suivantes</th></tr>
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
