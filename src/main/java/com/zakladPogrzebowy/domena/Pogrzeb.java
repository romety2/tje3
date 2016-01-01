package com.zakladPogrzebowy.domena;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.persistence.CascadeType;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.validation.constraints.Min;
import javax.validation.constraints.Size;

@Entity
@NamedQueries({ 
	@NamedQuery(name = "pogrzeb.wszystkie", query = "Select p from Pogrzeb p")
})
public class Pogrzeb {

	private Long id;
 	private Trumna trumna;
	private Date data = new Date();
	private Double cena = 0.0;
	private String opis = "";

	 public Pogrzeb() {
	}

	public Pogrzeb(Trumna trumna, Date data, Double cena, String opis)
	{
	this.trumna = trumna;
	this.data = data;
	this.cena = cena;
	this.opis = opis;
	}

	@Id
	@GeneratedValue(strategy = GenerationType.AUTO)
	public Long getId() {
		return id;
	}
	public void setId(Long id) {
		this.id = id;
	}

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "id_religia", nullable = false)
	public Trumna getTrumna() {
	return trumna;
	}
	public void setTrumna(Trumna trumna) { this.trumna = trumna; }
	
	@Temporal(TemporalType.DATE)
	public Date getData() {
		return data;
	}
	public void setData(Date data) {
		this.data = data;
	}

	@Min(0)
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
