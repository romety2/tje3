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
<title>${summary.productname} セッションの概要</title></head>

<body topmargin="12" leftmargin="12" rightmargin="12" bgcolor="#ffffff" marginheight="12" marginwidth="12">

  <#if (summary.totalinstallcount > 0)>
  <h2><a name="section-InstallationSummary"> ${summary.productname} のインストール概要</a></h2>
  </#if>
  <#if (summary.totalrepaircount > 0)>
  <h2><a name="section-InstallationSummary"> ${summary.productname} の修復概要</a></h2>
  </#if>
  <#if (summary.totaluninstallcount > 0)>
<h2><a name="section-InstallationSummary"> ${summary.productname} のアンインストール概要</a></h2>
  </#if>


  <hr>

<h4>${summary.productname} セッションの概要は下記で参照できます。
<#if (summary.totalinstallcount > 0)>  <b>${summary.totalinstallcount} 個中 ${summary.fullyinstalledcount} 個のコンポーネントが完全にインストールされました</b>. </#if>
<#if (summary.totalrepaircount > 0)>  <b>${summary.totalrepaircount} 個中 ${summary.fullyrepairedcount} 個のコンポーネントが完全に修復されました</b>. </#if>
<#if (summary.totalconfigcount > 0)>  <b>${summary.totalconfigcount} 個中 ${summary.fullyconfiguredcount} 個のコンポーネントが完全に設定されました</b>. </#if>
<#if (summary.totaluninstallcount > 0)>  <b>${summary.totaluninstallcount} 個中 ${summary.fullyuninstalledcount} 個のコンポーネントが完全に削除されました</b>. </#if>
<#if (summary.totalunconfigcount > 0)>  <b>${summary.totalunconfigcount} 個中 ${summary.fullyunconfiguredcount} 個のコンポーネントが完全に設定解除されました</b>. </#if>
To 完了 不完全なインストールまたは削除を完了するには、各コンポーネントに対して次の手順に従います。  </a></h4>
<h4>${summary.introtext?default("")}</h4>
<p>
<i>セッション 完了: ${summary.date}</i>
</p>

<#if (summary.componentstoinstall?size > 0)>
<h3><a name="section-ComponentsToInstall">インストールするコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th></tr>
<#list summary.componentstoinstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyInstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstorepair?size > 0)>
<h3><a name="section-ComponentsToRepair">修復するコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th></tr>
<#list summary.componentstorepair as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyRepairedComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstouninstall?size > 0)>
<h3><a name="section-ComponentsToUninstall">削除するコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th></tr>
<#list summary.componentstouninstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyUninstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ComponentsToConfigure">設定するコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-ComponentsToUnConfigure">設定解除するコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.installedcomponents?size > 0)>
<h3><a name="section-CompletelyInstalledComponents"> 完全にインストールされたコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>ログファイル</th><th>次の手順</th><th>マニュアルとその他の参考資料</th></tr>
<#list summary.installedcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">ログファイル</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.repairedcomponents?size > 0)>
<h3><a name="section-CompletelyRepairedComponents"> 完全に修復されたコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>ログファイル</th><th>次の手順</th><th>マニュアルとその他の参考資料</th></tr>
<#list summary.repairedcomponents as component>
<tr>
  <td><a name="section-CompletelyRepairedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">ログファイル</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.uninstalledcomponents?size > 0)>
<h3><a name="section-CompletelyUninstalledComponents"> 完全に削除されたコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>ログファイル</th><th>次の手順</th><th>マニュアルとその他の参考資料</th></tr>
<#list summary.uninstalledcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">ログファイル</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.failedcomponents?size > 0)>
<h3><a name="section-FailedComponents"> 失敗したコンポーネント</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>ログファイル</th><th>システムエラー</th><th>製品エラー</th><th>次の手順</th><th>マニュアルとその他の参考資料</th></tr>
<#list summary.failedcomponents as component>
<tr>
  <td><a name="section-FailedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">ログファイル</a></td>
  <td>${component.install.errormsg.system?default("")}<p>${component.install.errormsg.other?default("None")}</td>
  <td>${component.install.errormsg.product?default("None")}</td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ConfigurationReport"> 設定レポート</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th><th>ログファイル </th><th>システムエラー</th><th>製品エラー</th><th>次の手順</th><th>マニュアルとその他の参考資料</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">ログファイル</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-UnConfigurationReport"> 設定解除レポート</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>状況</th><th>ログファイル</th><th>システムエラー</th><th>製品エラー</th><th>次の手順</th><th>マニュアルとその他の参考資料</th></tr>
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
<h3><a name="section-NextStepsReport">${summary.productname} を使用するための次の手順</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>次の手順</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-NextStepsReport">${summary.productname} の設定解除を完了するための次の手順</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>コンポーネント</th><th>次の手順</th></tr>
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
