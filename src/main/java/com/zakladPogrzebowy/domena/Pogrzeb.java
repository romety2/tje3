package com.zakladPogrzebowy.domena;

import java.util.Date;

public class Pogrzeb {

	private Long id;
	private Date data = new Date();
	private Double cena = 0.0;
	private String opis = "";

	 public Pogrzeb() {
	}

	public Pogrzeb(Date data, Double cena, String opis)
	{
	this.data = data;
	this.cena = cena;
	this.opis = opis;
	}

	public Long getId() {
		return id;
	}
	public void setId(Long id) {
		this.id = id;
	}
	
	public Date getData() {
		return data;
	}
	public void setData(Date data) {
		this.data = data;
	}

	public Double getCena() {
		return cena;
	}
	public void setCena(Double cena) {
		this.cena = cena;
	}

	public String getOpis() {
		return opis;
	}
	public void setOpis(String opis) {
		this.opis = opis;
	}
}
