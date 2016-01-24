package com.zakladPogrzebowy.filtry;

import java.io.IOException;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.zakladPogrzebowy.web.LoginBean;

public class LoginFilter implements Filter
{
	public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException
	{
		LoginBean lb = (LoginBean)((HttpServletRequest)request).getSession().getAttribute("loginBean");
		
		if ((lb == null) || (!lb.getZalogowano()))
		{
			String strona = ((HttpServletRequest)request).getContextPath();
			((HttpServletResponse)response).sendRedirect(strona + "/login.jsf");
		}
		chain.doFilter(request, response);
	}

	public void init(FilterConfig config) throws ServletException
	{
	}

	public void destroy()
	{
	}	
}
