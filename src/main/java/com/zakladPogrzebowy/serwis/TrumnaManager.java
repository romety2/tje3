package com.zakladPogrzebowy.serwis;

import java.util.Date;
import java.util.List;
import java.util.ArrayList;

import javax.enterprise.context.ApplicationScoped;

import com.zakladPogrzebowy.domena.Trumna;

@ApplicationScoped
public class TrumnaManager {

	private List<Trumna> trumny = new ArrayList<Trumna>();

	public void dodaj(Trumna trumna) {
		Trumna tr = new Trumna();

		tr.setRodzaj(trumna.getRodzaj());
		tr.setCena(trumna.getCena());
		tr.setIlosc(trumna.getIlosc());

		trumny.add(tr);
	}

	public void usun(Trumna trumna) {

		trumny.remove(trumna);
	}

	public List<Trumna> dajWszystkie() {
		return trumny;
	}

}

