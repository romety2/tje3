package com.zakladPogrzebowy.web;

import java.io.Serializable;

import javax.enterprise.context.SessionScoped;
import javax.faces.model.ListDataModel;
import javax.inject.Inject;
import javax.inject.Named;

import com.zakladPogrzebowy.domena.Pogrzeb;
import com.zakladPogrzebowy.serwis.PogrzebManager;

@SessionScoped
@Named("pogrzebBean")
public class PogrzebBean implements Serializable {

	private static final long serialVersionUID = 1L;

	private Pogrzeb pogrzeb = new Pogrzeb();
	private ListDataModel<Pogrzeb> pogrzeby = new ListDataModel<Pogrzeb>();

	@Inject
	private PogrzebManager pm;

	public Pogrzeb getPogrzeb() {
		return pogrzeb;
	}
	public void setPogrzeb(Pogrzeb pogrzeb) {
		this.pogrzeb = pogrzeb;
	}
	
	public ListDataModel<Pogrzeb> getWszystkie() {
		pogrzeby.setWrappedData(pm.dajWszystkie());
		return pogrzeby;
	}

	
	public String dodaj() {
		pm.dodaj(pogrzeb);
		return "pogrzeby";
	}

	/*public String edytuj() {
		Pogrzeb p = pogrzeby.getRowData();
		pm.edytuj(p, pogrzeb.getTrumna(), pogrzeb.getData(),
				pogrzeb.getCena(), pogrzeb.getOpis());
		return null;
	}

	public String usun() {
		Pogrzeb p = pogrzeby.getRowData();
		pm.usun(p);
		return null;
	}*/
}

