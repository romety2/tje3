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
<title>${summary.productname} 階段作業摘要</title></head>

<body topmargin="12" leftmargin="12" rightmargin="12" bgcolor="#ffffff" marginheight="12" marginwidth="12">

  <#if (summary.totalinstallcount > 0)>
  <h2><a name="section-InstallationSummary"> ${summary.productname} 的安裝摘要</a></h2>
  </#if>
  <#if (summary.totalrepaircount > 0)>
  <h2><a name="section-InstallationSummary"> ${summary.productname} 的修復摘要</a></h2>
  </#if>
  <#if (summary.totaluninstallcount > 0)>
<h2><a name="section-InstallationSummary"> ${summary.productname} 的解除安裝摘要</a></h2>
  </#if>


  <hr>

<h4>可在下方找到 ${summary.productname} 階段作業的摘要。
<#if (summary.totalinstallcount > 0)>  <b>${summary.totalinstallcount} 個元件中有 ${summary.fullyinstalledcount} 個已完全安裝</b>. </#if>
<#if (summary.totalrepaircount > 0)>  <b>${summary.totalrepaircount} 個元件中有 ${summary.fullyrepairedcount} 個已完全修復</b>. </#if>
<#if (summary.totalconfigcount > 0)>  <b>${summary.totalconfigcount} 個元件中有 ${summary.fullyconfiguredcount} 個已完全配置</b>. </#if>
<#if (summary.totaluninstallcount > 0)>  <b>${summary.totaluninstallcount} 個元件中有 ${summary.fullyuninstalledcount} 個已完全移除</b>. </#if>
<#if (summary.totalunconfigcount > 0)>  <b>${summary.totalunconfigcount} 個元件中有 ${summary.fullyunconfiguredcount} 個已完全取消配置</b>. </#if>
若要 完成 任何部份安裝或移除，請按照下方針對每個元件的指示進行。  </a></h4>
<h4>${summary.introtext?default("")}</h4>
<p>
<i>階段作業 已完成: ${summary.date}</i>
</p>

<#if (summary.componentstoinstall?size > 0)>
<h3><a name="section-ComponentsToInstall">要安裝的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th></tr>
<#list summary.componentstoinstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyInstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstorepair?size > 0)>
<h3><a name="section-ComponentsToRepair">要修復的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th></tr>
<#list summary.componentstorepair as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyRepairedComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstouninstall?size > 0)>
<h3><a name="section-ComponentsToUninstall">要移除的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th></tr>
<#list summary.componentstouninstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyUninstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ComponentsToConfigure">要配置的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-ComponentsToUnConfigure">要取消配置的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.installedcomponents?size > 0)>
<h3><a name="section-CompletelyInstalledComponents"> 已完全安裝的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>記錄檔</th><th>接下來的步驟</th><th>文件與其他參照</th></tr>
<#list summary.installedcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">記錄檔</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.repairedcomponents?size > 0)>
<h3><a name="section-CompletelyRepairedComponents"> 已完全修復的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>記錄檔</th><th>接下來的步驟</th><th>文件與其他參照</th></tr>
<#list summary.repairedcomponents as component>
<tr>
  <td><a name="section-CompletelyRepairedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">記錄檔</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.uninstalledcomponents?size > 0)>
<h3><a name="section-CompletelyUninstalledComponents"> 已完全移除的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>記錄檔</th><th>接下來的步驟</th><th>文件與其他參照</th></tr>
<#list summary.uninstalledcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">記錄檔</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.failedcomponents?size > 0)>
<h3><a name="section-FailedComponents"> 失敗的元件</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>記錄檔</th><th>系統錯誤</th><th>產品錯誤</th><th>接下來的步驟</th><th>文件與其他參照</th></tr>
<#list summary.failedcomponents as component>
<tr>
  <td><a name="section-FailedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">記錄檔</a></td>
  <td>${component.install.errormsg.system?default("")}<p>${component.install.errormsg.other?default("None")}</td>
  <td>${component.install.errormsg.product?default("None")}</td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ConfigurationReport"> 配置報告</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th><th>記錄檔</th><th>系統錯誤</th><th>產品錯誤</th><th>接下來的步驟</th><th>文件與其他參照</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">記錄檔</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-UnConfigurationReport"> 取消配置報告</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>狀態</th><th>記錄檔</th><th>系統錯誤</th><th>產品錯誤</th><th>接下來的步驟</th><th>文件與其他參照</th></tr>
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
<h3><a name="section-NextStepsReport">接下來使用 ${summary.productname} 的步驟</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>接下來的步驟</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-NextStepsReport">接下來完成 ${summary.productname} 取消配置的步驟</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>組件</th><th>接下來的步驟</th></tr>
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
