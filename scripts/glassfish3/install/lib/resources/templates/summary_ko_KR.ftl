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
<title>${summary.productname} 세션 요약</title></head>

<body topmargin="12" leftmargin="12" rightmargin="12" bgcolor="#ffffff" marginheight="12" marginwidth="12">

  <#if (summary.totalinstallcount > 0)>
  <h2><a name="section-InstallationSummary"> ${summary.productname}에 대한 설치 요약</a></h2>
  </#if>
  <#if (summary.totalrepaircount > 0)>
  <h2><a name="section-InstallationSummary"> ${summary.productname}에 대한 복구 요약</a></h2>
  </#if>
  <#if (summary.totaluninstallcount > 0)>
<h2><a name="section-InstallationSummary"> ${summary.productname}에 대한 제거 요약</a></h2>
  </#if>


  <hr>

<h4>${summary.productname} 세션의 요약 정보는 아래에 나와 있습니다.
<#if (summary.totalinstallcount > 0)>  <b>${summary.totalinstallcount}의 ${summary.fullyinstalledcount} 구성 요소 설치 완료</b>. </#if>
<#if (summary.totalrepaircount > 0)>  <b>${summary.totalrepaircount}의 ${summary.fullyrepairedcount} 구성 요소 복구 완료</b>. </#if>
<#if (summary.totalconfigcount > 0)>  <b>${summary.totalconfigcount}개 구성 요소 중 ${summary.fullyconfiguredcount}개 구성 완료</b>. </#if>
<#if (summary.totaluninstallcount > 0)>  <b>${summary.totaluninstallcount}의 ${summary.fullyuninstalledcount} 구성 요소 제거 완료</b>. </#if>
<#if (summary.totalunconfigcount > 0)>  <b>${summary.totalunconfigcount}개 구성 요소 중 ${summary.fullyunconfiguredcount}개 구성 해제 완료</b>. </#if>
부분적으로 설치 또는 제거하려면 각 구성 요소에 대해 아래의 지침을 따라야 합니다.  </a></h4>
<h4>${summary.introtext?default("")}</h4>
<p>
<i>세션 완료됨: ${summary.date}</i>
</p>

<#if (summary.componentstoinstall?size > 0)>
<h3><a name="section-ComponentsToInstall">설치할 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th></tr>
<#list summary.componentstoinstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyInstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstorepair?size > 0)>
<h3><a name="section-ComponentsToRepair">복구할 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th></tr>
<#list summary.componentstorepair as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyRepairedComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstouninstall?size > 0)>
<h3><a name="section-ComponentsToUninstall">제거할 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th></tr>
<#list summary.componentstouninstall as component>
<tr>
<td><a href="#section-<#if component.install.status>CompletelyUninstalledComponents<#else>FailedComponents</#if>-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.install.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ComponentsToConfigure">구성할 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-ComponentsToUnConfigure">구성 해제할 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th></tr>
<#list summary.componentstounconfigure as component>
<tr>
<td><a href="#section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.installedcomponents?size > 0)>
<h3><a name="section-CompletelyInstalledComponents"> 설치 완료된 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>로그 파일</th><th>다음 단계</th><th>설명서 및 기타 참조 자료</th></tr>
<#list summary.installedcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">로그 파일</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.repairedcomponents?size > 0)>
<h3><a name="section-CompletelyRepairedComponents"> 복구 완료된 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>로그 파일</th><th>다음 단계</th><th>설명서 및 기타 참조 자료</th></tr>
<#list summary.repairedcomponents as component>
<tr>
  <td><a name="section-CompletelyRepairedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">로그 파일</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.uninstalledcomponents?size > 0)>
<h3><a name="section-CompletelyUninstalledComponents"> 제거 완료된 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>로그 파일</th><th>다음 단계</th><th>설명서 및 기타 참조 자료</th></tr>
<#list summary.uninstalledcomponents as component>
<tr>
  <td><a name="section-CompletelyInstalledComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">로그 파일</a></td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.failedcomponents?size > 0)>
<h3><a name="section-FailedComponents"> 실패한 구성 요소</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>로그 파일</th><th>시스템 오류</th><th>제품 오류</th><th>다음 단계</th><th>설명서 및 기타 참조 자료</th></tr>
<#list summary.failedcomponents as component>
<tr>
  <td><a name="section-FailedComponents-${component.name}">${component.name}</a></td>
  <td><a class="external" href="${component.log_url?default("None")}">로그 파일</a></td>
  <td>${component.install.errormsg.system?default("")}<p>${component.install.errormsg.other?default("None")}</td>
  <td>${component.install.errormsg.product?default("None")}</td>
  <td>${component.install.nextsteps?default("None")}</td>
  <td>${component.install.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstoconfigure?size > 0)>
<h3><a name="section-ConfigurationReport"> 구성 보고서</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th><th>로그 파일</th><th>시스템 오류</th><th>제품 오류</th><th>다음 단계</th><th>설명서 및 기타 참조 자료</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-Configuration-${component.name}">${component.name}</a></td>
<td><#if !component.install.status><font color="red"></#if>${component.config.statusMsg}<#if !component.install.status></font></#if></td>
  <td><a class="external" href="${component.log_url?default("None")}">로그 파일</a></td>
  <td>${component.config.errormsg.system?default("")}<p>${component.config.errormsg.other?default("None")}</td>
  <td>${component.config.errormsg.product?default("None")}</td>
  <td>${component.config.nextsteps?default("None")}</td>
  <td>${component.config.docreference?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-UnConfigurationReport"> 구성 해제 보고서</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>상태</th><th>로그 파일</th><th>시스템 오류</th><th>제품 오류</th><th>다음 단계</th><th>설명서 및 기타 참조 자료</th></tr>
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
<h3><a name="section-NextStepsReport">${summary.productname} 사용을 위한 다음 단계</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>다음 단계</th></tr>
<#list summary.componentstoconfigure as component>
<tr>
  <td><a name="section-NextSteps-${component.name}">${component.name}</a></td>
  <td>${component.config.nextsteps?default("None")}</td>
</tr>
</#list>
</tbody></table>
</#if>

<#if (summary.componentstounconfigure?size > 0)>
<h3><a name="section-NextStepsReport">${summary.productname}의 구성 해제를 완료하기 위한 다음 단계</a></h3>
<table class="wikitable" border="1">
<tbody><tr><th>구성 요소</th><th>다음 단계</th></tr>
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
