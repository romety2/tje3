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
@Named("trumnaBean")
public class SaleFormBean implements Serializable {

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
	
	public ListDataModel<Trumna> getTrumny() {
		trumny.setWrappedData(tm.dajWszystkie());
		return trumny;
	}

	public ListDataModel<Car> getOwnedCars() {
		ownedCars.setWrappedData(pm.getOwnedCars(personToShow));
		return ownedCars;
	}
	
	public String dodaj() {
		pm.dodaj(pogrzeb);
		return "Trumny";
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

