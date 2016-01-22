package com.zakladPogrzebowy.domena;

public class Pogrzeb {

	private Long id;
	private String data = "rrrr-mm-dd";
	private Double cena = 0.0;
	private String opis = "";

	 public Pogrzeb() {
	}

	public Pogrzeb(String data, Double cena, String opis)
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
	
	public String getData() {
		return data;
	}
	public void setData(String data) {
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
