package com.zakladPogrzebowy.web;

import java.io.Serializable;

import javax.enterprise.context.SessionScoped;
import javax.faces.model.ListDataModel;
import javax.inject.Inject;
import javax.inject.Named;

import com.zakladPogrzebowy.domena.Trumna;
import com.zakladPogrzebowy.serwis.TrumnaManager;

@SessionScoped
@Named("trumnaBean")
public class TrumnaBean implements Serializable {

	private static final long serialVersionUID = 1L;

	private Trumna trumna  = new Trumna();
	private ListDataModel<Trumna> trumny = new ListDataModel<Trumna>();


	@Inject
	private TrumnaManager tm;

	public Trumna getTrumna() {
		return trumna;
	}
	
	public void setTrumna(Trumna trumna) {
		this.trumna = trumna;
	}
	
	public ListDataModel<Trumna> getWszystkie() {
		trumny.setWrappedData(tm.dajWszystkie());
		return trumny;
	}
	
	public String dodaj() {
		tm.dodaj(trumna);
		return "trumny";
	}

	/*public String edytuj() {
		Trumna t = trumny.getRowData();
		tm.edytuj(t, trumna.getRodzaj(),
				trumna.getCena(), trumna.getIlosc());
		return null;
	}

	public String usun() {
		Trumna t = trumny.getRowData();
		tm.usun(t);
		return null;
	}*/
}

