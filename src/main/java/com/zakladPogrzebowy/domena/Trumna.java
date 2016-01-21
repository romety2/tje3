package com.zakladPogrzebowy.domena;

public class Trumna {
	
	private Long id;
	private String rodzaj = "";
	private Double cena = 0.0;
	private Integer ilosc = 0;

	public Trumna() {
	}

	public Trumna(String rodzaj, Double cena, Integer ilosc) {
	this.rodzaj = rodzaj;
	this.cena = cena;
	this.ilosc = ilosc;
	}
	
	public Long getId() {
		return id;
	}
	public void setId(Long id) {
		this.id = id;
	}

	public String getRodzaj() {
		return rodzaj;
	}
	public void setRodzaj(String rodzaj) {
		this.rodzaj = rodzaj;
	}

	public Double getCena() {
		return cena;
	}
	public void setCena(Double cena) {
		this.cena = cena;
	}

	public Integer getIlosc() {
		return ilosc;
	}
	public void setIlosc(Integer ilosc) {
		this.ilosc = ilosc;
	}
}
