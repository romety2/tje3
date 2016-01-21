package com.zakladPogrzebowy.serwis;

import java.util.Date;
import java.util.List;
import java.util.ArrayList;

import javax.enterprise.context.ApplicationScoped;

import com.zakladPogrzebowy.domena.Pogrzeb;

@ApplicationScoped
public class PogrzebManager {

	private List<Pogrzeb> pogrzeby = new ArrayList<Pogrzeb>();

	public void dodaj(Pogrzeb pogrzeb) {
		Pogrzeb pg = new Pogrzeb();

		pg.setData(pogrzeb.getData());
		pg.setCena(pogrzeb.getCena());
		pg.setOpis(pogrzeb.getOpis());

		pogrzeby.add(pg);
	}

	public List<Pogrzeb> get() {
		return pogrzeby;
	}

}

