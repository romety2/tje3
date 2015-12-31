package com.example.zakladPogrzebowy.web;

import java.io.Serializable;
import java.util.List;

import javax.enterprise.context.SessionScoped;
import javax.inject.Inject;
import javax.inject.Named;

import com.example.zakladPogrzebowy.domena.Pogrzeb;
import com.example.zakladPogrzebowy.domena.Trumna;
import com.example.zakladPogrzebowy.serwis.PogrzebManager;
import com.example.zakladPogrzebowy.serwis.TrumnaManager;

@SessionScoped
@Named("pogrzebBean")
public class SaleFormBean implements Serializable {

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
	
	public ListDataModel<Pogrzeb> getPogrzeby() {
		pogrzeby.setWrappedData(pm.dajWszystkie());
		return pogrzeby;
	}

	
	public String dodaj() {
		pm.dodaj(pogrzeb);
		return "Pogrzeby";
		//return null;
	}

	public String edytuj() {
		Pogrzeb p = p.getRowData();
		pm.edytuj(p);
		return null;
	}

	public String usun() {
		Pogrzeb p = p.getRowData();
		pm.usun(p);
		return null;
	}
}

