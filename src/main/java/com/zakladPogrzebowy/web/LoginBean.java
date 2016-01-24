package com.zakladPogrzebowy.web;

import java.io.Serializable;

import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.faces.bean.SessionScoped;
import javax.faces.bean.ManagedBean;


@SessionScoped
@ManagedBean(name="loginBean")
public class LoginBean implements Serializable
{

	private static final long serialVersionUID = 1L;

	private static final String login = "login";
	private static final String haslo = "haslo";
	
	private String mojLogin;
	private String mojeHaslo;

	private boolean zalogowano = false;
	
	public String zaloguj()
	{
		if (mojLogin.equals(login) && mojeHaslo.equals(haslo))
		{
			zalogowano = true;
			return "/zp/home.xhtml?faces-redirect=true";
		}
		else
		{
			FacesMessage fm = new FacesMessage("Zły login i/lub hasło", "ERROR MSG");
			fm.setSeverity(FacesMessage.SEVERITY_ERROR);
			FacesContext.getCurrentInstance().addMessage(null, fm);
			return "login.xhtml";
		}
	}

	public String getMojLogin() {
		return mojLogin;
	}
	public void setMojLogin(String mojLogin) {
		this.mojLogin = mojLogin;
	}

	public String getMojeHaslo() {
		return mojeHaslo;
	}
	
	public void setMojeHaslo(String mojeHaslo){
		this.mojeHaslo = mojeHaslo;
	}

	public boolean getZalogowano() {
		return zalogowano;
	}
	
	public void setZalogowano(boolean zalogowano){
		this.zalogowano = zalogowano;
	}
	
}
